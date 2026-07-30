<?php
// config.ini parsen, um $PythonDIR zu erhalten
require_once "config_parser.php";

// Erlaubte Basisverzeichnisse (Whitelist).
// Der Aufrufer übergibt nur den Schlüssel (z.B. "tmp" oder "py"), nicht den
// Pfad selbst - so ist kein Pfad-Traversal möglich und es sind keine
// dateinamenbezogenen Sonderfälle im Skript nötig.
$erlaubteVerzeichnisse = [
    'tmp' => '/tmp',
    'py'  => $PythonDIR,
];

// Parameter prüfen
if (!isset($_GET['file'])) {
    die('Keine Datei angegeben.');
}
if (!isset($_GET['dir']) || !isset($erlaubteVerzeichnisse[$_GET['dir']])) {
    die('Kein gültiges Verzeichnis angegeben.');
}

// Nur den reinen Dateinamen aus der URL holen (verhindert Pfad-Traversal)
$fileName = basename($_GET['file']);
$filePath = $erlaubteVerzeichnisse[$_GET['dir']] . '/' . $fileName;

// Überprüfen, ob die Datei existiert und gelesen werden darf
if (!file_exists($filePath)) {
    die('Datei nicht gefunden.');
}
if (!is_readable($filePath)) {
    die('Datei gefunden, aber PHP besitzt keine Leserechte im Container.');
}

$log = file_get_contents($filePath);

// --- HTML → ASCII Wandlung (betrifft nur Dateien, die HTML-Reste enthalten
// könnten, z.B. Logs; bei reinen Text-/CSV-Dateien ohne solche Zeichen
// unschädlich) ---
$log = preg_replace('/<br\s*\/?>/i', "\n", $log);
$log = strip_tags($log);
$log = html_entity_decode($log, ENT_QUOTES | ENT_HTML5, 'UTF-8');

// Header für den Download
// Sicherheitsnetz: falls doch irgendwo vorher etwas ausgegeben wurde,
// Puffer verwerfen, damit header() greift
while (ob_get_level() > 0) {
    ob_end_clean();
}
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
