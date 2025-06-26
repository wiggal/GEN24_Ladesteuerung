<?php

## BEGIN FUNCTIONS
function schalter_ausgeben ($DBersterTag, $DBletzterTag, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $Produktion, $Verbrauch, $Strompreis_Dia_optionen, $schaltertext, $durchschnitt_checked)
{
# Abstand von bis ermitteln
# Zeitpunkte mit Zeitzonen, die die Sommerzeit und Winterzeit berücksichtigen
$zeitpunkt1 = new DateTime($GLOBALS['_POST']['AnfangBis'], new DateTimeZone('Europe/Berlin')); 
$zeitpunkt2 = new DateTime($GLOBALS['_POST']['AnfangVon'], new DateTimeZone('Europe/Berlin'));
// Berechne die Differenz in Sekunden
$timestamp1 = $zeitpunkt1->getTimestamp();
$timestamp2 = $zeitpunkt2->getTimestamp();
// Differenz in Sekunden
$zeitdifferenz = $timestamp1 - $timestamp2;
$VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime("$DiaDatenVon -1 day")));
$VOR_DiaDatenBis = $DiaDatenVon;
$NACH_DiaDatenVon = $DiaDatenBis;
$NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime("$DiaDatenBis +1 day")));
$heute =  date("Y-m-d 00:00");
$morgen =  date("Y-m-d 00:00",(strtotime("+1 day", strtotime(date("Y-m-d")))));

# Schalter am Anfang und am Ende deaktivieren
$button_vor_on = '';
$PfeilGrauton_vor = '1.0';
$PfeilGrauton_back = '1.0';
if (strtotime($DiaDatenBis) > strtotime($DBletzterTag)) {
    $button_vor_on = 'disabled';
    $PfeilGrauton_vor = '0.3';
};
# Schalter für Tag out of DB  deaktivieren
$button_back_on = '';
if (strtotime($DiaDatenVon) <= strtotime($DBersterTag)) {
    $button_back_on = 'disabled';
    $PfeilGrauton_back = '0.3';
};

# Schalter zum Blättern usw.
echo '<table><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$VOR_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$VOR_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" style="opacity: '.$PfeilGrauton_back.'" class="navi" '.$button_back_on.'> &nbsp;&lt;&lt;&nbsp;</button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$heute.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$morgen.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$heute.'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$morgen.'">'."\n";
echo '<button type="submit" class="navi"> aktuell </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$NACH_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$NACH_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" style="opacity: '.$PfeilGrauton_vor.'" class="navi" '.$button_vor_on.'> &nbsp;&gt;&gt;&nbsp; </button>';
echo '</form>'."\n";

// HTML-Ausgabe
echo '</td><td>';
echo '<form method="POST" action="' . $_SERVER["PHP_SELF"] . '">' . "\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '&nbsp;&nbsp;<input type="checkbox" id="durchschnitt" name="durchschnitt" value="ja" ' . $durchschnitt_checked . ' onchange="zeigeBitteWarten(this)">' . "\n";
echo '<label id="durchschnittLabel" for="durchschnitt"> Durchschnittspreise anzeigen </label>' . "\n";
echo '<span id="ladehinweis" style="display:none;"><strong>Bitte warten...</strong></span>' . "\n";
echo '</form>' . "\n";

// JavaScript
echo '<script>' . "\n";
echo 'function zeigeBitteWarten(checkbox) {' . "\n";
echo '  // Checkbox & Label ausblenden, Hinweis einblenden' . "\n";
echo '  document.getElementById(\'durchschnitt\').style.display = \'none\';' . "\n";
echo '  document.getElementById(\'durchschnittLabel\').style.display = \'none\';' . "\n";
echo '  document.getElementById(\'ladehinweis\').style.display = \'inline\';' . "\n";
echo '  checkbox.form.submit();' . "\n";
echo '}' . "\n";
echo '</script>' . "\n";

