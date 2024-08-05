<?php
$SQLfile = '../CONFIG/Prog_Steuerung.sqlite';


$EV = array();
$ID = $_POST["ID"];
$Schluessel = $_POST["Schluessel"];
$Tag_Zeit = $_POST["Tag_Zeit"];
$Feld1 = $_POST['Res_Feld1'];
$Feld2 = $_POST['Res_Feld2'];

if(isset($_POST["Tag_Zeit"]))
{
 $trenner=',';
 $insertvalue = '';
 for($count = 0; $count < count($Tag_Zeit); $count++)
 {
 if ($count == count($Tag_Zeit)-1) $trenner='';
 $insertvalue .= '(\''.$ID[$count].'\',\''.$Schluessel[$count].'\',\''.$Tag_Zeit[$count].'\',\''.$Feld1[$count].'\',\''.$Feld2[$count].'\')'.$trenner;
 }
}

if(!file_exists($SQLfile)){
    $db = new SQLite3($SQLfile);
    $db->exec('CREATE TABLE IF NOT EXISTS steuercodes (
        ID TEXT,
        Schluessel TEXT,
        Zeit TEXT,
        Res_Feld1 INT,
        Res_Feld2 INT)');
    $db->exec('CREATE UNIQUE INDEX idx_positions_title ON steuercodes (ID, Schluessel)');
} else {
    $db = new SQLite3($SQLfile);
    $VALUE = ("REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2) VALUES  $insertvalue ");
    $db->exec($VALUE);
}

#print_r($VALUE);

?>
