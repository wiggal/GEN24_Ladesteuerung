<?php

## BEGIN FUNCTIONS
function schalter_ausgeben ($DBersterTag, $DBletzterTag, $Zeitraum, $DiaDatenVon, $DiaDatenBis, $Produktion, $Verbrauch, $Strompreis_Dia_optionen, $schaltertext, $durchschnitt_checked, $activeTab)
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
# Mobile Schalter
$mobile_schaltertext = substr($schaltertext, 2);

# Schalter zum Blättern usw.
echo '<table id="schaltertable"><tr><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$VOR_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$VOR_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" style="opacity: '.$PfeilGrauton_back.'" class="navi" '.$button_back_on.'> &lt;&lt;</button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$heute.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$morgen.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$heute.'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$morgen.'">'."\n";
echo '<button type="submit" class="navi"> aktuell </button>';
echo '</form>'."\n";

echo '</td><td>';
echo '<form method="POST" action="'.$_SERVER["PHP_SELF"].'">'."\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$NACH_DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$NACH_DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '<input type="hidden" name="AnfangVon" value="'.$GLOBALS['_POST']['AnfangVon'].'">'."\n";
echo '<input type="hidden" name="AnfangBis" value="'.$GLOBALS['_POST']['AnfangBis'].'">'."\n";
echo '<button type="submit" style="opacity: '.$PfeilGrauton_vor.'" class="navi" '.$button_vor_on.'> &gt;&gt; </button>';
echo '</form>'."\n";

// Checkbox um Strompreisstatistik auzugeben
// HTML-Ausgabe
echo '</td><td>';
echo '<form method="POST" action="' . $_SERVER["PHP_SELF"] . '">' . "\n";
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="DiaDatenVon" value="'.$DiaDatenVon.'">'."\n";
echo '<input type="hidden" name="DiaDatenBis" value="'.$DiaDatenBis.'">'."\n";
echo '<input type="hidden" name="Zeitraum" value="'.$Zeitraum.'">'."\n";
echo '&nbsp;<input type="checkbox" id="durchschnitt" name="durchschnitt" value="ja" ' . $durchschnitt_checked . ' onchange="zeigeBitteWarten(this)">' . "\n";
echo '<label id="durchschnittLabel" for="durchschnitt"> Statistik</label>' . "\n";
echo '<span id="ladehinweis" style="display:none;"><strong>&nbsp;&nbsp;Bitte warten .....</strong></span>' . "\n";
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
echo '<input type="hidden" name="tab" value="'.$activeTab.'">'."\n";
echo '<input type="hidden" name="programmpunkt" value="option">'."\n";
echo '<button type="submit" class="navi" >';
echo '<span class="desktop-text">'.$schaltertext.'</span>';
#echo '<span class="mobile-text">'.$mobile_schaltertext.'</span>';  #entWIGGlung
echo '<span class="mobile-text">'.$schaltertext.'</span>';
echo '</button>';
echo '</form>'."\n";

