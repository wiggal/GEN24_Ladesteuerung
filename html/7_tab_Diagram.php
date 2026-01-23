    <script src="chart.js"></script>
    <script src="chartjs-plugin-datalabels.js"></script>
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
    font-family:Arial;
    font-size: 150%;
    padding:6px 11px;
  }
    .summen {
    text-align:right;
    font-size: 170%;
    padding: 0px 6px;
  }
    .optionwahl {
    cursor:pointer;
    color:#000000;
    font-family:Arial;
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
    font-family:Arial;
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
  font-family: Arial;
  }
  .mobile-text {
  display: none;
  }

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
    h1 {
        font-size: 16px;
    }
    .navi {
    color:#000000;
    font-family:Arial;
    font-size: 14px;
    padding:3px;
    }
    #schaltertable {
      width: 55%;
    }
    /* Verkleinert die Schrift "Statistik" */
    #schaltertable th,
    #schaltertable td {
        font-size: 13px;
        padding: 2px;
    }

    #schaltertable td.summen,
    #schaltertable button {
        font-size: 13px;
        padding: 1px !important;
    }
    .optionwahl {
      font-size: 15px;
      padding: 1px !important;
    }
    .date {
      font-size: 15px;
    }
    .desktop-text {
      display: none;
    }
    .mobile-text {
      display: inline;
    }
}

</style>

<?php
# config.ini parsen
require_once "config_parser.php";

# Optionen für das Strompreisdiagramm
$Strompreis_Dia_optionen['BattStatus']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'1','linewidth'=>'4','order'=>'0','yAxisID'=>'y2','hidden'=>'false','type'=>'line','unit'=>'%','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['Boersenpreis']=['Farbe'=>'rgba(255,51,51,0.4)','fill'=>'true','stack'=>'3','linewidth'=>'0','order'=>'0','yAxisID'=>'y3','hidden'=>'false','type'=>'line','unit'=>'ct','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['Bruttopreis']=['Farbe'=>'rgba(255,51,51,1)','fill'=>'false','stack'=>'32','linewidth'=>'0','order'=>'0','yAxisID'=>'y3','hidden'=>'false','type'=>'bar','unit'=>'','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['Netzladen']=['Farbe'=>'rgba(60,215,60,1)','fill'=>'true','stack'=>'2','linewidth'=>'0','order'=>'4','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'Wh','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['Netzverbrauch']=['Farbe'=>'rgba(110,110,110,1)','fill'=>'true','stack'=>'2','linewidth'=>'0','order'=>'2','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'Wh','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['Vorhersage']=['Farbe'=>'rgba(255,140,05,1)','fill'=>'false','stack'=>'0','linewidth'=>'4','order'=>'0','yAxisID'=>'y','hidden'=>'false','type'=>'line','unit'=>'Wh','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['PV_Prognose']=['Farbe'=>'rgba(255,140,05,0.6)','fill'=>'false','stack'=>'10','linewidth'=>'4','order'=>'0','yAxisID'=>'y','hidden'=>'false','type'=>'line','unit'=>'Wh','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['PrognBattStatus']=['Farbe'=>'rgba(72,118,255,0.6)','fill'=>'false','stack'=>'11','linewidth'=>'4','order'=>'0','yAxisID'=>'y2','hidden'=>'false','type'=>'line','unit'=>'%','showLabel'=>'false','decimals'=>'1'];
$Strompreis_Dia_optionen['PrognNetzladen']=['Farbe'=>'rgba(60,215,60,0.6)','fill'=>'true','stack'=>'12','linewidth'=>'0','order'=>'4','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'Wh','showLabel'=>'false','decimals'=>'0'];
$Strompreis_Dia_optionen['PrognNetzverbrauch']=['Farbe'=>'rgba(110,110,110,0.6)','fill'=>'true','stack'=>'12','linewidth'=>'0','order'=>'2','yAxisID'=>'y','hidden'=>'false','type'=>'bar','unit'=>'Wh','showLabel'=>'false','decimals'=>'0'];

include "7_funktion_Diagram.php";

# Prüfen ob SQLite Voraussetzungen vorhanden sind
$SQLite_file = $PythonDIR."/PV_Daten.sqlite";
if (!file_exists($SQLite_file)) {
    echo "\nSQLitedatei $SQLite_file existiert nicht, keine Grafik verfügbar!";
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
    Optionenausgabe($DBersterTag_Jahr, $activeTab);
} else {

# AC Produktion 
$SQL = getSQL('Netzladen', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
$DC_Produktion = round($db->querySingle($SQL)/1000, 1);
# Netzverbrauch
$SQL = getSQL('Netzverbrauch', $DiaDatenVon, $DiaDatenBis_SQL, $groupSTR);
$AC_Verbrauch = round($db->querySingle($SQL)/1000, 1);

# Funktion Schalter aufrufen
schalter_ausgeben($DBersterTag, $DBletzterTag, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $DC_Produktion, $AC_Verbrauch, $Strompreis_Dia_optionen, $Tag, $durchschnitt_checked, $activeTab);

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

# Nun Chart ausgeben
if (empty($daten)) {
    echo '<br><br><p class="navi">Keine Strompreise für ausgewählten Tag vorhanden!!</p>';
} else {
    echo "<div class='container'>
    <canvas id='PVDaten'></canvas>
</div>";

Diagram_ausgabe($labels, $daten, $Strompreis_Dia_optionen, $Preisstatistik,  $MIN_y3, $MAX_y, $MAX_y3);
}

$db->close();
} # END if ($programmpunkt == 'option') {
?>
