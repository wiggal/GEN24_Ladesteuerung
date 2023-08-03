<?php

include "config.php";

$Watt = array();
$Tag_Zeit = $_POST["Tag_Zeit"];
$Feld1 = $_POST['Res_Feld1'];

if(isset($_POST["Tag_Zeit"]))
{
 for($count = 0; $count < count($Tag_Zeit); $count++)
 {
 //$EV[$Tag_Zeit[$count]]['Res_Feld1']=$Feld1[$count];
 $Watt[$Tag_Zeit[$count]]=(float) $Feld1[$count]*1000 + (float) $Feld2[$count]*1000;
 }
}

file_put_contents($EntLadeSteuerFile, json_encode($Watt, JSON_PRETTY_PRINT));
//file_put_contents($WattReservierungsFile, json_encode($Watt, JSON_PRETTY_PRINT));

?>