echo '</td><td class="summen" style="background-color: '.$Strompreis_Dia_optionen['Netzladen']['Farbe'].'"><b>';
echo "$Produktion kWh</b>";
echo '</td><td class="summen" style="background-color: '.$Strompreis_Dia_optionen['Netzverbrauch']['Farbe'].'"><b>';
echo "$Verbrauch kWh</b>";

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
    global $db;

    # SQL nach $SQLType wählen
    switch ($SQLType) {

        // --- 1. Einfacher Fall: Netzladen (Schnell durch Indizes) ---
        case 'Netzladen':
            $SQL = "SELECT MAX(AC_to_DC) - MIN(AC_to_DC) AS Netzladen
                    FROM pv_daten
                    WHERE Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'";
            return $SQL;

        // --- 2. Einfacher Fall: Netzverbrauch (Schnell durch Indizes) ---
        case 'Netzverbrauch':
            // Berechnung: (Max Netzverbrauch - Min Netzverbrauch) - (Max AC_to_DC - Min AC_to_DC)
            $SQL = "SELECT (MAX(Netzverbrauch) - MIN(Netzverbrauch)) -
                           (MAX(AC_to_DC) - MIN(AC_to_DC)) AS Netzverbrauch
                    FROM pv_daten
                    WHERE Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'";
            return $SQL;

        // --- 3. Komplexer Fall: Datenabruf mit Preisen ('daten') ---
        case 'daten':
             // --- Schritt 1 (PHP): Preis-Sektor bestimmen ---
             $checkSQL = "
                SELECT COUNT(*) AS cnt
                FROM strompreise
                WHERE Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
                  AND strftime('%M', Zeitpunkt) IN ('15','30','45')
            ";
            $results1 = $db->query($checkSQL);
            $check = $results1 ? $results1->fetchArray(SQLITE3_ASSOC) : ['cnt' => 0];

            $PreisSector = ($check['cnt'] > 0) ? 15 : 60;

            // --- Schritt 2 (SQL): Hauptabfrage mit optimiertem CTE ---
            $SQL = "
            WITH Aggregierte_PV AS (
                -- CTE 1: Aggregiere die Zählerstände und die Statuswerte
                SELECT
                    STRFTIME('%Y-%m-%d %H:', Zeitpunkt) ||
                    PRINTF('%02d:00', (CAST(STRFTIME('%M', Zeitpunkt) AS INTEGER) / ".$PreisSector.") * ".$PreisSector.") AS Zeitraum,
                    MAX(Netzverbrauch) AS Netzverbrauch_Ende,
                    MAX(AC_to_DC) AS AC_to_DC_Ende,
                    -- Hinzugefügt: Status/Vorhersage aggregiert (wir nehmen den Maximalwert der Periode)
                    MAX(BattStatus) AS BattStatus,
                    MAX(Vorhersage) AS Vorhersage
                FROM pv_daten
                WHERE Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
                GROUP BY Zeitraum
            )
            , Berechneter_Verbrauch AS (
                -- CTE 2: Berechne den Verbrauch (Differenz) zwischen den Perioden.
                SELECT
                    Zeitraum,
                    (LEAD(Netzverbrauch_Ende) OVER (ORDER BY Zeitraum) - Netzverbrauch_Ende) AS Netzbezug,
                    (LEAD(AC_to_DC_Ende) OVER (ORDER BY Zeitraum) - AC_to_DC_Ende) AS Netzladen
                FROM Aggregierte_PV
                ORDER BY Zeitraum
            )
            SELECT
                sp.Zeitpunkt,
                COALESCE(pv.Netzbezug, 0) - COALESCE(pv.Netzladen, 0) AS Netzverbrauch,
                COALESCE(pv.Netzladen, 0) AS Netzladen,

                -- Abruf der aggregierten Statuswerte über den Join zu 'agg'
                agg.BattStatus,
                agg.Vorhersage,

                sp.Boersenpreis * 100 AS Boersenpreis,
                sp.Bruttopreis * 100 AS Bruttopreis,
                pfc.PV_Prognose,
                pfc.PrognNetzverbrauch / 60 * ".$PreisSector." AS PrognNetzverbrauch,
                pfc.PrognNetzladen / 60 * ".$PreisSector." AS PrognNetzladen,
                pfc.PrognBattStatus
            FROM strompreise AS sp
            LEFT JOIN Berechneter_Verbrauch AS pv
                ON sp.Zeitpunkt = pv.Zeitraum
            LEFT JOIN Aggregierte_PV AS agg
                ON sp.Zeitpunkt = agg.Zeitraum -- NEUER JOIN für Status/Vorhersage
            LEFT JOIN priceforecast AS pfc
                ON sp.Zeitpunkt = pfc.Zeitpunkt
            WHERE sp.Zeitpunkt BETWEEN '".$DiaDatenVon."' AND '".$DiaDatenBis."'
            ORDER BY sp.Zeitpunkt;
            ";

            return $SQL;
    }

    // Standard-Rückgabe, falls $SQLType nicht erkannt wird (jetzt nur diese 3 Fälle)
    return null;
}
function Preisberechnung($DiaDatenVon, $DiaDatenBis, $groupSTR, $db)  # KI optimiert
{  
    $Preisstatistik = [];
    $Zeitraeume = ["T", "M", "J"];

    // 1. Ursprüngliche Grenzen speichern. Wichtig, da die Grenzen in der Schleife verändert werden.
    $Original_DiaDatenVon = $DiaDatenVon;
    $Original_DiaDatenBis = $DiaDatenBis;

    // SQL-Vorlage mit Platzhaltern für die Datumsangaben
    $SQL_TEMPLATE = "
    WITH Stündlicher_Netzverbrauch AS (
        -- Schritt 1: Aggregiere den Netzverbrauch (letzter Zählerstand) pro Stunde
        SELECT
            STRFTIME('%Y-%m-%d %H:00:00', Zeitpunkt) AS Stunde,
            MAX(Netzverbrauch) AS Netzverbrauch_Stunde
        FROM pv_daten
        WHERE Zeitpunkt BETWEEN '{{DiaDatenVon}}' AND '{{DiaDatenBis}}'
        GROUP BY Stunde
    )
    , Stündlicher_Netzbezug AS (
        -- Schritt 2: Berechne den Netzbezug (Verbrauch) pro Stunde mit LEAD
        SELECT
            Stunde,
            -- LEAD(Wert, 1) holt den Zählerstand der nächsten Stunde
            (LEAD(Netzverbrauch_Stunde, 1) OVER (ORDER BY Stunde) - Netzverbrauch_Stunde) AS Netzbezug
        FROM Stündlicher_Netzverbrauch
        ORDER BY Stunde
    )
    , Berechnungsbasis AS (
        -- Schritt 3: Preise zuordnen und Kosten berechnen
        SELECT
            sp.Bruttopreis,
            pv.Netzbezug,
            (pv.Netzbezug * sp.Bruttopreis / 1000.0) AS Preis
        FROM strompreise AS sp
        INNER JOIN Stündlicher_Netzbezug AS pv
            -- JOIN über die volle Stunde
            ON sp.Zeitpunkt = pv.Stunde
        WHERE
            -- Filtern: Nur positiver Verbrauch und gültige Preise
            pv.Netzbezug IS NOT NULL AND pv.Netzbezug > 0 AND sp.Bruttopreis IS NOT NULL
    )
    SELECT
        ROUND(MIN(Bruttopreis), 2) AS MIN,
        ROUND(MAX(Bruttopreis), 2) AS MAX,
        ROUND(AVG(Bruttopreis), 2) AS AVG,
        ROUND(SUM(Preis), 2) AS SUM,
        -- KostSUM: Gesamtkosten / Gesamtverbrauch (in kWh, daher /1000.0)
        ROUND((SUM(Preis) / (SUM(Netzbezug) / 1000.0)), 2) AS KostSUM
    FROM Berechnungsbasis;
    ";

    // 2. Schleife für Tag, Monat, Jahr
    foreach ($Zeitraeume as $Zeitraum) {

        // Aktuelle Zeitgrenzen für diesen Durchlauf
        $Aktuell_Von = $Original_DiaDatenVon;
        $Aktuell_Bis = $Original_DiaDatenBis;

        // Anpassen der Grenzen basierend auf dem Zeitraum (Monat oder Jahr)
        if ($Zeitraum == 'M') {
            // Monat: Start am ersten Tag des Startmonats, Ende am ersten Tag des Folgemonats
            $date = new DateTime($Original_DiaDatenVon);
            $date->modify('first day of this month');
            $Aktuell_Von = $date->format('Y-m-d H:i');

            $date = new DateTime($Original_DiaDatenBis);
            $date->modify('first day of next month');
            $Aktuell_Bis = $date->format('Y-m-d H:i');
        }

        if ($Zeitraum == 'J') {
            // Jahr: Start am 1. Januar des Startjahres, Ende am 1. Januar des Folgejahres
            $date = new DateTime($Original_DiaDatenVon);
            $date->modify('first day of January this year');
            $Aktuell_Von = $date->format('Y-m-d H:i');

            $date = new DateTime($Original_DiaDatenBis);
            $date->modify('first day of January next year');
            $Aktuell_Bis = $date->format('Y-m-d H:i');
        }

        // 3. Platzhalter im SQL-Template ersetzen
        $SQL = str_replace(
            ['{{DiaDatenVon}}', '{{DiaDatenBis}}', '{{groupSTR}}'],
            [$Aktuell_Von, $Aktuell_Bis, $groupSTR],
            $SQL_TEMPLATE
        );

        // 4. Abfrage ausführen und Ergebnisse speichern
        $result = $db->query($SQL);
        if ($result) {
            $Preisstatistik[$Zeitraum] = $result->fetchArray(SQLITE3_ASSOC);
        } else {
            // Fehlerbehandlung hinzufügen
            $Preisstatistik[$Zeitraum] = ['Error' => $db->lastErrorMsg()];
        }
    }

    return $Preisstatistik;
} # ENDE function Preisberechnung

