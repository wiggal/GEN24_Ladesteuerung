<?php
/**
 * weatherStats_ajax.php
 * ======================
 * Berechnet die Treffsicherheit (MAE, RMSE, Bias, MAPE) der einzelnen
 * PV-Prognosedienste in weatherData.sqlite gegen die tatsächliche Produktion
 * und schlägt daraus neue Gewichte je Dienst vor.
 *
 * Zusätzlich wird erkannt, mit welcher Methode die gespeicherte "Prognose"
 * berechnet wurde (gewichteter Mittelwert oder gewichteter Median der
 * Rohdienste) - durch Vergleich der gespeicherten Werte mit selbst
 * berechnetem Mittel/Median anhand der jeweils gespeicherten Gewichte.
 * Die Methode ist global gleich (nicht pro Zeitpunkt unterschiedlich) und
 * wird per Mehrheitsentscheid über alle klassifizierbaren Zeitpunkte
 * bestimmt und in der Ausgabe als Info-Zeile angezeigt.
 *
 * Nur Zeitpunkte mit Produktion > MIN_ACTUAL_FOR_STATS (Standard 500 W)
 * fließen in die Auswertung ein.
 *
 * Wird per AJAX aus weatherDataManager.php aufgerufen (Button "Prognose-
 * genauigkeit anzeigen") und gibt ein HTML-Fragment (Tabelle) zurück,
 * kein vollständiges HTML-Dokument.
 *
 * GET-Parameter:
 *   days  Anzahl der letzten Tage, die ausgewertet werden sollen.
 *         0 oder fehlend = kompletter verfügbarer Zeitraum.
 */

require_once "config_parser.php";

$SQLite_file = $PythonDIR . "/weatherData.sqlite";
if (!file_exists($SQLite_file)) {
    echo "<p>SQLite-Datei " . htmlspecialchars($SQLite_file) . " existiert nicht.</p>";
    exit;
}

// ---------------------------------------------------------------------
// Konfiguration
// ---------------------------------------------------------------------
$ACTUAL_SOURCE_LABEL    = 'Produktion';           // Quelle mit den Ist-Werten
$COMBINED_SOURCE_LABELS = ['Prognose', 'Basis'];  // bereits kombinierte Werte, nur Referenz
$METHOD_REFERENCE_LABEL = 'Prognose';             // welches Label zur Methodenerkennung herangezogen wird
$MIN_ACTUAL_FOR_STATS   = 500;                    // W, nur Zeitpunkte mit Produktion > diesem Wert werden gewertet
$MAX_RMSE_RATIO         = 2.0;                    // RMSE > bester RMSE * diesem Faktor -> Gewicht 0
$METHOD_EPSILON_REL     = 0.005;                  // relative Toleranz, ab der Mittel/Median nicht unterscheidbar sind

$days = isset($_GET['days']) ? intval($_GET['days']) : 0;

$db = new SQLite3($SQLite_file);

if ($days > 0) {
    $grenzeDatum = date('Y-m-d H:i:s', strtotime("-$days days"));
    $stmt = $db->prepare("SELECT Zeitpunkt, Quelle, Prognose_W, Gewicht FROM weatherData WHERE Zeitpunkt >= :grenze ORDER BY Zeitpunkt ASC");
    $stmt->bindValue(':grenze', $grenzeDatum, SQLITE3_TEXT);
    $result = $stmt->execute();
} else {
    $result = $db->query("SELECT Zeitpunkt, Quelle, Prognose_W, Gewicht FROM weatherData ORDER BY Zeitpunkt ASC");
}

// Nach Zeitpunkt gruppieren: $byTime[Zeitpunkt][Quelle] = ['wert' => .., 'gewicht' => ..]
$byTime = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    if ($row['Prognose_W'] === null) {
        continue;
    }
    $byTime[$row['Zeitpunkt']][$row['Quelle']] = [
        'wert'    => (float)$row['Prognose_W'],
        'gewicht' => $row['Gewicht'],
    ];
}

if (empty($byTime)) {
    echo "<p>Keine Daten im gewählten Zeitraum gefunden.</p>";
    exit;
}

// ---------------------------------------------------------------------
// Hilfsfunktionen: gewichteter Mittelwert / gewichteter Median
// ---------------------------------------------------------------------
function weightedMean(array $pairs) {
    $sw = 0.0; $swv = 0.0;
    foreach ($pairs as $p) {
        $sw += $p[1];
        $swv += $p[1] * $p[0];
    }
    return $sw > 0 ? $swv / $sw : null;
}

