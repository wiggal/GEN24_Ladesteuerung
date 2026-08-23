<?php
# config.ini parsen
require_once "config_parser.php";

$SQLfile = $PythonDIR.'/CONFIG/Prog_Steuerung.sqlite';
$ID = $_POST["ID"] ?? [];
$Schluessel = $_POST["Schluessel"] ?? [];
$Tag_Zeit = $_POST["Tag_Zeit"] ?? [];
$Feld1 = $_POST['Res_Feld1'] ?? [];
$Feld2 = $_POST['Res_Feld2'] ?? [];
$Options = $_POST['Options'] ?? [];

// Ohne Tag_Zeit (bzw. wenn leer) gibt es nichts zu speichern - insbesondere verhindert das
// eine ungültige SQL-Abfrage ("VALUES" ohne Wertetupel), falls der Request unvollständig ist.
if (empty($Tag_Zeit) || empty($Schluessel)) {
    http_response_code(400);
    echo "Fehler: Tag_Zeit/Schluessel fehlen oder sind leer - nichts gespeichert.";
    exit;
}

$trenner = ',';
$insertvalue = '';
for ($count = 0; $count < count($Tag_Zeit); $count++) {
    if ($count == count($Tag_Zeit) - 1) $trenner = '';
    $insertvalue .= '(\''.$ID[$count].'\',\''.$Schluessel[$count].'\',\''.$Tag_Zeit[$count].'\',\''.$Feld1[$count].'\',\''.$Feld2[$count].'\',\''.$Options[$count].'\')'.$trenner;
}

$db = new SQLite3($SQLfile);
# Alle elemente löschen, sonst bleiben welche übrig
$db->exec("DELETE FROM steuercodes WHERE Schluessel = '$Schluessel[0]' ");
$VALUE = ("REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES  $insertvalue ");
$db->exec($VALUE);
$db->close();

?>
