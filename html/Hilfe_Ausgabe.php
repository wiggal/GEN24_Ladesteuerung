<style>
html, body {
    width: 100%;             /* Stellt sicher, dass sie nie breiter als der Viewport sind */
    overflow-x: hidden;      /* Verhindert horizontales Scrollen der gesamten Seite */
    margin: 0;               /* Entfernt Standard-Browser-Margin */
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    /* WICHTIG: Fügt Padding hinzu, um den Platz des fixierten Headers auszugleichen. */
    padding-top: 0px; /* Ausgleich für fixierten Header */
    scroll-behavior: smooth;
    scroll-padding-top: 0px;
}
table {
    max-width: 100%;
    width: 100%;
    display: block;
    overflow-x: auto;
    border-collapse: collapse;
    border: none;
}

th, td {
    border: 2px solid #2E64FE;
    padding: 8px;
    text-align: left;
    word-wrap: break-word;
    overflow-wrap: break-word;
}
.hilfe{
        position: fixed;
        right: 8px;
        }
@media (max-width: 600px) {
  body {
    font-size: 100% !important;
  }
  table, th, td {
    font-size: 100% !important;
  }
}
</style>


    <main>
        <div id="content-container">
<?php
# bei Älteren PHP-Versionen fehlt str_ends_with
if (!function_exists('str_ends_with')) {
    function str_ends_with($haystack, $needle) {
        return $needle !== '' && substr($haystack, -strlen($needle)) === $needle;
    }
}

// Hilfe-Datei einlesen
$tab = isset($_GET['file']) ? basename($_GET['file']) : null;
$return_url = isset($_GET['return']) ? htmlspecialchars($_GET['return']) : null;
# Alle Dokus unter /docs abgelegt
$filename = $PythonDIR.'/docs/WIKI/' . $tab;
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
            '<!--HIERZURUECK-->',
            '<div class="hilfe" align="right"> <a href="index.php?tab=' . $tab . '"><b>Zurück</b></a></div>',
            $html_contend
            );

        echo $html;
    }
}
?>
        </div>
    </main>
