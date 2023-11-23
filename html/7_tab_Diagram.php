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
include "funktion_Diagram.php";

# ENTW 
#print_r($_POST);

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
$optionen = '';

# Diagrammtag festlegen
# UND _POST_VAR auslesen
$heute = date("Y-m-d 00:00");
$morgen =  date("Y-m-d 00:00",(strtotime("+1 day", strtotime(date("Y-m-d")))));
$DiaDatenVon = $heute;
$DiaDatenBis = $morgen;
if (!empty($_POST["DiaDatenVon"])) $DiaDatenVon = str_replace("T"," ",$_POST["DiaDatenVon"]);
if (!empty($_POST["DiaDatenBis"])) $DiaDatenBis = str_replace("T"," ",$_POST["DiaDatenBis"]);

# Schalter für morgen deaktivieren
$button_vor_on = '';
$button_back_on = '';
/* NOCH ENTW
if ($DiaTag == $heute) $button_vor_on = 'disabled';
# Schalter für Tag out of DB  deaktivieren
$button_back_on = '';
$DBersterTag = (explode(" ",$db->querySingle('SELECT MIN(Zeitpunkt) from pv_daten')));
if ($DiaTag == $DBersterTag[0]) $button_back_on = 'disabled';
*/

# energietype = Verbrauch oder Produktion
$energietype = 'Produktion';
if (!empty($_POST["energietype"])) $energietype = $_POST["energietype"];

# diagramtype = line oder bar
$diagramtype = 'line';
if (!empty($_POST["diagramtype"])) $diagramtype = $_POST["diagramtype"];

# Zeitraum = Tag, Monat, Jahr
$Zeitraum = 'Tag';
if (!empty($_POST["Zeitraum"])) $Zeitraum = $_POST["Zeitraum"];

# END _POST_VAR auslesen

if ($energietype == 'option') {
    Optionenausgabe();
} else {

# Datenbankverbindung herstellen
$db = new SQLite3($SQLite_file);

# Diagrammtype Auswahl
if ($diagramtype == 'line') {
# switch Verbrauch oder Produktion
switch ($energietype) {
   case 'Produktion':

        # AC Produktion 
        $SQL = getSQL('SUM_DC_Produktion', $DiaDatenVon, $DiaDatenBis);
        $DC_Produktion = round($db->querySingle($SQL)/1000, 1);
        
        # Funktion Schalter aufrufen
        schalter_ausgeben('Produktion', 'Verbrauch', $DiaDatenVon, $DiaDatenBis, $DC_Produktion, 'rgb(255,158,158)', 'rgb(0,255,127)', $button_vor_on, $button_back_on);
    
        # ProduktionsSQL und Daten holen
        $SQL = getSQL('Produktion_Line', $DiaDatenVon, $DiaDatenBis);
        $results = $db->query($SQL);
    
        # Diagrammdaten und Optionen holen
        $DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Direktverbrauch');
        list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1', $Zeitraum);
        $optionen = Dia_Options('Produktion_Line');

    break; # ENDE case Produktion

    case 'Verbrauch':

        # AC Verbrauch
        $SQL = getSQL('SUM_AC_Verbrauch', $DiaDatenVon, $DiaDatenBis);
        $AC_Verbrauch = round($db->querySingle($SQL)/1000, 1);
    
        # Schalter aufrufen
        schalter_ausgeben('Verbrauch', 'Produktion', $DiaDatenVon, $DiaDatenBis, $AC_Verbrauch, 'rgb(0,255,127)', 'rgb(255,158,158)', $button_vor_on, $button_back_on);

        # VerbrauchSQL und Daten holen
        $SQL = getSQL('Verbrauch_Line', $DiaDatenVon, $DiaDatenBis);
        $results = $db->query($SQL);

        # Diagrammdaten und Optionen holen
        $DB_Werte = array('Produktion', 'Netzverbrauch', 'VonBatterie', 'Direktverbrauch');
        list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1', $Zeitraum);
        $optionen = Dia_Options('Verbrauch_Line');

    break; # ENDE case Verbrauch
    
} # ENDE switch
# Nun Linechart ausgeben
echo "<div class='container'>
  <canvas id='PVDaten' style='height:100vh; width:100vw'></canvas>
</div>";
Diagram_ausgabe('line', $labels, $daten, $optionen, 'W');
} else {  # Dann bar = Balkendiagramm
switch ($energietype) {
   case 'Produktion':

        # AC Produktion 
        $SQL = getSQL('SUM_DC_Produktion', $DiaDatenVon, $DiaDatenBis);
        $DC_Produktion = round($db->querySingle($SQL)/1000, 1);
        
        # Funktion Schalter aufrufen
        schalter_ausgeben('Produktion', 'Verbrauch', $DiaDatenVon, $DiaDatenBis, $DC_Produktion, 'rgb(255,158,158)', 'rgb(0,255,127)', $button_vor_on, $button_back_on);
    
        # ProduktionsSQL und Daten holen
        $groupSTR = '%Y-%m-%d';
        switch ($Zeitraum) {
            case 'tag': $groupSTR = '%Y-%m-%d %H'; break;
            case 'monat': $groupSTR = '%Y-%m-%d'; break;
            case 'jahr': $groupSTR = '%Y-%m'; break;
        }

        $SQL = getSQL_bar('Produktion_bar', $DiaDatenVon, $DiaDatenBis, $groupSTR);
        $results = $db->query($SQL);
    
        # Diagrammdaten und Optionen holen
        $DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Direktverbrauch');
        list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1000', $Zeitraum);
        $optionen = Dia_Options('Produktion_Line');

    break; # ENDE case Produktion

   case 'Verbrauch':

        # AC Verbrauch 
        $SQL = getSQL('SUM_AC_Verbrauch', $DiaDatenVon, $DiaDatenBis);
        $AC_Verbrauch = round($db->querySingle($SQL)/1000, 1);
        
        # Funktion Schalter aufrufen
        schalter_ausgeben('Verbrauch', 'Produktion', $DiaDatenVon, $DiaDatenBis, $AC_Verbrauch, 'rgb(0,255,127)', 'rgb(255,158,158)', $button_vor_on, $button_back_on);
    
        # ProduktionsSQL und Daten holen
        $groupSTR = '%Y-%m-%d';
        switch ($Zeitraum) {
            case 'tag': $groupSTR = '%Y-%m-%d %H'; break;
            case 'monat': $groupSTR = '%Y-%m-%d'; break;
            case 'jahr': $groupSTR = '%Y-%m'; break;
        }

        $SQL = getSQL_bar('Verbrauch_bar', $DiaDatenVon, $DiaDatenBis, $groupSTR);
        $results = $db->query($SQL);
    
        # Diagrammdaten und Optionen holen
        $DB_Werte = array('Produktion', 'Netzverbrauch', 'VonBatterie', 'Direktverbrauch');
        list($daten, $labels) = diagrammdaten($results, $DB_Werte, '1000', $Zeitraum);
        $optionen = Dia_Options('Verbrauch_Line');

    break; # ENDE case Verbrauch

} # ENDE switch
# Nun Barchart ausgeben
echo "<div class='container'>
  <canvas id='PVDaten' style='height:100vh; width:100vw'></canvas>
</div>";
Diagram_ausgabe('bar', $labels, $daten, $optionen, 'KW');

} # END if ($diagramtype == 
    $db->close();
} # END if ($energietype == 'option') {

?>
    </body>
</html>
