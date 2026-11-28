<?php
// config.ini parsen, um $PythonDIR zu erhalten
require_once "config_parser.php";

// Erlaubte Basisverzeichnisse und Dateien (Whitelist).
// Der Aufrufer übergibt nur den Schlüssel (z.B. "tmp" oder "py"), nicht den Pfad.
//   'pfad'    => Basisverzeichnis
//   'dateien' => feste Liste erlaubter Dateinamen, oder null = beliebige *.log
$erlaubteVerzeichnisse = [
    'tmp' => ['pfad' => '/tmp',       'dateien' => ['ocpp.log']],
    'py'  => ['pfad' => $PythonDIR,   'dateien' => null],
];

// Parameter prüfen
if (!isset($_GET['file']) || !is_string($_GET['file'])) {
    http_response_code(400);
    die('Keine Datei angegeben.');
}
if (!isset($_GET['dir']) || !is_string($_GET['dir']) || !isset($erlaubteVerzeichnisse[$_GET['dir']])) {
    http_response_code(400);
    die('Kein gültiges Verzeichnis angegeben.');
}
$cfg = $erlaubteVerzeichnisse[$_GET['dir']];

// --- Fix 1 + 2: Dateiname streng prüfen (nur *.log, nur sichere Zeichen) ---
$fileName = basename($_GET['file']);
if (!preg_match('/^[A-Za-z0-9._-]+\.log$/', $fileName)) {
    http_response_code(400);
    die('Ungültiger Dateiname.');
}
if ($cfg['dateien'] !== null && !in_array($fileName, $cfg['dateien'], true)) {
    http_response_code(404);
    die('Datei nicht gefunden.');
}

// --- Fix 1: realpath-Prüfung (blockt auch Symlinks aus dem Verzeichnis heraus) ---
$baseDir  = realpath($cfg['pfad']);
$filePath = $baseDir !== false ? realpath($baseDir . '/' . $fileName) : false;

if ($filePath === false
    || strpos($filePath, $baseDir . DIRECTORY_SEPARATOR) !== 0
    || !is_file($filePath)) {
    http_response_code(404);
    die('Datei nicht gefunden.');
}
if (!is_readable($filePath)) {
    http_response_code(403);
    die('Datei gefunden, aber PHP besitzt keine Leserechte im Container.');
}

$fh = fopen($filePath, 'r');
if ($fh === false) {
    http_response_code(500);
    die('Datei konnte nicht geöffnet werden.');
}

// Sicherheitsnetz: falls vorher etwas ausgegeben wurde, Puffer verwerfen
while (ob_get_level() > 0) {
    ob_end_clean();
}
header('Content-Description: File Transfer');
header('Content-Type: text/plain; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Content-Disposition: attachment; filename="' . $fileName . '"');
header('Cache-Control: must-revalidate');
header('Pragma: public');
// Kein Content-Length: Die Größe ist wegen der Zeilenumwandlung vorab unbekannt.

// --- Fix 3: Nur bekannte Markup-Reste entfernen, Rest des Logs bleibt unverändert ---
// Erkannt werden nur die Tags, die das Log selbst erzeugt (bei Bedarf ergänzen).
$tagMuster = '/<\/?(?:span|b|i|u|em|strong|font|br)\b[^>]*>/i';

while (($zeile = fgets($fh)) !== false) {
    // <br> als Zeilenumbruch behalten
    $zeile = preg_replace('/<br\s*\/?>/i', "\n", $zeile);

    // Nur Zeilen, in denen tatsächlich eigene Tags standen, werden umgewandelt.
    // Zeilen mit "a < b", JSON o.ä. und echtem "&amp;" bleiben unangetastet.
    if (preg_match($tagMuster, $zeile)) {
        $zeile = preg_replace($tagMuster, '', $zeile);
        $zeile = html_entity_decode($zeile, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }
    echo $zeile;
}
fclose($fh);
exit;
