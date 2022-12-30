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
  </style>
 </head>

 <body>
  <div class="container">
   <br />
  <div align="center"><button type="button" id="import_data" class="speichern">PV Planung ==&#62;&#62; speichern</button></div>
   <br />
   <div id="csv_file_data">
<?php
include "config.php";
$Prognose = json_decode(file_get_contents($PrognoseFile), true);
$EV_Reservierung = json_decode(file_get_contents($ReservierungsFile), true);
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
// Prognose in % von 11.4 KWp
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
  $.ajax({
   url:"speichern.php",
   method:"post",
   data:{Tag_Zeit:Tag_Zeit, Res_Feld1:Res_Feld1, Res_Feld2:Res_Feld2},
   success:function(data)
   {
    location.reload();
    //$('#csv_file_data').html('<div class="alert alert-success">Daten erfolgreich gespeichert!</div>');
   }
  })
 });
});
</script>
