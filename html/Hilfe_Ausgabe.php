<?php
# bei Älteren PHP-Versionen fehlt str_ends_with
if (!function_exists('str_ends_with')) {
    function str_ends_with($haystack, $needle) {
        return $needle !== '' && substr($haystack, -strlen($needle)) === $needle;
    }
}

// Markdown-Datei einlesen
$filename = isset($_GET['file']) ? basename($_GET['file']) : null;
$return_url = isset($_GET['return']) ? htmlspecialchars($_GET['return']) : null;
# Alle Dokus unter /docs abgelegt
$filename = '../docs/' . $filename;
if ($filename && !str_ends_with($filename, '.html')) {
    $filename .= '.html';
}

$warning = '';
$html = '';

if (!$filename) {
    $warning = '<p style="color:red;">Fehler: Es wurde keine Datei angegeben. Beispiel: ?file=Setup.md</p>';
} else {
    $html_contend = file_get_contents($filename);

    if ($html_contend === false) {
        $warning = "<center><p style=\"color:red;\">Fehler: Die Datei <strong>$filename</strong> konnte nicht geladen werden.</p></center>";
        echo $warning;
        exit();
    } else {
        // Tag ersetzen
        $html = str_replace(
            '<!HIERZURUECK>',
            '<div class="hilfe" align="right"> <a href="'.$return_url.'"><b>Zurück</b></a></div>',
            $html_contend
            );
        echo $html;
    }
}
