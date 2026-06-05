<?php
// Datei-Parameter prüfen
if (!isset($_GET['log_file'])) {
    die('Keine Datei angegeben.');
}

// 1. SCHRITT: Nur den reinen Dateinamen aus der URL holen (Sicherheit!)
$fileName = basename($_GET['log_file']); 

// 2. SCHRITT: Den Pfad zum Log-Verzeichnis fest definieren
$directory = '../'; 
$filePath = $directory . $fileName;

// Überprüfen, ob die Datei existiert
if (!file_exists($filePath)) {
    // Debug-Hilfe: Falls es nicht klappt, kommentiere die nächste Zeile ein:
    // die('Datei nicht gefunden unter: ' . realpath($filePath));
    die('Datei nicht gefunden.');
}

$log = file_get_contents($filePath);

// --- HTML → ASCII Wandlung ---
$log = preg_replace('/<br\s*\/?>/i', "\n", $log);
$log = strip_tags($log);
$log = html_entity_decode($log, ENT_QUOTES | ENT_HTML5, 'UTF-8');

// Header für den Download
header('Content-Description: File Transfer');
header('Content-Type: text/plain; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $fileName . '"');
header('Content-Length: ' . strlen($log));
header('Cache-Control: must-revalidate');
header('Pragma: public');

// Dateiinhalt ausgeben
echo $log;

exit;
?>
