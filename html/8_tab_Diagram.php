<!doctype html>
<html>
    <head>
    <title>Diagramme</title>
    <script src="chart.js"></script>
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
include "8_funktion_Diagram.php";

# Prüfen ob SQLite Voraussetzungen vorhanden sind
$SQLite_file = "../PV_Daten.sqlite";
if (!file_exists($SQLite_file)) {
    echo "\nSQLitedatei $filename existiert nicht, keine Grafik verfügbar!";
    echo "</body></html>";
    exit();
}

# Variablendefinitionen
$labels = '';
$daten = array();
$optionen = '';

# Diagrammtag festlegen
# UND _POST_VAR auslesen
$heute = date("Y-m-d 00:00");
$morgen =  date("Y-m-d 00:00",(strtotime("+1 day", strtotime(date("Y-m-d")))));
$DiaDatenVon = $heute;
$DiaDatenBis = $morgen;
if (!empty($_POST["DiaDatenVon"])) $DiaDatenVon = str_replace("T"," ",$_POST["DiaDatenVon"]);
if (!empty($_POST["DiaDatenBis"])) $DiaDatenBis = str_replace("T"," ",$_POST["DiaDatenBis"]);
# Anfangszeitraum  bei Start setzen
if (empty($_POST["AnfangVon"])) $_POST["AnfangVon"] = $DiaDatenVon;
if (empty($_POST["AnfangBis"])) $_POST["AnfangBis"] = $DiaDatenBis;

# energietype = Verbrauch oder Produktion
$energietype = 'Produktion';
if (!empty($_POST["energietype"])) $energietype = $_POST["energietype"];

# diagramtype = line oder bar
$diagramtype = 'line';
if (!empty($_POST["diagramtype"])) $diagramtype = $_POST["diagramtype"];

# Zeitraum = hours, day, mounth, year
$Zeitraum = 'stunden';
if (!empty($_POST["Zeitraum"])) $Zeitraum = $_POST["Zeitraum"];

# ProduktionsSQL und Daten holen
$groupSTR = '%Y-%m-%d';
switch ($Zeitraum) {
    case 'stunden': $groupSTR = '%Y-%m-%d %H'; break;
    case 'tage': $groupSTR = '%Y-%m-%d'; break;
    case 'monate': $groupSTR = '%Y-%m'; break;
    case 'jahre': $groupSTR = '%Y'; break;
}

# Datenbankverbindung herstellen
$db = new SQLite3($SQLite_file);
$DBersterTag = $GLOBALS['db']->querySingle('SELECT MIN(Zeitpunkt) from pv_daten');

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
# DiaDatenBis um 5 Minuten erhöhen, damit der Zähler XX:01 auch noch erfasst wird
$DiaDatenBis_SQL = date('Y-m-d 00:05', strtotime($DiaDatenBis));
$DBersterTag_Jahr = date_format(date_create($DBersterTag), 'Y');
if ($energietype == 'option') {
    Optionenausgabe($DBersterTag_Jahr);
} else {

# AC Produktion 
$SQL = getSQL('SUM_DC_Produktion', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
$DC_Produktion = round($db->querySingle($SQL)/1000, 1);
# AC Verbrauch
$SQL = getSQL('SUM_AC_Verbrauch', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
$AC_Verbrauch = round($db->querySingle($SQL)/1000, 1);

# Diagrammtype Auswahl
if ($diagramtype == 'line') {
    # Funktion Schalter aufrufen
    schalter_ausgeben($DBersterTag, $diagramtype, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $DC_Produktion, $AC_Verbrauch);

    # ProduktionsSQL und Daten holen
    $SQL = getSQL('line', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
    $results = $db->query($SQL);

    # Diagrammdaten und Optionen holen
    $DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Netzverbrauch');
    list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1', $Zeitraum);
    $optionen = Dia_Options('line');

    # Nun Linechart ausgeben
    echo "<div class='container'>
        <canvas id='PVDaten' style='height:100vh; width:100vw'></canvas>
    </div>";
Diagram_ausgabe($Footer, 'line', $labels, $daten, $optionen, 'Wh', $Diagrammgrenze);
} else {  # Dann bar = Balkendiagramm

    # Funktion Schalter aufrufen
    schalter_ausgeben($DBersterTag, $diagramtype, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $DC_Produktion, $AC_Verbrauch);

    $SQL = getSQL('bar', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR, $groupSTR);
    $results = $db->query($SQL);

    # Diagrammdaten und Optionen holen
    $DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Direktverbrauch');
    list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1000', $Zeitraum);
    $optionen = Dia_Options('bar');

    # Nun Barchart ausgeben
    echo "<div class='container'>
        <canvas id='PVDaten' style='height:100vh; width:100vw'></canvas>
    </div>";
    Diagram_ausgabe($Footer, 'bar', $labels, $daten, $optionen, 'kWh', $Diagrammgrenze);

} # END if ($diagramtype == 
    $db->close();
} # END if ($energietype == 'option') {

?>
    </body>
</html>