echo '</td><td style="text-align:center; width: 100%;">';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="programmpunkt" value="option">'."\n";
echo '<button type="submit" class="navi" > '.$schaltertext.' </button>';
echo '</form>'."\n";

echo '</td><td style="text-align:right; font-size: 170%; background-color: '.$Strompreis_Dia_optionen['Netzladen']['Farbe'].'"><b>';
echo "&nbsp;$Produktion kWh&nbsp;</b>";
echo '</td><td style="text-align:right; font-size: 170%; background-color: '.$Strompreis_Dia_optionen['Netzverbrauch']['Farbe'].'"><b>';
echo "&nbsp;$Verbrauch kWh&nbsp;</b>";

echo '</td></tr></table><br>';
} #END function schalter_ausgeben 

function diagrammdaten( $results, $XScaleEinheit )
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
    
$rows = [];
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
    $rows[] = $row; // Alle Zeilen aufsammeln
}

$count = count(array_filter($rows, fn($entry) => strpos($entry["Zeitpunkt"], "00:00:00") !== false));

// Letzte Zeile entfernen, wenn 00:00:00 vom nächsten Tag enthalten ist
if ( $count  > 1) array_pop($rows);

# MIN und MAX für Y-Achsen setzen
$MIN_y3=0;
$MAX_y3=0;
$MAX_y=0;

foreach ($rows as $row) {
        $first = true;
        $MAX_y_ist=0;
        $MAX_y_prog=0;
        $MAX_y3_Brutto=0;
        foreach($row as $x => $val) {
        if ( $first ){
            # Datum zuschneiden 
            $label_element = substr($val, $cut_von, $cut_anzahl);
            $labels = $labels.$trenner.'"'.$label_element.'"';
            $first = false;
        } else {
            ## MIN und MAX für Y-Achsen ermitteln
            if ($x == 'Boersenpreis' AND $val < $MIN_y3) $MIN_y3 = $val;
            if ($x == 'Bruttopreis' AND $val < $MIN_y3) $MIN_y3 = $val;
            if (($x == 'Boersenpreis' OR $x == 'Bruttopreis') AND $val > $MAX_y3_Brutto) $MAX_y3_Brutto = $val;
            if (($x == 'Vorhersage' OR $x == 'PV_Prognose') AND $val > $MAX_y) $MAX_y = $val;
            if ($x == 'Netzverbrauch' OR $x == 'Netzladen') $MAX_y_ist += $val;
            if ($x == 'PrognNetzverbrauch' OR $x == 'PrognNetzladen') $MAX_y_prog+= $val;

            if (!isset($daten[$x])) $daten[$x] = "";
            $daten[$x] = $daten[$x] .$trenner.$val;
            }
        }
        if ($MAX_y_ist > $MAX_y) $MAX_y = $MAX_y_ist;
        if ($MAX_y_prog > $MAX_y) $MAX_y = $MAX_y_prog;
        if ($MAX_y3_Brutto > $MAX_y3) $MAX_y3 = $MAX_y3_Brutto;
$trenner = ",";
}
$MIN_y3 = $MIN_y3;
$MAX_y3 = $MAX_y3 * 1.1;
$MAX_y = ceil($MAX_y / 100) * 100;
return array($daten, $labels, $MIN_y3, $MAX_y, $MAX_y3);
} #END function diagrammdaten


