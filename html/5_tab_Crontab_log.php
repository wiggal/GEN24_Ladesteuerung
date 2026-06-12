<style>
button {
  font-size: 1.3em;
  background-color: #4CAF50;
}
input { font-size: 1.3em; }
a.ende{
  display: inline-block;
  text-decoration: none !important;
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

/* Spezielle Anpassung für Mobilgeräte */
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

  .content {
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
  .content button {
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
$log_file_param = isset($_REQUEST['log_file']) ? $_REQUEST['log_file'] : 'Crontab.log';

// Wenn ocpp.log angefordert wird, nutzen wir direkt den absoluten Pfad im Container
if ($log_file_param === 'ocpp.log' || basename($log_file_param) === 'ocpp.log') {
    $file = '/tmp/ocpp.log';
    $file_name = 'ocpp.log';
} elseif (strpos($log_file_param, '/') === 0) {
    $file = $log_file_param;
    $file_name = basename($log_file_param);
} else {
    $file_name = basename($log_file_param);
    $file = $PythonDIR . '/' . $file_name;
}

if(!file_exists($file)) {
  die("Datei ". htmlspecialchars($file) ." ist nicht vorhanden!");
} else {
  // Sicherheits-Check für Container-Berechtigungen
  if (!is_readable($file)) {
      die("Datei " . htmlspecialchars($file) . " ist vorhanden, aber PHP hat keine Leserechte! (chmod 666 prüfen)");
  }
  $myfile = fopen($file, "r");
}

// --- Logdateien im Verzeichnis auslesen ---
$logFiles = glob($PythonDIR . '/*.log');

// --- /tmp/ocpp.log ergänzen wenn im Container vorhanden ---
if (file_exists('/tmp/ocpp.log')) {
    $logFiles[] = '/tmp/ocpp.log';
}

// --- Tabelle mit Download-Symbol & Anzeige-Link ---
echo '<div class="download">';
echo '<table>';
foreach ($logFiles as $log) {
    $basename = basename($log); 
    $nameWithoutExt = preg_replace('/\.log$/', '', $basename);

    // Spezialfall ocpp.log abfangen
    if ($log === '/tmp/ocpp.log') {
        $downloadLink = '5_download_log.php?log_file=ocpp.log';
        $viewLink = '?log_file=ocpp.log';
        $nameWithoutExt = 'ocpp';
    } else {
        $downloadLink = '5_download_log.php?log_file=' . urlencode($basename);
        $viewLink = '?log_file=' . urlencode($basename);
    }

    echo '<tr>';
    echo '<td><a class="ende" href="' . htmlspecialchars($viewLink) . '&tab=' . htmlspecialchars($activeTab) . '">' . htmlspecialchars($nameWithoutExt) . '</a></td>';
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
$datum_kurz = date("m-d", time());

$case = '';
if (isset($_POST["case"])) $case = $_POST["case"];
$DEBUG = 'aus';
if (isset($_POST["DEBUG"])) $DEBUG = $_POST["DEBUG"];
$TAGE = 'aus';
if (isset($_POST["TAGE"])) $TAGE = $_POST["TAGE"];
if($TAGE == 'ein') $Ausgabe = 1;

if (!empty($_POST['suchstring'])) {
    $suchstring_anzeige = htmlspecialchars($_POST['suchstring']);
} else {
    $suchstring_anzeige = htmlspecialchars($_POST['letzte_suche'] ?? 'geschrieben');
}
echo '<form id="filterform" method="POST" action="">'."\n";
echo '<input type="hidden" name="log_file" value="'.$file.'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="case" value="filter">'."\n";
echo '<label style="display:none"><input type="checkbox" name="DEBUG" value="ein"' . ($DEBUG == 'ein' ? ' checked' : '') . '></label>';
echo '<label style="display:none"><input type="checkbox" name="TAGE" value="ein"' . ($TAGE == 'ein' ? ' checked' : '') . '></label>';
echo "\n";
echo '<input type="hidden" name="letzte_suche" value="'.$suchstring_anzeige.'">'."\n";
echo '<input type="text" name="suchstring" placeholder="'.$suchstring_anzeige.'" size="10" title="Mehrere Suchbegriffe mit | trennen (z.B. OK|INFO)">'."\n";
echo '<button type="submit"> &gt;&gt;filtern&lt;&lt; </button>';
echo '</form>'."\n";
echo '</div>';
echo '<br><br><br><br><br><br><br><br>';

$letzteWarLeer = false;

switch ($case) {
    case '':
    # AUSGEBEN DER Logdatei von Heute
    while(!feof($myfile)) {
        $Zeile = fgets($myfile);
        // Datum am Zeilenanfang erkennen: mm-dd HH:MM:SS oder BEGINN mit Datum
        if (strpos($Zeile, 'BEGINN') !== false && (strpos($Zeile, $datum) !== false || strpos($Zeile, $datum_kurz) !== false)) $Ausgabe = 1;
        if (preg_match('/^(\d{2}-\d{2}) \d{2}:\d{2}:\d{2}/', $Zeile, $m) && ($m[1] === $datum_kurz)) $Ausgabe = 1;
        if ($TAGE == 'ein') $Ausgabe = 1;
        if ($Ausgabe == 1) {
            // DEBUG ausblenden
            if ($DEBUG == "aus") {
                if (
                preg_match('/^\s*DEBUG/', $Zeile) ||
                preg_match('/^\s*>> /', $Zeile) ||
                preg_match('/^\s*\+\+ /', $Zeile) ||
                preg_match('/^\d{2}-\d{2} \d{2}:\d{2}:\d{2} 🐞DEBUG/', $Zeile)
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
            echo htmlspecialchars($Zeile) . "<br>";
        }
    }
    break;

    case 'filter':
    if (!empty($_POST['suchstring'])) {
        $suchstring = trim($_POST["suchstring"] ?? '');
    } else {
        $suchstring = htmlspecialchars($_POST['letzte_suche'] ?? 'geschrieben');
    }
    
    $BEGIN_DATUM = '';
    $BEGIN_UHRZEIT = '';
    $BEGIN_Merken = '';
    # Ausgabe der gesuchten Zeile mit Datumszeile 
    while(!feof($myfile)) {
        $Zeile = fgets($myfile);
        // Datum/Zeit aus Zeilenanfang lesen: mm-dd HH:MM:SS
        if (preg_match('/^(\d{2}-\d{2}) (\d{2}:\d{2}):\d{2}/', $Zeile, $m)) {
            $zeile_datum = $m[1];
            $zeile_uhrzeit = $m[2];
            if ($TAGE == 'ein' || $zeile_datum === $datum_kurz) {
                $Ausgabe = 1;
                $BEGIN_DATUM = $zeile_datum;
                $BEGIN_UHRZEIT = $zeile_uhrzeit;
            }
        }
        // Fallback: BEGINN-Zeilen wie bisher
        if (strpos($Zeile, 'BEGINN') !== false) {
            if ($TAGE == 'ein' || strpos($Zeile, $datum) !== false || strpos($Zeile, $datum_kurz) !== false) {
                $Ausgabe = 1;
                $tmp = explode(" ", $Zeile);
                $BEGIN_DATUM = $tmp[3] ?? '';
                $BEGIN_UHRZEIT = isset($tmp[4]) ? substr($tmp[4], 0, 5) : '';
            }
        }
        if ($Ausgabe == 1) {
            if (strpos($Zeile, 'BEGINN') === false && preg_match('/' . $suchstring . '/', $Zeile)) {
                $hatEigeneDatumzeile = preg_match('/^\d{2}-\d{2} \d{2}:\d{2}:\d{2}/', $Zeile);
                if (!$hatEigeneDatumzeile && ($BEGIN_DATUM !== '' || $BEGIN_UHRZEIT !== '')) {
                    if ($BEGIN_Merken !== $BEGIN_DATUM . $BEGIN_UHRZEIT) {
                        echo htmlspecialchars($BEGIN_UHRZEIT . " " . $BEGIN_DATUM) . "<br>";
                        $BEGIN_Merken = $BEGIN_DATUM . $BEGIN_UHRZEIT;
                    }    
                }
                echo htmlspecialchars($Zeile) . "<br>";
            }
        }
    }
    echo "<br><br>";
    break;
}
fclose($myfile);

echo '<br><br><br><br><br><div id="bottom">';
echo '<div class="bottom-bar">';
echo '<a class="ende" name="bottom" href="#top">An den Anfang springen!</a><br>';
echo "\n";
echo '<form method="post" action="#bottom" enctype="multipart/form-data">';
echo '<label class="checkbox">';
echo '<input type="checkbox" name="DEBUG" value="ein"' . ($DEBUG == 'ein' ? ' checked' : '') . '> DEBUG-Zeilen anzeigen';
echo '</label>';
echo "\n";
echo '<label class="checkbox">';
echo '<input type="checkbox" name="TAGE" value="ein"' . ($TAGE == 'ein' ? ' checked' : '') . '> Alle Tage anzeigen';
echo '</label>';
echo "\n";
echo '<input type="hidden" name="log_file" value="'.$file.'">'."\n";
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

    // Beim Filtern: Checkbox-Zustand aus bottom-bar ins Filter-Formular übernehmen
    var filterForm = document.getElementById('filterform');
    if (filterForm) {
        filterForm.addEventListener('submit', function () {
            var debugCb    = document.querySelector('.bottom-bar input[name="DEBUG"]');
            var tageCb     = document.querySelector('.bottom-bar input[name="TAGE"]');
            var hiddenDebug = filterForm.querySelector('input[name="DEBUG"]');
            var hiddenTage  = filterForm.querySelector('input[name="TAGE"]');
            if (debugCb && hiddenDebug) hiddenDebug.checked = debugCb.checked;
            if (tageCb  && hiddenTage)  hiddenTage.checked  = tageCb.checked;
        });
    }
});
</script>
