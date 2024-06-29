<!DOCTYPE html>
<html>
 <head>
  <title>PV_Ladeplanung</title>
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
/* RADIOBUTTON */
.wrapper{
  display: inline-flex;
  background: #fff;
  align-items: center;
  padding: 20px 15px;
  box-shadow: 5px 5px 30px rgba(0,0,0,0.2);
}
.wrapper .option{
  background: #fff;
  height: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-evenly;
  margin: 0 10px;
  border-radius: 5px;
  cursor: pointer;
  padding: 0 10px;
  border: 2px solid lightgrey;
  transition: all 0.3s ease;
}
.wrapper .option .dot{
  height: 20px;
  width: 20px;
  background: #d9d9d9;
  border-radius: 50%;
  position: relative;
}
.wrapper .option .dot::before{
  position: absolute;
  content: "";
  top: 4px;
  left: 4px;
  width: 12px;
  height: 12px;
  background: #44c767;
  border-radius: 50%;
  opacity: 0;
  transform: scale(1.5);
  transition: all 0.3s ease;
}
input[type="radio"]{
  display: none;
}
#auto:checked:checked ~ .auto,
#aus:checked:checked ~ .aus,
#halb:checked:checked ~ .halb,
#voll:checked:checked ~ .voll{
  border-color: #44c767;
  background: #44c767;
}
#auto:checked:checked ~ .auto .dot,
#aus:checked:checked ~ .aus .dot,
#halb:checked:checked ~ .halb .dot,
#voll:checked:checked ~ .voll .dot{
  background: #000;
}
#auto:checked:checked ~ .auto .dot::before,
#aus:checked:checked ~ .aus .dot::before,
#halb:checked:checked ~ .halb .dot::before,
#voll:checked:checked ~ .voll .dot::before{
  opacity: 1;
  transform: scale(1);
}
.wrapper .option span{
  font-family:Arial;
  font-size:130%;
  color: #808080;
}
.wrapper .beschriftung{
  font-family:Arial;
  font-size:150%;
  color: #000000;
}
#auto:checked:checked ~ .auto span,
#aus:checked:checked ~ .aus span,
#halb:checked:checked ~ .halb span,
#voll:checked:checked ~ .voll span{
  color: #000;
}
.hilfe{
  font-family:Arial;
  font-size:150%;
  color: #000000;
}

  </style>
 </head>

 <body>
  <div class="hilfe" align="right"> <a href="1_Hilfe.html"><b>Hilfe</b></a></div>
  <div class="container">
   <br />
  <div align="center"><button type="button" id="import_data" class="speichern">PV Ladeplanung ==&#62;&#62; speichern</button></div>
   <br />

<?php
include "config.php";
$Prognose = json_decode(file_get_contents($PrognoseFile), true);
$EV_Reservierung = json_decode(file_get_contents($ReservierungsFile), true);

//$ManuelleSteuerung_check = array('auto', 'aus', 'halb', 'voll');
$ManuelleSteuerung_check = array(
    "auto" => "",
    "aus" => "",
    "halb" => "",
    "voll" => "",
);

if (isset($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'])) {
if ($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'] == 0) $ManuelleSteuerung_check['auto'] = 'checked';
if ($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'] == 0.000001) $ManuelleSteuerung_check['aus'] = 'checked';
if ($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'] == 0.0005) $ManuelleSteuerung_check['halb'] = 'checked';
if ($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'] == 0.001) $ManuelleSteuerung_check['voll'] = 'checked';
} else {
$ManuelleSteuerung_check['auto'] = 'checked';
}
?>

<center>
<div class="wrapper">
<div class="beschriftung" title='Ladung des Hausakkus mit einem Anteil der konfigurierten "MaxLadung" 
                  (Auto= nach Prognose, AUS=0%, HALB=50%, VOLL=100%)'>
<nobr>Ladegrenze</nobr>
</div>
 <input type="radio" name="hausakkuladung" id="auto" value="0" <?php echo $ManuelleSteuerung_check['auto'] ?>>
 <input type="radio" name="hausakkuladung" id="aus" value="0.000001" <?php echo $ManuelleSteuerung_check['aus'] ?> >
 <input type="radio" name="hausakkuladung" id="halb" value="0.0005" <?php echo $ManuelleSteuerung_check['halb'] ?> >
 <input type="radio" name="hausakkuladung" id="voll" value="0.001" <?php echo $ManuelleSteuerung_check['voll'] ?> >
   <label for="auto" class="option auto">
     <div class="dot"></div>
      <span>&nbsp;AUTO</span>
      </label>
   <label for="aus" class="option aus">
     <div class="dot"></div>
      <span>&nbsp;AUS</span>
      </label>
   <label for="halb" class="option halb">
     <div class="dot"></div>
      <span>&nbsp;HALB</span>
   </label>
   <label for="voll" class="option voll">
     <div class="dot"></div>
      <span>&nbsp;VOLL</span>
   </label>
</div>
</center>
   <br />
   <div id="csv_file_data">

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
    $Res_Feld1_wert = (float) $EV_Reservierung[$date]['Res_Feld1'];
} else {
    $Res_Feld1_wert = 0;
}

if ($Res_Feld1_wert <> 0) {
$Res_Feld1_Watt = number_format($Res_Feld1_wert, 1);
} else  { 
$Res_Feld1_Watt = "" ;
}

if (isset($EV_Reservierung[$date]['Res_Feld2'])){
    $Res_Feld2_wert = (float) $EV_Reservierung[$date]['Res_Feld2'];
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
  <div align="center"><button type="button" id="import_data" class="speichern">PV Ladeplanung ==&#62;&#62; speichern</button></div>

<?php echo "</br>Prognose von $Prognose[messageCreated]"; ?> 
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
   Res_Feld1.push($(this).text().replace(",", "."));
  });
  $('.Res_Feld2').each(function(){
   Res_Feld2.push($(this).text().replace(",", "."));
  });
  const js = document.querySelectorAll('input[name="hausakkuladung"]');
  for(var i=0; i < js.length; i++){
        if(js[i].checked == true){
            js_value = js[i].value;
        }
    }
  if (js != "") {
  Tag_Zeit.push("ManuelleSteuerung");
  Res_Feld1.push(js_value);
  Res_Feld2.push(0);
  //alert (Tag_Zeit + "\n" + Res_Feld1 + "\n" + Res_Feld2);
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
 </body>
</html>
