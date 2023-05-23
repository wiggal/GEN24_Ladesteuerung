<html>
<body>
<a href="#bottom">Ans Ende springen!</a>
<br><br><br>
<?php
include "config.php";
$path_parts = pathinfo($PrognoseFile);
$file = $path_parts['dirname'].'/Crontab.log';
$myfile = fopen($file, "r") or die("Kann Datei nicht öffnen!");
$Ausgabe = 0;
$datum = date("Y-m-d", time());

while(!feof($myfile)) {
    $Zeile = fgets($myfile);
    if (strpos($Zeile, $datum) !== false) $Ausgabe = 1;
    if ($Ausgabe == 1) {
        echo $Zeile . "<br>";
    }
  }
#$config_ini = file_get_contents($path_parts['dirname'].'/Crontab.log');
#echo nl2br($config_ini);
?>

<a name="bottom" href="#top">An den Anfang springen!</a>
</body>
</html>
