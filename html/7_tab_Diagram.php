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
# Prüfen ob SQLite Voraussetzungen vorhanden sind
$SQLite_file = "../" . $python_config['Logging']['Logging_file'];
if (!file_exists($SQLite_file)) {
    echo "\nSQLitedatei $filename existiert nicht, keine Grafik verfügbar!";
    echo "</body></html>";
    exit();
}
#print_r($_POST);

## BEGIN FUNCTIONS
function schalter_ausgeben ( $energietype, $nextenergietype , $heute, $morgen, $DiaDatenVon, $DiaDatenBis, $VOR_DiaDatenVon, $VOR_DiaDatenBis, $NACH_DiaDatenVon, $NACH_DiaDatenBis, $Produktion, $buttoncolor, $mengencolor, $button_vor_on, $button_back_on)
{

$schaltername = explode(" ", $DiaDatenVon);
# Schalter zum Blättern usw.
echo '<table><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$VOR_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$VOR_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="energietype" value="'.$energietype.'">'."\n";
echo '<button type="submit" class="navi" '.$button_back_on.'> &nbsp;&lt;&lt;&nbsp;</button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$heute.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$morgen.'">'."\n";
echo '<input type="hidden" name="energietype" value="'.$energietype.'">'."\n";
echo '<button type="submit" class="navi"> '.$schaltername[0].' </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$NACH_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$NACH_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="energietype" value="'.$energietype.'">'."\n";
echo '<button type="submit" class="navi" '.$button_vor_on.'> &nbsp;&gt;&gt;&nbsp; </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$DiaTag.'">'."\n";
echo '<input type="hidden" name="energietype" value="'.$nextenergietype.'">'."\n";
echo '<button type="submit" class="navi" style="background-color:'.$buttoncolor.'"> '.$nextenergietype.'&gt;&gt; </button>';
echo '</form>'."\n";

echo '</td><td style="text-align:center; width: 100%;">';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaTag" value="'.$Tag_danach.'">'."\n";
echo '<input type="hidden" name="energietype" value="option">'."\n";
echo '<button type="submit" class="navi" > Optionen </button>';
echo '</form>'."\n";

echo '</td><td style="text-align:right; font-size: 170%; background-color: '.$mengencolor.'">';
echo "&nbsp;$Produktion KWh&nbsp;";

echo '</td></tr></table><br>';
}

function diagrammdaten ( $results, $DB_Werte)
{
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
return array($daten, $labels);
}
## END FUNCTIONS

# Datenbankverbindung herstellen
$db = new SQLite3($SQLite_file);

# Diagrammtag festlegen
$heute = date("Y-m-d 00:00");
$morgen =  date("Y-m-d 00:00",(strtotime("+1 day", strtotime(date("Y-m-d")))));
$DiaDatenVon = $heute;
$DiaDatenBis = $morgen;
#$DiaTag = $heute;
if (isset($_POST["DiaDatenVon"])) $DiaDatenVon = str_replace("T"," ",$_POST["DiaDatenVon"]);
if (isset($_POST["DiaDatenBis"])) $DiaDatenBis = str_replace("T"," ",$_POST["DiaDatenBis"]);
$VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime("-1 day", strtotime($DiaDatenVon))));
$VOR_DiaDatenBis = date("Y-m-d 00:00",(strtotime("-1 day", strtotime($DiaDatenBis))));
$NACH_DiaDatenVon = date("Y-m-d 00:00",(strtotime("+1 day", strtotime($DiaDatenVon))));
$NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime("+1 day", strtotime($DiaDatenBis))));
# Schalter für morgen deaktivieren
$button_vor_on = '';
if ($DiaTag == $heute) $button_vor_on = 'disabled';
# Schalter für Tag out of DB  deaktivieren
$button_back_on = '';
$DBersterTag = (explode(" ",$db->querySingle('SELECT MIN(Zeitpunkt) from pv_daten')));
if ($DiaTag == $DBersterTag[0]) $button_back_on = 'disabled';

# energietype = Verbrauch oder Produktion
$energietype = 'Produktion';
if (isset($_POST["energietype"])) $energietype = $_POST["energietype"];

