<?php
# config.ini parsen
require_once "config_parser.php";

$file = $PythonDIR.'/CONFIG/default.ini';
if(file_exists($PythonDIR.'/CONFIG/default_priv.ini')){
    $file = $PythonDIR.'/CONFIG/default_priv.ini';
}

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
            }
}
header("Location: http://$Zeilenteil[1]");
?>