function getSQL($SQLType, $DiaDatenVon, $DiaDatenBis, $groupSTR)
{
# SQL nach $SQLType wählen
switch ($SQLType) {
    case 'Netzladen':
$SQL = "SELECT 
        MAX (AC_to_DC) - MIN (AC_to_DC) AS Netzladen
from pv_daten where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'";
return $SQL;
    break; # ENDE case 'SUM_DC_Produktion'

    case 'Netzverbrauch':
# AC Verbrauch
$SQL = "SELECT 
        (MAX (Netzverbrauch) - MIN (Netzverbrauch)) - (MAX (AC_to_DC) - MIN (AC_to_DC)) AS Netzverbrauch
from pv_daten where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
";
return $SQL;
    break; # ENDE case 'SUM_Netzverbrauch'

    case 'daten':
# Anpassung an viertestündliche Strompreise
$SQL = "WITH Alle_PVDaten AS (
    SELECT
        STRFTIME('%Y-%m-%d %H:', Zeitpunkt) ||
    printf('%02d:00', (CAST(STRFTIME('%M', Zeitpunkt) AS INTEGER) / 15) * 15) AS Zeitraum_15min,
        LEAD(Netzverbrauch) OVER (ORDER BY Zeitpunkt) - Netzverbrauch AS Netzbezug,
        LEAD(AC_to_DC) OVER (ORDER BY Zeitpunkt) - AC_to_DC AS Netzladen,
        BattStatus,
        Vorhersage
    FROM pv_daten
    where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
    GROUP BY Zeitraum_15min
)
SELECT
    sp.Zeitpunkt,
    pv.Netzbezug - pv.Netzladen AS Netzverbrauch,
    pv.Netzladen AS Netzladen,
    pv.BattStatus AS BattStatus,
    pv.Vorhersage,
    sp.Boersenpreis * 100 AS Boersenpreis,
    sp.Bruttopreis * 100 AS Bruttopreis,
	pfc.PV_Prognose,
	pfc.PrognNetzverbrauch,
	pfc.PrognNetzladen,
	pfc.PrognBattStatus
FROM strompreise AS sp
LEFT JOIN Alle_PVDaten AS pv
    ON sp.Zeitpunkt = pv.Zeitraum_15min -- JOIN über die Stunden
LEFT JOIN priceforecast AS pfc
    ON sp.Zeitpunkt = pfc.Zeitpunkt -- JOIN über die Stunden
where sp.Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
ORDER BY sp.Zeitpunkt
";
return $SQL;
    break; # ENDE case 'Produktion_bar'
} # ENDE switch
} # END function getSQL

function Preisberechnung($DiaDatenVon, $DiaDatenBis, $groupSTR, $db) {
# Schleife für Tag, Monat, Jahr
$Preisstatistik = [];
$Zeitraeume = ["T", "M", "J"];

foreach ($Zeitraeume as $Zeitraum) {


    if ($Zeitraum == 'M') {
        $date = new DateTime($DiaDatenVon);
        $date->modify('first day of this month');
        $DiaDatenVon =  $date->format('Y-m-d H:i'); 
        $date = new DateTime($DiaDatenBis);
        $date->modify('first day of next month');
        $DiaDatenBis =  $date->format('Y-m-d H:i'); 
    }
    if ($Zeitraum == 'J') {
        $date = new DateTime($DiaDatenVon);
        $date->modify('first day of January this year');
        $DiaDatenVon =  $date->format('Y-m-d H:i'); 
        $date = new DateTime($DiaDatenBis);
        $date->modify('first day of January next year');
        $DiaDatenBis =  $date->format('Y-m-d H:i'); 
    }

    $SQL = "WITH Alle_PVDaten AS (
        SELECT
            STRFTIME('%Y-%m-%d %H:00:00', Zeitpunkt) AS Zeitpunkt,
            LEAD(Netzverbrauch) OVER (ORDER BY Zeitpunkt) - Netzverbrauch AS Netzbezug
        FROM pv_daten
        where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
        group by STRFTIME('".$groupSTR."', Zeitpunkt)
    )
    , Alle_PVDaten2 AS (SELECT
        sp.Zeitpunkt,
        COALESCE(pv.Netzbezug, 'null') AS Netzverbrauch,
        sp.Bruttopreis AS Bruttopreis
    FROM strompreise AS sp
    LEFT JOIN Alle_PVDaten AS pv
        ON sp.Zeitpunkt = pv.Zeitpunkt -- JOIN über die Stunden
    where sp.Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."' AND Netzverbrauch is not 'null')
    , Alle_PVDaten3 AS (SELECT
    Netzverbrauch,
    Bruttopreis,
    Netzverbrauch * Bruttopreis/1000.0 AS Preis
    FROM Alle_PVDaten2)
    SELECT
    round(MIN(Bruttopreis),2) AS MIN,
    round(MAX(Bruttopreis),2) AS MAX,
    round(AVG(Bruttopreis),2) AS AVG,
    round(sum(Preis),2) AS SUM,
    round((sum(Preis)/(sum(Netzverbrauch)/1000.0)),2) AS KostSUM
    FROM Alle_PVDaten3
    ";

    $result = $db->query($SQL);
    $Preisstatistik[$Zeitraum] = $result->fetchArray(SQLITE3_ASSOC);

} # ENDE foreach ($Zeitraeume 

return $Preisstatistik;
} # ENDE function Preisberechnung

