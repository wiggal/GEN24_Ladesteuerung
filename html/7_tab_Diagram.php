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
$SQLite_file = "../PV_Daten.sqlite";
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
    echo "\nSQLitetabellen strompreise bzw. priceforecast existieren nicht, keine Grafik verfügbar!<br>
    Die Tabellen werden durch das Logging von DynamicPriceCheck.py erzeugt!";
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

# Schalter für Durchschnitspeis übergeben
$durchschnitt = 'nein';
$durchschnitt_checked = '';
if (!empty($_POST['durchschnitt'])) $durchschnitt = ($_POST['durchschnitt']);
if ($durchschnitt == 'ja') $durchschnitt_checked = 'checked';

# programmpunkt = option 
$programmpunkt = 'Produktion';
if (!empty($_POST["programmpunkt"])) $programmpunkt = $_POST["programmpunkt"];

# Zeitraum = hours, day, mounth, year
$Zeitraum = 'stunden';
if (!empty($_POST["Zeitraum"])) $Zeitraum = $_POST["Zeitraum"];

# ProduktionsSQL und Daten holen
# DiaDatenBis um 5 Minuten erhöhen, damit der Zähler XX:01 auch noch erfasst wird
$DiaDatenBis_SQL = date('Y-m-d 00:05', strtotime($DiaDatenBis));

$groupSTR = '%Y-%m-%d %H';
$Tag = date_format(date_create($DiaDatenVon), str_replace("%","",'%Y-%m-%d'));

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

# Funktion Schalter aufrufen
schalter_ausgeben($DBersterTag, $DBletzterTag, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $DC_Produktion, $AC_Verbrauch, $Strompreis_Dia_optionen, $Tag, $durchschnitt_checked);

$SQL = getSQL('daten', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR, $groupSTR);
$results = $db->query($SQL);

# Diagrammdaten und Optionen holen
list($daten, $labels, $MIN_y3, $MAX_y, $MAX_y3) = diagrammdaten($results, $Zeitraum);

# Preisstatistikdaten erzeugen
if ($durchschnitt == 'ja') {
    $Preisstatistik = Preisberechnung($DiaDatenVon, $DiaDatenBis_SQL, $groupSTR, $db);
} else {
    $Preisstatistik = '';
    }

# Nun Barchart ausgeben
    echo "<div class='container'>
    <canvas id='PVDaten' style='height:100vh; width:100vw'></canvas>
</div>";
Diagram_ausgabe($labels, $daten, $Strompreis_Dia_optionen, $Preisstatistik,  $MIN_y3, $MAX_y, $MAX_y3);

$db->close();
} # END if ($programmpunkt == 'option') {
?>
    </body>
</html>