function weightedMedian(array $pairs) {
    if (empty($pairs)) {
        return null;
    }
    usort($pairs, function ($a, $b) { return $a[0] <=> $b[0]; });
    $total = array_sum(array_column($pairs, 1));
    if ($total <= 0) {
        return null;
    }
    $cum = 0.0;
    foreach ($pairs as $p) {
        $cum += $p[1];
        if ($cum >= $total / 2) {
            return $p[0];
        }
    }
    $last = end($pairs);
    return $last[0];
}

// ---------------------------------------------------------------------
// Methode je Zeitpunkt erkennen: "Prognose" mit selbst berechnetem
// gewichtetem Mittel/Median der Rohdienste vergleichen
// ---------------------------------------------------------------------
$methodByZeit = [];
$methodCounts = ['mittelwert' => 0, 'median' => 0, 'unklar' => 0, 'nicht_bestimmbar' => 0];

foreach ($byTime as $zeitpunkt => $werte) {
    if (!isset($werte[$ACTUAL_SOURCE_LABEL]) || $werte[$ACTUAL_SOURCE_LABEL]['wert'] <= $MIN_ACTUAL_FOR_STATS) {
        continue; // gleiche Schwelle wie bei der eigentlichen Statistik
    }
    if (!isset($werte[$METHOD_REFERENCE_LABEL])) {
        continue; // keine gespeicherte Prognose zum Vergleich vorhanden
    }

    $rawPairs = [];
    foreach ($werte as $q => $info) {
        if ($q === $ACTUAL_SOURCE_LABEL || in_array($q, $COMBINED_SOURCE_LABELS)) {
            continue;
        }
        $w = (float)$info['gewicht'];
        if ($w <= 0) {
            continue; // Quellen mit Gewicht 0 fließen definitionsgemäß nicht in Mittel/Median ein
        }
        $rawPairs[] = [$info['wert'], $w];
    }

    if (count($rawPairs) < 2) {
        $methodCounts['nicht_bestimmbar']++;
        continue;
    }

    $mean = weightedMean($rawPairs);
    $median = weightedMedian($rawPairs);
    $stored = $werte[$METHOD_REFERENCE_LABEL]['wert'];

    $diffMean = abs($stored - $mean);
    $diffMedian = abs($stored - $median);
    $scale = max(abs($mean), abs($median), 1.0);

    if (abs($diffMean - $diffMedian) <= $scale * $METHOD_EPSILON_REL) {
        $methodByZeit[$zeitpunkt] = 'unklar';
        $methodCounts['unklar']++;
    } elseif ($diffMean < $diffMedian) {
        $methodByZeit[$zeitpunkt] = 'mittelwert';
        $methodCounts['mittelwert']++;
    } else {
        $methodByZeit[$zeitpunkt] = 'median';
        $methodCounts['median']++;
    }
}

