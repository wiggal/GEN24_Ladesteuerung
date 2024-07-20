<?php

include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}

$EV = array();
$Tag_Zeit = $_POST["Tag_Zeit"];
$Feld1 = $_POST['Res_Feld1'];
$Feld2 = $_POST['Res_Feld2'];

if(isset($_POST["Tag_Zeit"]))
{
 for($count = 0; $count < count($Tag_Zeit); $count++)
 {
 //print_r($Tag_Zeit[$count);
 $EV[$Tag_Zeit[$count]]['Res_Feld1']=(float) $Feld1[$count]*1000;
 $EV[$Tag_Zeit[$count]]['Res_Feld2']=(float) $Feld2[$count]*1000;
 }
}

file_put_contents($EntLadeSteuerFile, json_encode($EV, JSON_PRETTY_PRINT));

?>
