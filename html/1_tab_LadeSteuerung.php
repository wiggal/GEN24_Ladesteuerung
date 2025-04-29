<!DOCTYPE html>
<html>
 <head>
  <title>PV_Ladeplanung</title>
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
  font-family: Arial, Helvetica, sans-serif;
  border-collapse: collapse;
  border-spacing: 0;
  border-width: thin 0 0 thin;
  margin: 0 0 1em;
  table-layout: auto;
  }
  th, td {
  font-size: 200%;
  font-weight: normal;
  text-align: right;
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
	font-family:Arial;
	font-size:200%;
	padding:16px 31px;
	text-decoration:none;
	text-shadow:0px 1px 0px #2f6627;
    white-space: nowrap;
    position: fixed;
    top: 0;
    transform: translate(-50%, 0);
  }
  .speichern:hover {
	background-color:#5cbf2a;
  }
  .speichern:active {
	position:fixed;
	top:1px;
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
   width: 30px;
   height: 35px;
   accent-color: #44c767;
}
.checkboxlabel {
  font-family: system-ui, sans-serif;
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
	font-family:Arial;
	font-size:100%;
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

.hilfe{
  font-family:Arial;
  font-size:150%;
  color: #000000;
  position: fixed;
  right: 8px;
}
.sliderbeschriftung{
  font-family:Arial;
  font-weight: bold;
  font-size:120%;
  color: #000000;
}
.prognosevon{
  position: fixed;
  top: 8px;
  left: 0px;
}

  </style>
 </head>

 <body>
  <div class="hilfe"> <a href="1_Hilfe.html"><b>Hilfe</b></a></div>
   <br />
  <div align="center"><button type="button" id="import_data" class="speichern">PV Ladeplanung ==&#62;&#62; speichern</button></div>
   <br />
   <br />

<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}
$Prognose = json_decode(file_get_contents($PrognoseFile), true);
$date = new DateTime($Prognose['messageCreated']);
$erzeugt_um = $date->format('d.m. \u\m H:i');
echo "<div class=\"prognosevon\">$Prognose[createdfrom] $erzeugt_um</div>"; 
include 'SQL_steuerfunctions.php';
$EV_Reservierung = getSteuercodes('Reservierung');

$DB_ManuelleSteuerung_wert = 0;
$DB_ManuelleSteuerung_check = '';

if (isset($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'])) {
    $DB_ManuelleSteuerung_wert = $EV_Reservierung['ManuelleSteuerung']['Res_Feld1'];

    if ($DB_ManuelleSteuerung_wert == -1){
    $DB_ManuelleSteuerung_wert = 0;
    $DB_ManuelleSteuerung_check = 'checked';
    }
}
?>

<!-- SLIDER -->
<div style='text-align: center;'>
  <p class="sliderbeschriftung">Ladegrenze:</p>
<div class="flex-container">
    <div>
    <label class="checkboxlabel" ><input type="checkbox" name="hausakkuladung" value="-1" id="auto" <?php echo $DB_ManuelleSteuerung_check ?>>AUTO</label>
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
$Prognosewert =number_format($Watt/1000*$Faktor_PVLeistung_Prognose, 1);
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

echo '<tr><td style="white-space: nowrap;" bgcolor='.$Hintergrund_Tag.' class="Tag_Zeit_lesbar" contenteditable="false">';
echo date('d.m. H:i',strtotime($date));
echo '<td style="white-space: nowrap; display:none" class="Tag_Zeit" contenteditable="false">';
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
  $('.Res_Feld1').each(function(){
   Res_Feld1.push($(this).text().replace(",", ".")*1000);
  });
  $('.Res_Feld2').each(function(){
   Res_Feld2.push($(this).text().replace(",", ".")*1000);
  });
  const js = document.querySelectorAll('input[name="hausakkuladung"]');
  if(js[0].checked == true){
      js_value = js[0].value;
  } else {
      // wenn AUTO nicht gechecked slider lesen
      js_value = js[1].value;
  }

  if (js != "") {
  ID.push("23:59");
  Schluessel.push("Reservierung");
  Tag_Zeit.push("ManuelleSteuerung");
  Res_Feld1.push(js_value);
  Res_Feld2.push(0);
  Options.push('');
  //alert(js_value);
  }

  $.ajax({
   url:"SQL_speichern.php",
   method:"post",
   data:{ID:ID, Schluessel:Schluessel, Tag_Zeit:Tag_Zeit, Res_Feld1:Res_Feld1, Res_Feld2:Res_Feld2, Options:Options},
   success:function(data)
   {
    //alert(data);
    window.location.reload();
   }
  })
 });
});
</script>
 </body>
</html>
