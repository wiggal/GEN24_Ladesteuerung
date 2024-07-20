<!DOCTYPE html>
<html>
 <head>
  <title>Einstellungen</title>
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
  .speichern {
	background-color:#FB5555;
	border-radius:28px;
	border:1px solid #FB5555;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-family:Arial;
	font-size:200%;
	padding:16px 31px;
	text-decoration:none;
	text-shadow:0px 1px 0px #FB5555;
  }
  .speichern:hover {
	background-color:#EE3030;
  }
  .speichern:active {
	position:relative;
	top:1px;
  }
/* RADIOBUTTON */
.wrapper{
  width: 500px;
  background: #fff;
  align-items: center;
  padding: 20px 15px;
  box-shadow: 5px 5px 30px rgba(0,0,0,0.2);
}
.wrapper .option{
  background: #fff;
  height: 100%;
  display: flex;
  align-items: center;
  margin: 0px 10px;
  border-radius: 5px;
  cursor: pointer;
  padding: 10px 10px;
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
  background: #FB5555;
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
#analyse:checked:checked ~ .analyse,
#logging:checked:checked ~ .logging,
#voll:checked:checked ~ .voll{
  border-color: #FB5555;
  background: #FB5555;
}
#auto:checked:checked ~ .auto .dot,
#aus:checked:checked ~ .aus .dot,
#analyse:checked:checked ~ .analyse .dot,
#logging:checked:checked ~ .logging .dot,
#voll:checked:checked ~ .voll .dot{
  background: #000;
}
#auto:checked:checked ~ .auto .dot::before,
#aus:checked:checked ~ .aus .dot::before,
#analyse:checked:checked ~ .analyse .dot::before,
#logging:checked:checked ~ .logging .dot::before,
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
#analyse:checked:checked ~ .analyse span,
#logging:checked:checked ~ .logging span,
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
 <div class="hilfe" align="right"> <a href="9_Hilfe.html"><b>Hilfe</b></a></div>
  <div class="container">
   <br />
   <div class="hilfe" align="center"><p>
   <b>ACHTUNG:</b> Diese Einstellungen überschreiben, außer beim Punkt 'unverändert lassen', die Aufrufparameter (z.B. vom Cronjob)!
   </p></div>
   <br />
  </div>

<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}
$EV_Reservierung = json_decode(file_get_contents('../Prog_Steuerung.json'), true);

$LadesteuerungSetting_check = array(
    "auto" => "",
    "aus" => "",
    "analyse" => "",
    "logging" => "",
    "voll" => "",
);

if (isset($EV_Reservierung['Steuerung'])) {
if ($EV_Reservierung['Steuerung'] == 0) $LadesteuerungSetting_check['auto'] = 'checked';
if ($EV_Reservierung['Steuerung'] == 1) $LadesteuerungSetting_check['aus'] = 'checked';
if ($EV_Reservierung['Steuerung'] == 2) $LadesteuerungSetting_check['logging'] = 'checked';
if ($EV_Reservierung['Steuerung'] == 3) $LadesteuerungSetting_check['logging'] = 'checked';
if ($EV_Reservierung['Steuerung'] == 4) $LadesteuerungSetting_check['voll'] = 'checked';
} else {
$LadesteuerungSetting_check['auto'] = 'checked';
}
?>

<center>
<div class="wrapper">
<div class="beschriftung" title='Hier kann ein vom Aufruf abweichender Programmablauf gewählt werden.'>
Ladesteuerung:<br>
&nbsp;
<br\>
</div>
 <input type="radio" name="hausakkuladung" id="auto" value="0" <?php echo $LadesteuerungSetting_check['auto'] ?>>
 <input type="radio" name="hausakkuladung" id="aus" value="1" <?php echo $LadesteuerungSetting_check['aus'] ?> >
 <input type="radio" name="hausakkuladung" id="analyse" value="2" <?php echo $LadesteuerungSetting_check['analyse'] ?> >
 <input type="radio" name="hausakkuladung" id="logging" value="3" <?php echo $LadesteuerungSetting_check['logging'] ?> >
 <input type="radio" name="hausakkuladung" id="voll" value="4" <?php echo $LadesteuerungSetting_check['voll'] ?> >
   <label for="auto" class="option auto">
     <div class="dot"></div>
      <span>&nbsp;unverändert lassen</span>
      </label>
   <label for="aus" class="option aus">
     <div class="dot"></div>
      <span>&nbsp;AUS</span>
      </label>
   <label for="analyse" class="option analyse">
     <div class="dot"></div>
      <span>&nbsp;NUR Analyse in Crontab.log</span>
      </label>
   <label for="logging" class="option logging">
     <div class="dot"></div>
      <span>&nbsp;NUR Logging</span>
   </label>
   <label for="voll" class="option voll">
     <div class="dot"></div>
      <span>&nbsp;WR-Steuerung und Logging</span>
   </label>
</div>
</center>
   <br />
   <div id="csv_file_data">
   <br />
  </div>
  <div align="center"><button type="button" id="import_data" class="speichern">Einstellungen ==&#62;&#62; speichern</button></div>

<script>

$(document).ready(function(){

 $(document).on('click', '#import_data', function(){
  var Tag_Zeit = [];
  var Res_Feld1 = [];
  var Res_Feld2 = [];
  const js = document.querySelectorAll('input[name="hausakkuladung"]');
  for(var i=0; i < js.length; i++){
        if(js[i].checked == true){
            js_value = js[i].value;
        }
    }
  if (js != "") {
  Tag_Zeit.push("Steuerung");
  Res_Feld1.push(js_value);
  //alert (Tag_Zeit + "\n" + Res_Feld1 );
  }

  $.ajax({
   url:"steuern_speichern.php",
   method:"post",
   data:{Tag_Zeit:Tag_Zeit, Steuerung:Res_Feld1},
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
