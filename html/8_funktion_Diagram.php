<?php

## BEGIN FUNCTIONS
function schalter_ausgeben ($DBersterTag, $diagramtype, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $Produktion, $Verbrauch)
{
$next_diagramtype = 'line';
if ($diagramtype == 'line') $next_diagramtype = 'bar';

# Abstand von bis ermitteln
$zeitdifferenz = strtotime($DiaDatenBis) - strtotime($DiaDatenVon);
$VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime($DiaDatenVon)-$zeitdifferenz));
$VOR_DiaDatenBis = $DiaDatenVon;
$NACH_DiaDatenVon = $DiaDatenBis;
$NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime($DiaDatenBis)+$zeitdifferenz));

# Schalter am Anfang und am Ende deaktivieren
$button_vor_on = '';
$heute = date("Y-m-d H:i");
if (strtotime($DiaDatenBis) >= strtotime($heute)) $button_vor_on = 'disabled';
# Schalter für Tag out of DB  deaktivieren
$button_back_on = '';
if (strtotime($DiaDatenVon) <= strtotime($DBersterTag)) $button_back_on = 'disabled';

# Schalter zum Blättern usw.
echo '<table><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$VOR_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$VOR_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="diagramtype" value="'.$diagramtype.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" class="navi" '.$button_back_on.'> &nbsp;&lt;&lt;&nbsp;</button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<input type="hidden" name="diagramtype" value="'.$diagramtype.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" class="navi"> aktuell </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$NACH_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$NACH_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="diagramtype" value="'.$diagramtype.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" class="navi" '.$button_vor_on.'> &nbsp;&gt;&gt;&nbsp; </button>';
echo '</form>'."\n";

/*
echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="diagramtype" value="'.$next_diagramtype.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" class="navi" > '.$next_diagramtype.'&gt;&gt; </button>';
echo '</form>'."\n";
*/

echo '</td><td style="text-align:center; width: 100%;">';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="energietype" value="option">'."\n";
echo '<button type="submit" class="navi" > Optionen </button>';
echo '</form>'."\n";

echo '</td><td style="text-align:right; font-size: 170%; background-color: rgb(0,255,127)">';
echo "&nbsp;$Produktion KWh&nbsp;";
echo '</td><td style="text-align:right; font-size: 170%; background-color: rgb(255,158,158)">';
echo "&nbsp;$Verbrauch KWh&nbsp;";

echo '</td></tr></table><br>';
} #END function schalter_ausgeben 

function diagrammdaten ( $results, $DB_Werte, $EnergieEinheit, $XScaleEinheit )
{
$trenner = "";
$labels = "";
$daten = array();
$cut_von = 11;
$cut_anzahl = 5;
switch ($XScaleEinheit) {
    case 'stunden': $cut_von = 11; $cut_anzahl = 5; break;  # Stunde ausgeben
    case 'tage': $cut_von = 8; $cut_anzahl = 2; break; # Tag ausgeben
    case 'monate': $cut_von = 5; $cut_anzahl = 2; break;  # Monat ausgeben
    case 'jahre': $cut_von = 0; $cut_anzahl = 4; break;  # Monat ausgeben
}
    
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
        $first = true;
        foreach($row as $x => $val) {
        if ( $first ){
            # Datum zuschneiden 
            $label_element = substr($val, $cut_von, $cut_anzahl);
            $labels = $labels.$trenner.'"'.$label_element.'"';
            $first = false;
        } else {
            if (!isset($daten[$x])) $daten[$x] = "";
            # keine Minuswerte und auf 10 Watt runden
            foreach ($DB_Werte as $i) {
                if ($x == $i) { 
                    $val = (round($val/10))*10;
                    # if ($val < 10 and $val > -100) $val = 0;
                    if ($val < 0) $val = 0;
                }
            }
            $daten[$x] = $daten[$x] .$trenner.$val/$EnergieEinheit;
            }
        }
$trenner = ",";
}
return array($daten, $labels);
} #END function diagrammdaten


function getSQL($SQLType, $DiaDatenVon, $DiaDatenBis, $groupSTR)
{
# SQL nach $SQLType wählen
switch ($SQLType) {
    case 'SUM_DC_Produktion':
$SQL = "SELECT 
        MAX(DC_Produktion)- MIN(DC_Produktion)
        AS DC_Produktion
from pv_daten where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'";
return $SQL;
    break; # ENDE case 'SUM_DC_Produktion'

    case 'line':
$SQL = "WITH Alle_PVDaten AS (
        select  Zeitpunkt,
		ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Zeitabstand,
		(DC_Produktion - LAG(DC_Produktion) OVER(ORDER BY Zeitpunkt)) AS DC_Produktion,
		(Netzverbrauch - LAG(Netzverbrauch) OVER(ORDER BY Zeitpunkt)) AS Netzbezug,
        ((DC_Produktion - LAG(DC_Produktion) OVER(ORDER BY Zeitpunkt)) - (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt)) - (Batterie_IN - LAG(Batterie_IN) OVER(ORDER BY Zeitpunkt))) AS Direktverbrauch,
		((Batterie_OUT - LAG(Batterie_OUT) OVER(ORDER BY Zeitpunkt))) AS VonBatterie,
		((Batterie_IN - LAG(Batterie_IN) OVER(ORDER BY Zeitpunkt))) AS InBatterie,
        (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt)) AS Einspeisung,
        Vorhersage,
        BattStatus
