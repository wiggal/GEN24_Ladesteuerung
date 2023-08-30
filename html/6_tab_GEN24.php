<!DOCTYPE html>
<html>
<body>
<?php
include "config.php";
$path_parts = pathinfo($PrognoseFile);
$file = $path_parts['dirname'].'/config.ini';

$case = '';
if (isset($_POST["case"])) $case = $_POST["case"];
$nachricht = '';
if (isset($_GET["nachricht"])) $nachricht = $_GET["nachricht"];
if ($nachricht != '') echo $nachricht . "<br><br>";

$myfile = fopen($file, "r") or die("Kann Datei ".$file." nicht öffnen!");
$Zeilencounter = 0;
while(!feof($myfile)) {
    $Zeile = fgets($myfile);
    $Zeilencounter++;

    # Suche nach Kommentarzeilen
            # Hier die Variablenbelegung suchen
            if ((strpos($Zeile, '=') !== false) and (strpos($Zeile, 'hostNameOrIp') !== false)) {
                $Zeilenteil = explode("=", $Zeile);
                $Zeilenteil[1] = ltrim(rtrim($Zeilenteil[1]));
                # echo '<td><input type="text" name="Zeile['.$Zeilencounter.'][1]" value=\''.$Zeilenteil[1].'\'></td></tr>'."\n";
            }
}
header("Location: http://$Zeilenteil[1]");
?>
</body>
</html>