// ---------------------------------------------------------------------
// Statistik + Gewichtsvorschlag für eine Menge von Zeitpunkten berechnen
// $erlaubteZeitpunkte === null bedeutet: alle Zeitpunkte zulassen
// ---------------------------------------------------------------------
function berechneStatistik(array $byTime, $erlaubteZeitpunkte, $ACTUAL_SOURCE_LABEL, $COMBINED_SOURCE_LABELS, $MIN_ACTUAL_FOR_STATS, $MAX_RMSE_RATIO, $basisMetrik = 'rmse') {
    // $basisMetrik bestimmt, welche Fehlergröße für Ausschluss/Gewichtsvorschlag/Sortierung
    // herangezogen wird: 'rmse' passt zum gewichteten Mittelwert (minimiert den quadratischen
    // Fehler -> inverse-Varianz-Gewichtung), 'mae' passt zum gewichteten Median (minimiert den
    // absoluten Fehler; RMSE würde Ausreißer bestrafen, gegen die der Median ohnehin robust ist).
    $stats = [];
    $minZeit = null;
    $maxZeit = null;

    foreach ($byTime as $zeitpunkt => $werte) {
        if ($erlaubteZeitpunkte !== null && !isset($erlaubteZeitpunkte[$zeitpunkt])) {
            continue;
        }
        if (!isset($werte[$ACTUAL_SOURCE_LABEL])) {
            continue;
        }
        $actual = $werte[$ACTUAL_SOURCE_LABEL]['wert'];
        if ($actual <= $MIN_ACTUAL_FOR_STATS) {
            continue;
        }

        if ($minZeit === null || $zeitpunkt < $minZeit) $minZeit = $zeitpunkt;
        if ($maxZeit === null || $zeitpunkt > $maxZeit) $maxZeit = $zeitpunkt;

        foreach ($werte as $quelle => $info) {
            if ($quelle === $ACTUAL_SOURCE_LABEL) {
                continue;
            }
            $prognose = $info['wert'];
            $signedErr = $prognose - $actual;
            $absErr = abs($signedErr);

            if (!isset($stats[$quelle])) {
                $stats[$quelle] = [
                    'n' => 0, 'sumAbs' => 0.0, 'sumSq' => 0.0, 'sumSigned' => 0.0,
                    'sumPct' => 0.0, 'nPct' => 0, 'gewicht' => $info['gewicht'],
                ];
            }
            $stats[$quelle]['n']++;
            $stats[$quelle]['sumAbs'] += $absErr;
            $stats[$quelle]['sumSq'] += $signedErr * $signedErr;
            $stats[$quelle]['sumSigned'] += $signedErr;
            $stats[$quelle]['gewicht'] = $info['gewicht'];
            $stats[$quelle]['sumPct'] += $absErr / $actual;
            $stats[$quelle]['nPct']++;
        }
    }

    if (empty($stats)) {
        return null;
    }

    foreach ($stats as $quelle => &$s) {
        $s['mae']  = $s['sumAbs'] / $s['n'];
        $s['rmse'] = sqrt($s['sumSq'] / $s['n']);
        $s['bias'] = $s['sumSigned'] / $s['n'];
        $s['mape'] = $s['nPct'] > 0 ? ($s['sumPct'] / $s['nPct']) * 100 : null;
    }
    unset($s);

    $rawQuellen = array_values(array_filter(array_keys($stats), function ($q) use ($COMBINED_SOURCE_LABELS) {
        return !in_array($q, $COMBINED_SOURCE_LABELS);
    }));
    $nRaw = count($rawQuellen);

    foreach ($stats as $q => &$s) {
        $s['vorschlag'] = null;
    }
    unset($s);

    if ($nRaw > 0) {
        $metrikWerte = array_map(function ($q) use ($stats, $basisMetrik) { return $stats[$q][$basisMetrik]; }, $rawQuellen);
        $minMetrik = min($metrikWerte);

        $infQuellen = [];
        $schlechteQuellen = [];
        $invMetrik = [];

        foreach ($rawQuellen as $q) {
            $metrik = $stats[$q][$basisMetrik];
            if ($metrik <= 0) {
                $infQuellen[] = $q;
            } elseif ($minMetrik > 0 && $metrik > $minMetrik * $MAX_RMSE_RATIO) {
                $schlechteQuellen[] = $q;
                $stats[$q]['vorschlag'] = 0.0;
            } else {
                $invMetrik[$q] = 1.0 / $metrik;
            }
        }

        if (!empty($infQuellen)) {
            foreach ($rawQuellen as $q) {
                if (in_array($q, $schlechteQuellen)) {
                    continue;
                }
                $stats[$q]['vorschlag'] = in_array($q, $infQuellen)
                    ? round($nRaw / count($infQuellen), 3)
                    : 0.0;
            }
        } elseif (!empty($invMetrik)) {
            $total = array_sum($invMetrik);
            if ($total > 0) {
                foreach ($invMetrik as $q => $v) {
                    $stats[$q]['vorschlag'] = round($v / $total * $nRaw, 3);
                }
            }
        }
    }

    uasort($stats, function ($a, $b) use ($basisMetrik) { return $a[$basisMetrik] <=> $b[$basisMetrik]; });

    return ['stats' => $stats, 'minZeit' => $minZeit, 'maxZeit' => $maxZeit];
}

