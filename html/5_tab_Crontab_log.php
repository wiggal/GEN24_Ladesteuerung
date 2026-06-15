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

/* ==========================================================================
   DESKTOP-EINSTELLUNGEN
   ========================================================================== */
.headertop{
  background-color:#ffffff;
  position: fixed;
  left: 16px;
  top: 55px; /* Unterhalb der blauen Hauptnavigation (50px) */
  z-index: 100;
}
.download{
  background-color:#ffffff;
  position: fixed;
  right: 25px;
  top: 55px; /* Unterhalb der blauen Hauptnavigation (50px) */
  z-index: 101;
}
.checkbox {
  display: block;
}

table a {
  display: inline-block;
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

/* Schiebt den Log-Text auf dem Desktop unter die fixierten Elemente */
body {
  padding-top: 130px !important;
}

/* ==========================================================================
   MOBIL-EINSTELLUNGEN (max-width: 600px)
   ========================================================================== */
@media (max-width: 600px) {
  /* Genug Platz nach oben für Hauptnavigation + Klappmenü + Filter */
  body {
    padding-top: 150px !important;
  }

  /* Das Klappmenü sitzt mobil unter der blauen Navigationsleiste (40px) */
  .download {
    position: fixed;
    left: 0;
    right: 0;
    top: 40px;
    padding: 6px 10px 12px 10px; /* Erhöhtes Padding unten, um Lücke zu schließen */
    z-index: 102; /* Höherer z-index, damit das Menü beim Aufklappen oben liegt */
    background: #fff;
  }

  /* Der Filter wandert mobil direkt unter das Klappmenü */
  .headertop {
    position: fixed;
    left: 0;
    right: 0;
    top: 80px;
    padding: 6px 10px;
    z-index: 101;
    background: #fff;
    border-bottom: 1px solid #ccc; /* Schließt den gesamten Block optisch ab */
    margin-top: -5px; /* Zieht das Element minimal hoch, um Blitzen zu verhindern */
  }

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
    margin-top: 0 !important;
  }

  /* Suchfeld kleiner */
  input[type="input"],
  input[type="text"] {
    font-size: 12px !important;
    padding: 4px 6px;
    width: 140px;
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

<div id="top"></div>

<?php
// --- Datei auswählen ---
$log_file_param = isset($_REQUEST['log_file']) ? $_REQUEST['log_file'] : 'Crontab.log';

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
  if (!is_readable($file)) {
      die("Datei " . htmlspecialchars($file) . " ist vorhanden, aber PHP hat keine Leserechte! (chmod 666 prüfen)");
  }
  $myfile = fopen($file, "r");
}

// --- Logdateien im Verzeichnis auslesen ---
$logFiles = glob($PythonDIR . '/*.log');

if (file_exists('/tmp/ocpp.log')) {
    $logFiles[] = '/tmp/ocpp.log';
}

// --- Tabelle mit Download-Symbol & Anzeige-Link ---
echo '<div class="download">';
echo '<details id="logdateien">';
echo '<summary><b>Logdateien (Größe MB):</b></summary>';
echo '<table>';
foreach ($logFiles as $log) {
    $basename = basename($log); 
    $nameWithoutExt = preg_replace('/\.log$/', '', $basename);

    $fileSizeInMB = 0;
    if (file_exists($log)) {
        $bytes = filesize($log);
        $fileSizeInMB = round($bytes / 1048576, 2);
    }

    if ($log === '/tmp/ocpp.log') {
        $downloadLink = '5_download_log.php?log_file=ocpp.log';
        $viewLink = '?log_file=ocpp.log';
        $nameWithoutExt = 'ocpp';
    } else {
        $downloadLink = '5_download_log.php?log_file=' . urlencode($basename);
        $viewLink = '?log_file=' . urlencode($basename);
    }

    echo '<tr>';
    echo '<td><a class="ende" href="' . htmlspecialchars($viewLink) . '&tab=' . htmlspecialchars($activeTab) . '">' . htmlspecialchars($nameWithoutExt) . ' (' . $fileSizeInMB . ')</a></td>';
    echo '<td style="text-align:center;"><a class="ende" href="' . htmlspecialchars($downloadLink) . '" title="Download"><span class="icon">💾</span></a></td>';
    echo '</tr>';
}
echo '</table>';
echo '</details>';
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
echo '<br><br><br><br><br><br>'; // Die Abstände sorgen dafür, dass der eigentliche Log-Inhalt nicht unter dem Header startet

$letzteWarLeer = false;

echo '<pre style="font-family: monospace; white-space: pre-wrap; word-wrap: break-word; font-size: 14px; text-align: left;">';
switch ($case) {
    case '':
    # AUSGEBEN DER Logdatei
    
    // KOMBINTION 1: Extrem-Turbo, wenn ALLES (inklusive Debug) angezeigt werden soll.
    if ($TAGE == 'ein' && $DEBUG == 'ein') {
        while (!feof($myfile)) {
            echo htmlspecialchars(fread($myfile, 8192));
        }
    } else {
        // KOMBINATION 2 & 3: Für "Nur Heute" oder "Alle Tage OHNE Debug"
        while(!feof($myfile)) {
            $Zeile = fgets($myfile);
            
            // Datum am Zeilenanfang erkennen: mm-dd HH:MM:SS oder BEGINN mit Datum
            if (strpos($Zeile, 'BEGINN') !== false && (strpos($Zeile, $datum) !== false || strpos($Zeile, $datum_kurz) !== false)) $Ausgabe = 1;
            if (preg_match('/^(\d{2}-\d{2}) \d{2}:\d{2}:\d{2}/', $Zeile, $m) && ($m[1] === $datum_kurz)) $Ausgabe = 1;
            if ($TAGE == 'ein') $Ausgabe = 1;
            
            if ($Ausgabe == 1) {
                // Wenn DEBUG ausgeschaltet ist, filtern wir hier im Eiltempo
                if ($DEBUG == "aus") {
                    // PHP 7.4 KOMPATIBEL: strpos() ist genauso schnell wie str_contains
                    if (
                        strpos($Zeile, 'DEBUG') !== false || 
                        strpos($Zeile, '>> ') !== false || 
                        strpos($Zeile, '++ ') !== false
                    ) {
                        continue; // Debug-Zeile überspringen
                    }
                }

                // Zeile von unsichtbaren Umbrüchen befreien
                $Zeile = rtrim($Zeile, "\r\n");

                // Leerzeilen prüfen und ggf. überspringen
                if (trim($Zeile) === '') {
                    if ($letzteWarLeer) {
                        continue; 
                    } else {
                        $letzteWarLeer = true;
                        echo "\n";
                        continue;
                    }
                }
                
                // Reguläre Zeile anzeigen
                $letzteWarLeer = false;
                if (preg_match('/<[a-zA-Z\/]|&[a-zA-Z#]/', $Zeile)) {
                    echo $Zeile . "\n";
                } else {
                    echo htmlspecialchars($Zeile) . "\n";
                }
            }
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
                        echo "\n" . htmlspecialchars($BEGIN_UHRZEIT . " " . $BEGIN_DATUM) . "\n";
                        $BEGIN_Merken = $BEGIN_DATUM . $BEGIN_UHRZEIT;
                    }    
                }
                // Auch beim Filtern die Zeilenenden säubern
                $Zeile = rtrim($Zeile, "\r\n");
                if (preg_match('/<[a-zA-Z\/]|&[a-zA-Z#]/', $Zeile)) {
                    echo $Zeile . "\n";
                } else {
                    echo htmlspecialchars($Zeile) . "\n";
                }
            }
        }
    }
    break;
}
echo '</pre>';
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
    // 1. Automatisch ans Ende der Seite springen
    if (location.hash !== '#bottom') {
        location.hash = '#bottom';
    }

    // =========================================================================
    // NEU: JavaScript-Automatik für die Checkboxen in der bottom-bar
    // =========================================================================
    var debugCb = document.querySelector('.bottom-bar input[name="DEBUG"]');
    var tageCb  = document.querySelector('.bottom-bar input[name="TAGE"]');

    if (tageCb && debugCb) {
        tageCb.addEventListener('change', function() {
            // Wenn "Alle Tage anzeigen" aktiviert wird, hake automatisch auch "DEBUG" an
            if (tageCb.checked) {
                debugCb.checked = true;
            }
        });
    }
    // =========================================================================

    // 2. Beim Filtern: Checkbox-Zustand aus bottom-bar ins Filter-Formular übernehmen
    var filterForm = document.getElementById('filterform');
    if (filterForm) {
        filterForm.addEventListener('submit', function () {
            var hiddenDebug = filterForm.querySelector('input[name="DEBUG"]');
            var hiddenTage  = filterForm.querySelector('input[name="TAGE"]');

            if (debugCb && hiddenDebug) {
                hiddenDebug.value = debugCb.checked ? 'ein' : 'aus';
            }
            if (tageCb && hiddenTage) {
                hiddenTage.value = tageCb.checked ? 'ein' : 'aus';
            }
        });
    }
});
</script>
