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
  $current_url = urlencode($_SERVER['REQUEST_URI']);
  $hilfe_link = "Hilfe_Ausgabe.php?file=config&return=$current_url";
?>
  <div class="hilfe"> <a href="<?php echo $hilfe_link; ?>"><b>Hilfe</b></a></div>
<!-- Hilfeaufruf ENDE -->

<div class="version" align="center">
<br><br>
<b>  GEN24_Ladesteuerung Version: 0.31.0 </b>
</div>
<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}

function getinifile($dir) 
{
	$files = '';
	$i = 0;
	// Read all items
    $entry = scandir($dir);
    foreach ($entry as $element) {
		if ($element != '.' && $element != '..') {
			// Filter only files mit priv.ini
			if ((is_file($dir . '/' . $element)) and strpos($element, '_priv.ini')) {
                $files .= "<option value=\"$dir$element\"> $element </option>";
				$i++;
			}
		}
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
                }
    
            $Zeilencounter++;

        }
    } #ENDE foreach ($file_array

    #print_r($all_ini_daten);  #entWIGGlung
    #exit();  #entWIGGlung

    # Ab hier wierden die gesammelten Zeilen ausgegeben
    if ($edit_methode !== 'update') {
        $zeilenzaehler = 0;
        foreach ($all_ini_daten['_priv'] as $key1 => $element) {
            echo '<tr><th colspan="2"><input type="hidden" name="Zeile['.$zeilenzaehler.']" value=\''.$key1.'\' >'.$key1.'</th></tr>'."\n";
            $zeilenzaehler++;
            foreach ($element as $key2 => $subelement) {
                if (substr($key2, 0, 9) === 'leerzeile') {
                    echo '<tr><td colspan="2"><input type="hidden" name="Zeile['.$zeilenzaehler.']" value=\'\' ></td></tr>'."\n";
                }
                if ($subelement['comment'] !== '') {
                    echo '<tr class="comment"><td colspan="2">
                            <input type="hidden" name="Zeile['.$zeilenzaehler.']" value=\''. $subelement['comment'] .'\' >'. $subelement['comment'] .'
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
            if(!isset($all_ini_daten['_priv'][$key1])) $Zeilenhintergrund_block = 'style="background-color: #FFCCCC;"';  #rot
            echo '<tr><th colspan="2"'.$Zeilenhintergrund_block.'><input type="hidden" name="Zeile['.$zeilenzaehler.']" value=\''.$key1.'\' >'.$key1.'</th></tr>'."\n";
            $zeilenzaehler++;
            foreach ($element as $key2 => $subelement) {
                if (substr($key2, 0, 9) === 'leerzeile') {
                    echo '<tr><td colspan="2"><input type="hidden" name="Zeile['.$zeilenzaehler.']" value=\'\' ></td></tr>'."\n";
                }
                if ($subelement['comment'] !== '') {
                    if (!isset ($all_ini_daten['_priv'][$key1][$key2]['comment'])) {
                        $Zeilenhintergrund_comm = 'style="background-color: #FFCCCC;"';  #rot
                    } elseif ($all_ini_daten['_priv'][$key1][$key2]['comment'] !== $subelement['comment']) {
                        $Zeilenhintergrund_comm = 'style="background-color: #CCE5FF;"';  #blau
                    } 
                    if ($key1 === '[monats_priv.ini]') $Zeilenhintergrund_comm = '';
                        
                    echo '<tr class="comment" '.$Zeilenhintergrund_comm.'><td colspan="2">
                           <input type="hidden" name="Zeile['.$zeilenzaehler.']" value=\''. $subelement['comment'] .'\' >'. $subelement['comment'];
                    echo '</td></tr>'."\n";

                    $Zeilenhintergrund_comm = '';
                    $zeilenzaehler++;

                    # Alle Sonderkonfigurationen aus der charge_priv.ini übernehmen
                    if ($key1 === '[monats_priv.ini]') {
                        // Nur Schlüssel mit '_priv.ini' übernehmen
                        foreach ($all_ini_daten['_priv']['[monats_priv.ini]'] as $key_monats_priv => $value) {
                            if (strpos($key_monats_priv, '_priv.ini') !== false) {
                                echo '<tr '.$Zeilenhintergrund_var.'><td><input type="hidden" name="Zeile['.$zeilenzaehler.'][0]" value=\''.$key_monats_priv.' = \'>'.$key_monats_priv.'</td>'."\n";
                                echo '<td><input type="text" name="Zeile['.$zeilenzaehler.'][1]" value="'. htmlspecialchars($value['wert'], ENT_QUOTES) .'" '.$readonly.'></td></tr>'."\n";
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
                    echo '</td></tr>'."\n";
                $Zeilenhintergrund_var = '';
                $zeilenzaehler++;
                }
        $zeilenzaehler++;
        }
    }
}
}

$case = '';
$org_ini_file = '';
if (isset($_POST["case"])) $case = $_POST["case"];
if (isset($_POST["ini_file"])) $ini_file = $_POST["ini_file"];
if (isset($ini_file)) $org_ini_file = str_replace('_priv', '', $ini_file);
$nachricht = '';
if (isset($_GET["nachricht"])) $nachricht = $_GET["nachricht"];
if ($nachricht != '') echo $nachricht . "<br><br>";

switch ($case) {
    case '':
# AUSWAEHLEN  _priv.ini

echo '<br><center>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<select name="ini_file">';
echo getinifile('../CONFIG/');
echo '</select><br><br>';
echo '<input type="hidden" name="case" value="lesen">'."\n";
echo '<button type="submit">Auswahl lesen</button>';
echo '</form>'."\n";
echo '<br><br>';
    break;


    case 'lesen':
# AUSGEBEN DER gewählten _priv.ini

echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
echo '<input type="hidden" name="case" value="">'."\n";
echo '<div class="button-container">';
echo '<button class="dateiauswahl" type="submit">Zurück zur Dateiauswahl</button>';
echo '&nbsp;<button class="Kommentare" type="button" onclick="toggleComments()">Kommentare ein/aus</button>';
echo '</div>';
echo '</form>'."\n";
echo '<br>';

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
    echo '<button type="submit" style="background-color: #FFCCCC;">!BETA! Update mit '.basename($org_ini_file).'</button>';  #entWIGGlung
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
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
echo '<input type="hidden" name="case" value="">'."\n";
echo '<button class="dateiauswahl" type="submit">Zurück zur Dateiauswahl</button>';
echo '</form>'."\n";
echo '<br><br>';

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
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$ini_file.'">'."\n";
echo '<input type="hidden" name="case" value="">'."\n";
echo '<div class="button-container">';
echo '<button class="dateiauswahl" type="submit">Zurück zur Dateiauswahl</button>';
echo '&nbsp;<button type="button" onclick="toggleComments()">Kommentare ein/aus</button>';
echo '</div>';
echo '</form>'."\n";
echo '<br>';

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
    if (is_array($zeile_value)) {
        // key = value
        $final_lines[] = rtrim($zeile_value[0] . $zeile_value[1]);
    } else {
        // ggf. <br> durch \n ersetzen bei Kommentarblöcken
        $zeile_value = str_replace('<br>', "\n", $zeile_value);
        // in echte einzelne Zeilen splitten
        $lines = explode("\n", $zeile_value);
        foreach ($lines as $line) {
            $final_lines[] = rtrim($line);
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

</body>
</html>
