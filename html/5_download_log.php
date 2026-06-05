<?php
// Datei-Parameter prüfen
if (!isset($_GET['log_file'])) {
    die('Keine Datei angegeben.');
}

// Nur den reinen Dateinamen aus der URL holen
$fileName = basename($_GET['log_file']); 

// Pfad-Weiche: ocpp.log liegt fest in /tmp/ des Containers
if ($fileName === 'ocpp.log') {
    $filePath = '/tmp/ocpp.log';
} else {
    $directory = '../'; 
    $filePath = $directory . $fileName;
}

// Überprüfen, ob die Datei existiert und gelesen werden darf
if (!file_exists($filePath)) {
    die('Datei nicht gefunden.');
}
if (!is_readable($filePath)) {
    die('Datei gefunden, aber PHP besitzt keine Leserechte im Container.');
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