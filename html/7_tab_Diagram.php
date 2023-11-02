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
    font-size:150%;
    padding:6px 11px;
  }

</style>
    </head>
    <body>


<?php
include "config.php";
# Diagrammtag festlegen
$heute = date("Y-m-d");
$DiaTag = $heute;
if (isset($_POST["DiaTag"])) $DiaTag = $_POST["DiaTag"];
$Tag_davor = date("Y-m-d",(strtotime("-1 day", strtotime($DiaTag))));
$Tag_danach = date("Y-m-d",(strtotime("+1 day", strtotime($DiaTag))));

# Schalter zum Blättern usw.
echo '<table border="0" ><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$Tag_davor.'">'."\n";
echo '<button type="submit" class="navi"> &lt;&lt;'.$Tag_davor.' </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$heute.'">'."\n";
echo '<button type="submit" class="navi"> &gt;&gt; heute &lt;&lt;  </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$Tag_danach.'">'."\n";
echo '<button type="submit" class="navi"> '.$Tag_danach.'&gt;&gt; </button>';
echo '</form>'."\n";

echo '</td></tr></table><br>';


# $heute = "2023-10-28"; #TEST
$db = new SQLite3($SQLite_file);
$SQL = "select Zeitpunkt,
       CASE WHEN Gesamtverbrauch < 0 THEN 0
            WHEN PVProduktion > Gesamtverbrauch THEN Gesamtverbrauch
            ELSE PVProduktion
        END AS Direktverbrauch,
        BatteriePower, Einspeisung, Gesamtverbrauch, Vorhersage, BattStatus
from pv_daten
where Zeitpunkt LIKE '".$DiaTag."%'";

$results = $db->query($SQL);

$optionen = array();
$optionen['Gesamtverbrauch']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'1','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y'];
$optionen['Vorhersage']=['Farbe'=>'rgba(255,140,05,1)','fill'=>'false','stack'=>'2','linewidth'=>'2','order'=>'0','borderDash'=>'[15,8]','yAxisID'=>'y'];
$optionen['BattStatus']=['Farbe'=>'rgba(34,139,34,1)','fill'=>'false','stack'=>'3','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y2'];
$optionen['Einspeisung'] = ['Farbe' => 'rgba(148,148,148,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '3', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['BatteriePower'] = ['Farbe' => 'rgba(50,205,50,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '2', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Direktverbrauch'] = ['Farbe' => 'rgba(255,215,0,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '1', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];

$trenner = "";
$labels = "";
$daten = array();
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
    $first = true;
    foreach($row as $x => $val) {
      if ( $first ){
        # Datum zuschneiden und nur ganze Stungen ausgeben
        $label_element = substr($val, 11, -3);
        $labels = $labels.$trenner.'"'.$label_element.'"';
        $first = false;
      } else {
        if (!isset($daten[$x])) $daten[$x] = "";
        if ($x == 'Gesamtverbrauch' and $val < 0) $val = 0;
        if ($x == 'BatteriePower' and $val < 0) $val = 0;
        if ($x == 'Einspeisung' and $val < 0) $val = 0;
        $daten[$x] = $daten[$x] .$trenner.$val;
        }
    }
$trenner = ",";
}

?>
<div class="container">
  <!--<canvas id="PVDaten" style="border: 1px dotted red; height:99vh; width:98vw"></canvas>-->
  <canvas id="PVDaten" style="height:95vh; width:98vw"></canvas>
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
            display: false,
            //text: (ctx) => 'Tooltip position mode: ' + ctx.chart.options.plugins.tooltip.position,
        },
      },
    scales: {
      x: {
        ticks: {
          // For a category axis, the val is the index so the lookup via getLabelForValue is needed
          callback: function(val, index) {
            // nur halbe Stunden in der X-Beschriftung ausgeben
            return index % 6 === 0 ? this.getLabelForValue(val) : '';
          },
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
  });
</script>

    </body>
</html>
