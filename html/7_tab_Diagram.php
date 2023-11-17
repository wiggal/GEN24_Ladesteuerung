<!doctype html>
<html>
    <head>
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
# Prüfen ob SQLite Voraussetzungen vorhanden sind
$SQLite_file = "../" . $python_config['Logging']['Logging_file'];
if (!file_exists($SQLite_file)) {
    echo "\nSQLitedatei $filename existiert nicht, keine Grafik verfügbar!";
    echo "</body></html>";
    exit();
}

function schalter_ausgeben ( $case, $nextcase , $heute, $DiaTag, $Tag_davor, $Tag_danach, $AC_Produktion, $buttoncolor, $mengencolor)
{

# Schalter zum Blättern usw.
echo '<table><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$Tag_davor.'">'."\n";
echo '<input type="hidden" name="case" value="'.$case.'">'."\n";
echo '<button type="submit" class="navi"> &nbsp;&lt;&lt;&nbsp;</button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$heute.'">'."\n";
echo '<input type="hidden" name="case" value="'.$case.'">'."\n";
echo '<button type="submit" class="navi"> '.$DiaTag.' </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$Tag_danach.'">'."\n";
echo '<input type="hidden" name="case" value="'.$case.'">'."\n";
echo '<button type="submit" class="navi"> &nbsp;&gt;&gt;&nbsp; </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$DiaTag.'">'."\n";
echo '<input type="hidden" name="case" value="'.$nextcase.'">'."\n";
echo '<button type="submit" class="navi" style="background-color:'.$buttoncolor.'"> '.$nextcase.'&gt;&gt; </button>';
echo '</form>'."\n";

# Hier noch die Zweiträume einbinden
/*
echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$DiaTag.'">'."\n";
echo '<input type="hidden" name="case" value="'.$nextcase.'">'."\n";
echo '<select name="top5">';
echo '<option>Tag</option>';
echo '<option>Monat</option>';
echo '<option>Jahr</option>';
echo '<option>gesamt</option>';
echo '</select>';
echo '</form>'."\n";
*/

echo '</td><td style="text-align:right; width: 100%; font-size: 170%">';
echo '</td><td style="text-align:right; font-size: 170%; background-color: '.$mengencolor.'">';
echo "&nbsp;$AC_Produktion KWh&nbsp;";

echo '</td></tr></table><br>';
}


# Diagrammtag festlegen
$heute = date("Y-m-d");
$DiaTag = $heute;
if (isset($_POST["DiaTag"])) $DiaTag = $_POST["DiaTag"];
$Tag_davor = date("Y-m-d",(strtotime("-1 day", strtotime($DiaTag))));
$Tag_danach = date("Y-m-d",(strtotime("+1 day", strtotime($DiaTag))));


# case = Verbrauch oder Produktion
$case = 'Produktion';
if (isset($_POST["case"])) $case = $_POST["case"];


$db = new SQLite3($SQLite_file);

# switch Verbrauch oder Produktion
switch ($case) {
    case 'Produktion':

# AC Produktion 
$SQL = "SELECT 
        MAX(DC_Produktion)- MIN(DC_Produktion)
        AS DC_Produktion
from pv_daten where Zeitpunkt LIKE '".$DiaTag."%'";
$DC_Produktion = round($db->querySingle($SQL)/1000, 1);

# Schalter aufrufen
schalter_ausgeben('Produktion', 'Verbrauch', $heute, $DiaTag, $Tag_davor, $Tag_danach, $DC_Produktion, 'red', 'rgb(34,139,34)');

# ProduktionsSQL
# Aussieben der manchmal entstehenden Minuswerte im Verbrauch durch "AND Gesamtverbrauch > 1"
$SQL = "WITH Alle_PVDaten AS (
        select  Zeitpunkt,
        ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Zeitabstand,
        ((DC_Produktion - LAG(DC_Produktion) OVER(ORDER BY Zeitpunkt)) - (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt)) - (Batterie_IN - LAG(Batterie_IN) OVER(ORDER BY Zeitpunkt))) AS Direktverbrauch,
        ((DC_Produktion - LAG(DC_Produktion) OVER(ORDER BY Zeitpunkt)) + (Netzverbrauch - LAG(Netzverbrauch) OVER(ORDER BY Zeitpunkt)) - (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt))
			+ (Batterie_OUT - LAG(Batterie_OUT) OVER(ORDER BY Zeitpunkt)) - (Batterie_IN - LAG(Batterie_IN) OVER(ORDER BY Zeitpunkt))) AS Gesamtverbrauch,
        (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt)) AS Einspeisung,
        ((Batterie_IN - LAG(Batterie_IN) OVER(ORDER BY Zeitpunkt)) - (Batterie_OUT - LAG(Batterie_OUT) OVER(ORDER BY Zeitpunkt))) AS InBatterie,
        Vorhersage,
        BattStatus
