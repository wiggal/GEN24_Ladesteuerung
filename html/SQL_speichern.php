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
// eine ungültige SQL-Abfrage (leere Wertetupel), falls der Request unvollständig ist.
// Alle Felder müssen Arrays sein (kommt von jQuery als ID[]=... usw.), sonst wird nichts geändert.
if (!is_array($ID) || !is_array($Schluessel) || !is_array($Tag_Zeit) || !is_array($Feld1)
    || !is_array($Feld2) || !is_array($Options) || empty($Tag_Zeit) || empty($Schluessel)) {
    http_response_code(400);
    echo "Fehler: Tag_Zeit/Schluessel fehlen oder sind leer - nichts gespeichert.";
    exit;
}

# Wert an Position $i als Text, fehlende Einträge (oder verschachtelte Arrays) werden zu ''
function sql_wert($feld, $i) {
    return (isset($feld[$i]) && is_scalar($feld[$i])) ? (string)$feld[$i] : '';
}

$db = new SQLite3($SQLfile);
$db->enableExceptions(true);
$db->busyTimeout(5000);
try {
    # Löschen und Schreiben in einer Transaktion: schlägt etwas fehl, bleiben die alten Zeilen erhalten
    $db->exec('BEGIN IMMEDIATE');

    # Alle elemente löschen, sonst bleiben welche übrig
    $del = $db->prepare('DELETE FROM steuercodes WHERE Schluessel = :schluessel');
    $del->bindValue(':schluessel', sql_wert($Schluessel, 0), SQLITE3_TEXT);
    $del->execute();

    $ins = $db->prepare('REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options)
                         VALUES (:id, :schluessel, :zeit, :feld1, :feld2, :options)');
    for ($count = 0; $count < count($Tag_Zeit); $count++) {
        # als TEXT binden: gleiches Verhalten wie bisher ('..' im SQL), Typ-Umwandlung übernimmt die Spaltenaffinität
        $ins->bindValue(':id',         sql_wert($ID, $count),         SQLITE3_TEXT);
        $ins->bindValue(':schluessel', sql_wert($Schluessel, $count), SQLITE3_TEXT);
        $ins->bindValue(':zeit',       sql_wert($Tag_Zeit, $count),   SQLITE3_TEXT);
        $ins->bindValue(':feld1',      sql_wert($Feld1, $count),      SQLITE3_TEXT);
        $ins->bindValue(':feld2',      sql_wert($Feld2, $count),      SQLITE3_TEXT);
        $ins->bindValue(':options',    sql_wert($Options, $count),    SQLITE3_TEXT);
        $ins->execute();
    }
    $db->exec('COMMIT');
} catch (Exception $e) {
    try { $db->exec('ROLLBACK'); } catch (Exception $e2) { }
    $db->close();
    http_response_code(500);
    echo "Fehler beim Speichern: ".$e->getMessage()." - nichts geändert.";
    exit;
}
$db->close();

?>
