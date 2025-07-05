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
<b>  GEN24_Ladesteuerung Version: 0.30.6 </b>
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
		

function config_lesen( $file, $readonly )
{
    $myfile = fopen($file, "r") or die("Kann Datei ".$file." nicht öffnen!");
    $Zeilencounter = 0;
    $KommentarBlock = '';
    while(!feof($myfile)) {
        $Zeile = fgets($myfile);
        $Zeile = rtrim($Zeile);

        // Kommentarzeile
        if ((strpos($Zeile, ';') !== false) && (strpos($Zeile, ';') < 2)) {
            $KommentarZeilen[] = htmlspecialchars($Zeile);
            continue;
        }

        // Falls ein Kommentarblock fertig ist, jetzt ausgeben
        if (!empty($KommentarZeilen)) {
            $block = implode('<br>', $KommentarZeilen);
            echo '<tr class="comment"><td colspan="2">
                    <input type="hidden" name="Zeile['.$Zeilencounter.']" value=\''.$block.'\' >'.$block.'
                </td></tr>'."\n";
            $Zeilencounter++;
            $KommentarZeilen = [];
        }
    
        // Rest wie gehabt...
        if ((strpos($Zeile, '[') !== false) && (strpos($Zeile, '[') < 1)) {
            echo '<tr><th colspan="2"><input type="hidden" name="Zeile['.$Zeilencounter.']" value=\''.$Zeile.'\' >'.$Zeile.'</th></tr>'."\n";
        }
        elseif (strpos($Zeile, '=') !== false) {
            $Zeilenteil = explode("=", $Zeile, 2);
            $Zeilenteil[0] = trim($Zeilenteil[0]);
            $Zeilenteil[1] = trim($Zeilenteil[1]);
            echo '<tr><td><input type="hidden" name="Zeile['.$Zeilencounter.'][0]" value=\''.$Zeilenteil[0].' = \'>'.$Zeilenteil[0].'</td>'."\n";
            echo '<td><input type="text" name="Zeile['.$Zeilencounter.'][1]" value="'.htmlentities($Zeilenteil[1]).'" '.$readonly.'></td></tr>'."\n";
        } else {
            echo '<tr><td colspan="2"><input type="hidden" name="Zeile['.$Zeilencounter.']" value=\''.$Zeile.'\' >'.$Zeile.'</td></tr>'."\n";
        }

        $Zeilencounter++;
    }

    // Falls Datei mit Kommentar endet
    if (!empty($KommentarZeilen)) {
        $block = implode('<br>', $KommentarZeilen);
        echo '<tr class="comment"><td colspan="2">
                <input type="hidden" name="Zeile['.$Zeilencounter.']" value=\''.$block.'\' >'.$block.'
            </td></tr>'."\n";
    }
}

$case = '';
if (isset($_POST["case"])) $case = $_POST["case"];
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
echo '<input type="hidden" name="ini_file" value="'.$_POST["ini_file"].'">'."\n";
echo '<input type="hidden" name="case" value="">'."\n";
echo '<div class="button-container">';
echo '<button class="dateiauswahl" type="submit">Zurück zur Dateiauswahl</button>';
echo '&nbsp;<button class="Kommentare" type="button" onclick="toggleComments()">Kommentare ein/aus</button>';
echo '</div>';
echo '</form>'."\n";
echo '<br>';

echo '<b>"'.basename($_POST["ini_file"]).'" hier nur lesbar! <br>Zum editieren Button klicken!</b>';
echo '<br><br>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$_POST["ini_file"].'">'."\n";
echo '<input type="hidden" name="case" value="editieren">'."\n";
echo '<button type="submit">'.basename($_POST["ini_file"]).' editieren</button>';
echo '</form>'."\n";
echo '<br>';
echo '<table>';

config_lesen($_POST["ini_file"], 'readonly');

echo '</table>';
    break;

    case 'editieren':
# PASSWORDABFRAGE 
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$_POST["ini_file"].'">'."\n";
echo '<input type="hidden" name="case" value="">'."\n";
echo '<button class="dateiauswahl" type="submit">Zurück zur Dateiauswahl</button>';
echo '</form>'."\n";
echo '<br><br>';

echo '<span style="color:red"><b>ACHTUNG!!</b></span><br>evtl. Sicherungskopie der '.basename($_POST["ini_file"]).' erstellen.<br>';

echo '<br><br>';
echo 'Kennwort um '.basename($_POST["ini_file"]).' zu editieren:<br>';
echo '(Kennwortänderung in html/config.php)<br>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$_POST["ini_file"].'">'."\n";
echo '<input type="hidden" name="case" value="editieren_passwd">'."\n";
echo '<input type="password" name="password" size="10">'."\n";
echo '<button type="submit">OK</button>';
echo '</form>'."\n";
echo '<br>';

    break;

    case 'editieren_passwd':
# EDITIEREN DER INI-Datei 
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="ini_file" value="'.$_POST["ini_file"].'">'."\n";
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

config_lesen($_POST["ini_file"], '');

echo '</table>';
echo '<br>';
echo '<input type="hidden" name="ini_file" value="'.$_POST["ini_file"].'">'."\n";
echo '<input type="hidden" name="case" value="schreiben">'."\n";
echo '<button class="schreiben" type="submit" >'.basename($_POST["ini_file"]).' neu schreiben</button>';
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

$write = implode("\n", $final_lines);

if(is_writeable($_POST["ini_file"],)) {
    $handle = fopen($_POST["ini_file"],"w");
    if (fwrite($handle, $write)) {
        $nachricht= '<span style="color:green"> '.$_POST["ini_file"].' wurde neu geschrieben!</span>';
    } else {
        $nachricht= '<span style="color:red"> '.$_POST["ini_file"].' konnte nicht geschrieben werden!!!</span>';
    }
    fclose($handle);
} else {
    $nachricht= '<span style="color:red"> '.$_POST["ini_file"].' konnte nicht geschrieben werden!!!</span>';
}

header('location: '.$_SERVER["PHP_SELF"].'?nachricht='.$nachricht);
exit();
    break;
} # ENDE switch
?>
<script>
function toggleComments() {
    const rows = document.querySelectorAll('.comment');
    rows.forEach(row => {
        row.style.display = (row.style.display === 'none') ? '' : 'none';
    });
}
</script>


</body>
</html>