from pv_daten where Zeitpunkt LIKE '".$DiaTag."%')
SELECT Zeitpunkt,
    Direktverbrauch*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Direktverbrauch,
    Gesamtverbrauch*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Gesamtverbrauch,
    Einspeisung*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Einspeisung,
    InBatterie*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS InBatterie,
    Vorhersage,
    BattStatus
FROM Alle_PVDaten
Where Zeitabstand > 4 AND Gesamtverbrauch > 1";

$results = $db->query($SQL);

$optionen = array();
$optionen['Gesamtverbrauch']=['Farbe'=>'rgba(255,0,0,1)','fill'=>'false','stack'=>'1','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y'];
$optionen['Vorhersage']=['Farbe'=>'rgba(255,140,05,1)','fill'=>'false','stack'=>'2','linewidth'=>'2','order'=>'0','borderDash'=>'[15,8]','yAxisID'=>'y'];
$optionen['BattStatus']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'3','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y2'];
$optionen['Einspeisung'] = ['Farbe' => 'rgba(148,148,148,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '3', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['InBatterie'] = ['Farbe' => 'rgba(50,205,50,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '2', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Direktverbrauch'] = ['Farbe' => 'rgba(255,215,0,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '1', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];

$trenner = "";
$labels = "";
$daten = array();
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
        $first = true;
        foreach($row as $x => $val) {
        if ( $first ){
            # Datum zuschneiden 
            $label_element = substr($val, 11, -3);
            $labels = $labels.$trenner.'"'.$label_element.'"';
            $first = false;
        } else {
            if (!isset($daten[$x])) $daten[$x] = "";
            # keine Minuswerte und auf 10 Watt runden
            $DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Direktverbrauch');
            foreach ($DB_Werte as $i) {
                if ($x == $i) { 
                    $val = (round($val/10))*10;
                    if ($val < 0) $val = 0;
                }
            }
            $daten[$x] = $daten[$x] .$trenner.$val;
            }
        }
$trenner = ",";
}
    break; # ENDE case Produktion

    case 'Verbrauch':

# AC Verbrauch
$SQL = "SELECT 
        MAX(Netzverbrauch)- MIN(Netzverbrauch) + 
        MAX(AC_Produktion) - min(AC_Produktion) + 
        MIN (Einspeisung) - MAX (Einspeisung)
        AS AC_Produktion
from pv_daten where Zeitpunkt LIKE '".$DiaTag."%'";
$AC_Verbrauch = round($db->querySingle($SQL)/1000, 1);

# Schalter aufrufen
schalter_ausgeben('Verbrauch', 'Produktion', $heute, $DiaTag, $Tag_davor, $Tag_danach, $AC_Verbrauch, 'rgb(34,139,34)', 'red');

# VerbrauchSQL
# Aussieben der manchmal entstehenden Minuswerte im Verbrauch durch "AND Gesamtverbrauch > 1"
$SQL = "WITH Alle_PVDaten AS (
        select  Zeitpunkt,
        ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Zeitabstand,
		((Netzverbrauch - LAG(Netzverbrauch) OVER(ORDER BY Zeitpunkt)) + (AC_Produktion - LAG(AC_Produktion) OVER(ORDER BY Zeitpunkt)) - (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt))) AS Gesamtverbrauch,
        ((AC_Produktion - LAG(AC_Produktion) OVER(ORDER BY Zeitpunkt)) - (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt)) - (Batterie_OUT - LAG(Batterie_OUT) OVER(ORDER BY Zeitpunkt))) AS Direktverbrauch,
        (Netzverbrauch - LAG(Netzverbrauch) OVER(ORDER BY Zeitpunkt)) AS Netzverbrauch,
        (DC_Produktion - LAG(DC_Produktion) OVER(ORDER BY Zeitpunkt)) AS Produktion,
        ((Batterie_OUT - LAG(Batterie_OUT) OVER(ORDER BY Zeitpunkt)) - (Batterie_IN - LAG(Batterie_IN) OVER(ORDER BY Zeitpunkt))) AS VonBatterie,
        BattStatus