# switch Verbrauch oder Produktion
switch ($energietype) {
    case 'Produktion':

# AC Produktion 
$SQL = "SELECT 
        MAX(DC_Produktion)- MIN(DC_Produktion)
        AS DC_Produktion
from pv_daten where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'";
$DC_Produktion = round($db->querySingle($SQL)/1000, 1);

# Funtkion Schalter aufrufen
schalter_ausgeben('Produktion', 'Verbrauch', $heute, $morgen, $DiaDatenVon, $DiaDatenBis, $VOR_DiaDatenVon, $VOR_DiaDatenBis, $NACH_DiaDatenVon, $NACH_DiaDatenBis, $DC_Produktion, 'rgb(255,158,158)', 'rgb(0,255,127)', $button_vor_on, $button_back_on);

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
from pv_daten where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."')
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

# Funktion Diagrammdaten
$DB_Werte = array('Gesamtverbrauch', 'Einspeisung', 'InBatterie', 'Direktverbrauch');
list($daten, $labels) = diagrammdaten($results, $DB_Werte);

$optionen = array();
$optionen['Gesamtverbrauch']=['Farbe'=>'rgba(255,0,0,1)','fill'=>'false','stack'=>'1','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y'];
$optionen['Vorhersage']=['Farbe'=>'rgba(255,140,05,1)','fill'=>'false','stack'=>'2','linewidth'=>'2','order'=>'0','borderDash'=>'[15,8]','yAxisID'=>'y'];
$optionen['BattStatus']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'3','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y2'];
$optionen['Einspeisung'] = ['Farbe' => 'rgba(148,148,148,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '3', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['InBatterie'] = ['Farbe' => 'rgba(50,205,50,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '2', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Direktverbrauch'] = ['Farbe' => 'rgba(255,215,0,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '1', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];

    break; # ENDE case Produktion

    case 'Verbrauch':

# AC Verbrauch
$SQL = "SELECT 
        MAX(Netzverbrauch)- MIN(Netzverbrauch) + 
        MAX(AC_Produktion) - min(AC_Produktion) + 
        MIN (Einspeisung) - MAX (Einspeisung)
        AS AC_Produktion
from pv_daten where Zeitpunkt BETWEEN '".$heute."' AND '".$morgen."'";
$AC_Verbrauch = round($db->querySingle($SQL)/1000, 1);

# Schalter aufrufen
schalter_ausgeben('Verbrauch', 'Produktion', $heute, $morgen, $DiaDatenVon, $DiaDatenBis, $VOR_DiaDatenVon, $VOR_DiaDatenBis, $NACH_DiaDatenVon, $NACH_DiaDatenBis, $AC_Verbrauch, 'rgb(0,255,127)', 'rgb(255,158,158)', $button_vor_on, $button_back_on);

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
from pv_daten where Zeitpunkt BETWEEN '".$heute."' AND '".$morgen."')
SELECT Zeitpunkt,
    Direktverbrauch*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Direktverbrauch,
    Produktion*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Produktion,
    Netzverbrauch*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Netzverbrauch,
    VonBatterie*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS VonBatterie,
    BattStatus
FROM Alle_PVDaten
Where Zeitabstand > 4 AND Gesamtverbrauch > 1";

$results = $db->query($SQL);

# Funktion diagrammdaten
$DB_Werte = array('Produktion', 'Netzverbrauch', 'VonBatterie', 'Direktverbrauch');
list($daten, $labels) = diagrammdaten($results, $DB_Werte);

$optionen = array();
$optionen['Produktion']=['Farbe'=>'rgba(34,139,34,1)','fill'=>'false','stack'=>'1','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y'];
$optionen['BattStatus']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'3','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y2'];
$optionen['Netzverbrauch'] = ['Farbe' => 'rgba(148,148,148,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '3', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['VonBatterie'] = ['Farbe' => 'rgba(50,205,50,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '2', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Direktverbrauch'] = ['Farbe' => 'rgba(255,215,0,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '1', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];

    break; # ENDE case Verbrauch
    
} # ENDE switch
if ($energietype == 'option') {
echo "
<center>
<br><p class='optionwahl'>Diagrammoptionen auswählen!</p><br><br>
</center>
";
# Hier Auswahllisten 
echo "
<script type='text/javascript'>
function zeitsetzer(offset) {
const date = new Date();

let day_von = date.getDate();
let day_bis = date.getDate();
let month_von = date.getMonth() + 1;
let month_bis = date.getMonth() + 1;
let year_von = date.getFullYear();
let year_bis = date.getFullYear();
let hours = '0';
let minutes_html = '0' - date.getTimezoneOffset();

// 1 = Tag
if (offset == 1) {
  day_bis  = day_bis + 1;
  document.getElementsByName('diagramtype')[0].checked = true;
}

// 2 = Monat
if (offset == 2) {
  day_von  = 1;
  day_bis  = 1;
  month_bis = month_bis + 1;
  document.getElementsByName('diagramtype')[1].checked = true;
}

// 3 = Monat
if (offset == 3) {
  day_von  = 1;
  day_bis  = 1;
  month_von = 1;
  month_bis = 1;
  year_bis = year_bis + 1;
  document.getElementsByName('diagramtype')[1].checked = true;
}


let von = year_von + '-' + ('0'+month_von).substr(-2) + '-' + ('0'+day_von).substr(-2) + 'T00:00:00';
//alert(von);
let bis = year_bis + '-' + ('0'+month_bis).substr(-2)+ '-' + ('0'+day_bis).substr(-2) + 'T00:00:00';
//alert(bis);
document.getElementById('DiaDatenVon').value = von;
document.getElementById('DiaDatenBis').value = bis;
}
window.onload = function() { zeitsetzer(1); };
</script>

<div style='text-align: center;'>
<form method='POST' action='$_SERVER[PHP_SELF]'>
  <fieldset style='display: inline-block;'>
  <legend class='optionwahl'>Energieart:</legend>
  <div style='text-align: left'>
  <input style='text-align: left' type='radio' id='Produktion' name='energietype' value='Produktion' checked>
  <label class='optionwahl' for='Produktion'>Produktion</label><br>
  <input type='radio' id='Verbrauch' name='energietype' value='Verbrauch'>
  <label class='optionwahl' for='Verbrauch'>Verbrauch</label><br>
  </div>
  </fieldset>
  <br>

  <fieldset style='display: inline-block;'>
  <legend class='optionwahl'>Diagrammart:</legend>
  <div style='text-align: left'>
  <input type='radio' id='line' name='diagramtype' value='line' checked>
  <label class='optionwahl' for='line'>Linien</label><br>
  <input type='radio' id='bar' name='diagramtype' value='bar'>
  <label class='optionwahl' for='bar'>Balken&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</label><br>
  </div>
  </fieldset>
  <br>

  <fieldset style='display: inline-block;'>
  <legend class='optionwahl'>Zeitraum:</legend>
  <div style='text-align: left'>
  <label class='optionwahl' >Von:&nbsp;</label>
  <input class='date' type='datetime-local' name='DiaDatenVon' id='DiaDatenVon' value='' /><br><br>
  <label class='optionwahl' >Bis:&nbsp;&nbsp;&nbsp;</label>
  <input class='date' type='datetime-local' name='DiaDatenBis' id='DiaDatenBis' value='' /><br><br>
  <input type='radio' id='tag' name='Zeitraum' value='tag' onclick='zeitsetzer(1)' checked>
  <label class='optionwahl' for='tag'>Tag&nbsp;&nbsp;&nbsp;&nbsp;</label>
  <input type='radio' id='monat' name='Zeitraum' value='monat' onclick='zeitsetzer(2)'>
  <label class='optionwahl' for='monat'>Monat</label>
  <input type='radio' id='jahr' name='Zeitraum' value='jahr' onclick='zeitsetzer(3)'>
  <label class='optionwahl' for='jahr'>Jahr</label>
  </div>
  </fieldset>

<br><br>
<button type='submit' class='navi' > Diagramm aufrufen</button>
</form>
</div>
<b>Noch nicht umgesetzt:</b><br>
- Blättern in den Zeitreihen<br>
- Balkendiagramme<br>
";
} else {
# Wenn Optionen dann kein Chart
$db->close();
echo "<div class='container'>
  <canvas id='PVDaten' style='height:100vh; width:100vw'></canvas>
</div>
<script>
new Chart('PVDaten', {
    type: 'line',
    data: {
      labels: [". $labels ."],
      datasets: [{";
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
echo "    }]
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
        legend: {
             position: 'top',
             labels: {
                 font: {
                   size: 20,
                 }
            }
        },
        tooltip: {
            titleFont: { size: 20 },
            bodyFont: { size: 20 },
            // Einheitt beim Tooltip hinzufügen
            callbacks: {
                label: function(context) {
                    let label = context.dataset.label || '';
                    let unit = ' W';
                    if ( label == 'BattStatus' ) {
                        unit = ' %';
                    }
                    return label + ' ' + context.parsed.y + unit;
                }
            }
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
</script>";
}
?>

    </body>
</html>