// ---------------------------------------------------------------------
// Render-Funktion für eine Ergebnistabelle
// ---------------------------------------------------------------------
function renderTabelle($titel, $ergebnis, $COMBINED_SOURCE_LABELS, $MIN_ACTUAL_FOR_STATS, $basisMetrik = 'rmse') {
    if ($ergebnis === null) {
        echo "<h4 style=\"margin-bottom:4px;\">" . htmlspecialchars($titel) . "</h4>";
        echo "<p style=\"font-size:0.85em; color:#888;\">Keine ausreichenden Daten für diese Methode gefunden.</p>";
        return;
    }
    $stats = $ergebnis['stats'];
    $maeStyle  = $basisMetrik === 'mae'  ? 'text-decoration:underline;' : '';
    $rmseStyle = $basisMetrik === 'rmse' ? 'text-decoration:underline;' : '';
    ?>
    <h4 style="margin-bottom:4px;"><?php echo htmlspecialchars($titel); ?></h4>
    <p style="font-size:0.85em; color:#555; margin-top:0;">
        <?php echo htmlspecialchars($ergebnis['minZeit']); ?> bis <?php echo htmlspecialchars($ergebnis['maxZeit']); ?>
        &mdash; Produktion &gt; <?php echo $MIN_ACTUAL_FOR_STATS; ?> W
    </p>
    <table id="StatistikTable">
        <thead>
        <tr>
            <th>Quelle</th>
            <th>n</th>
            <th style="<?php echo $maeStyle; ?>" title="Basis für den Gewichtsvorschlag, wenn Methode = Median">MAE (W)</th>
            <th style="<?php echo $rmseStyle; ?>" title="Basis für den Gewichtsvorschlag, wenn Methode = Mittelwert">RMSE (W)</th>
            <th>Bias (W)</th>
            <th>MAPE (%)</th>
            <th>Gewicht aktuell</th>
            <th>Gewicht Vorschlag</th>
        </tr>
        </thead>
        <tbody>
        <?php foreach ($stats as $quelle => $s):
            $isReference = in_array($quelle, $COMBINED_SOURCE_LABELS);
            $rowStyle = $isReference ? "background-color:#ffecec;" : "";
        ?>
            <tr style="<?php echo $rowStyle; ?>">
                <td>
                    <b><?php echo htmlspecialchars($quelle); ?></b><?php echo $isReference ? " <i>(Referenz)</i>" : ""; ?>
                </td>
                <td><?php echo $s['n']; ?></td>
                <td><?php echo round($s['mae'], 1); ?></td>
                <td><?php echo round($s['rmse'], 1); ?></td>
                <td><?php echo round($s['bias'], 1); ?></td>
                <td><?php echo $s['mape'] !== null ? round($s['mape'], 1) : 'n/a'; ?></td>
                <td><?php echo htmlspecialchars($s['gewicht']); ?></td>
                <td><b><?php echo $s['vorschlag'] !== null ? number_format($s['vorschlag'], 3) : '-'; ?></b></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    <?php
}

// Die Berechnungsmethode ist global (nicht pro Zeitpunkt unterschiedlich) -
// per Mehrheitsentscheid über alle klassifizierten Zeitpunkte ermitteln
if ($methodCounts['mittelwert'] > $methodCounts['median']) {
    $erkannteMethode = 'gewichteter Mittelwert';
    $basisMetrik = 'rmse';
} elseif ($methodCounts['median'] > $methodCounts['mittelwert']) {
    $erkannteMethode = 'gewichteter Median';
    $basisMetrik = 'mae';
} else {
    $erkannteMethode = 'nicht eindeutig bestimmbar';
    $basisMetrik = 'rmse'; // Fallback
}

$ergebnis = berechneStatistik($byTime, null, $ACTUAL_SOURCE_LABEL, $COMBINED_SOURCE_LABELS, $MIN_ACTUAL_FOR_STATS, $MAX_RMSE_RATIO, $basisMetrik);
?>
<p style="margin-bottom:4px;">
    Erkannte Berechnungsmethode für "<?php echo htmlspecialchars($METHOD_REFERENCE_LABEL); ?>":
    <b style="font-size:1.1em;"><?php echo $erkannteMethode; ?></b>
</p>

<?php renderTabelle('Statistik – Prognosegenauigkeit', $ergebnis, $COMBINED_SOURCE_LABELS, $MIN_ACTUAL_FOR_STATS, $basisMetrik); ?>

<p style="font-size: 0.85em; color:#555; margin-top: 15px; max-width: 100%; overflow-wrap: break-word;">
    Nur Zeitpunkte mit Produktion &gt; <?php echo $MIN_ACTUAL_FOR_STATS; ?> W gehen ein.<br>
    Bei erkanntem <b>Mittelwert</b> basiert der Gewichtsvorschlag auf RMSE (unterstrichene Spalte), bei erkanntem <b>Median</b> auf MAE.<br>
    Niedrigere RMSE/MAE = treffsicherer &rarr; höheres Gewicht.<br>
    Negativer Bias = Dienst prognostiziert zu niedrig, positiver = zu hoch.<br>
    Gewicht wird 0, wenn die Basismetrik (RMSE bzw. MAE) mehr als <?php echo $MAX_RMSE_RATIO; ?>&times; so hoch ist wie die der besten Quelle.<br>
    &bdquo;Prognose&ldquo;/&bdquo;Basis&ldquo; sind Referenzwerte, kein Rohdienst.
</p>
