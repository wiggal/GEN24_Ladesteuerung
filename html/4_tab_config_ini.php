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
button {
  font-size: 1.3em;
  background-color: #4CAF50;
}
@media screen and (max-width: 64em) {
body{ font-size: 160%; }
input { font-size: 100%; }
th { font-size: 1.5em; }
td {font-size: 160%;
    width:48%;
	max-width: 120px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
/*
td:hover {
  overflow: visible;
}
td { width: 50px; }
button { font-size: 3.0em; }
*/
}

</style>
</head>
<body>

<?php
# <h1>config.ini</h1>
include "config.php";

function config_lesen( $file, $readonly )
{
    $myfile = fopen($file, "r") or die("Kann Datei ".$file." nicht öffnen!");
    $Zeilencounter = 0;
    while(!feof($myfile)) {
        $Zeile = fgets($myfile);
        $Zeilencounter++;

        # Suche nach Kommentarzeilen
        if ((strpos($Zeile, ';') !== false) AND (strpos($Zeile, ';') < 2)) {
            $Zeile = rtrim($Zeile);
            echo '<tr class="comment"><td colspan="2"><input type="hidden" name="Zeile['.$Zeilencounter.']" value=\''.$Zeile.'\' >'.$Zeile.'</td></tr>'."\n";
        } else {
            # Hier die Configblöcke suchen []
            if ((strpos($Zeile, '[') !== false) AND (strpos($Zeile, '[') < 1)) {
                $Zeile = rtrim($Zeile);
                echo '<tr><th colspan="2"><input type="hidden" name="Zeile['.$Zeilencounter.']" value=\''.$Zeile.'\' >'.$Zeile.'</th></tr>'."\n";
            } else {
                # Hier die Variablenbelegung suchen
                if ((strpos($Zeile, '=') !== false)) {
                    $Zeilenteil = explode("=", $Zeile);
                    $Zeilenteil[0] = ltrim(rtrim($Zeilenteil[0]));
                    $Zeilenteil[1] = ltrim(rtrim($Zeilenteil[1]));
                    echo '<tr><td><input type="hidden" name="Zeile['.$Zeilencounter.'][0]" value=\''.$Zeilenteil[0].' = \'>'.$Zeilenteil[0].'</td>'."\n";
                    echo '<td><input type="text" name="Zeile['.$Zeilencounter.'][1]" value="'.$Zeilenteil[1].'" '.$readonly.'></td></tr>'."\n";
                } else {
                    #hier noch die Leerzeilen behandeln
                    $Zeile = rtrim($Zeile);
                    echo '<tr><td colspan="2"><input type="hidden" name="Zeile['.$Zeilencounter.']" value=\''.$Zeile.'\' >'.$Zeile.'</td></tr>'."\n";
                }
            }
        }
    }
}

$path_parts = pathinfo($PrognoseFile);
$file = $path_parts['dirname'].'/config.ini';

$case = '';
if (isset($_POST["case"])) $case = $_POST["case"];
$nachricht = '';
if (isset($_GET["nachricht"])) $nachricht = $_GET["nachricht"];
if ($nachricht != '') echo $nachricht . "<br><br>";

switch ($case) {
    case '':
# AUSGEBEN DER config.ini

echo '<b>"config.ini" hier nur lesbar! <br>Zum editieren Button klicken!</b>';
echo '<br><br>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="case" value="editieren">'."\n";
echo '<button type="submit">config.ini editieren</button>';
echo '</form>'."\n";
echo '<br>';
echo '<table>';

config_lesen($file, 'readonly');

echo '</table>';
    break;

    case 'editieren':
# PASSWORDABFRAGE 
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="case" value="">'."\n";
echo '<button type="submit">Zurück zu config.ini lesen</button>';
echo '</form>'."\n";
echo '<br><br>';

echo '<span style="color:red"><b>ACHTUNG!!</b></span><br>evtl. Sicherungskopie der config.ini erstellen.<br>';

echo '<br><br>';
echo 'Kennwort um config.ini zu editieren:<br>';
echo '(Kennwortänderung in html/config.php)<br>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="case" value="editieren_passwd">'."\n";
echo '<input type="password" name="password" size="10">'."\n";
echo '<button type="submit">OK</button>';
echo '</form>'."\n";
echo '<br>';

    break;

    case 'editieren_passwd':
# EDITIEREN DER config.ini 
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="case" value="">'."\n";
echo '<button type="submit">Zurück zu config.ini lesen</button>';
echo '</form>'."\n";
echo '<br>';

if ($_POST["password"] == $passwd_configedit) {

echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<table>';

config_lesen($file, '');

echo '</table>';
echo '<br>';
echo '<input type="hidden" name="case" value="schreiben">'."\n";
echo '<button type="submit">config.ini neu schreiben</button>';
echo '</form>';
    } else {
    echo '<br><br> <span style="color:red"><b> Falsches Kennwort!!</b></span>';
    } # if passwd
    break;

    case 'schreiben':
# SCHREIBEN DER config.ini
$write = '';
$Zeile = $_POST["Zeile"];
foreach($Zeile AS $zeile_key => $zeile_value) {
 if(is_array($zeile_value)){
 $Zeile[$zeile_key] = $Zeile[$zeile_key]['0'].$Zeile[$zeile_key]['1'];
 }
 $Zeile[$zeile_key] = rtrim($Zeile[$zeile_key]);
}
$write = implode("\n",$Zeile);
if(is_writeable($file,)) {
    $handle = fopen($file,"w");
    if (fwrite($handle, $write)) {
        $nachricht= '<span style="color:green"> '.$file.' wurde neu geschrieben!</span>';
    } else {
        $nachricht= '<span style="color:red"> '.$file.' konnte nicht geschrieben werden!!!</span>';
    }
    fclose($handle);
} else {
    $nachricht= '<span style="color:red"> '.$file.' konnte nicht geschrieben werden!!!</span>';
}

header('location: '.$_SERVER["PHP_SELF"].'?nachricht='.$nachricht);
exit();
    break;
} # ENDE switch
?>

</body>
</html>
