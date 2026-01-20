<style>
body{font-family:Arial;}
button {
  font-size: 1.3em;
  background-color: #4CAF50;
}
input { font-size: 1.3em; }
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
  right: 15px
}
.checkbox {
  display: block;
}

table a {
  display: inline-block;           /* wichtig, sonst unterstrich bei <span> */
  text-decoration: none !important;
  color: #007bff;
}
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  background: #fff;
  border-top: 1px solid #ccc;
  padding: 8px 10px;
  z-index: 9999;
}

/* Checkboxen untereinander auf Desktop */
.checkbox {
  display: block;
}

/* Mobile: kompakt */
@media (max-width: 600px) {
  .bottom-bar form {
    flex-direction: column;
    align-items: flex-start;
  }

  .checkbox {
    display: flex;
    align-items: center;
    font-size: 12px;
  }
}

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
  body {
    font-size: 100% !important;
  }

  /* Suchfeld kleiner */
  input[type="input"],
  input[type="text"] {
    font-size: 12px !important;
    padding: 4px 6px;
    width: 100px;   /* optional, je nach Wunsch */
  }
  /* Filter-Button kleiner */
  button {
    font-size: 12px !important;
    padding: 4px 8px;
  }

  .checkbox {
    font-size: 14px !important;
    display: flex;
    align-items: center;
    height: 16px;
    line-height: 1.2;
    margin-bottom: 2px;
    cursor: pointer;
  }

  .checkbox input[type="checkbox"] {
    width: 14px;
    height: 14px;
    margin-right: 6px;
    transform: scale(0.9);
    flex-shrink: 0;
  }
  a.ende {
    font-size: 16px;
  }
}

</style>
<?php
# config.ini parsen
require_once "config_parser.php";

?>
<div id="top"><div>
<?php
// --- Datei auswählen ---
$file_name = isset($_REQUEST['log_file']) ? basename($_REQUEST['log_file']) : 'Crontab.log';
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
    $downloadLink = '5_download_log.php?log_file=' . urlencode($log);
    $viewLink = '?log_file=' . urlencode($basename);

    echo '<tr>';
    echo '<td><a class="ende" href="' . htmlspecialchars($viewLink) . '&tab=' . $activeTab . '">' . htmlspecialchars($nameWithoutExt) . '</a></td>';
    echo '<td style="text-align:center;"><a class="ende" href="' . htmlspecialchars($downloadLink) . '" title="Download"><span class="icon">💾</span></a></td>';
    echo '</tr>';
}
echo '</table>';
echo '</div>';
echo "\n";

echo '<div class="headertop">';
echo '<a class="ende" href="#bottom">Ans Ende springen!</a>';
echo '<br>';

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
    echo '<input type="hidden" name="log_file" value="'.$file_name.'">'."\n";
    echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
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
echo '<br><br><br><br><br><div id="bottom">';
echo '<div class="bottom-bar">';
echo '<a class="ende" name="bottom" href="#top">An den Anfang springen!</a><br>';
echo "\n";
echo '<form method="post" action="#bottom" enctype="multipart/form-data">';
echo '<label class="checkbox">';
echo '<input type="checkbox" name="DEBUG" value="ein"> DEBUG-Zeilen anzeigen';
echo '</label>';
echo "\n";
echo '<label class="checkbox">';
echo '<input type="checkbox" name="TAGE" value="ein"> Alle Tage anzeigen';
echo '</label>';
echo "\n";
echo '<input type="hidden" name="log_file" value="'.$file_name.'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<button type="submit">Neu laden</button>';
echo '</form><br>';
echo '</div>';

?>
<script>
document.addEventListener('DOMContentLoaded', function () {
    if (location.hash !== '#bottom') {
        location.hash = '#bottom';
    }
});
</script>

