<?php

include "config.php";

//import.php

$EV = array();
$Tag_Zeit = $_POST["Tag_Zeit"];
$Feld1 = $_POST['Res_Feld1'];
$Feld2 = $_POST['Res_Feld2'];

if(isset($_POST["Tag_Zeit"]))
{
 for($count = 0; $count < count($Tag_Zeit); $count++)
 {
 $EV[$Tag_Zeit[$count]]['Res_Feld1']=$Feld1[$count];
 $EV[$Tag_Zeit[$count]]['Res_Feld2']=$Feld2[$count];
 $Watt[$Tag_Zeit[$count]]=(float) $Feld1[$count]*1000 + (float) $Feld2[$count]*1000;
 }
}

file_put_contents($ReservierungsFile, json_encode($EV, JSON_PRETTY_PRINT));
file_put_contents($WattReservierungsFile, json_encode($Watt, JSON_PRETTY_PRINT));

?>
