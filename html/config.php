<?php
$PrognoseFile = "../weatherData.json";
$PV_Leistung_KWp = 11.4;
$Faktor_PVLeistung_Prognose = 1.00;
$Diagrammgrenze = 25000;
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
                array ( 'name' => 'Strompreis','file' => '7_tab_Diagram.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'QZ-Bilanz','file' => '8_tab_Diagram.php','checked' => 'nein','sichtbar' => 'ein'),
                array ( 'name' => 'Settings','file' => '9_tab_settigs.php','checked' => 'nein','sichtbar' => 'ein'),
            );
# Optionen für das Strompreisdiagramm
$Strompreis_Dia_optionen = array();
$Strompreis_Dia_optionen['BattStatus']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'1','linewidth'=>'4','order'=>'0','yAxisID'=>'y2','hidden'=>'false','type'=>'line','unit'=>'%','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['Boersenpreis']=['Farbe'=>'rgba(255,51,51,0.6)','fill'=>'true','stack'=>'3','linewidth'=>'0','order'=>'0','yAxisID'=>'y3','hidden'=>'false','type'=>'line','unit'=>'ct','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['Bruttopreis']=['Farbe'=>'rgba(255,51,51,1)','fill'=>'false','stack'=>'32','linewidth'=>'0','order'=>'0','yAxisID'=>'y3','hidden'=>'false','type'=>'bar','unit'=>'','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['Netzladen']=['Farbe'=>'rgba(60,215,60,1)','fill'=>'true','stack'=>'2','linewidth'=>'0','order'=>'4','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'W','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['Netzverbrauch']=['Farbe'=>'rgba(110,110,110,1)','fill'=>'true','stack'=>'2','linewidth'=>'0','order'=>'2','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'W','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['Vorhersage']=['Farbe'=>'rgba(255,140,05,1)','fill'=>'false','stack'=>'0','linewidth'=>'4','order'=>'0','yAxisID'=>'y','hidden'=>'false','type'=>'line','unit'=>'W','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['PV_Prognose']=['Farbe'=>'rgba(255,140,05,0.5)','fill'=>'false','stack'=>'10','linewidth'=>'4','order'=>'0','yAxisID'=>'y','hidden'=>'false','type'=>'line','unit'=>'W','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['PrognBattStatus']=['Farbe'=>'rgba(72,118,255,0.5)','fill'=>'false','stack'=>'11','linewidth'=>'4','order'=>'0','yAxisID'=>'y2','hidden'=>'false','type'=>'line','unit'=>'%','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['PrognNetzladen']=['Farbe'=>'rgba(60,215,60,0.5)','fill'=>'true','stack'=>'12','linewidth'=>'0','order'=>'4','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'W','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['PrognNetzverbrauch']=['Farbe'=>'rgba(110,110,110,0.5)','fill'=>'true','stack'=>'12','linewidth'=>'0','order'=>'2','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'W','showLabel'=>'false','decimals'=>'0'];
?>
