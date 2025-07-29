<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}
$SQLfile = $PythonDIR.'/CONFIG/Prog_Steuerung.sqlite';
$EV = array();
$ID = $_POST["ID"];
$Schluessel = $_POST["Schluessel"];
$Tag_Zeit = $_POST["Tag_Zeit"];
$Feld1 = $_POST['Res_Feld1'];
$Feld2 = $_POST['Res_Feld2'];
$Options = $_POST['Options'];

if(isset($_POST["Tag_Zeit"]))
{
 $trenner=',';
 $insertvalue = '';
 for($count = 0; $count < count($Tag_Zeit); $count++)
 {
 if ($count == count($Tag_Zeit)-1) $trenner='';
 $insertvalue .= '(\''.$ID[$count].'\',\''.$Schluessel[$count].'\',\''.$Tag_Zeit[$count].'\',\''.$Feld1[$count].'\',\''.$Feld2[$count].'\',\''.$Options[$count].'\')'.$trenner;
 }
}

$db = new SQLite3($SQLfile);
# Alle elemente löschen, sonst bleiben welche übrig
$db->exec("DELETE FROM steuercodes WHERE Schluessel = '$Schluessel[0]' ");
$VALUE = ("REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES  $insertvalue ");
$db->exec($VALUE);
$db->close();

?>
