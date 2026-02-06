  <script src="jquery.min.js"></script>
  <style>
  .box
  {
   max-width:600px;
   width:100%;
   margin: 0 auto;;
  }
  .center {
  margin-left: auto;
  margin-right: auto;
  }
  table, th, td, caption {
  border: thin solid #a0a0a0;
  }

  table {
  border-collapse: collapse;
  border-spacing: 0;
  border-width: thin 0 0 thin;
  margin: 0 0 1em;
  table-layout: auto;
  }
  th {
  position: sticky;
  top: 65px;
  z-index: 101; /* soll vor dem Button liegen */
  }
  th, td {
  font-size: 200%;
  font-weight: normal;
  text-align: right;
  padding: 4px;
  }
  th {
    text-align: center;
  }

  th, caption {
  background-color: #C1C0C0;
  font-weight: 700;
  }

  .speichern {
	background-color:#44c767;
	border-radius:28px;
	border:1px solid #18ab29;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-size:200%;
	padding:16px 31px;
	text-decoration:none;
	text-shadow:0px 1px 0px #2f6627;
    white-space: nowrap;
    position: fixed;
    transform: translate(-50%, 0);
    z-index: 100;  /* <-- sorgt dafür, dass der Button oben bleibt */
  }
  .speichern:hover {
	background-color:#5cbf2a;
  }
  .speichern:active {
	position:fixed;
  }

/* LADEGRENZBOX */
.flex-container {
  display: flex;
  width: 80%;
  max-width: 800px;
  margin: auto;
  background: #fff;
  align-items: center;
  padding: 5px 8px;
  box-shadow: 5px 5px 30px rgba(0,0,0,0.2);
}
.flex-container > div {
  background-color: #fff;
  margin: 5px;
  padding: 10px;
  font-size: 30px;
}
/* END LADEGRENZBOX */

/* CHECKBOX */
input[type="checkbox"] {
   position: relative;
   width: 20px;
   height: 25px;
   top: +.5em;
   accent-color: #44c767;
}
.dropdown {
  font-size: 2rem;
  line-height: 1.4;
  display: grid;
  justify-items: left;
  grid-template-columns: 1.3em auto;
}

/* ENDE CHECKBOX */

label.slider {
	background-color:#44c767;
	border-radius:10px;
	border:1px solid #18ab29;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-size:90%;
	padding:5px 10px;
	text-decoration:none;
	text-shadow:0px 1px 0px #2f6627;
    flex-shrink: 0;
  }
input.slider {
   width: 100%;
   height: 35px;
   accent-color: #44c767;
  }

.sliderbeschriftung{
  font-weight: bold;
  font-size:120%;
  color: #000000;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin-top: 50px !important; /* Abstand nach oben zum Button */
  margin-bottom: 10px !important; /* Abstand nach unten zum Slider */
}
.checkbox-wrap {
  white-space: nowrap;
}
.prognosevon{
  position: fixed;
  top: 8px;
  left: 0px;
}
.gueltig {
  font-weight: normal;
  color: #555;
  font-size: 90%;
}

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
  .gueltig {
    width: 100%;
    display: block;
  }

  th, td {
    font-size: 90%; /* Schrift auf Handys deutlich verkleinern */
  }

  .sliderbeschriftung{
    font-size:90%;
    margin-top: 15px !important; /* Abstand nach oben zum Button */
    margin-bottom: 10px !important; /* Abstand nach unten zum Slider */
  }

  .flex-container {
    width: 95% !important; /* Container fast volle Breite */
    padding: 5px 2px !important;
  }

  .flex-container > div {
    margin: 2px !important;      /* Abstand zwischen den Elementen im Block verringern */
    padding: 2px !important;     /* Inneres Padding der Divs verringern */
    font-size: 18px !important; /* Slider-Beschriftung kleiner */
  }

  .speichern {
    font-size: 100% !important; /* Speicher-Button verkleinern */
    padding: 8px 10px !important;
  }

  .dropdown {
    font-size: 1.2rem !important; /* Dropdown kleiner */
  }

  /* Tabelle zwingen, in die Breite zu passen */
  table.center {
    width: 90% !important;
    display: table; /* Stellt sicher, dass sie sich wie eine Tabelle verhält */
  }
}
</style>

<div class="weatherDataManager"> <a href="index.php?tab=WeatherMgr&file=<?php echo $activeTab; ?>"><b>FcastMgr</b></a></div>
<!-- Hilfeaufruf ANFANG -->
<?php
  $hilfe_link = "index.php?tab=Hilfe&file={$activeTab}";
