<?php
// Hier die Pythonkonfigs lesen
if(file_exists("../CONFIG/default_priv.ini")){
    $python_config = parse_ini_file("../CONFIG/default_priv.ini", true);
} else {
    $python_config = parse_ini_file("../CONFIG/default.ini", true);
}
$PrognoseFile = "../weatherData.json";
$PV_Leistung_KWp = 11.4;
$Faktor_PVLeistung_Prognose = 1.00;
$Res_Feld1 = "EV_1";
$Res_Feld2 = "EV_2";
$passwd_configedit = "0815";
// Hier können die TABs konfiguriert werden (Name, Dateiname, Starttab, anzeigen ja/nein)
$TAB_config = array (
                array ( 'name' => 'LadeStrg','file' => '1_tab_LadeSteuerung.php','checked' => 'ja','sichtbar' => 'ein'),
                array ( 'name' => 'ENTLadeStrg', 'file' => '2_tab_EntladeSteuerung.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'config','file' => '4_tab_config_ini.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'Logfile','file' => '5_tab_Crontab_log.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'GEN24','file' => '6_tab_GEN24.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'PV-Bilanz','file' => '7_tab_Diagram.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'QZ-Bilanz','file' => '8_tab_Diagram.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'Settings','file' => '9_tab_settigs.php','checked' => 'nein','sichtbar' => 'ein'),
            );
?>
