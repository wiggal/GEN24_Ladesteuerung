    <script src="chart.js"></script>
    <script src="chartjs-adapter-date-fns.js"></script>
    <style>
    html, body {
        height: 98%;
        margin: 0px;
    }
    .container {
      width: 100%;
      height: calc(100dvh - 35px - 60px); /* Header + Tabelle */
    }
    #PVDaten {
    width: 100%;
    height: 100%;
    display: block;
    }
    .navi {
    cursor:pointer;
    color:#000000;
    font-size: 150%;
    padding:6px 11px;
  }
    .summen {
    text-align:right;
    font-size: 170%;
  }
    .optionwahl {
    cursor:pointer;
    color:#000000;
    font-size: 200%;
    padding: 6px;
  }
    input[type="radio"] {
    margin: 0 !important;
    padding: 0 !important;
  }
    .date {
    cursor:pointer;
    color:#000000;
    font-size: 150%;
    padding:6px 11px;
  }
  table {
  width: 98%;
  border: 1px solid;
  position: absolute;
  margin-top: 5px;
  }
  td {
  white-space: nowrap;
  }

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
    h1 {
        font-size: 16px;
    }
    .navi {
    color:#000000;
    font-size: 15px;
    padding:3px 6px;
    }
    #schaltertable {
      width: 95%;
    }
    #schaltertable td.summen,
    #schaltertable button {
        font-size: 14px;
    }
  .optionwahl {
    font-size: 15px;
    padding: 1px !important;
}
  .date {
    font-size: 15px;
  }
}
</style>

<?php
# config.ini parsen
require_once "config_parser.php";

include "8_funktion_Diagram.php";

# Prüfen ob SQLite Voraussetzungen vorhanden sind
$SQLite_file = $PythonDIR."/PV_Daten.sqlite";
if (!file_exists($SQLite_file)) {
    echo "\nSQLitedatei $SQLite_file existiert nicht, keine Grafik verfügbar!";
    echo "</body></html>";
    exit();
}
# Datenbankverbindung herstellen
$db = new SQLite3($SQLite_file);
// Abfrage der internen sqlite_master Tabelle
$result = $db->querySingle("SELECT name FROM sqlite_master WHERE type='table' AND name='pv_daten'");
if (!$result) {
    echo "SQLitetabelle pv_daten existiert nicht, keine Grafik verfügbar!<br>";
    echo "Die Tabelle wird durch das Logging von EnergyController.py erzeugt!";
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
# X-Achsen konfiguration je nach Diagramm
$X_ACHSE_min_day = date('Y-m-d', strtotime($DiaDatenVon));
$groupSTR = '%Y-%m-%d';
switch ($Zeitraum) {
    case 'stunden':
        $groupSTR = '%Y-%m-%d %H';
        $X_Achse['unit'] = 'hour';
        $X_Achse['displayFormat'] = "hour: 'HH:mm'";
        $X_Achse['tooltipFormat'] = 'HH:mm dd.MM.yy';
        $X_Achse['min'] = $X_ACHSE_min_day.' 00:00:00';
        $X_Achse['max'] = date('Y-m-d 23:59:59', strtotime('-1 day', strtotime($DiaDatenBis)));
        break;
    case 'tage':
        $groupSTR = '%Y-%m-%d';
        $X_Achse['unit'] = 'day';
        $X_Achse['displayFormat'] = "day: 'dd'";
        $X_Achse['tooltipFormat'] = 'EEE dd.MM.yy';
        $X_Achse['min'] = $X_ACHSE_min_day.' 00:00:00';
        $X_Achse['max'] = date('Y-m-d 00:00:00', strtotime('-1 day', strtotime($DiaDatenBis)));
        break;
    case 'monate':
        $groupSTR = '%Y-%m';
        $X_Achse['unit'] = 'month';
        $X_Achse['displayFormat'] = "month: 'MMM'";
        $X_Achse['tooltipFormat'] = 'MMM yyyy';
        $X_Achse['min'] = $X_ACHSE_min_day.' 00:00:00';
        $X_Achse['max'] = date('Y-m-d 00:00:00', strtotime('-1 month', strtotime($DiaDatenBis)));
        break;
    case 'jahre':
        $groupSTR = '%Y';
        $X_Achse['unit'] = 'year';
        $X_Achse['displayFormat'] = "year: 'yyyy'";
        $X_Achse['tooltipFormat'] = 'yyyy';
        $X_Achse['min'] = $X_ACHSE_min_day.' 00:00:00';
        $X_Achse['max'] = '';
        break;
}

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
    Optionenausgabe($DBersterTag_Jahr, $activeTab);
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
    schalter_ausgeben($DBersterTag, $diagramtype, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $DC_Produktion, $AC_Verbrauch, $activeTab);

    # ProduktionsSQL und Daten holen
    $SQL = getSQL('line', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
    $results = $db->query($SQL);

    # Diagrammdaten und Optionen holen
    $DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Netzverbrauch');
    list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1', $Zeitraum);
    $optionen = Dia_Options('line');

    # Nun Linechart ausgeben
    if (empty($daten)) {
        echo '<br><br><p class="navi">Keine Daten für ausgewählten Tag vorhanden!!</p>';
    } else {
        echo "\n<div class='container'>
            <canvas id='PVDaten'></canvas>
        </div>";
    }

Diagram_ausgabe($Footer, 'line', $labels, $daten, $optionen, 'W', $Diagrammgrenze, $X_Achse);

} else {  # Dann bar = Balkendiagramm

    # Funktion Schalter aufrufen
    schalter_ausgeben($DBersterTag, $diagramtype, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $DC_Produktion, $AC_Verbrauch, $activeTab);

    $SQL = getSQL('bar', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR, $groupSTR);
    $results = $db->query($SQL);

    # Diagrammdaten und Optionen holen
    $DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Direktverbrauch');
    list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1000', $Zeitraum);
    $optionen = Dia_Options('bar');

    # Nun Barchart ausgeben
    if (empty($daten)) {
        echo '<br><br><p class="navi">Keine Daten für ausgewählten Tag vorhanden!!</p>';
    } else {
        echo "\n<div class='container'>
            <canvas id='PVDaten'></canvas>
        </div>";
    }

Diagram_ausgabe($Footer, 'bar', $labels, $daten, $optionen, 'kWh', $Diagrammgrenze, $X_Achse);

} # END if ($diagramtype == 

    $db->close();
} # END if ($energietype == 'option') {

?>
