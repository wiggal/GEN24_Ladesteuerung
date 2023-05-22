<?php
include "config.php";
$path_parts = pathinfo($PrognoseFile);
$config_ini = file_get_contents($path_parts['dirname'].'/config.ini');
echo nl2br($config_ini);
?>
