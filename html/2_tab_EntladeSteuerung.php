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
	background-color:#58ACFA;
	border-radius:28px;
	border:1px solid #58ACFA;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-family:Arial;
	font-size:200%;
	padding:16px 31px;
	text-decoration:none;
	text-shadow:0px 1px 0px #58ACFA;
  }
  .speichern:hover {
	background-color:#2E64FE;
  }
  .speichern:active {
	position:relative;
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
   accent-color: #58ACFA;
}

/* ENDE CHECKBOX */

label.slider {
	background-color:#58ACFA;
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
   accent-color: #58ACFA;
  }

.hilfe{
  font-family:Arial;
  font-size:150%;
  color: #000000;
}
.sliderbeschriftung{
  font-family:Arial;
  font-weight: bold;
  font-size:120%;
  color: #000000;
}

  </style>
 </head>

 <body>
  <div class="hilfe" align="right"> <a href="2_Hilfe.html"><b>Hilfe</b></a></div>
  <div class="container">
   <br />
  <div align="center"><button type="button" id="import_data" class="speichern">Akku Entladesteuerung ==&#62;&#62; speichern</button></div>
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
  var ID = [];
  var Schluessel = [];
  var Tag_Zeit = [];
  var Res_Feld1 = [];
  var Res_Feld2 = [];
  $('.Tag_Zeit').each(function(){
   ID.push($(this).text());
   Schluessel.push('ENTLadeStrg');
   Tag_Zeit.push($(this).text());
  });
  $('.Res_Feld1').each(function(){
   Res_Feld1.push($(this).text().replace(",", ".")*1000);
  });
  $('.Res_Feld2').each(function(){
   Res_Feld2.push($(this).text().replace(",", ".")*1000);
  });
  je_value = 0.1;
  const je = document.querySelectorAll('input[name="hausakkuentladung"]');
  je_value = je[0].value;

  if (je != "") {
  ID.push("23:58");
  Schluessel.push("ENTLadeStrg");
  Tag_Zeit.push("ManuelleEntladesteuerung");
  Res_Feld1.push(je_value);
  Res_Feld2.push(0);
  //alert (Tag_Zeit + "\n" + Res_Feld1 + "\n" + Res_Feld2);
  }

  $.ajax({
   url:"SQL_speichern.php",
   method:"post",
   data:{ID:ID, Schluessel:Schluessel, Tag_Zeit:Tag_Zeit, Res_Feld1:Res_Feld1, Res_Feld2:Res_Feld2},
   success:function(data)
   {
    //alert(data);
    location.reload();
   }
  })
 });
});
</script>
 </body>
</html>
