<!DOCTYPE html>
<html>
 <head>
  <title>PV_Planung</title>
  <script src="jquery.min.js"></script>
    <!--
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.0/jquery.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js"></script>
  //-->
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
  /*
  font-size: calc(6px + (20 - 6) * (100vw - 400px) / (800 - 400));
  */
  font-size: 200%;
  font-weight: normal;
  text-align: right;
  }

  th, caption {
  background-color: #C1C0C0;
  font-weight: 700;
  }

  /* 3. und 4. Spalte zentriert 
  td:nth-of-type(3), td:nth-of-type(5), td:nth-of-type(6) {
  text-align: right;
  }
  */

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
  }
  .speichern:hover {
	background-color:#5cbf2a;
  }
  .speichern:active {
	position:relative;
	top:1px;
  }
  form.example {
  /*
  width: 100%;
  float: left;
  border:1px dotted red;
  box-sizing: border-box;
  margin: 15px 0;
  */
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px;
}
  [type="checkbox"] {
  position: relative;
  left: 30px;
  top: 0px;
  z-index: 0;
  -webkit-appearance: none;
}
[type="checkbox"] + label {
  position: relative;
  display: block;
  cursor: pointer;
  font-family: sans-serif;
  font-size: 24px;
  line-height: 1.3;
  padding-left:70px;
  position: relative;
  margin-top: -30px;
}
[type="checkbox"] + label:before {
  width: 60px;
  height: 30px;
  border-radius: 30px;
  border: 2px solid #ddd;
  background-color: #EEE;
  content: "";
  margin-right: 15px;
  transition: background-color 0.5s linear;
  z-index: 5;
  position: absolute;
  left: 0px;
}
[type="checkbox"] + label:after {
  width: 30px;
  height: 30px;
  border-radius: 30px;
  background-color: #fff;
  content: "";
  transition: margin 0.1s linear;
  box-shadow: 0px 0px 5px #aaa;
  position: absolute;
  left: 2px;
  top: 2px;
  z-index: 10;
}
[type="checkbox"]:checked + label:before {
  background-color: #44c767;
}
[type="checkbox"]:checked + label:after {
  margin: 0 0 0 30px;
}
  </style>
 </head>

 <body>
 <div  style="position:absolute; right:5%; top:3px;">
 <input type=button onClick="location.href='hilfe.html'" value='Hilfeseite' ></div>

  <div class="container">
   <br />
  <div align="center"><button type="button" id="import_data" class="speichern">PV Planung ==&#62;&#62; speichern</button></div>
   <br />

   <br />
   <div id="csv_file_data">
<?php
include "config.php";
$Prognose = json_decode(file_get_contents($PrognoseFile), true);
$EV_Reservierung = json_decode(file_get_contents($ReservierungsFile), true);

$VollePulle_check = '';
if (!isset($EV_Reservierung['VollePulle']['Res_Feld1'])) $EV_Reservierung['VollePulle']['Res_Feld1'] ='';
// echo $EV_Reservierung['VollePulle']['Res_Feld1'];
if ($EV_Reservierung['VollePulle']['Res_Feld1'] == 1) $VollePulle_check = 'checked';
echo "<form class=\"example\"><input type=\"checkbox\" id=\"VollePulle\" $VollePulle_check>";
echo "<label for=\"VollePulle\"> Hausakku mit voller Kapazität laden!!</label>";
echo "</form><br>";

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

if (isset($EV_Reservierung[$date]['Res_Feld1'])) $Res_Feld1_wert = (float) $EV_Reservierung[$date]['Res_Feld1'];
if ($Res_Feld1_wert <> 0) {
$Res_Feld1_Watt = number_format($Res_Feld1_wert, 1);
} else  { 
$Res_Feld1_Watt = "" ;
}
if (isset($EV_Reservierung[$date]['Res_Feld2'])) $Res_Feld2_wert = (float) $EV_Reservierung[$date]['Res_Feld2'];
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
echo "<tr bgcolor=#C1C0C0><td>Summen: </td><td style=\"display:none\" >Tag,Zeit zum Dateieintrag noetig, versteckt</td><td>$Prognosewert_Sum</td><td>$Rest_KW_Sum</td><td>$Res_Feld1_Watt_Sum</td><td>$Res_Feld2_Watt_Sum</td></tr>";
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
  <div align="center"><button type="button" id="import_data" class="speichern">PV Planung ==&#62;&#62; speichern</button></div>
 </body>
</html>

<script>

$(document).ready(function(){

 $(document).on('click', '#import_data', function(){
  var Tag_Zeit = [];
  var Res_Feld1 = [];
  var Res_Feld2 = [];
  $('.Tag_Zeit').each(function(){
   Tag_Zeit.push($(this).text());
  });
  $('.Res_Feld1').each(function(){
   Res_Feld1.push($(this).text());
  });
  $('.Res_Feld2').each(function(){
   Res_Feld2.push($(this).text());
  });
  const js = document.querySelector('#VollePulle');
  if (js.checked) {
  Tag_Zeit.push("VollePulle");
  Res_Feld1.push(1);
  Res_Feld2.push(1);
  // alert (Tag_Zeit + "\n" + Res_Feld1 + "\n" + Res_Feld2);
  }

  $.ajax({
   url:"speichern.php",
   method:"post",
   data:{Tag_Zeit:Tag_Zeit, Res_Feld1:Res_Feld1, Res_Feld2:Res_Feld2},
   success:function(data)
   {
    location.reload();
   }
  })
 });
});
</script>