?>
  <div class="hilfe"> <a href="<?php echo $hilfe_link; ?>"><b>Hilfe</b></a></div>
<!-- Hilfeaufruf ENDE -->
  <div align="center"><button type="button" id="import_data" class="speichern">Ladesteuerung speichern</button></div>
  <br />

<?php
# config.ini parsen
require_once "config_parser.php";

include 'SQL_steuerfunctions.php';
$EV_Reservierung = getSteuercodes('Reservierung');
$PrstLadeStd = getPrstLadeStd();
$Prognose = getPrognose();

$Res_Feld1 = 'einmal';
$Res_Feld2 = 'laufend';
$DB_ManuelleSteuerung_wert = 0;
$DB_Auto_selected = '';
$DB_Slider_selected = '';
$DB_MaxLadung_selected = '';
$Akkuschon_check = '';
# Prüfen, ob Einträge für ManuelleSteuerung schon abgelaufen
date_default_timezone_set('Europe/Berlin');
# Wenn Feld in DB keine Zahl
if (!is_numeric($EV_Reservierung['ManuelleSteuerung']['Options'])){
    $EV_Reservierung['ManuelleSteuerung']['Options'] = 0;
}
# Akkuschonung aus DB
if (isset($EV_Reservierung['ManuelleSteuerung']['Res_Feld2']) and ($EV_Reservierung['ManuelleSteuerung']['Res_Feld2']) == 1) {
    $Akkuschon_check = 'checked';
}
if ($EV_Reservierung['ManuelleSteuerung']['Options'] < time() OR $EV_Reservierung['ManuelleSteuerung']['Res_Feld1'] == -1) {
    $EV_Reservierung['ManuelleSteuerung']['Res_Feld1'] = -1;
    $gueltig_bis = '';
    $Akkuschon_check = '';
    } else {
    $gueltig_bis = "&nbsp;gültig bis " . date("Y-m-d H:i", $EV_Reservierung['ManuelleSteuerung']['Options']);
    }
