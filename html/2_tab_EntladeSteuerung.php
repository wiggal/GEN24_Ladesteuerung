  <script src="jquery.min.js"></script>
  <style>
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
  }
  th, td {
  font-size: 200%;
  font-weight: normal;
  text-align: center;
  padding: 4px;
  }

  th, caption {
  background-color: #C1C0C0;
  font-weight: 700;
  }

  .speichern {
	background-color:#58ACFA;
	border-radius:28px;
	border:1px solid #58ACFA;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-size:200%;
	padding:16px 31px;
	text-decoration:none;
	text-shadow:0px 1px 0px #58ACFA;
    white-space: nowrap;
    position: fixed;
    transform: translate(-50%, 0);
  }
  .speichern:hover {
	background-color:#2E64FE;
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

label.slider {
	background-color:#58ACFA;
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
   accent-color: #58ACFA;
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

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
  th, td {
    font-size: 90%; /* Schrift auf Handys deutlich verkleinern */
  }

  .sliderbeschriftung{
    font-size:90%;
    margin-top: 25px !important; /* Abstand nach oben zum Button */
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
  table.center td,
  table.center th {
    white-space: normal;        /* Umbruch erlauben */
    word-wrap: break-word;      /* alte Browser */
    overflow-wrap: break-word;  /* moderne Browser */
  }
}
</style>

<!-- Hilfeaufruf ANFANG -->
<?php
  $hilfe_link = "index.php?tab=Hilfe&file={$activeTab}";
?>
  <div class="hilfe"> <a href="<?php echo $hilfe_link; ?>"><b>Hilfe</b></a></div>
<!-- Hilfeaufruf ENDE -->

  <div class="container">
  <div align="center"><button type="button" id="import_data" class="speichern">Entladesteuerung speichern</button></div>
   <br />

<?php
include 'SQL_steuerfunctions.php';
$Akku_EntLadung = getSteuercodes('ENTLadeStrg');

$DB_ManuelleEntladesteuerung_wert = 0;
if (isset($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1'])) {
    $DB_ManuelleEntladesteuerung_wert = $Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1'];
}

?>


<!-- SLIDER -->
<div style='text-align: center;'>
  <p class="sliderbeschriftung">Feste Entladegrenze:</p>
<div class="flex-container">
    <div>
<label class="slider" id="sliderlabel" for="slider"><?php echo $DB_ManuelleEntladesteuerung_wert ?>%</label>

    </div>
    <div style="flex-grow: 1">
<input class="slider" id="slider" name="hausakkuentladung" type="range" min="0" max="100" step="5" value="<?php echo $DB_ManuelleEntladesteuerung_wert ?>" oninput="sliderlabel.innerText = this.value + '%';">
    </div>
</div>
</div>
<!-- ENDE SLIDER -->

<br /><div id="csv_file_data">

<?php
echo "<table class=\"center\"><tbody><tr><th>Stunde</th><th style=\"display:none\" >Stunde zum Dateieintrag noetig, versteckt</th><th>Verbrauchs&shy;grenze Entladung(KW)</th><th>Feste Entladegrenze(KW)</th><th>Options</th></tr>";
echo "\n";

// Alle Stunden in Array
$Uhrzeiten= [];
$start_std = new DateTime();   // aktuelle Uhrzeit
$start_std->setTimezone(new DateTimeZone('Europe/Berlin'));
for ($i = 0; $i < 24; $i++) {
    $Uhrzeiten[] = $start_std->format('H').':00'; // nur Stunde extrahieren
    $start_std->modify('+1 hour');          // eine Stunde weiter
}

foreach($Uhrzeiten AS $date) {

$Res_Feld1_Watt = "";
$Res_Feld2_Watt = "";

if ($date == 'ManuelleEntladesteuerung') break;

if (isset($Akku_EntLadung[$date]['Res_Feld1']) and $Akku_EntLadung[$date]['Res_Feld1'] <> ""){
    $Res_Feld1_wert = (float) $Akku_EntLadung[$date]['Res_Feld1']/1000;
} else {
    $Res_Feld1_wert = 0;
}
if ($Res_Feld1_wert <> 0) {
$Res_Feld1_Watt = number_format($Res_Feld1_wert, 3);
} else  { 
$Res_Feld1_Watt = "" ;
}

if (isset($Akku_EntLadung[$date]['Res_Feld2']) and $Akku_EntLadung[$date]['Res_Feld2'] !== ""){
        # String nach ; aufteilen und formatieren
        $teile = explode(";", $Akku_EntLadung[$date]['Res_Feld2']);
        $ergebnisse = [];
        foreach ($teile as $wert) {
            if($wert == 0){
                $ergebnis = 0;
            }else{
                $ergebnis = $wert/1000;
                # Immer mindestens eine Nachkommastelle, auch wenn Null
                if (strpos($ergebnis, '.') === false) {
                    $ergebnis .= '.0';
                }
            }
            $ergebnisse[] = $ergebnis;
        }
        $Res_Feld2_Watt = implode(";", $ergebnisse);
        # damit es sowohl in php7 alsuch in php8 funktioniert
        if(is_numeric($Res_Feld2_Watt) && (float)$Res_Feld2_Watt == 0)$Res_Feld2_Watt = "";
}

if (isset($Akku_EntLadung[$date]['Options']) and $Akku_EntLadung[$date]['Options'] <> ""){
    $Options_wert = $Akku_EntLadung[$date]['Options'];
} else {
    $Options_wert = "";
}
# Zeilenumbruch für schmale Displays einfügen
# z.B.: -0.001;-0.001 => ; ersetzen durch ;<wbr>
$Res_Feld1_Watt = str_replace(';', ';<wbr>', $Res_Feld1_Watt);
$Res_Feld2_Watt = str_replace(';', ';<wbr>', $Res_Feld2_Watt);

echo '<tr><td style="white-space: nowrap;" bgcolor=#F1F3F4 class="Tag_Zeit_lesbar" contenteditable="false">';
echo $date;
echo '<td style="white-space: nowrap; display:none" class="Tag_Zeit" contenteditable="false">';
echo $date;
echo '</td><td bgcolor=#F1F3F4 class="Res_Feld1" contenteditable="true">';
echo $Res_Feld1_Watt;
echo '</td><td bgcolor=#F1F3F4 class="Res_Feld2" contenteditable="true">';
echo $Res_Feld2_Watt;
echo '<td style="white-space: nowrap;" bgcolor=#F1F3F4 class="Options" contenteditable="true">';
echo $Options_wert;
echo "</td></tr>\n";

} //foreach($Akku_EntLadung....

echo "</tbody></table>\n";
?>
   <br />
  </div>
  </div>

<script>

$(document).ready(function(){

 $(document).on('click', '#import_data', function(){
  var ID = [];
  var Schluessel = [];
  var Tag_Zeit = [];
  var Res_Feld1 = [];
  var Res_Feld2 = [];
  var Options = [];
  $('.Tag_Zeit').each(function(){
   ID.push($(this).text());
   Schluessel.push('ENTLadeStrg');
   Tag_Zeit.push($(this).text());
  });
  $('.Options').each(function(){
   Options.push($(this).text());
  });
  // Res_Feld1 darf nur Zahlen enthalten
  $('.Res_Feld1').each(function(){
    let val = parseFloat($(this).text().replace(",", ".")) * 1000;
    Res_Feld1.push(Number.isFinite(val) ? val : 0);
  });
  // Hier müssen evtl. viertelstündliche Werte aufgesplitet werden.
  $('.Res_Feld2').each(function() {
    let inputString = $(this).text()
    let teile = inputString.split(";");
    let ergebnisse = teile.map(wert => {
        let zahl = parseFloat(wert.replace(",", "."));
        return isNaN(zahl) ? 0 : Math.round(zahl * 1000);
    });

    let neuerString = ergebnisse.join(";");
    Res_Feld2.push(neuerString);
  });

  je_value = 0.001;
  const je = document.querySelectorAll('input[name="hausakkuentladung"]');
  je_value = je[0].value;

  if (je != "") {
  ID.push("23:58");
  Schluessel.push("ENTLadeStrg");
  Tag_Zeit.push("ManuelleEntladesteuerung");
  Res_Feld1.push(je_value);
  Res_Feld2.push(0);
  Options.push('');
  //alert (Tag_Zeit + "\n" + Res_Feld1 + "\n" + Res_Feld2);
  }

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