function Optionenausgabe($DBersterTag_Jahr)
{
# HTML-Seite mit Ptionsauswahl ausgeben
echo "
<center>
<br><br><br><p class='optionwahl'>Tag auswählen!</p>
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

let von = year_von + '-' + ('0'+month_von).substr(-2) + '-' + ('0'+day_von).substr(-2);
let bis = year_bis + '-' + ('0'+month_bis).substr(-2)+ '-' + ('0'+day_bis).substr(-2);
document.getElementById('DiaDatenVon').value = von;
document.getElementById('DiaDatenBis').value = bis;
}
window.onload = function() { zeitsetzer(1); };
</script>

<div style='text-align: center;'>
<form method='POST' action='$_SERVER[PHP_SELF]'>
  <fieldset style='display: none;'>
  <legend class='optionwahl'>Diagrammart:</legend>
  <div style='text-align: left'>
  <input type='radio' id='bar' name='diagramtype' value='bar' checked>
  <label class='optionwahl' for='bar'>Balken&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</label><br>
  </div>
  </fieldset>
  <br>

  <fieldset style='display: inline-block;'>
  <legend class='optionwahl'></legend>
  <div style='text-align: left'>
  <input class='date' type='date' name='DiaDatenVon' id='DiaDatenVon' value='' /><br><br>
  <input type='hidden' id='stunden' name='Zeitraum' value='stunden' onclick='zeitsetzer(1)' checked>
  </div>
  </fieldset>

<br><br>
<button type='submit' class='navi' > Diagramm aufrufen</button>
</form>
</div>
";
} # END function Optionenausgabe

function Diagram_ausgabe($labels, $daten, $optionen, $Preisstatistik,  $MIN_y3, $MAX_y, $MAX_y3)
{
if ($Preisstatistik != '') {
    $Preisstatistik_ausgabe="['Bruttopreis (T|M|J): Min = {$Preisstatistik['T']['MIN']}€ | {$Preisstatistik['M']['MIN']}€ | {$Preisstatistik['J']['MIN']}€ \
    Max = {$Preisstatistik['T']['MAX']}€ | {$Preisstatistik['M']['MAX']}€ | {$Preisstatistik['J']['MAX']}€ \
    Durchschnitt = {$Preisstatistik['T']['AVG']}€ | {$Preisstatistik['M']['AVG']}€ | {$Preisstatistik['J']['AVG']}€',
                'Kosten (T|M|J):      Gesamt = {$Preisstatistik['T']['SUM']}€ | {$Preisstatistik['M']['SUM']}€ | {$Preisstatistik['J']['SUM']}€ \
                Pro kWh = {$Preisstatistik['T']['KostSUM']}€ | {$Preisstatistik['M']['KostSUM']}€ | {$Preisstatistik['J']['KostSUM']}€']";
} else {
    $Preisstatistik_ausgabe='\'\'';
    }