$std_diff = ($EV_Reservierung['ManuelleSteuerung']['Options'] - time())/3600;
$std_diff = ($std_diff <= 0) ? 24 : round($std_diff,2);
if (isset($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'])) {
    $DB_ManuelleSteuerung_wert = $EV_Reservierung['ManuelleSteuerung']['Res_Feld1'];

    if ($DB_ManuelleSteuerung_wert == -1){
    $DB_ManuelleSteuerung_wert = 0;
    $DB_Auto_selected = 'selected';
    } elseif ($DB_ManuelleSteuerung_wert == -2) {
    $DB_ManuelleSteuerung_wert = 0;
    $DB_MaxLadung_selected = 'selected';
    } else {
    $DB_Slider_selected = 'selected';
    }
}
?>

<!-- SLIDER -->
<div style='text-align: center;'>
  <p class="sliderbeschriftung">Ladegrenze mit Akkuschonung: 
  <span class="checkbox-wrap">
  <input type="checkbox" name="akkuschonung"  <?php echo $Akkuschon_check ?>>
  </span>
  <span class="gueltig" ><?php echo $gueltig_bis ?></span></p>
<div class="flex-container">
    <div>
      <label for="modus" class="dropdown" ></label>
  <select id="modus" class="dropdown" name="hausakkuladung" >
    <option value="Auto" <?php echo $DB_Auto_selected ?>>Auto</option>
    <option value="Slider" <?php echo $DB_Slider_selected ?>>Slider</option>
    <option value="MaxLadung" <?php echo $DB_MaxLadung_selected ?>>MaxLadung</option>
  </select>
</div>
    <div>
<label class="slider" id="sliderlabel" for="slider"><?php echo $DB_ManuelleSteuerung_wert ?>%</label>

    </div>
    <div style="flex-grow: 1">
<input class="slider" id="slider" name="hausakkuladung" type="range" min="0" max="100" step="5" value="<?php echo $DB_ManuelleSteuerung_wert ?>" oninput="sliderlabel.innerText = this.value + '%';">
    </div>
</div>
</div>
<!-- ENDE SLIDER -->

<br /> <div id="csv_file_data">

<?php
echo "<table class=\"center\"><tbody><tr><th>Tag und Zeit</th><th style=\"display:none\" >Tag,Zeit zum Dateieintrag noetig, versteckt</th><th>Prognose(KW)</th><th>Rest</th><th>$Res_Feld1</th><th>$Res_Feld2</th></tr>";
echo "\n";

// Variablen definieren
$Prognosewert_Sum = 0;
$Rest_KW_Sum = 0;
$Res_Feld1_Watt_Sum = 0;
$Res_Feld2_Watt_Sum = 0;
$Prognosewert = 0;
$Rest_KW = 0;
$Res_Feld1_Watt = 0;
$Res_Feld2_Watt = 0;
// Variablen definieren ENDE


foreach($Prognose['result']['watts'] AS $date => $Watt) {

// Summenbildung
$Prognosewert_Sum = number_format($Prognosewert_Sum + $Prognosewert,1);
$Rest_KW_Sum = number_format($Rest_KW_Sum + (float) $Rest_KW,1);
$Res_Feld1_Watt_Sum = number_format($Res_Feld1_Watt_Sum + (float) $Res_Feld1_Watt,1);
$Res_Feld2_Watt_Sum = number_format($Res_Feld2_Watt_Sum + (float) $Res_Feld2_Watt,1);
// Stunde aus $date extrahieren
$stunde = date('H:00:00', strtotime($date));
$datum = date('Y-m-d', strtotime($date));
$heute = date('Y-m-d');
# Wenn  Res_Feld2 = 'laufend' gesetzt dann zuweisen
if (isset($PrstLadeStd[$stunde]) and $datum == $heute) {
    if ($PrstLadeStd[$stunde]['Res_Feld2'] !== '0') $EV_Reservierung[$date]['Res_Feld2'] = $PrstLadeStd[$stunde]['Res_Feld2'];
}
if (isset($EV_Reservierung[$date]['Res_Feld1'])){
    $Res_Feld1_wert = (float) $EV_Reservierung[$date]['Res_Feld1']/1000;
} else {
    $Res_Feld1_wert = 0;
}

if ($Res_Feld1_wert <> 0) {
$Res_Feld1_Watt = number_format($Res_Feld1_wert, 1);
} else  { 
$Res_Feld1_Watt = "" ;
}

if (isset($EV_Reservierung[$date]['Res_Feld2'])){
    $Res_Feld2_wert = (float) $EV_Reservierung[$date]['Res_Feld2']/1000;
} else {
    $Res_Feld2_wert = 0;
}
if ($Res_Feld2_wert <> 0) {
$Res_Feld2_Watt = number_format($Res_Feld2_wert, 1);
} else  { 
$Res_Feld2_Watt = "" ;
}
$Prognosewert =number_format($Watt/1000, 1);
$Rest_KW = number_format($Prognosewert - (float) $Res_Feld2_Watt - (float) $Res_Feld1_Watt, 1);

// Hintergrund heute bzw. morgen 
$Tag_akt_Schl = substr($date,0,10);
$Tag_heute = date("Y-m-d");
$Hintergrund_Tag = '#FFFFFF';
if ($Tag_akt_Schl != $Tag_heute) $Hintergrund_Tag = '#F1F3F4';

// Hintergrund Rest
if ($Rest_KW >= 0) {
$Hintergrund_Rest = '#CCFFCC';
} else {
$Hintergrund_Rest = '#ff9090';
}
// Prognose in % von $PV_Leistung_KWp
$ProgProzent = $Prognosewert / $PV_Leistung_KWp * 100;

// Ausgabe der Summen
if (isset($Tag_vor_Schl) and $Tag_akt_Schl != $Tag_vor_Schl) {
echo "<tr bgcolor=#C1C0C0><td>Summen: </td><td style=\"display:none\" >Tag,Zeit zum Dateieintrag noetig, versteckt</td><td>$Prognosewert_Sum</td><td>$Rest_KW_Sum</td><td>$Res_Feld1_Watt_Sum</td><td>$Res_Feld2_Watt_Sum</td></tr>\n";
$Prognosewert_Sum = 0;
$Rest_KW_Sum = 0;
$Res_Feld1_Watt_Sum = 0;
$Res_Feld2_Watt_Sum = 0;
}

$Tag_vor_Schl = $Tag_akt_Schl;
# Wochentag in Deutsch ausgeben
$wochentage = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
$timestamp = strtotime($date);
$tagIndex = date('w', $timestamp); // 0 (So) bis 6 (Sa)

echo '<tr><td style="white-space: nowrap; text-align: left;" bgcolor='.$Hintergrund_Tag.' class="Tag_Zeit_lesbar" contenteditable="false">';
echo $wochentage[$tagIndex] . ' ' . date('d.m. H:i', $timestamp);
echo '</td><td style="white-space: nowrap; display:none" class="Tag_Zeit" contenteditable="false">';
echo $date;
echo '</td><td style="background: linear-gradient(90deg,  #ff5733 '.$ProgProzent.'%, '.$Hintergrund_Tag.' 0%)" class="Prognose" contenteditable="false">';
echo $Prognosewert;
echo '</td><td bgcolor='.$Hintergrund_Rest.' class="Rest" contenteditable="false">';
echo $Rest_KW;
echo '</td><td bgcolor='.$Hintergrund_Tag.' class="Res_Feld1" contenteditable="true">';
echo $Res_Feld1_Watt;
echo '</td><td bgcolor='.$Hintergrund_Tag.' class="Res_Feld2" contenteditable="true">';
echo $Res_Feld2_Watt;
echo "</td></tr>\n";

} //foreach($Prognose....

echo "<tr bgcolor=#C1C0C0><td>Summen: </td><td style=\"display:none\" >Tag,Zeit zum Dateieintrag noetig, versteckt</td><td>$Prognosewert_Sum</td><td>$Rest_KW_Sum</td><td>$Res_Feld1_Watt_Sum</td><td>$Res_Feld2_Watt_Sum</td></tr>";
echo "</tbody></table>\n";
?>
   <br />
  </div>
<script>
/* den Slider beim Seitenaufbau auf dem Wert des Labels sezen */
  document.addEventListener('DOMContentLoaded', function () {
    //const slider = document.getElementById('slider');
    const sliderlabel = document.getElementById('sliderlabel');
    // Label-Wert lesen  Slider setzen
    const labelValue = parseInt(sliderlabel.innerText.replace('%', ''), 10);
    // Wert auf Slider übertragen
    slider.value = labelValue;
  });

/* Lesen und speichern der Daten */
$(document).ready(function(){

 $(document).on('click', '#import_data', function(){
  var ID = [];
  var tagzahler = 0;
  var tag_old = 0;
  var Schluessel = [];
  var Tag_Zeit = [];
  var Res_Feld1 = [];
  var Res_Feld2 = [];
  var Options = [];
  $('.Tag_Zeit').each(function(){
   var datum = new Date($(this).text());
    if (tag_old != datum.getDate()) {
        tagzahler++;
        tag_old = datum.getDate();
    }
   var std = String(tagzahler) + "-" + (String(datum.getHours()).padStart(2, "0") + ":" + String(datum.getMinutes()).padStart(2, "0"));
   ID.push(std);
   Schluessel.push('Reservierung');
   Options.push('');
   Tag_Zeit.push($(this).text());
  });
  // Nur Zahlen in den Feldern Res_Feldx erlauben
  $('.Res_Feld1').each(function(){
    let val = parseFloat($(this).text().replace(",", ".")) * 1000;
    Res_Feld1.push(Number.isFinite(val) ? val : 0);
  });
  $('.Res_Feld2').each(function(){
    let val = parseFloat($(this).text().replace(",", ".")) * 1000;
    Res_Feld2.push(Number.isFinite(val) ? val : 0);
  });

  const modus = document.querySelector('select[name="hausakkuladung"]').value;
  let js_value = -1;
  let hours = 0;
  let std_diff = <?php echo $std_diff; ?>;

  if (modus == "Auto") {
      js_value = -1;
    } else if (modus == "MaxLadung" || modus == "Slider") {
      let input = prompt(`Bitte gib die Gültigkeitsstunden für "${modus}" ein:`, std_diff);
      if (input === null) {
        // Nutzer hat auf Abbrechen geklickt -> Funktion beenden
        return;
        }
      // Wenn Buchstaben eingegeben werden, hours = 0
      let trimmed = input.trim();
      let parsed = parseFloat(trimmed);
      if (trimmed !== "" && !isNaN(parsed) && parsed >= 0 && parsed <= 100) {
            hours = parsed;
        } else {
            hours = 0;
        }
      js_value = (modus === "MaxLadung") ? -2 : parseInt(document.querySelector('input[name="hausakkuladung"]').value);
    }

  // Akkuschonung auslesen
  let as_modus = 0;
    if (document.querySelector('input[name="akkuschonung"]').checked) {
    as_modus = 1;
  }

  ID.push("23:59");
  Schluessel.push("Reservierung");
  Tag_Zeit.push("ManuelleSteuerung");
  Res_Feld1.push(js_value);
  Res_Feld2.push(as_modus);
  Options.push(Math.floor(Date.now() / 1000) + hours * 3600);
  //alert(js_value);

  $.ajax({
   url:"SQL_speichern.php",
   method:"post",
   data:{ID:ID, Schluessel:Schluessel, Tag_Zeit:Tag_Zeit, Res_Feld1:Res_Feld1, Res_Feld2:Res_Feld2, Options:Options},
   success:function(data)
   {
    //alert(data);
    window.location.href = "index.php?tab=<?php echo $activeTab; ?>";
   }
  })
 });
});
</script>
