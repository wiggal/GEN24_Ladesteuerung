<!DOCTYPE html>
<html>
 <head>
  <title>Akku Entladesteuerung</title>
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
  font-size: 200%;
  font-weight: normal;
  text-align: center;
  padding: .2em .2em;
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
	background-color:#2E64FE;
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
	background-color:#58ACFA;
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
  background: #2E64FE;
  border-radius: 50%;
  opacity: 0;
  transform: scale(1.5);
  transition: all 0.3s ease;
}
input[type="radio"]{
  display: none;
}
#E0:checked:checked ~ .E0,
#E20:checked:checked ~ .E20,
#E40:checked:checked ~ .E40,
#E60:checked:checked ~ .E60,
#E80:checked:checked ~ .E80,
#E100:checked:checked ~ .E100{
  border-color: #2E64FE;
  background: #2E64FE;
}
#E0:checked:checked ~ .E0 .dot,
#E20:checked:checked ~ .E20 .dot,
#E40:checked:checked ~ .E40 .dot,
#E60:checked:checked ~ .E60 .dot,
#E80:checked:checked ~ .E80 .dot,
#E100:checked:checked ~ .E100 .dot{
  background: #000;
}
#E0:checked:checked ~ .E0 .dot::before,
#E20:checked:checked ~ .E20 .dot::before,
#E40:checked:checked ~ .E40 .dot::before,
#E60:checked:checked ~ .E60 .dot::before,
#E80:checked:checked ~ .E80 .dot::before,
#E100:checked:checked ~ .E100 .dot::before{
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
#E0:checked:checked ~ .E0 span,
#E20:checked:checked ~ .E20 span,
#E40:checked:checked ~ .E40 span,
#E60:checked:checked ~ .E60 span,
#E80:checked:checked ~ .E80 span,
#E100:checked:checked ~ .E100 span{
  color: #000;
}

  </style>
 </head>

 <body>
  <div class="container">
   <br />
  <div align="center"><button type="button" id="import_data" class="speichern">Akku Entladesteuerung ==&#62;&#62; speichern</button></div>
   <br />

<?php
include "config.php";
$Akku_EntLadung = json_decode(file_get_contents($EntLadeSteuerFile), true);

//$ManuelleSteuerung_check = array('E0', 'E20', 'E40', 'E60', 'E80', 'E100');
$ManuelleSteuerung_check = array(
    "E0" => "",
    "E20" => "",
    "E40" => "",
    "E60" => "",
    "E80" => "",
    "E100" => "",
);

