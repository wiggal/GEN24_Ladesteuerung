<?php

## BEGIN FUNCTIONS
function schalter_ausgeben ($DBersterTag, $diagramtype, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $Produktion, $Verbrauch, $activeTab)
{
date_default_timezone_set('UTC');
$date1 = new DateTime($DiaDatenVon);
$date2 = new DateTime($DiaDatenBis);
// Differenz berechnen
$diff = $date1->diff($date2);

$next_diagramtype = 'line';
if ($diagramtype == 'line') $next_diagramtype = 'bar';
$VOR_DiaDatenBis = $DiaDatenVon;
$NACH_DiaDatenVon = $DiaDatenBis;

# Hier prüfen ob Jahre, Monate, oder Tage geblättert werden soll
if ( $diff->y == 0 AND $diff->m == 0 AND $diff->d == 1) {
    $VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime("$DiaDatenVon -1 day")));
    $NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime("$DiaDatenBis +1 day")));
} elseif ( $diff->y == 0 AND $diff->m == 1 AND $diff->d == 0) {
    $VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime("$DiaDatenVon -1 month")));
    $NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime("$DiaDatenBis +1 month")));
} elseif ( $diff->y == 1 AND $diff->m == 0 AND $diff->d == 0) {
    $VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime("$DiaDatenVon -1 year")));
    $NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime("$DiaDatenBis +1 year")));
} else {
    # Für Freie Auswahl Abstand von bis ermitteln
    # Zeitpunkte mit Zeitzonen, die die Sommerzeit und Winterzeit berücksichtigen
    $zeitpunkt1 = new DateTime($GLOBALS['_POST']['AnfangBis'], new DateTimeZone('Europe/Berlin')); 
    $zeitpunkt2 = new DateTime($GLOBALS['_POST']['AnfangVon'], new DateTimeZone('Europe/Berlin'));
    // Berechne die Differenz in Sekunden
    $timestamp1 = $zeitpunkt1->getTimestamp();
    $timestamp2 = $zeitpunkt2->getTimestamp();
    // Differenz in Sekunden
    $zeitdifferenz = $timestamp1 - $timestamp2;
    $VOR_DiaDatenVon = date("Y-m-d 00:00",(strtotime($DiaDatenVon)-$zeitdifferenz));
    $NACH_DiaDatenBis = date("Y-m-d 00:00",(strtotime($DiaDatenBis)+$zeitdifferenz));
}

# Schalter am Anfang und am Ende deaktivieren
$button_vor_on = '';
$PfeilGrauton_vor = '1.0';
$PfeilGrauton_back = '1.0';
$heute = date("Y-m-d H:i");
if (strtotime($DiaDatenBis) >= strtotime($heute)) {
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
echo '<table id="schaltertable"><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$VOR_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$VOR_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="diagramtype" value="'.$diagramtype.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" style="opacity: '.$PfeilGrauton_back.'" class="navi" '.$button_back_on.'> &nbsp;&lt;&lt;&nbsp;</button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
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
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$NACH_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$NACH_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="diagramtype" value="'.$diagramtype.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" style="opacity: '.$PfeilGrauton_vor.'" class="navi" '.$button_vor_on.'> &nbsp;&gt;&gt;&nbsp; </button>';
echo '</form>'."\n";

echo '</td><td style="text-align:center; width: 100%;">';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="energietype" value="option">'."\n";
echo '<button type="submit" class="navi" > Optionen </button>';
echo '</form>'."\n";

echo '</td><td class="summen" style="background-color: rgba(255,200,0,1)"><b>';
echo "&nbsp;$Produktion kWh&nbsp;</b>";
echo '</td><td class="summen" style="background-color: rgba(255,0,0,1)"><b>';
echo "&nbsp;$Verbrauch kWh&nbsp;</b>";

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
    
$rows = [];
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
    $rows[] = $row; // Alle Zeilen speichern
}

