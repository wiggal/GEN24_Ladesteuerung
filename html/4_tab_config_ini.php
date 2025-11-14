<!DOCTYPE html>
<html>
<head>
<style>
table {
  font-family: Arial, Helvetica, sans-serif;
  border-collapse: collapse;
  width: 100%;
}

td, th {
  border: 1px solid #ddd;
  padding: 4px;
}

/*
tr:nth-child(even){background-color: #f2f2f2;}
*/
.comment {background-color: #f2f2f2;}

tr:hover {background-color: #ddd;}

th {
  text-align: left;
  background-color: #CCFFCC;
}
input:read-only {
  background-color: #fadbd8;
}
select {
  font-size: 1.3em;
  background-color: #F5F5DC;
}
.button-container {
  position: fixed;
  top: 8px;
  left: 8px;
  display: flex;
  gap: 8px; /* Abstand zwischen den Buttons */
}

button {
  padding: 6px 12px;
  font-size: 14px;
}
button {
  font-size: 1.3em;
  background-color: #4CAF50;
}
button.schreiben {
    position: fixed;
    bottom: 0;
}
@media screen and (max-width: 64em) {
body{ font-size: 140%; }
input { font-size: 100%; }
th { font-size: 1.5em; }
td {font-size: 140%;
    width:48%;
	max-width: 120px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
}
.hilfe{
    font-family:Arial;
    font-size:150%;
    color: #000000;
    position: fixed;
    right: 8px;
    }
.version{
    font-family:Arial;
    font-size:150%;
    color: #000000;
    }

</style>
</head>
<body>

<!-- Hilfeaufruf ANFANG -->
<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}
  $current_url = urlencode($_SERVER['REQUEST_URI']);
  $hilfe_link = "Hilfe_Ausgabe.php?file=config&return=$current_url";
    $config = parse_ini_file($PythonDIR.'/version.ini', true);
    $prg_version = $config['Programm']['version'];

# Pfade und Logdatei für Updatefunktion
$repoPath = realpath($PythonDIR);
$logFile = $repoPath . '/Update.log';

echo '<div class="hilfe"> <a href="' . $hilfe_link . '"><b>Hilfe</b></a></div>';
# <!-- Hilfeaufruf ENDE -->

echo '<div style="text-align:center;">';
echo '<span class="version">';
echo '<b>Ladesteuerung: ' .  htmlspecialchars($prg_version) . '</b>';
echo '</span>';

// --- Hilfsfunktion fürs Logging ---
function writeLog($file, $message) {
    $timestamp = '';
    if($message != ''){
        $timestamp = date('[Y-m-d H:i:s] ');
    }
    $entry = $timestamp . trim($message) . "\n";
    if ($fh = fopen($file, 'a')) {
        flock($fh, LOCK_EX);
        fwrite($fh, $entry);
        flock($fh, LOCK_UN);
        fclose($fh);
    }
}

function get_updatebutton($repoPath, $logFile, $prg_version) {
    $originalDir = getcwd();
    $error = 'nein';
    $meldungen[] = "=== BEGINN Update-Check ===\n";

    // --- Prüfen, ob Git-Repository vorhanden ist ---
    if (!is_dir($repoPath . '/.git') || !is_readable($repoPath . '/.git')) {
        // Kein gültiges Git-Repo => Funktion ohne Log beenden
        echo '</div>';
        return;
    }

    // --- Logging erst ab hier ---

    $localVersion = $prg_version ?? 'unbekannt';
    $remoteVersion = null;
    $compare = null;

    // --- Prüfen, ob Git verfügbar ist ---
    exec('git --version 2>&1', $gitCheckOut, $gitCheckCode);
    if ($gitCheckCode !== 0) {
        $meldungen[] = "Git ist nicht installiert oder nicht im PATH verfügbar.";
        $error = 'ja';
    }

    if ($error == 'nein') {
        // --- In Repo wechseln ---
        if (!chdir($repoPath)) {
            $meldungen[] = "Fehler: Konnte nicht ins Repository wechseln (Zugriffsrechte?).";
            $error = 'ja';
        } else {
            // --- Aktuellen Branch prüfen ---
            exec('git rev-parse --abbrev-ref HEAD 2>&1', $branchOut, $branchCode);
            $currentBranch = $branchOut[0] ?? '';
            if ($branchCode !== 0 || $currentBranch !== 'main') {
                $meldungen[] = "Aktueller Branch ist '$currentBranch'. Erwartet wird 'main'.";
                $error = 'ja';
            } else {
                // --- Git fetch ---
                exec('git fetch origin main 2>&1', $fetchOut, $fetchCode);
                $meldungen[] = "git fetch origin main -> Exit $fetchCode\n" . implode("\n", $fetchOut);

                // --- Git show version.ini ---
                exec('git show origin/main:version.ini 2>&1', $remoteIni, $retCode);
                $meldungen[] =  "git show origin/main:version.ini -> Exit $retCode";

                if ($fetchCode !== 0 || $retCode !== 0 || empty($remoteIni)) {
                    $meldungen[] = "Git-Fehler: Fetch/Show fehlgeschlagen.";
                    $meldungen[] = implode("\n", $remoteIni ?: $fetchOut);
                    $error = 'ja';
                } else {
                    // --- Remote-Version parsen ---
                    $tmp = tmpfile();
                    fwrite($tmp, implode("\n", $remoteIni));
                    $meta = stream_get_meta_data($tmp);
                    $parsed = @parse_ini_file($meta['uri'], true);
                    fclose($tmp);

                    if ($parsed && isset($parsed['Programm']['version'])) {
                        $remoteVersion = $parsed['Programm']['version'];
                        $compare = version_compare(ltrim($localVersion, 'vV'), ltrim($remoteVersion, 'vV'));
                        $meldungen[] = "Remote-Version gelesen: $remoteVersion (lokal: $localVersion)";
                    } else {
                        $meldungen[] = "Remote version.ini konnte nicht gelesen oder geparst werden.";
                        $error = 'ja';
                    }
                }
            }
            chdir($originalDir);
        }
    }

    // --- Button oder Fehlerausgabe ---
    if ($error == 'nein') {
        // ✅ Alles ok => Button erzeugen
        $buttonText = '✅ Aktuell';
        $buttonStyle = 'background-color: #44c767; cursor: not-allowed;';
        $buttonDisabled = 'disabled';

        if ($compare !== null && $compare < 0) {
            $buttonText = "🔄 $remoteVersion";
            $buttonStyle = 'background-color: #FF5555; cursor: pointer;';
            $buttonDisabled = '';
        }

        echo '<form method="post" action="' . htmlspecialchars($_SERVER['PHP_SELF']) . '" style="display:inline;">' . "\n";
        echo '<input type="hidden" name="case" value="git_update">';
        echo '<button type="submit" style="' . htmlspecialchars($buttonStyle) . '" ' . $buttonDisabled . '>';
        echo htmlspecialchars($buttonText);
        echo '</button>';
        echo '</form>';
        echo "</div>\n";
    } else {
        // ❌ Fehler vorhanden → ins Log schreiben
        $meldungen[] = "=== FEHLER beim Update-Check ===";
        $meldungen[] = "=== ENDE Update-Check ===";
        $meldungen[] = "";
        foreach ($meldungen as $msg) writeLog($logFile, $msg);
    }

} #ENDE  get_updatebutton

function getinifile($dir) 
{
	$files = '';
    $entry = glob($dir . '*_priv.ini');
    foreach ($entry as $element) {
        $filename = basename($element);
        $files .= "<option value=\"$element\"> $filename </option>";
	}
return $files;
}
		

function config_lesen( $priv_ini_file, $readonly, $edit_methode, $org_ini_file )
{
    $file_array['_priv'] = $priv_ini_file;
    if ($edit_methode == 'update') $file_array['_org'] = $org_ini_file;
    foreach ($file_array as $schluessel => $file) {
        $myfile = fopen($file, "r") or die("Kann Datei ".$file." nicht öffnen!");
        $Zeilencounter = 0;
        $block_key = 'dummy';
        while (($Zeile = fgets($myfile)) !== false) {
            $Zeile = rtrim($Zeile);
    
            // Kommentarzeile
            if ((strpos($Zeile, ';') !== false) && (strpos($Zeile, ';') < 2)) {
                $KommentarZeilen[] = htmlspecialchars($Zeile);
                $Zeilencounter++;
                continue; 
            }
            if (!empty($KommentarZeilen)) {
                // Falls ein Kommentarblock fertig ist, jetzt ausgeben
                $block = implode('<br>', $KommentarZeilen);
                $Zeilencounter++;
                $KommentarZeilen = [];
            }
            if ((strpos($Zeile, '[') !== false) && (strpos($Zeile, '[') < 1)) {
                // vorherigen Kommentarblock anhängen (falls vorhanden)
                if (!empty($block)) {
                    $all_ini_daten[$schluessel][$block_key]['comment_'.$Zeilencounter] = [
                        'comment' => $block,
                        'variable' => '',
                        'wert' => ''
                    ];
                    $block = '';
                    }

                // neuen Block beginnen
                $block_key = $Zeile;
                }

                elseif (strpos($Zeile, '=') !== false) {
                    $Zeilenteil = explode("=", $Zeile, 2);
                    $Zeilenteil[0] = trim($Zeilenteil[0]);
                    $Zeilenteil[1] = trim($Zeilenteil[1]);
                    $all_ini_daten[$schluessel][$block_key][$Zeilenteil[0]]= [
                        'comment' => $block,
                        'variable' => $Zeilenteil[0],
                        'wert' => $Zeilenteil[1]
                        ];
                    $block = '';
                } elseif ($Zeile == '') {
                    $all_ini_daten[$schluessel][$block_key]['leerzeile_'.$Zeilencounter]= [
                        'comment' => $block,
                        'variable' => '',
                        'wert' => ''
                        ];
                        $block = '';
                }
    
            $Zeilencounter++;

        }
    } #ENDE foreach ($file_array

    # Ab hier werden die gesammelten Zeilen ausgegeben
    if ($edit_methode !== 'update') {
        $zeilenzaehler = 0;
        foreach ($all_ini_daten['_priv'] as $key1 => $element) {
            echo '<tr><th colspan="2"><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''.$key1.'\' >'.$key1.'</th></tr>'."\n";
            $zeilenzaehler++;
            foreach ($element as $key2 => $subelement) {
                if (substr($key2, 0, 9) === 'leerzeile') {
                    echo '<tr><td colspan="2"><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\'\' ></td></tr>'."\n";
                }
                if ($subelement['comment'] !== '') {
                    echo '<tr class="comment"><td colspan="2">
                            <input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''. $subelement['comment'] .'\' >'. $subelement['comment'] .'
                        </td></tr>'."\n";
                    $zeilenzaehler++;
                }
                if ($subelement['variable'] !== '') {
                    echo '<tr><td><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''.$subelement['variable'].' = \'>'.$subelement['variable'].'</td>'."\n";
                    echo '<td><input type="text" name="Zeile['.$zeilenzaehler.'][1]" value="'. htmlspecialchars($subelement['wert'], ENT_QUOTES) .'" '.$readonly.'></td></tr>'."\n";
                }
            $zeilenzaehler++;
            }
        $zeilenzaehler++;
        }
   } else {
        $zeilenzaehler = 0;
        foreach ($all_ini_daten['_org'] as $key1 => $element) {
            $Zeilenhintergrund_block = '';
            $Zeilenhintergrund_comm = '';
            $Zeilenhintergrund_var = '';
            $checkbox_group = '';
            if(!isset($all_ini_daten['_priv'][$key1])) $Zeilenhintergrund_block = 'style="background-color: #FFCCCC;"';  #rot
            $checkbox_group = str_replace(['[', ']','.','_'], '', $key1);
            echo '<tr><th colspan="2"'.$Zeilenhintergrund_block.'><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''.$key1.'\' >'.$key1."\n";
            echo '<input type="hidden" name="Zeile['.$zeilenzaehler.'][2]" value="off">'."\n";
            echo '<input type="checkbox" name="Zeile['.$zeilenzaehler.'][2]" class="check-all" data-group="'.$checkbox_group.'" checked></th></tr>'."\n";
            $zeilenzaehler++;
            foreach ($element as $key2 => $subelement) {
                if (substr($key2, 0, 9) === 'leerzeile') {
                    echo '<tr><td colspan="2"><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\'\' ></td></tr>'."\n";
                }
                if ($subelement['comment'] !== '') {
                    if (!isset ($all_ini_daten['_priv'][$key1][$key2]['comment'])) {
                        $Zeilenhintergrund_comm = 'style="background-color: #FFCCCC;"';  #rot
                    } elseif ($all_ini_daten['_priv'][$key1][$key2]['comment'] !== $subelement['comment']) {
                        $Zeilenhintergrund_comm = 'style="background-color: #CCE5FF;"';  #blau
                    } 
                    if ($key1 === '[monats_priv.ini]') $Zeilenhintergrund_comm = '';
                        
                    echo '<tr class="comment" '.$Zeilenhintergrund_comm.'><td colspan="2">
                           <input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''. $subelement['comment'] .'\' >'. $subelement['comment'];
                    echo '<input type="hidden" name="Zeile['.$zeilenzaehler.'][2]" value="off">'."\n";
                    echo '<input type="checkbox" name="Zeile['.$zeilenzaehler.'][2]" class="'.$checkbox_group.'" checked>'."\n";
                    echo '</td></tr>'."\n";

                    $Zeilenhintergrund_comm = '';
                    $zeilenzaehler++;

                    # Alle Sonderkonfigurationen aus der charge_priv.ini übernehmen
                    if ($key1 === '[monats_priv.ini]') {
                        // Nur Schlüssel mit '_priv.ini' übernehmen
                        foreach ($all_ini_daten['_priv']['[monats_priv.ini]'] as $key_monats_priv => $value) {
                            if (strpos($key_monats_priv, '_priv.ini') !== false) {
                                echo '<tr '.$Zeilenhintergrund_var.'><td><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''.$key_monats_priv.' = \'>'.$key_monats_priv.'</td>'."\n";
                                echo '<td><input type="text" name="Zeile['.$zeilenzaehler.'][1]" value="'. htmlspecialchars($value['wert'], ENT_QUOTES) .'" '.$readonly.">\n";
                                echo '<input type="hidden" name="Zeile['.$zeilenzaehler.'][2]" value="off">'."\n";
                                echo '<input type="checkbox" name="Zeile['.$zeilenzaehler.'][2]" class="'.$checkbox_group.'" checked>'."\n";
                                echo '</td></tr>'."\n";
                            }
                        $zeilenzaehler++;
                        }
                    }
                    $zeilenzaehler++;
                }

                if ($subelement['variable'] !== '') {
                    # Variablenwert aus _priv holen, wenn vorhanden
                    $input_ueber_farbe = '';
                    if (isset($all_ini_daten['_priv'][$key1][$subelement['variable']])) {
                        $subelement['wert'] = $all_ini_daten['_priv'][$key1][$subelement['variable']]['wert'];
                        $input_ueber_farbe = 'style="background-color: #FFF5CC;"';  #gelb
                    } else {
                        $Zeilenhintergrund_var = 'style="background-color: #FFCCCC;"';  #rot
                    }
                        
                   # Hintergrundfarbe definieren
                   if ($Zeilenhintergrund_block !== '') {
                        $Zeilenhintergrund_var = $Zeilenhintergrund_block;
                   }
                    echo '<tr '.$Zeilenhintergrund_var.'><td><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''.$subelement['variable'].' = \'>'.$subelement['variable'].'</td>'."\n";
                    echo '<td><input type="text" '.$input_ueber_farbe.' name="Zeile['.$zeilenzaehler.'][1]" value="'. htmlspecialchars($subelement['wert'], ENT_QUOTES) .'" '.$readonly.'>';
                    echo '<input type="hidden" name="Zeile['.$zeilenzaehler.'][2]" value="off">'."\n";
                    echo '<input type="checkbox" name="Zeile['.$zeilenzaehler.'][2]" class="'.$checkbox_group.'" checked>'."\n";
                    echo '</td></tr>'."\n";
                $Zeilenhintergrund_var = '';
                $zeilenzaehler++;
                }
        $zeilenzaehler++;
        }
    }
}
}

function Dateiauswahl_button($Anzahl, $ini_file, $updatecheck = 'ja'){
    echo "</div>\n";
    echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
    echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
    echo '<input type="hidden" name="case" value="">'."\n";
    echo '<input type="hidden" name="updatecheck" value="'.$updatecheck.'">'."\n";
    echo '<div class="button-container">';
    echo '<button class="dateiauswahl" type="submit">Zurück zur Dateiauswahl</button>';
    if ($Anzahl == 2){ 
        echo '&nbsp;<button class="Kommentare" type="button" onclick="toggleComments()">Kommentare ein/aus</button>';
    }
    echo '</div>';
    echo '</form>'."\n";
    echo '<br>';
}

$case = '';
$org_ini_file = '';
$updatecheck = 'ja';
if (isset($_POST["case"])) $case = $_POST["case"];
if (isset($_POST["ini_file"])) $ini_file = $_POST["ini_file"];
if (isset($ini_file)) $org_ini_file = str_replace('_priv', '', $ini_file);
if (isset($_POST["updatecheck"])) $updatecheck = $_POST["updatecheck"];
$nachricht = '';
if (isset($_GET["nachricht"])) $nachricht = $_GET["nachricht"];
if ($nachricht != '') echo $nachricht . "<br><br>";

switch ($case) {
    case '':
# AUSWAEHLEN  _priv.ini

if ($updatecheck == 'ja') {
    get_updatebutton($PythonDIR, $logFile, $prg_version);
} else {
echo '</div>';
}
echo '<br><center>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<select name="ini_file">';
echo getinifile($PythonDIR.'/CONFIG/');
echo '</select><br><br>';
echo '<input type="hidden" name="case" value="lesen">'."\n";
echo '<button type="submit">Auswahl anzeigen</button>';
echo '</form>'."\n";
echo '<br><br>';
    break;


    case 'lesen':
# AUSGEBEN DER gewählten _priv.ini

Dateiauswahl_button('2', $ini_file, 'nein');

echo '<div style="display:inline-block; margin-right: 10px;">';
echo '<b>"'.basename($ini_file).'" hier nur lesbar! <br>Zum editieren Button klicken!</b>';
echo '<br><br>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
echo '<input type="hidden" name="case" value="editieren">'."\n";
echo '<input type="hidden" name="editcase" value="editieren">'."\n";
echo '<button type="submit">'.basename($ini_file).' editieren</button>';
echo '</form>';
echo '</div>';
echo "\n";
// Update-Button, wenn Original.ini existiert
if (file_exists($org_ini_file)) {
    echo '<div style="display:inline-block;">';
    echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
    echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
    echo '<input type="hidden" name="org_ini_file" value="'.$org_ini_file.'">'."\n";
    echo '<input type="hidden" name="case" value="editieren">'."\n";
    echo '<input type="hidden" name="editcase" value="update">'."\n";
    echo '<button type="submit" style="background-color: #FFCCCC;">Update mit '.basename($org_ini_file).'</button>';
    echo '</form>'."\n";
    echo '</div>';
}

echo '<br><br>';
echo '<table>';

config_lesen($ini_file, 'readonly', '', '');

echo '</table>';
    break;

    case 'editieren':
# PASSWORDABFRAGE 

Dateiauswahl_button('1', $ini_file, 'nein');

echo '<br><br>';
echo 'Kennwort um '.basename($ini_file).' zu editieren oder upzudaten:<br>';
echo '(Kennwortänderung in html/config.php)<br>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
echo '<input type="hidden" name="case" value="editieren_passwd">'."\n";
echo '<input type="hidden" name="editcase" value="'.$_POST["editcase"].'">'."\n";
echo '<input type="password" name="password" size="10">'."\n";
echo '<button type="submit">OK</button>';
echo '</form>'."\n";
echo '<br>';

    break;

    case 'editieren_passwd':
# EDITIEREN DER INI-Datei 
# Erläuterungen zu Hintergrundfarben ausgeben
echo "<br><br></div>\n";
echo "<br><table style='width: auto;'><tr><td style='border: 1; padding: 8px;'><b>".$_POST["editcase"]."</b>";
$SpeichernButton  = ' speichern!';
if ($_POST["editcase"] == 'update') {
# SpeichernButton unterschied edit/update
$SpeichernButton  = ' updaten!';
echo "</td><td style='border: 0; padding: 8px; background-color: #FFF5CC;'>Werte aus ".$ini_file;
echo "</td><td style='border: 0; padding: 8px; background-color: #CCE5FF;'>Veränderte Werte aus ".$org_ini_file;
echo "</td><td style='border: 0; padding: 8px; background-color: #FFCCCC;'>Fehlende Werte aus ".$org_ini_file;
}
echo "</td></tr></table>";
# Button
Dateiauswahl_button('2', $ini_file, 'nein');

if ($_POST["password"] == $passwd_configedit) {

echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<table>';

    config_lesen($ini_file, '', $_POST["editcase"], $org_ini_file);

echo '</table>';
echo '<br>';
echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
echo '<input type="hidden" name="case" value="schreiben">'."\n";
echo '<button class="schreiben" type="submit" >'.basename($ini_file).$SpeichernButton.' </button>';
echo '</form>';
    } else {
    echo '<br><br> <span style="color:red"><b> Falsches Kennwort!!</b></span>';
    } # if passwd
    break;

    case 'schreiben':

# SCHREIBEN DER INI-Datei
// Jetzt alle Zeilen flach machen:
$final_lines = [];

foreach ($_POST['Zeile'] as $zeile_value) {
    if (isset($zeile_value[1])) {
        // key = value
        if (!isset($zeile_value[2]) || $zeile_value[2] == 'on') {
            $final_lines[] = rtrim($zeile_value[0] . $zeile_value[1]);
        }
    } else {
        if (!isset($zeile_value[2]) || $zeile_value[2] == 'on') {
            // ggf. <br> durch \n ersetzen bei Kommentarblöcken
            $zeile_value_str = str_replace('<br>', "\n", $zeile_value[0]);
            // in echte einzelne Zeilen splitten
            $lines = explode("\n", $zeile_value_str);
            foreach ($lines as $line) {
                $final_lines[] = rtrim($line);
            }
        }
    }
}

$write = implode("\n", $final_lines)."\n";

// Basisname ohne Pfad und ohne Erweiterung ermitteln
$basename = pathinfo($ini_file, PATHINFO_FILENAME);
$timestamp = date("Ymd_His");
$DIR = dirname($ini_file) . "/SIC/";
$backup_file = $DIR . $basename . "_" . $timestamp . ".sic";
// Nur die 2 neuesten Backups behalten
$backup_pattern = $DIR . $basename . "_*.sic";
$backups = glob($backup_pattern);
usort($backups, function($a, $b) {
    return filemtime($b) - filemtime($a); // Neueste zuerst
});
foreach (array_slice($backups, 2) as $old_backup) {
    unlink($old_backup);
}

$nachricht = '';
if (!is_dir($DIR)) {
    if (mkdir($DIR, 0777, true)) {
        $nachricht .= "Verzeichnis '$DIR' wurde erfolgreich erstellt.<br>";
    } else {
        $nachricht .= "Fehler beim Erstellen des Verzeichnisses '$DIR'.<br>";
    }
} 
if (!copy($ini_file, $backup_file)) {
    $error = error_get_last();
    $nachricht .=  '<span style="color:red"> Fehler beim Sichern der Datei: <br>' . $error['message'].'<br>'.$ini_file.' wurde nicht geschrieben!!</span>';
} elseif (is_writeable($ini_file,)) { # Sicherung OK nun neue _priv.ini schreiben
    $handle = fopen($ini_file,"w");
    if (fwrite($handle, $write)) {
        $nachricht .= '<span style="color:green"> '.$ini_file.' wurde neu geschrieben!</span><br><span style="color:red"> Backup in '.$backup_file.'!</span>';
    } else {
        $nachricht .= '<span style="color:red"> '.$ini_file.' konnte nicht geschrieben werden!!!</span>';
    }
    fclose($handle);
}

header('location: '.$_SERVER["PHP_SELF"].'?nachricht='.$nachricht);
exit();
    break;

        case 'git_update':

$originalDir = getcwd();
// ins lokales Repo wechseln
chdir($PythonDIR);

Dateiauswahl_button('1', '', 'ja');
// Pull durchführen
exec('git pull 2>&1', $output, $returnCode);

echo '<center>';
echo "<h2>🔄 Update durchgeführt</h2>";
echo "<pre>" . htmlspecialchars(implode("\n", $output)) . "</pre>";
echo "<p><b>Exit-Code:</b> $returnCode</p>";

// Logfile schreiben
$output_str = htmlspecialchars(implode("\n\t\t", $output));
writeLog($logFile, "=== BEGINN Update mit git pull ===");
writeLog($logFile, $output_str);
writeLog($logFile, "Exit-Code: $returnCode");
writeLog($logFile, "=== END Update mit git pull ===");
writeLog($logFile, "");

// Neue Version anzeigen (falls version.ini geändert wurde)
$iniFile = $repoPath . '/version.ini';
if (file_exists($iniFile) and $returnCode == 0) {
    $ini = parse_ini_file($iniFile, true);
    $newVersion = $ini['Programm']['version'] ?? 'unbekannt';
    echo "<p><b>Neue Version:</b> " . htmlspecialchars($newVersion) . "</p>";
}
echo '</center>';

//wieder zurück wechseln
chdir($originalDir);

break;

} # ENDE switch
?>
<script>
function toggleComments() {
    // Kommentare ausblenden
    const rows = document.querySelectorAll('.comment');
    rows.forEach(row => {
        row.style.display = (row.style.display === 'none') ? '' : 'none';
    });
}
</script>
<script>
  // checkboxgruppen auswählen
  document.querySelectorAll('.check-all').forEach(masterCheckbox => {
    const group = masterCheckbox.dataset.group;
    const groupCheckboxes = document.querySelectorAll('.' + group);

    // Wenn "Alle auswählen" geändert wird
    masterCheckbox.addEventListener('change', () => {
      groupCheckboxes.forEach(cb => {
        cb.checked = masterCheckbox.checked;
      });
    });

    // Wenn ein einzelnes Kontrollkästchen geändert wird
    groupCheckboxes.forEach(cb => {
      cb.addEventListener('change', () => {
        const allChecked = [...groupCheckboxes].every(c => c.checked);
        masterCheckbox.checked = allChecked;
      });
    });
  });
</script>

</body>
</html>
