<?php
// Hier die ../config.ini aus dem Pythonverzeichnis lesen
$python_config = parse_ini_file("../config.ini", true);
// Hier die Variablen für die PV-Reservierung definieren
$PrognoseFile = "../weatherData.json";
$ReservierungsFile = "EV_Reservierung.json";
$WattReservierungsFile = "../Watt_Reservierung.json";
$EntLadeSteuerFile = "../Akku_EntLadeSteuerFile.json";
$PV_Leistung_KWp = 11.4;
$Faktor_PVLeistung_Prognose = 1.00;
$Res_Feld1 = "EV_1";
$Res_Feld2 = "EV_2";
$passwd_configedit = "0815";
$TAB_config = array (
                array ( 'name' => 'LadeStrg','file' => '1_tab_LadeSteuerung.php','checked' => 'ja','sichtbar' => 'ein'),
                array ( 'name' => 'ENTLadeStrg', 'file' => '2_tab_EntladeSteuerung.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'Hilfe','file' => '3_tab_Hilfe.html','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'config','file' => '4_tab_config_ini.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'Logfile','file' => '5_tab_Crontab_log.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'GEN24','file' => '6_tab_GEN24.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'Diagramm','file' => '7_tab_Diagram.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'Diagramm2','file' => '8_tab_Diagram.php','checked' => 'nein','sichtbar' => 'ein'),
            );
?>