if (isset($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1'])) {
if ($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1']/1000 == 0) $ManuelleSteuerung_check['E0'] = 'checked';
if ($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1']/1000 == 0.02) $ManuelleSteuerung_check['E20'] = 'checked';
if ($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1']/1000 == 0.04) $ManuelleSteuerung_check['E40'] = 'checked';
if ($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1']/1000 == 0.06) $ManuelleSteuerung_check['E60'] = 'checked';
if ($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1']/1000 == 0.08) $ManuelleSteuerung_check['E80'] = 'checked';
if ($Akku_EntLadung['ManuelleEntladesteuerung']['Res_Feld1']/1000 == 0.1) $ManuelleSteuerung_check['E100'] = 'checked';
} else {
$ManuelleSteuerung_check['E100'] = 'checked';
}
?>

<center>
<div class="wrapper">
<div class="beschriftung" title="Entladung des Hausakkus in Prozent der WR-Leistung">
<nobr>Feste Entladegrenze %</nobr>
</div>
 <input type="radio" name="hausakkuentladung" id="E0" value="0" <?php echo $ManuelleSteuerung_check['E0'] ?>>
 <input type="radio" name="hausakkuentladung" id="E20" value="0.02" <?php echo $ManuelleSteuerung_check['E20'] ?> >
 <input type="radio" name="hausakkuentladung" id="E40" value="0.04" <?php echo $ManuelleSteuerung_check['E40'] ?> >
 <input type="radio" name="hausakkuentladung" id="E60" value="0.06" <?php echo $ManuelleSteuerung_check['E60'] ?> >
 <input type="radio" name="hausakkuentladung" id="E80" value="0.08" <?php echo $ManuelleSteuerung_check['E80'] ?> >
 <input type="radio" name="hausakkuentladung" id="E100" value="0.1" <?php echo $ManuelleSteuerung_check['E100'] ?> >
   <label for="E0" class="option E0">
     <div class="dot"></div>
      <span>&nbsp;0</span>
      </label>
   <label for="E20" class="option E20">
     <div class="dot"></div>
      <span>&nbsp;20</span>
      </label>
   <label for="E40" class="option E40">
     <div class="dot"></div>
      <span>&nbsp;40</span>
   </label>
   <label for="E60" class="option E60">
     <div class="dot"></div>
      <span>&nbsp;60</span>
   </label>
   <label for="E80" class="option E80">
     <div class="dot"></div>
      <span>&nbsp;80</span>
   </label>
   <label for="E100" class="option E100">
     <div class="dot"></div>
      <span>&nbsp;100</span>
   </label>
</div>
</center>
   <br />
   <div id="csv_file_data">

<?php
echo "<table class=\"center\"><tbody><tr><th>Stunde</th><th style=\"display:none\" >Stunde zum Dateieintrag noetig, versteckt</th><th>Verbrauchsgrenze Entladung(KW)</th><th>Feste Entladegrenze(KW)</th></tr>";
echo "\n";

// Variablen definieren
$Rest_KW = 0;
$Res_Feld1_Watt = 0;
$Res_Feld2_Watt = 0;
// Variablen definieren ENDE


foreach($Akku_EntLadung AS $date => $Watt) {

if ($date == 'ManuelleEntladesteuerung') break;

if (isset($Watt['Res_Feld1']) and $Watt['Res_Feld1'] <> ""){
    $Res_Feld1_wert = (float) $Watt['Res_Feld1']/1000;
} else {
    $Res_Feld1_wert = 0;
}
if ($Res_Feld1_wert <> 0) {
$Res_Feld1_Watt = number_format($Res_Feld1_wert, 1);
} else  { 
$Res_Feld1_Watt = "" ;
}

if (isset($Watt['Res_Feld2']) and $Watt['Res_Feld2'] <> ""){
    $Res_Feld2_wert = (float) $Watt['Res_Feld2']/1000;
} else {
    $Res_Feld2_wert = 0;
}
if ($Res_Feld2_wert <> 0) {
$Res_Feld2_Watt = number_format($Res_Feld2_wert, 1);
} else  { 
$Res_Feld2_Watt = "" ;
}

echo '<tr><td style="white-space: nowrap;" bgcolor=#F1F3F4 class="Tag_Zeit_lesbar" contenteditable="false">';
echo $date;
echo '<td style="white-space: nowrap; display:none" class="Tag_Zeit" contenteditable="false">';
echo $date;
echo '</td><td bgcolor=#F1F3F4 class="Res_Feld1" contenteditable="true">';
echo $Res_Feld1_Watt;
echo '</td><td bgcolor=#F1F3F4 class="Res_Feld2" contenteditable="true">';
echo $Res_Feld2_Watt;
echo "</td></tr>\n";

} //foreach($Prognose....

echo "</tbody></table>\n";
?>
   <br />
  </div>
  <div align="center"><button type="button" id="import_data" class="speichern">Akku Entladesteuerung ==&#62;&#62; speichern</button></div>
  </div>

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
  je_value = 0.1;
  const je = document.querySelectorAll('input[name="hausakkuentladung"]');
  for(var i=0; i < je.length; i++){
        if(je[i].checked == true){
            je_value = je[i].value;
        }
    }
  if (je != "") {
  Tag_Zeit.push("ManuelleEntladesteuerung");
  Res_Feld1.push(je_value);
  Res_Feld2.push(0);
  //alert (Tag_Zeit + "\n" + Res_Feld1 + "\n" + Res_Feld2);
  }

  $.ajax({
   url:"entlade_speichern.php",
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
