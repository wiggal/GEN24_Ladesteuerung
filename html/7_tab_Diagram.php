<!doctype html>
<html>
    <head>
    <script src="chart.js"></script>
    <style>
    html, body {
        height: 100%;
        margin: 0px;
    }
    .container {
        height: 100%;
    }
</style>
    </head>
    <body>
<div class="container">
  <canvas id="PVDaten" </canvas>
</div>


<?php
include "config.php";
$heute = date("Y-m-d");
# $heute = "2023-10-28"; #TEST
$db = new SQLite3($SQLite_file);
$SQL = "select Zeitpunkt,
       CASE WHEN Gesamtverbrauch < 0 THEN 0
            WHEN PVProduktion > Gesamtverbrauch THEN Gesamtverbrauch
            ELSE PVProduktion
        END AS Direktverbrauch,
        BatteriePower, Einspeisung, Gesamtverbrauch, Vorhersage, BattStatus
from pv_daten
where Zeitpunkt LIKE '".$heute."%'";

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
        }
      },
    scales: {
      x: {
        ticks: {
          // For a category axis, the val is the index so the lookup via getLabelForValue is needed
          callback: function(val, index) {
            // nur halbe Stunden in der X-Beschriftung ausgeben
            return index % 6 === 0 ? this.getLabelForValue(val) : '';
          }
        }
      },
      y: {
        type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
        position: 'left',
        stacked: true
      },
      y2: {
        type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
        position: 'right',
        reverse: false,
        min: 0,
        max: 100
      },
    }
    },
  });
</script>
    </body>
</html>