# Wenn Jahre und erster Zeitpunkt ist nicht XXXX-01-01 00:00:00, dann setzen
// Prüfen, ob $rows mindestens einen Datensatz hat
if (!empty($rows) && $XScaleEinheit === 'jahre') {
    // Erstes Element
    $first = &$rows[0];  // Referenz, damit Änderung direkt im Array passiert

    // Jahr aus dem aktuellen Zeitpunkt extrahieren
    $jahr = date('Y', strtotime($first['Zeitpunkt']));

    // Zeitpunkt auf Jahresanfang setzen
    $first['Zeitpunkt'] = $jahr . '-01-01 00:00:00';
}

foreach ($rows as $row) {
        $first = true;
        foreach($row as $x => $val) {
        if ( $first ){
            # Datum nicht mehr zuschneiden, da time als X-Achse
            $label_element = $val;
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

function getSQL(string $SQLType, string $DiaDatenVon, string $DiaDatenBis, string $groupSTR = null): string  #KI optimiert
{
    // Gemeinsame WHERE-Bedingung
    $where = "Zeitpunkt BETWEEN '$DiaDatenVon' AND '$DiaDatenBis'";

    switch ($SQLType) {

        /* -------------------------------------------------------------
         * SUMME DC PRODUKTION
         * ------------------------------------------------------------- */
        case 'SUM_DC_Produktion':
            return "
                SELECT 
                    MAX(DC_Produktion) - MIN(DC_Produktion) AS DC_Produktion
                FROM pv_daten
                WHERE $where
            ";


        /* -------------------------------------------------------------
         * LINE – Zeitreihen-Auswertung
         * ------------------------------------------------------------- */
        case 'line':
            return "
                WITH Alle_PVDaten AS (
                    SELECT *
                    FROM pv_daten
                    WHERE $where
                    GROUP BY STRFTIME('%Y%m%d%H%M', Zeitpunkt) / 10
                ),
                Alle_PVDaten1 AS (
                    SELECT 
                        Zeitpunkt,
                        ROUND((JULIANDAY(Zeitpunkt) 
                               - JULIANDAY(LAG(Zeitpunkt) OVER(ORDER BY Zeitpunkt))) * 1440) AS Zeitabstand,

                        (DC_Produktion - LAG(DC_Produktion) OVER(ORDER BY Zeitpunkt)) AS DC_Produktion,
                        (Netzverbrauch - LAG(Netzverbrauch) OVER(ORDER BY Zeitpunkt)) AS Netzbezug,

                        ( (DC_Produktion - LAG(DC_Produktion) OVER(ORDER BY Zeitpunkt))
                        - (Einspeisung - LAG(Einspeisung) OVER(ORDER BY Zeitpunkt))
                        - (Batterie_IN - LAG(Batterie_IN) OVER(ORDER BY Zeitpunkt)) ) AS Direktverbrauch,

                        (Batterie_OUT - LAG(Batterie_OUT) OVER(ORDER BY Zeitpunkt)) AS VonBatterie,
                        (Batterie_IN  - LAG(Batterie_IN)  OVER(ORDER BY Zeitpunkt)) AS InBatterie,
                        (Einspeisung  - LAG(Einspeisung)  OVER(ORDER BY Zeitpunkt)) AS Einspeisung,

                        Vorhersage * -1 AS Vorhersage,
                        BattStatus
                    FROM Alle_PVDaten
                ),
                Alle_PVDaten2 AS (
                    SELECT 
                        Zeitpunkt,
                        DC_Produktion   * 60 / Zeitabstand AS Produktion,
                        Netzbezug       * 60 / Zeitabstand AS Netzbezug,
                        Direktverbrauch * 60 / Zeitabstand AS Direktverbrauch,
                        VonBatterie     * 60 / Zeitabstand AS VonBatterie,
                        InBatterie      * 60 / Zeitabstand AS InBatterie,
                        Einspeisung     * 60 / Zeitabstand AS Einspeisung,
                        Vorhersage,
                        BattStatus
                    FROM Alle_PVDaten1
                ),
                Netzladen AS (
                    SELECT 
                        Zeitpunkt,
                        Produktion * -1 AS Produktion,
                        Netzbezug  * -1 AS Netzbezug,
                        Direktverbrauch,
                        VonBatterie,
                        InBatterie,
                        Einspeisung,

                        Produktion + Netzbezug - Einspeisung - InBatterie - Direktverbrauch AS Netzverbrauch,
                        Produktion + Netzbezug - Einspeisung + VonBatterie - InBatterie AS Gesamtverbrauch,

                        Vorhersage,
                        BattStatus
                    FROM Alle_PVDaten2
                )
                SELECT 
                    Zeitpunkt,
                    Produktion,
                    Netzbezug,
                    CASE WHEN Direktverbrauch > 0 THEN Direktverbrauch ELSE 0 END AS Direktverbrauch,
                    VonBatterie,
                    InBatterie,
                    Einspeisung,
                    CASE 
                        WHEN Direktverbrauch > 0 THEN Netzverbrauch
                        ELSE Netzverbrauch + Direktverbrauch
                    END AS Netzverbrauch,
                    Gesamtverbrauch,
                    Vorhersage,
                    BattStatus
                FROM Netzladen
            ";


        /* -------------------------------------------------------------
         * SUMME AC VERBRAUCH
         * ------------------------------------------------------------- */
        case 'SUM_AC_Verbrauch':
            return "
                SELECT 
                    (MAX(Netzverbrauch) - MIN(Netzverbrauch)) +
                    (MAX(AC_Produktion) - MIN(AC_Produktion)) -
                    (MAX(Einspeisung)   - MIN(Einspeisung)) 
                    AS AC_Produktion
                FROM pv_daten
                WHERE $where
            ";


        /* -------------------------------------------------------------
         * BAR – Balkendiagramm-Auswertung
         * ------------------------------------------------------------- */
        case 'bar':

            // Sicherheits-Check: groupSTR darf keine Quotes enthalten
            $group = preg_replace('/[^%a-zA-Z0-9]/', '', $groupSTR);

            return "
                WITH Alle_PVDaten AS (
                    SELECT
                        MIN(Zeitpunkt) AS Zeitpunkt,
                        DC_Produktion,
                        Netzverbrauch,
                        Batterie_IN,
                        Batterie_OUT,
                        Einspeisung
                    FROM pv_daten
                    WHERE $where
                    GROUP BY STRFTIME('$group', Zeitpunkt)

                    UNION

                    SELECT
                        MAX(Zeitpunkt) AS Zeitpunkt,
                        DC_Produktion,
                        Netzverbrauch,
                        Batterie_IN,
                        Batterie_OUT,
                        Einspeisung
                    FROM pv_daten
                    WHERE $where
                    ORDER BY Zeitpunkt
                ),
                Alle_PVDaten2 AS (
                    SELECT 
                        Zeitpunkt,
                        LEAD(DC_Produktion) OVER (ORDER BY Zeitpunkt)  - DC_Produktion  AS Produktion,
                        LEAD(Netzverbrauch) OVER (ORDER BY Zeitpunkt)  - Netzverbrauch  AS Netzbezug,
                        LEAD(Batterie_IN)   OVER (ORDER BY Zeitpunkt)  - Batterie_IN    AS InBatterie,
                        LEAD(Batterie_OUT)  OVER (ORDER BY Zeitpunkt)  - Batterie_OUT   AS AusBatterie,
                        LEAD(Einspeisung)   OVER (ORDER BY Zeitpunkt)  - Einspeisung    AS Einspeisung
                    FROM Alle_PVDaten
                )
                SELECT 
                    Zeitpunkt,
                    Produktion * -1 AS Produktion,
                    Netzbezug  * -1 AS Netzbezug,
                    Einspeisung,
                    Netzbezug AS Netzverbrauch,
                    InBatterie,
                    AusBatterie AS VonBatterie,
                    Produktion - InBatterie - Einspeisung AS Direktverbrauch
                FROM Alle_PVDaten2
                WHERE AusBatterie IS NOT NULL
                ORDER BY Zeitpunkt
            ";


        default:
            throw new InvalidArgumentException("Unbekannter SQLType: $SQLType");
    }
}

function Dia_Options($Diatype)
{
$optionen = array();
$optionen['Gesamtverbrauch']=['Farbe'=>'rgba(255,0,0,1)',      'fill'=>'false', 'stack'=>'1','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
$optionen['Vorhersage']=     ['Farbe'=>'rgba(255,140,05,1)',   'fill'=>'false', 'stack'=>'2','linewidth'=>'2','order'=>'0','borderDash'=>'[15,8]','yAxisID'=>'y', 'hidden'=>'false'];
$optionen['BattStatus']=     ['Farbe'=>'rgba(72,118,255,1)',   'fill'=>'false', 'stack'=>'3','linewidth'=>'2','order'=>'0','borderDash'=>'[0,0]', 'yAxisID'=>'y2', 'hidden'=>'false'];
$optionen['Einspeisung'] =   ['Farbe' => 'rgba(110,110,110,1)','fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'5','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
$optionen['InBatterie'] =    ['Farbe' => 'rgba(60,215,60,1)',  'fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'4','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
$optionen['VonBatterie'] =   ['Farbe' => 'rgba(45,180,45,1)',  'fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'3','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
$optionen['Netzverbrauch'] = ['Farbe' => 'rgba(148,148,148,1)','fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'2','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
$optionen['Direktverbrauch']=['Farbe' => 'rgba(255,215,0,1)',  'fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'1','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
$optionen['Produktion']=     ['Farbe'=>'rgba(255,200,0,1)',    'fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'6','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
$optionen['Netzbezug'] =     ['Farbe' => 'rgba(110,110,110,1)','fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'7','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'false'];
# Ausnahme im Balkendiagramm VonBatterie beim Aufruf ausblenden:
if ( $Diatype == 'bar') {
$optionen['VonBatterie'] =   ['Farbe' => 'rgba(45,180,45,1)',  'fill'=> 'true', 'stack'=>'4','linewidth'=>'0','order'=>'3','borderDash'=>'[0,0]', 'yAxisID'=>'y', 'hidden'=>'true'];
}

return $optionen;
}  # END function Dia_Options



function Optionenausgabe($DBersterTag_Jahr, $activeTab)
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
  <input type='hidden' name='tab' value='$activeTab'>
  <fieldset style='display: inline-block;'>
  <legend class='optionwahl'>Diagrammart:</legend>
  <div style='text-align: left'>
  <input type='radio' id='line' name='diagramtype' value='line' checked>
  <label class='optionwahl' for='line'>Linien</label><br>
  <input type='radio' id='bar' name='diagramtype' value='bar'>
  <label class='optionwahl' for='bar'>Balken</label><br>
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
  <label class='optionwahl' for='stunden'>Stunden</label>
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

function Diagram_ausgabe($Footer, $Diatype, $labels, $daten, $optionen, $EnergieEinheit, $Diagrammgrenze, $X_Achse)
{
$Nachkommastellen = 2;
if ($EnergieEinheit == 'W') $Nachkommastellen = 0;
$Y1_stepSize = 100;
if ($EnergieEinheit == 'kWh') $Y1_stepSize = 10;
echo " <script>
// Schriftgrößen-Bereiche
const isMobile = window.innerWidth < 768;
const fontSize = isMobile ? 10 : 20;
const legendboxWidth = isMobile ? 10 : 20;

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
      echo "borderWidth: (isMobile ? 1 : ".$optionen[$x]['linewidth']."),\n";
      echo "borderDash: ".$optionen[$x]['borderDash'].",\n";
      echo "pointRadius: 0,\n";
      echo "cubicInterpolationMode: 'monotone',\n";
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
      maintainAspectRatio: false,
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
                 boxWidth: legendboxWidth,
                 font: {
                   size: fontSize,
                 }
            }
        },
        tooltip: {
            titleAlign: 'center',  // zentriert die Überschrift!
            titleFont: { size: fontSize },
            bodyFont: { size: fontSize },
            footerFont: { size: fontSize },
            callbacks: {
                  label: function(context) {
                    let total_Q = 0;
                    let total_Z = 0;
                    for (var i = 0; i < context.chart.tooltip.dataPoints.length; i++){
                    switch (context.chart.tooltip.dataPoints[i].dataset.label) {
                        case 'Netzbezug':
                        case 'Produktion':
                            total_Q += context.chart.tooltip.dataPoints[i].raw;
                        break;
                        case 'Direktverbrauch':
                        case 'InBatterie':
                        case 'VonBatterie':
                        case 'Einspeisung':
                        case 'Netzverbrauch':
                            total_Z += context.chart.tooltip.dataPoints[i].raw;
                        break;
                    }
                    };
                    // return value in tooltip
                    const labelName = context.dataset.label;
                    const labelValue = context.parsed.y;
                    let unit = ' ". $EnergieEinheit ."';
                    if ( labelName == 'BattStatus' ) {
                        unit = ' %';
                    }
                    const line1 = labelName + ' ' + Math.abs(labelValue.toFixed(". $Nachkommastellen ."))  + ' ' + unit;
                    arrayLines = [ line1 ];
                    const line2 = '==============';
                    const line4 = ' ';
                    if (labelName == 'BattStatus') {
                    arrayLines = [ line1, line4 ];
                    }
                    if (labelName == 'Einspeisung') {
                        line3 = 'Ziel: ' + Math.abs(total_Z.toFixed(". $Nachkommastellen ."))  + ' ' + unit;
                        arrayLines = [ line1, line2, line3, line4 ];
                    }
                    if (labelName == 'Netzbezug') {
                        line3 = 'Quelle: ' + Math.abs(total_Q.toFixed(". $Nachkommastellen ."))  + ' ' + unit;
                        arrayLines = [ line1, line2, line3 ];
                    }
                    return arrayLines;
                }
            } // Ende callbacks:
        }
    },
    scales: {
      x: {
        type: 'time',       // Zeitachse
        time: {
            parser: 'yyyy-MM-dd HH:mm:ss',
            unit: '". $X_Achse['unit'] ."',
            displayFormats: {
                ". $X_Achse['displayFormat'] ."
        },
        tooltipFormat: '". $X_Achse['tooltipFormat'] ."' // Format für den Tooltip-Titel
        },
        min: '". $X_Achse['min'] ."',   // Startzeit
        max: '". $X_Achse['max'] ."',   // Endzeit
        ticks: {
          font: {
             size: fontSize,
           }
        },
        title: {
          display: true,
          text: '". $Footer ."',
          font: {
             size: fontSize,
           },
        },
      },
      y: {
        type: 'linear', 
        position: 'left',
        stacked: true,
        ticks: {
           stepSize: '". $Y1_stepSize ."',
           font: {
             size: fontSize,
           }
        },
        // Hier die Scala auf X-Wert begrenzen
        afterDataLimits(scale) {
          if(scale.max > ".$Diagrammgrenze.") {
          scale.max = ".$Diagrammgrenze.";
          }
          if(scale.min < -".$Diagrammgrenze.") {
          scale.min = -".$Diagrammgrenze.";
          }
        }
      },
      y2: {
        type: 'linear',
        display: 'auto',
        position: 'right',
        min: (context) => {
            return (context.chart.scales.y.min / context.chart.scales.y.max * 100)
        },
        max: 100,
        grid: {
            drawOnChartArea: false
        },
        ticks: {
           stepSize: fontSize,
           font: {
             size: fontSize,
           },
           callback: function(value, index, values) {
              return value >= 0 ? Math.round(value) + ' %' : '';
           }
        }
      },
    }
    },
  });
</script>";
}  # END function Diagram_ausgabe
?>
