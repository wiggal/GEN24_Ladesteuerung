<?php

## BEGIN FUNCTIONS
function schalter_ausgeben ($DBersterTag, $DBletzterTag, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $Produktion, $Verbrauch, $Strompreis_Dia_optionen, $schaltertext)
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
$VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime($DiaDatenVon)-$zeitdifferenz));
$VOR_DiaDatenBis = $DiaDatenVon;
$NACH_DiaDatenVon = $DiaDatenBis;
$NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime($DiaDatenBis)+$zeitdifferenz));
$heute =  date("Y-m-d 00:00");
$morgen =  date("Y-m-d 00:00",(strtotime("+1 day", strtotime(date("Y-m-d")))));

# Schalter am Anfang und am Ende deaktivieren
$button_vor_on = '';
if (strtotime($DiaDatenBis) > strtotime($DBletzterTag)) $button_vor_on = 'disabled';
# Schalter für Tag out of DB  deaktivieren
$button_back_on = '';
if (strtotime($DiaDatenVon) <= strtotime($DBersterTag)) $button_back_on = 'disabled';

# Schalter zum Blättern usw.
echo '<table><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$VOR_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$VOR_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" class="navi" '.$button_back_on.'> &nbsp;&lt;&lt;&nbsp;</button>';
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
echo '<button type="submit" class="navi" '.$button_vor_on.'> &nbsp;&gt;&gt;&nbsp; </button>';
echo '</form>'."\n";

echo '</td><td style="text-align:center; width: 100%;">';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="programmpunkt" value="option">'."\n";
echo '<button type="submit" class="navi" > '.$schaltertext.' </button>';
echo '</form>'."\n";

echo '</td><td style="text-align:right; font-size: 170%; background-color: '.$Strompreis_Dia_optionen['Netzladen']['Farbe'].'">';
echo "&nbsp;$Produktion KWh&nbsp;";
echo '</td><td style="text-align:right; font-size: 170%; background-color: '.$Strompreis_Dia_optionen['Netzverbrauch']['Farbe'].'">';
echo "&nbsp;$Verbrauch KWh&nbsp;";

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
    $rows[] = $row; // Alle Zeilen speichern
}

$count = count(array_filter($rows, fn($entry) => strpos($entry["Zeitpunkt"], "00:00:00") !== false));

// Letzte Zeile entfernen, wnn 00:00:00 vom nächsten Tag enthalten ist
if ( $count  > 1) array_pop($rows);

foreach ($rows as $row) {
        $first = true;
        foreach($row as $x => $val) {
        if ( $first ){
            # Datum zuschneiden 
            $label_element = substr($val, $cut_von, $cut_anzahl);
            $labels = $labels.$trenner.'"'.$label_element.'"';
            $first = false;
        } else {
            if (!isset($daten[$x])) $daten[$x] = "";
            $daten[$x] = $daten[$x] .$trenner.$val;
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
$SQL = "WITH Alle_PVDaten AS (
    SELECT
        STRFTIME('%Y-%m-%d %H:00:00', Zeitpunkt) AS Zeitpunkt,
        LEAD(Netzverbrauch) OVER (ORDER BY Zeitpunkt) - Netzverbrauch AS Netzbezug,
        LEAD(AC_to_DC) OVER (ORDER BY Zeitpunkt) - AC_to_DC AS Netzladen,
        BattStatus
    FROM pv_daten
    where Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
    group by STRFTIME('".$groupSTR."', Zeitpunkt)
)
SELECT
    sp.Zeitpunkt,
    pv.Netzbezug - pv.Netzladen AS Netzverbrauch,
    pv.Netzladen AS Netzladen,
    pv.BattStatus AS BattStatus,
    sp.Bruttopreis * 100 AS Bruttopreis,
	pfc.PrognNetzverbrauch,
	pfc.PrognNetzladen,
	pfc.PrognBattStatus
FROM strompreise AS sp
LEFT JOIN Alle_PVDaten AS pv
    ON sp.Zeitpunkt = pv.Zeitpunkt -- JOIN über die Stunden
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

function Diagram_ausgabe($labels, $daten, $optionen, $Preisstatistik)
{
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
      echo "pointRadius: 2,\n";
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
                display: (context) => context.dataset.data[context.dataIndex] > 10 && context.dataset.showLabel, // Verhindert, dass < 10  und nicht gewünschte Datasets Labels anzeigen
                formatter: function(value, context) {
                    const decimals = context.dataset.decimals || 0; // Standard: 0
                    return value > 10 ? value.toFixed(decimals) + context.dataset.unit: ''; // Zeigt nur Werte größer 10 an und Einheit pro Dataset
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
          text: ['Bruttopreis (T|M|J): Min = ".$Preisstatistik['T']['MIN']."€ | ".$Preisstatistik['M']['MIN']."€ | ".$Preisstatistik['J']['MIN']."€ \
    Max = ".$Preisstatistik['T']['MAX']."€ | ".$Preisstatistik['M']['MAX']."€ | ".$Preisstatistik['J']['MAX']."€ \
    Durchschnitt = ".$Preisstatistik['T']['AVG']."€ | ".$Preisstatistik['M']['AVG']."€ | ".$Preisstatistik['J']['AVG']."€',
                'Kosten (T|M|J):      Gesamt = ".$Preisstatistik['T']['SUM']."€ | ".$Preisstatistik['M']['SUM']."€ | ".$Preisstatistik['J']['SUM']."€ \
                Pro kWh = ".$Preisstatistik['T']['KostSUM']."€ | ".$Preisstatistik['M']['KostSUM']."€ | ".$Preisstatistik['J']['KostSUM']."€'],
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
           font: {
             size: 20,
           },
           callback: function(value, index, values) {
              return value >= 0 ? Math.round(value) + 'W' : '';
           }
        },
      },
      y2: {
        type: 'linear',
        display: 'auto',
        position: 'right',
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
      y3: {
        type: 'linear',
        display: false,
        position: 'left',
        grid: {
            drawOnChartArea: false
        },
        ticks: {
           stepSize: 20,
           font: {
             size: 20,
           },
           callback: function(value, index, values) {
              return value >= 0 ? Math.round(value) + 'ct.' : '';
           }
        }
      },
    }
    },
  });
</script>";
}  # END function Diagram_ausgabe
?>