echo " <script>
Chart.register(ChartDataLabels);
new Chart('PVDaten', {
    data: {
      labels: [". $labels ."],
      datasets: [{";
      $trenner = "";
      foreach($daten as $x => $val) {
      echo $trenner;
      echo "label: '$x',\n";
      echo "data: [ $val ],\n";
      echo "decimals: '".$optionen[$x]['decimals']."',\n";
      echo "type: '".$optionen[$x]['type']."',\n";
      echo "borderColor: '".$optionen[$x]['Farbe']."',\n";
      echo "backgroundColor: '".$optionen[$x]['Farbe']."',\n";
      echo "borderWidth: '".$optionen[$x]['linewidth']."',\n";
      echo "unit: '".$optionen[$x]['unit']."',\n";
      echo "showLabel: ".$optionen[$x]['showLabel'].",\n";
      echo "pointRadius: 0,\n";
      echo "cubicInterpolationMode: 'default',\n";
      echo "fill: ".$optionen[$x]['fill'].",\n";
      echo "stack: '".$optionen[$x]['stack']."',\n";
      echo "order: '".$optionen[$x]['order']."',\n";
      echo "yAxisID: '".$optionen[$x]['yAxisID']."',\n";
      echo "hidden: ".$optionen[$x]['hidden']."\n";
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
        // hier werden die Labels definiert
        datalabels: {
                display: (context) => context.dataset.showLabel, // nicht gewünschte Datasets Labels weglassen
                formatter: function(value, context) {
                    const datasetLabel = context.dataset.label;
                    const dataIndex = context.dataIndex;
                    const chart = context.chart;
                    const decimals = context.dataset.decimals || 0; // Standard: 0
                    let displayValue = value;
                    return displayValue !== 0 ? displayValue.toFixed(decimals) + context.dataset.unit : ''; // Zeigt nur Werte ungleich 0 an und Einheit pro Dataset
                },
                align: (context) => {
                    // Wechselt die Position der Labels, um Überlappungen zu vermeiden
                    const index = context.datasetIndex;
                    return index % 2 === 0 ? 'top' : 'bottom';
                },
                offset: (context) => context.datasetIndex * 4, // Dynamischer Abstand zur Vermeidung von Überlappungen
                color: function(context) {
                    return context.dataset.backgroundColor;
                },
                anchor: 'end',
                align: 'top',
                font: {
                    size: 18,
                }
            },
        title: {
            display: true,
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
            //filter: (tooltipItem) => tooltipItem.raw !== '', 
            callbacks: {
                  label: function(context) {
                    // return value in tooltip
                    let labelName = context.dataset.label || '';
                    //let labelValue = context.raw;
                    let labelValue = context.parsed.y;
                    let decimals = context.dataset.decimals || 0; // Standard: 0
                    let unit = context.dataset.unit || '';

                    if (labelValue !== null && labelValue !== undefined) {
                        return `\${labelName}: \${labelValue.toFixed(decimals)} \${unit}`;
                    }
                    return null;
                }
            } // Ende callbacks:
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
          align: 'start',
          text: $Preisstatistik_ausgabe ,
          font: {
             size: 20,
           },
        },
      },
      y3: {
        type: 'linear',
        display: true,
        position: 'left',
        min: ".$MIN_y3.",
        max: ".$MAX_y3.",
        grid: {
            drawOnChartArea: true
        },
        ticks: {
           stepSize: 5,
           font: {
             size: 20,
           },
           callback: function(value, index, values) {
              return value.toFixed(0) + 'ct';
           }
        }
      },
      y: {
        type: 'linear', 
        position: 'right',
        stacked: true,
        max: ".$MAX_y.",
        min: (context) => {
            let maxY = context.chart.scales.y.max;
            return (context.chart.scales.y3.min / context.chart.scales.y3.max * maxY)
        },
        grid: {
            drawOnChartArea: false
        },
        ticks: {
           font: {
             size: 20,
           },
           callback: function(value, index, values) {
              return value >= 0 ? value.toFixed(0) + 'W' : '';
           }
        },
      },
      y2: {
        type: 'linear',
        display: false,
        position: 'right',
        min: (context) => {
            return (context.chart.scales.y3.min / context.chart.scales.y3.max * 100)
        },
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
              return value >= 0 ? Math.round(value) + '%' : '';
           }
        }
      },
      },
    },
  });
</script>";
}  # END function Diagram_ausgabe
?>