from pv_daten where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."')
 , Alle_PVDaten2 AS (
	SELECT Zeitpunkt,
    DC_Produktion*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440)  AS Produktion,
	Netzbezug*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440)      AS Netzbezug,
    (CASE WHEN Direktverbrauch < 0 THEN 0 ELSE Direktverbrauch*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) END) AS Direktverbrauch,
	VonBatterie*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440)     AS VonBatterie,
    InBatterie*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440)      AS InBatterie,
	Einspeisung*60/ROUND((JULIANDAY(Zeitpunkt) - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440)     AS Einspeisung,
	Vorhersage,
    BattStatus
FROM Alle_PVDaten
Where Zeitabstand > 4 )
select Zeitpunkt,
		Produktion * -1 AS Produktion,
		Netzbezug * -1 AS Netzbezug,
		Direktverbrauch,
		VonBatterie,
		InBatterie,
		Einspeisung,
		Produktion + Netzbezug - Einspeisung - InBatterie - Direktverbrauch AS Netzverbrauch,
		Produktion + Netzbezug - Einspeisung + VonBatterie - InBatterie AS Gesamtverbrauch,
		Vorhersage,
		BattStatus
FROM Alle_PVDaten2";
return $SQL;
    break; # ENDE case 'line'

    case 'SUM_AC_Verbrauch':
# AC Verbrauch
$SQL = "SELECT 
        MAX(Netzverbrauch)- MIN(Netzverbrauch) + 
        MAX(AC_Produktion) - min(AC_Produktion) + 
        MIN (Einspeisung) - MAX (Einspeisung)
        AS AC_Produktion
from pv_daten where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'";
return $SQL;
    break; # ENDE case 'SUM_AC_Verbrauch'

    case 'bar':
$SQL = "WITH Alle_PVDaten AS (
select Zeitpunkt,
	(max(DC_Produktion) - min(DC_Produktion)) as Produktion,
	(max(Netzverbrauch) - min(Netzverbrauch)) as Netzbezug,
    (max(DC_Produktion) - min(DC_Produktion)) - (max(Einspeisung) - min(Einspeisung)) - (max(Batterie_IN) - min(Batterie_IN)) AS Direktverbrauch,
    (max(Batterie_IN) - min(Batterie_IN)) as InBatterie,
    (max(Batterie_OUT) - min(Batterie_OUT)) as AusBatterie,
    (max(Einspeisung) - min(Einspeisung)) as Einspeisung
from pv_daten
where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
group by STRFTIME('".$groupSTR."', Zeitpunkt))
SELECT Zeitpunkt,
	Produktion * -1 as Produktion,
	Netzbezug * -1 as Netzbezug,
    (CASE WHEN Direktverbrauch < 0 THEN 0 ELSE Direktverbrauch END) as Direktverbrauch,
    (CASE WHEN Direktverbrauch < 0 THEN InBatterie + (Direktverbrauch) ELSE InBatterie END) as InBatterie,
    Produktion + Netzbezug - Einspeisung - InBatterie - Direktverbrauch AS Netzverbrauch,
    Einspeisung
FROM Alle_PVDaten";
return $SQL;
    break; # ENDE case 'Produktion_bar'
} # ENDE switch
} # END function getSQL

