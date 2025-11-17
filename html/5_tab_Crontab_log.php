<!DOCTYPE html>
<html>
<head>
<style>
body{font-family:Arial;}
button {
  font-size: 1.3em;
  background-color: #4CAF50;
}
input { font-size: 1.3em; }
@media screen and (max-width: 64em) {
body{ font-size: 160%; }
input { font-size: 140%; }
a{
  text-decoration: none;
  font-family:Arial;
  font-size: 180%;
}
input[type="checkbox"] {
    width: 0.8em;
    height: 0.8em;
  }
.checkbox{
  font-family:Arial;
  font-size: 1.4em;
}
}
a.ende{
  display: inline-block;
  text-decoration: none !important;
  font-family:Arial;
  font-size: 110%;
}
.headertop{
  background-color:#ffffff;
  position: fixed;
  left: 8px;
}
.download{
  background-color:#ffffff;
  position: fixed;
  right: 8px
}
table a {
  display: inline-block;           /* wichtig, sonst unterstrich bei <span> */
  text-decoration: none !important;
  color: #007bff;
}
</style>
</head>
<?php
# config.ini parsen
require_once "config_parser.php";

?>
<body onLoad="if (location.hash != '#bottom') location.hash = '#bottom';">
<div name="top"><div>
<?php
// --- Datei auswählen ---
$file_name = isset($_REQUEST['file']) ? basename($_REQUEST['file']) : 'Crontab.log';
$file = $PythonDIR . '/' . $file_name;
if(!file_exists($file)) {
  die("Datei ". $file ." ist nicht vorhanden!");
} else {
  $myfile = fopen($file, "r");
}

// --- Logdateien im Verzeichnis auslesen ---
$logFiles = glob($PythonDIR . '/*.log');

// --- Tabelle mit Download-Symbol & Anzeige-Link ---
echo '<div class="download">';
echo '<table>';
foreach ($logFiles as $log) {
    $basename = basename($log);
    $nameWithoutExt = preg_replace('/\.log$/', '', $basename); // ".log" entfernen
    $downloadLink = '5_download_log.php?file=' . urlencode($log);
    $viewLink = '?file=' . urlencode($basename);

    echo '<tr>';
    echo '<td><a class="ende" href="' . htmlspecialchars($viewLink) . '">' . htmlspecialchars($nameWithoutExt) . '</a></td>';
    echo '<td style="text-align:center;"><a class="ende" href="' . htmlspecialchars($downloadLink) . '" title="Download"><span class="icon">💾</span></a></td>';
    echo '</tr>';
}
echo '</table><br>';
echo '</div>';

echo '<div class="headertop">';
echo '<a class="ende" href="#bottom">Ans Ende springen!</a>';
echo '<br><br>';

$Ausgabe = 0;
$datum = date("Y-m-d", time());

$case = '';
if (isset($_POST["case"])) $case = $_POST["case"];
$DEBUG = 'aus';
if (isset($_POST["DEBUG"])) $DEBUG = $_POST["DEBUG"];
$TAGE = 'aus';
if (isset($_POST["TAGE"])) $TAGE = $_POST["TAGE"];
if($TAGE == 'ein') $Ausgabe = 1;

switch ($case) {
    case '':
    echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
    echo '<input type="hidden" name="file" value="'.$file_name.'">'."\n";
    echo '<input type="hidden" name="case" value="filter">'."\n";
    echo '<input type="input" name="suchstring" value="geschrieben" size="10">'."\n";
    echo '<button type="submit"> &gt;&gt;filtern&lt;&lt; </button>';
    echo '</form>'."\n";
    echo '</div>';
    echo '<br><br><br><br><br>';

    # AUSGEBEN DER Crontab.log von Heute
    while(!feof($myfile)) {
        $Zeile = fgets($myfile);
        if (strpos($Zeile, 'BEGINN') !== false && strpos($Zeile, $datum) !== false) $Ausgabe = 1;
        if ($Ausgabe == 1) {
            // DEBUG ausblenden
            if ($DEBUG == "aus") {
                if (
                preg_match('/^\s*DEBUG/', $Zeile) ||
                preg_match('/^\s*>> /', $Zeile) ||
                preg_match('/^\s*\+\+ /', $Zeile)
                ) {
                    continue;
                }
            }
            // Leerzeilen prüfen und ggf. überspringen
            if (trim($Zeile) === '') {
                if ($letzteWarLeer) {
                    continue; // mehrere Leerzeilen → nur die erste anzeigen
                } else {
                    $letzteWarLeer = true;
                    echo "<br>";
                    continue;
                }
            }
            // reguläre Zeile anzeigen und Flag zurücksetzen
            $letzteWarLeer = false;
            echo $Zeile . "<br>";
        }
    }
    break;

    case 'filter':
    $suchstring = '';
    if (isset($_POST["suchstring"])) $suchstring = $_POST["suchstring"];
    echo '</div>';
    echo '<br><br>';
    # Ausgabe der gesuchten Zeile mit Datumszeile 
    while(!feof($myfile)) {
        $Zeile = fgets($myfile);
        if (strpos($Zeile, 'BEGINN') !== false && strpos($Zeile, $datum) !== false) $Ausgabe = 1;
        if ($Ausgabe == 1) {
            if (strpos($Zeile, 'BEGINN') !== false) {
                $BEGIN_DATE = explode(" ", $Zeile);
                $BEGIN_TIME = explode(":", $BEGIN_DATE[4]);
            }
            if (strpos($Zeile, $suchstring) !== false) {
                echo $BEGIN_TIME[0] . ":" . $BEGIN_TIME[1] . " " . $BEGIN_DATE[3] . "<br>" .  $Zeile . "<br><br>";
            }
        }
    }
    break;
}

echo '<br><a class="ende" name="bottom" href="#top">An den Anfang springen!</a><br><br>';
echo '<form method="post" action="#bottom" enctype="multipart/form-data">';
echo '<div class="checkbox" ><input type="checkbox" name="DEBUG" value="ein"> DEBUG-Zeilen anzeigen</div>';
echo '<div class="checkbox" ><input type="checkbox" name="TAGE" value="ein"> Alle Tage anzeigen</div>';
echo '<input type="hidden" name="file" value="'.$file_name.'">'."\n";
echo '<button type="submit">Neu laden</button></form>';
?>

</body>
</html>
