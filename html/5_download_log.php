<?php
// Datei-Parameter prüfen (z. B. Datei-Name in der URL)
if (!isset($_GET['log_file'])) {
    die('Keine Datei angegeben.');
}

$fileName = basename($_GET['log_file']); // Entfernt Pfad-Anteile
$filePath = $_GET['log_file'];

// Überprüfen, ob die Datei existiert
if (!file_exists($filePath)) {
    die('Datei nicht gefunden.');
}

$log = file_get_contents($filePath);

// --- HTML → ASCII Wandlung ---
// 1) <br> durch echte Zeilenumbrüche ersetzen
$log = preg_replace('/<br\s*\/?>/i', "\n", $log);
// 2) HTML-Tags entfernen
$log = strip_tags($log);
// 3) HTML-Entities (&nbsp; &gt; &lt; …) decodieren
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

// Skript beenden
exit;
?>