function Optionenausgabe($DBersterTag_Jahr, $activeTab)
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
  <input type='hidden' name='tab' value='$activeTab'>
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
// Schriftgrößen-Bereiche
const isMobile = window.innerWidth < 768;
const fontSize = isMobile ? 10 : 20;
const legendboxWidth = isMobile ? 10 : 20;

// Statistik im Mobile auf 4 Zeilen umbrechen
let preisTitel = $Preisstatistik_ausgabe;
if (isMobile && Array.isArray(preisTitel)) {
    preisTitel = preisTitel
        .map(line =>
            line
                .replace(' Durchschnitt = ', ',Durchschnitt = ')
                .replace(' Pro kWh = ', ',Pro kWh = ')
        )
        .map(l => l.split(','))
        .flat()
        .map(l => l.trim());
}

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
      echo "borderWidth: (isMobile ? 1 : ".$optionen[$x]['linewidth']."),\n";
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
      maintainAspectRatio: false,
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
                 boxWidth: legendboxWidth,
                 font: {
                   size: fontSize,
                 }
            }
        },
        tooltip: {
            titleFont: { size: fontSize },
            bodyFont: { size: fontSize },
            footerFont: { size: fontSize },
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
             size: fontSize,
           }
        },
        title: {
          display: true,
          align: 'start',
          text: preisTitel,
          font: {
             size: fontSize,
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
             size: fontSize,
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
             size: fontSize,
           },
           callback: function(value, index, values) {
              return value >= 0 ? value.toFixed(0) + '' : ''; //Einheit Wh weggelassen
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
           stepSize: fontSize,
           font: {
             size: fontSize,
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