from pv_daten where Zeitpunkt LIKE '".$DiaTag."%')
SELECT Zeitpunkt,
    Direktverbrauch*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Direktverbrauch,
    Produktion*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Produktion,
    Netzverbrauch*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Netzverbrauch,
    VonBatterie*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS VonBatterie,
    BattStatus
FROM Alle_PVDaten
Where Zeitabstand > 4 AND Gesamtverbrauch > 1";

$results = $db->query($SQL);

$optionen = array();
$optionen['Produktion']=['Farbe'=>'rgba(34,139,34,1)','fill'=>'false','stack'=>'1','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y'];
$optionen['BattStatus']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'3','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y2'];
$optionen['Netzverbrauch'] = ['Farbe' => 'rgba(148,148,148,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '3', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['VonBatterie'] = ['Farbe' => 'rgba(50,205,50,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '2', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Direktverbrauch'] = ['Farbe' => 'rgba(255,215,0,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '1', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];

$trenner = "";
$labels = "";
$daten = array();
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
        $first = true;
        foreach($row as $x => $val) {
        if ( $first ){
            # Datum zuschneiden 
            $label_element = substr($val, 11, -3);
            $labels = $labels.$trenner.'"'.$label_element.'"';
            $first = false;
        } else {
            if (!isset($daten[$x])) $daten[$x] = "";
            # keine Minuswerte und auf 10 Watt runden
            $DB_Werte = array('Produktion', 'Netzverbrauch', 'VonBatterie', 'Direktverbrauch');
            foreach ($DB_Werte as $i) {
                if ($x == $i) { 
                    $val = (round($val/10))*10;
                    if ($val < 0) $val = 0;
                }
            }
            $daten[$x] = $daten[$x] .$trenner.$val;
            }
        }
$trenner = ",";
}
    break; # ENDE case Verbrauch
    
} # ENDE switch
$db->close();
?>
<div class="container">
  <canvas id="PVDaten" style="height:100vh; width:100vw"></canvas>
</div>
<script>
new Chart("PVDaten", {
    type: 'line',
    data: {
      labels: [<?php echo $labels; ?>],
      datasets: [{
<?php
      $trenner = "";
      foreach($daten as $x => $val) {
      echo $trenner;
      echo "label: '$x',\n";
      echo "data: [ $val ],\n";
      echo "borderColor: '".$optionen[$x]['Farbe']."',\n";
      echo "backgroundColor: '".$optionen[$x]['Farbe']."',\n";
      echo "borderWidth: '".$optionen[$x]['linewidth']."',\n";
      echo "borderDash: ".$optionen[$x]['borderDash'].",\n";
      echo "pointRadius: 0,\n";
      echo "cubicInterpolationMode: 'monotone',\n";
      echo "fill: ".$optionen[$x]['fill'].",\n";
      echo "stack: '".$optionen[$x]['stack']."',\n";
      echo "order: '".$optionen[$x]['order']."',\n";
      echo "yAxisID: '".$optionen[$x]['yAxisID']."'\n";
      $trenner = "},{\n";
      }
?>
    }]
    },
    options: {
      responsive: true,
      interaction: {
        intersect: false,
        mode: 'index',
        },
      plugins: {
        title: {
            display: true,
            //text: (ctx) => 'Tooltip position mode: ' + ctx.chart.options.plugins.tooltip.position,
        },
                tooltip: {
        titleFont: { size: 25 },
        bodyFont: { size: 25 },
      }
    },
    scales: {
      x: {
        ticks: {
          /*
          // Hier nur jede 6te Beschriftung ausgeben
          // For a category axis, the val is the index so the lookup via getLabelForValue is needed
          callback: function(val, index) {
            // nur halbe Stunden in der X-Beschriftung ausgeben
            return index % 6 === 0 ? this.getLabelForValue(val) : '';
          },
          */
          font: {
             size: 20,
           }
        }
      },
      y: {
        type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
        position: 'left',
        stacked: true,
        ticks: {
           font: {
             size: 20,
           }
        }
      },
      y2: {
        type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
        position: 'right',
        reverse: false,
        min: 0,
        max: 100,
        ticks: {
           font: {
             size: 20,
           }
        }
      },
    }
    },
  // Funktion: durch klicken auf Legende, Elemente ausblenden 
  function(e, legendItem, legend) {
    const index = legendItem.datasetIndex;
    const ci = legend.chart;
    if (ci.isDatasetVisible(index)) {
        ci.hide(index);
        legendItem.hidden = true;
    } else {
        ci.show(index);
        legendItem.hidden = false;
    }
},
  });
</script>

    </body>
</html>
