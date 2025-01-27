<?php
// Datei-Parameter prüfen (z. B. Datei-Name in der URL)
if (!isset($_GET['file'])) {
    die('Keine Datei angegeben.');
}

$fileName = basename($_GET['file']); // Entfernt Pfad-Anteile
$filePath = $_GET['file'];

// Überprüfen, ob die Datei existiert
if (!file_exists($filePath)) {
    die('Datei nicht gefunden.');
}

// MIME-Typ ermitteln
$fileType = "log/txt";
$fileSize = filesize($filePath);

// Header für den Download
header('Content-Description: File Transfer');
header('Content-Type: ' . $fileType);
header('Content-Disposition: attachment; filename="' . $fileName . '"');
header('Content-Length: ' . $fileSize);
header('Cache-Control: must-revalidate');
header('Pragma: public');

// Datei ausgeben
readfile($filePath);

// Skript beenden
exit;
?>

