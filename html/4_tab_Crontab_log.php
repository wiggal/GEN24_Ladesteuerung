<html>
<head>
<style>
button {
  font-size: 1.3em;
  background-color: #4CAF50;
}
@media screen and (max-width: 64em) {
body{ font-size: 160%; }
input { font-size: 100%; }
}
</style>
</head>
<body>
<a name="top" href="#bottom">Ans Ende springen!</a>
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
?>

<a name="bottom" href="#top">An den Anfang springen!</a>
<br><br>
<form method="post" action="#bottom" enctype="multipart/form-data">
<button type="submit">Neu laden</button>
</form>
</body>
</html>
