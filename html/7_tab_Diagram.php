<!doctype html>
<html>
    <head>
    <title>Strompreise</title>
    <script src="chart.js"></script>
    <script src="chartjs-plugin-datalabels.js"></script>
    <style>
    html, body {
        height: 98%;
        margin: 0px;
    }
    .container {
        height: 100%;
    }
    .navi {
    cursor:pointer;
    color:#000000;
    font-family:Arial;
    font-size: 150%;
    padding:6px 11px;
  }
    .optionwahl {
    cursor:pointer;
    color:#000000;
    font-family:Arial;
    font-size: 200%;
    padding:6px 11px;
  }
    .date {
    cursor:pointer;
    color:#000000;
    font-family:Arial;
    font-size: 150%;
    padding:6px 11px;
  }
  table {
  width: 95%;
  border: 1px solid;
  position: absolute;
  }
  td {
  white-space: nowrap;
  font-family: Arial;
  }

</style>
    </head>
    <body>


<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}
include "7_funktion_Diagram.php";

# Prüfen ob SQLite Voraussetzungen vorhanden sind
$SQLite_file = "../" . $python_config['Logging']['Logging_file'];
if (!file_exists($SQLite_file)) {
    echo "\nSQLitedatei $filename existiert nicht, keine Grafik verfügbar!";
    echo "</body></html>";
    exit();
}

# Variablendefinitionen
$labels = '';
$daten = array();

# Datenbankverbindung herstellen und ersten und letzten Tag ermitteln
$db = new SQLite3($SQLite_file);
# Prüfen, ob die Strompreistabellen existieren
$query = "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('strompreise', 'priceforecast');";
$result = $db->query($query);
$count = 0;
while ($row = $result->fetchArray()) {
    $count++;
}
if ($count != 2) {
    echo "\nSQLitetabellen strompreise bzw. priceforecast existieren nicht, keine Grafik verfügbar!";
    echo "</body></html>";
    exit();
}

$DBersterTag = $GLOBALS['db']->querySingle('SELECT MIN(Zeitpunkt) from strompreise');
$DBletzterTag = strtotime($GLOBALS['db']->querySingle('SELECT MAX(Zeitpunkt) from strompreise'));
$DBletzterTag = date('Y-m-d 00:00', $DBletzterTag);

# Diagrammtag festlegen
# UND _POST_VAR auslesen
$heute =  date("Y-m-d 00:00");
$morgen =  date("Y-m-d 00:00",(strtotime("+1 day", strtotime(date("Y-m-d")))));
$DiaDatenVon = $heute;
$DiaDatenBis = $morgen;
if (!empty($_POST["DiaDatenVon"])) $DiaDatenVon = str_replace("T"," ",$_POST["DiaDatenVon"]);
$DiaDatenBis =  date("Y-m-d 00:00",(strtotime("+1 day", strtotime($DiaDatenVon))));
# Anfangszeitraum  bei Start setzen
if (empty($_POST["AnfangVon"])) $_POST["AnfangVon"] = $DiaDatenVon;
if (empty($_POST["AnfangBis"])) $_POST["AnfangBis"] = $DiaDatenBis;

$diagramtype = 'bar';

# programmpunkt = option 
$programmpunkt = 'Produktion';
if (!empty($_POST["programmpunkt"])) $programmpunkt = $_POST["programmpunkt"];

# Zeitraum = hours, day, mounth, year
$Zeitraum = 'stunden';
if (!empty($_POST["Zeitraum"])) $Zeitraum = $_POST["Zeitraum"];

# ProduktionsSQL und Daten holen
# DiaDatenBis um 5 Minuten erhöhen, damit der Zähler XX:01 auch noch erfasst wird
$DiaDatenBis_SQL = date('Y-m-d 00:05', strtotime($DiaDatenBis));

$groupSTR = '%Y-%m-%d';
switch ($Zeitraum) {
    case 'stunden': $groupSTR = '%Y-%m-%d %H'; break;
    case 'tage': $groupSTR = '%Y-%m-%d'; break;
}

#$Footer_groupSTR = str_replace(" ","\T",$groupSTR);
$Footer_groupSTR = str_replace(" %H","",$groupSTR);
$Footer_DiaDatenVon = date_format(date_create($DiaDatenVon), str_replace("%","",$Footer_groupSTR));
# Eine Minute von DiaDatenBis abziehen
$Footer_DiaDatenBis = date_format(date_add(date_create($DiaDatenBis), date_interval_create_from_date_string("-1 minutes")), str_replace("%","",$Footer_groupSTR));

if ( $Footer_DiaDatenBis != '' and $Footer_DiaDatenVon != $Footer_DiaDatenBis ) {
    $Footer = $Footer_DiaDatenVon . ' bis '.$Footer_DiaDatenBis;
} else {
    $Footer = $Footer_DiaDatenVon;
}

# END _POST_VAR auslesen
# Erstes Jahr aus DB, wenn alle Jahre dargestellt werden sollen
$DBersterTag_Jahr = date_format(date_create($DBersterTag), 'Y');
if ($programmpunkt == 'option') {
    Optionenausgabe($DBersterTag_Jahr);
} else {

# AC Produktion 
$SQL = getSQL('Netzladen', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
$DC_Produktion = round($db->querySingle($SQL)/1000, 1);
# Netzverbrauch
$SQL = getSQL('Netzverbrauch', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
$AC_Verbrauch = round($db->querySingle($SQL)/1000, 1);

# Diagrammtype bar
# Funktion Schalter aufrufen
schalter_ausgeben($DBersterTag, $DBletzterTag, $diagramtype, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $DC_Produktion, $AC_Verbrauch, $Strompreis_Dia_optionen);

$SQL = getSQL('bar', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR, $groupSTR);
$results = $db->query($SQL);

# Diagrammdaten und Optionen holen
$DB_Werte = array('Netzverbrauch', 'Netzladen', 'Bruttopreis');
list($daten, $labels) = diagrammdaten($results, $DB_Werte, $Zeitraum);

# Nun Barchart ausgeben
    echo "<div class='container'>
    <canvas id='PVDaten' style='height:100vh; width:100vw'></canvas>
</div>";
Diagram_ausgabe($Footer, 'bar', $labels, $daten, $Strompreis_Dia_optionen);

$db->close();
} # END if ($programmpunkt == 'option') {

?>
    </body>
</html>