function Dia_Options()
{
$optionen = array();
$optionen['Gesamtverbrauch']=['Farbe'=>'rgba(255,0,0,1)','fill'=>'false','stack'=>'1','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y'];
$optionen['Vorhersage']=['Farbe'=>'rgba(255,140,05,1)','fill'=>'false','stack'=>'2','linewidth'=>'2','order'=>'0','borderDash'=>'[15,8]','yAxisID'=>'y'];
$optionen['BattStatus']=['Farbe'=>'rgba(72,118,255,1)','fill'=>'false','stack'=>'3','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]','yAxisID'=>'y2'];
$optionen['Direktverbrauch'] = ['Farbe' => 'rgba(255,215,0,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '1', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['VonBatterie'] = ['Farbe' => 'rgba(45,180,45,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '2', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['InBatterie'] = ['Farbe' => 'rgba(60,215,60,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '3', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Einspeisung'] = ['Farbe' => 'rgba(110,110,110,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '4', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Netzverbrauch'] = ['Farbe' => 'rgba(148,148,148,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '5', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
$optionen['Produktion']=['Farbe'=>'rgba(255,200,0,1)','fill'=>'true','stack'=>'0','linewidth'=>'2','order'=>'1','borderDash'=>'[0,0]','yAxisID'=>'y'];
$optionen['Netzbezug'] = ['Farbe' => 'rgba(110,110,110,1)', 'fill' => 'true', 'stack' => '0', 'linewidth' => '0', 'order' => '1', 'borderDash' => '[0, 0]', 'yAxisID' => 'y'];
return $optionen;
}  # END function Dia_Options



function Optionenausgabe($DBersterTag_Jahr)
{
# HTML-Seite mit Ptionsauswahl ausgeben
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
let year_von = date.getFullYear();
let hours = '0';
let minutes_html = '0' - date.getTimezoneOffset();

// 1 = stunden
if (offset == 1) {
  date.setDate(date.getDate() + 1);
  day_bis = date.getDate();
  month_bis = date.getMonth() + 1;
  year_bis = date.getFullYear();
  document.getElementsByName('diagramtype')[0].checked = true;
  document.getElementsByName('Zeitraum')[0].checked = true;
}

// 2 = tage
if (offset == 2) {
  date.setMonth(date.getMonth() + 1);
  day_von  = 1;
  day_bis  = 1;
  month_bis = date.getMonth() + 1;
  year_bis = date.getFullYear();
  document.getElementsByName('diagramtype')[1].checked = true;
}

// 3 = monate
if (offset == 3) {
  date.setFullYear(date.getFullYear() + 1);
  day_von  = 1;
  day_bis  = 1;
  month_von = 1;
  month_bis = 1;
  year_bis = date.getFullYear();
  document.getElementsByName('diagramtype')[1].checked = true;
}

// 4 = jahre
if (offset == 4) {
  day_von  = 1;
  day_bis  = 1;
  month_von = 1;
  month_bis = 1;
  year_von = $DBersterTag_Jahr;
  year_bis = year_bis + 1;
  document.getElementsByName('diagramtype')[1].checked = true;
}


let von = year_von + '-' + ('0'+month_von).substr(-2) + '-' + ('0'+day_von).substr(-2);
let bis = year_bis + '-' + ('0'+month_bis).substr(-2)+ '-' + ('0'+day_bis).substr(-2);
document.getElementById('DiaDatenVon').value = von;
document.getElementById('DiaDatenBis').value = bis;
}
window.onload = function() { zeitsetzer(1); };
</script>

<div style='text-align: center;'>
<form method='POST' action='$_SERVER[PHP_SELF]'>
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
  <input class='date' type='date' name='DiaDatenVon' id='DiaDatenVon' value='' /><br><br>
  <label class='optionwahl' >Bis:&nbsp;&nbsp;&nbsp;</label>
  <input class='date' type='date' name='DiaDatenBis' id='DiaDatenBis' value='' /><br><br>

  <input type='radio' id='stunden' name='Zeitraum' value='stunden' onclick='zeitsetzer(1)' checked>
  <label class='optionwahl' for='stunden'>Stunden&nbsp;&nbsp;&nbsp;&nbsp;</label>
  <input type='radio' id='tage' name='Zeitraum' value='tage' onclick='zeitsetzer(2)'>
  <label class='optionwahl' for='tage'>Tage</label>
  <input type='radio' id='monate' name='Zeitraum' value='monate' onclick='zeitsetzer(3)'>
  <label class='optionwahl' for='monate'>Monate</label>
  <input type='radio' id='jahre' name='Zeitraum' value='jahre' onclick='zeitsetzer(4)'>
  <label class='optionwahl' for='jahre'>Jahre</label>
  </div>
  </fieldset>

<br><br>
<button type='submit' class='navi' > Diagramm aufrufen</button>
</form>
</div>
";
} # END function Optionenausgabe

function Diagram_ausgabe($Footer, $Diatype, $labels, $daten, $optionen, $EnergieEinheit)
{
$Nachkommastellen = 2;
$Y2_Achse = '';
if ($Diatype == 'line'){
$Y2_Achse = "
      y2: {
        type: 'linear',
        position: 'right',
        min: 0,
        max: 100,
        grid: {
            drawOnChartArea: false
        },
        ticks: {
           stepSize: 20,
           font: {
             size: 20,
           },
           callback: function(value, index, values) {
              return value + ` %`;
           }
        }
      },
";
}
if ($EnergieEinheit == 'W') $Nachkommastellen = 0;
echo " <script>
new Chart('PVDaten', {
    type: '". $Diatype ."',
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
            footerFont: { size: 20 },
            // Einheit beim Tooltip hinzufügen
            callbacks: {
                label: function(context) {
                    let label = context.dataset.label || '';
                    let unit = ' ". $EnergieEinheit ."';
                    if ( label == 'BattStatus' ) {
                        unit = ' %';
                    }
                    return label + ' ' + context.parsed.y + unit;
                },
                footer: function(context) {
                    var total = 0;
                    for (var i = (context.length - 3); i < context.length; i++){
                    total += context[i].raw;
                    }
                    return 'Summe: ' + total.toFixed(". $Nachkommastellen .") + ' ". $EnergieEinheit ."';
                    }
            }
      }
    },
    scales: {
      x: {
        ticks: {
          font: {
             size: 20,
           }
        },
        title: {
          display: true,
          text: '". $Footer ."',
          font: {
             size: 20,
           },
        },
      },
      y: {
        type: 'linear', 
        position: 'left',
        stacked: true,
        ticks: {
           stepSize: 1000,
           font: {
             size: 20,
           }
        }
      },
    ". $Y2_Achse ."
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
}  # END function Diagram_ausgabe
?>

