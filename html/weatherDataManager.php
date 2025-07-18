<?php
# Daten aus DB lesen
$db = new SQLite3('../weatherData.sqlite');
$result = $db->query("SELECT * FROM weatherData ORDER BY Zeitpunkt ASC");

$data = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    // SQLITE3_ASSOC stellt sicher, dass die Zeilen als assoziative Arrays geholt werden
    $data[] = $row;
}

// Wenn keine Daten vorhanden sind
if (empty($data)) {
    echo "Keine Daten gefunden.";
    exit;
}

// --- DATEN UMWANDELN ---
$structuredData = [];
$alleQuellen = [];

$tage2 = [];
foreach ($data as $row) {
    # Prognosen 0 aussieben
    if ($row['Prognose_W'] > 0) {
        $zeit = $row['Zeitpunkt'];
        $tage2[] = date('Y-m-d', strtotime($zeit));
        $quelle = $row['Quelle'];
        $wert = $row['Prognose_W'];
        $gewicht = $row['Gewicht'];

        if (!isset($structuredData[$zeit])) {
            $structuredData[$zeit] = ['Zeitpunkt' => $zeit];
        }
        $structuredData[$zeit][$quelle] = $wert;
            $structuredData_Diagram[$zeit][$quelle]['wert'] = $wert;
            $structuredData_Diagram[$zeit][$quelle]['gewicht'] = $gewicht;
        $alleQuellen[$quelle] = true; // zur späteren Spaltenreihenfolge
    }
}
$tageOhneDuplikate = array_unique($tage2);
# Index neu durchummerieren
$tage = array_values($tageOhneDuplikate);

// Sortieren
ksort($structuredData);

// Quellen sortieren: Produktion zuerst, Ergebnis an zweiter Stelle
$quellenListe = array_keys($alleQuellen);
// Manuell sortieren
$priorisiert = ['Produktion', 'Prognose', 'Basis'];
// Nur priorisiert ausgeben, wenn auch vorhanden
$existierendePriorisierte = array_intersect($priorisiert, $quellenListe);
$rest = array_diff($quellenListe, $priorisiert);
$quellenListe = array_merge($existierendePriorisierte, $rest);

# Download als CSV Funktion
if (isset($_GET['download']) && $_GET['download'] === 'csv') {
    // --- CSV EXPORT ---
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="weatherData.csv"');
    header('Pragma: no-cache');
    header('Expires: 0');

    $output = fopen('php://output', 'w');

    // Kopfzeile schreiben
    fputcsv($output, array_merge(['Zeitpunkt'], $quellenListe));

    foreach ($structuredData as $row) {
        $zeile = [$row['Zeitpunkt']];
        foreach ($quellenListe as $q) {
            $zeile[] = $row[$q] ?? '';
        }
        fputcsv($output, $zeile);
    }

    fclose($output);
    exit;
}
?>

<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Prognose Tabelle</title>
    <script src="chart.js"></script>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: calc(100vh - 90px); 
            font-family: Arial, sans-serif;
            background: #f7f7f7;
        }

        h1, p {
            margin: 20px;
        }

        .table-container {
            height: calc(100vh - 120px); /* Fensterhöhe minus Header etc. */
            overflow-y: auto;
            border: 1px solid #ccc;
            margin: 0 20px 20px 20px;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }

        table {
            border-collapse: collapse;
            width: 100%;
            min-width: 800px;
        }

        th, td {
            padding: 10px;
            border: 1px solid #ccc;
            text-align: center;
        }

        thead th {
            position: sticky;
            top: 0;
            background-color: gray;
            color: white;
            z-index: 2;
        }

        tbody tr:nth-child(even) td {
            background-color: #f2f2f2;
        }
    .hilfe{
        font-family:Arial;
        font-size:150%;
        color: #000000;
        position: fixed;
        right: 8px;
        }
    .past {
        opacity: 0.4;
    }
    </style>
</head>
<body>
<div class="hilfe" align="right"> <a href="1_tab_LadeSteuerung.php"><b>Zurück</b></a></div>
    <h1>Solarprognosen aus weatherData</h1>
    <?php
    // Aktuellen Tag bestimmen (POST hat Vorrang)
    $selectedDay = $_POST['selected_day'] ?? date('Y-m-d');
    // Index des aktuellen Tags im $tage-Array finden
    $currentIndex = array_search($selectedDay, $tage);
    $prevDay = $tage[$currentIndex - 1] ?? null;
    $nextDay = $tage[$currentIndex + 1] ?? null;
    
    echo '<div style="white-space: nowrap; margin-left: 20px;">Tag auswählen:&nbsp;&nbsp;';
    // Zurück-Button
    if ($prevDay) {
        echo '<form method="POST" style="display:inline;">';
        echo '<input type="hidden" name="selected_day" value="' . htmlspecialchars($prevDay) . '">';
        echo '<button type="submit">&laquo; Zurück</button>';
        echo '</form>';
    }
    echo '&nbsp;&nbsp;<nobr>';
    // Dropdown
    echo '<form method="POST" style="display:inline;"">';
    echo '<select name="selected_day" id="selected_day" onchange="this.form.submit()">';
    $jetzt = new DateTime();
    $heute = $jetzt->format('Y-m-d');
    foreach ($tage as $tag) {
        $selected = ($tag === $selectedDay) ? 'selected' : '';
        $tag_show = $tag;
        if ($tag == $heute) $tag_show = 'heute';
        echo "<option value=\"$tag\" $selected>$tag_show</option>";
    }
    echo '</select>';
    echo '</form>';

    // Vor-Button
    if ($nextDay) {
        echo '<form method="POST" style="display:inline; margin-left: 10px;">';
        echo '<input type="hidden" name="selected_day" value="' . htmlspecialchars($nextDay) . '">';
        echo '<button type="submit">Vor &raquo;</button>';
        echo '</form>';
    }
    echo '</div>';
    ?>

<canvas id="dayChart" style='height:75vh; width:100vw'></canvas>

    <button onclick="toggleTable()">Tabelle ein-/ausklappen</button>
    <div id="tableWrapper" class="table-container" style="display: none;">
    <p>(Werte mit Gewicht <b>0</b> werden <span style="color: red;"><b>rot</b></span>, mit Gewicht größer <b>1</b> <span style="color: blue;"><b>blau</b></span>, dargestellt!)</p>
        <table id="Prognosetable">
            <thead>
            <tr>
                <th>Zeitpunkt</th>
                <?php
                // Quellenliste abrufen
                $quellen = [];
                foreach ($quellenListe as $row) {
                    $quellen[] = $row;
                    $Style_bg = '';
                    if ($row == 'Produktion') {
                        $Style_bg = 'style="background-color: #4CAF50;"';
                    } elseif (in_array($row, ['Prognose', 'Basis'])) {
                      $Style_bg = 'style="background-color: red;"';
                    }
                    echo "<th {$Style_bg}>{$row}</th>";
                }
                ?>
            </tr>
            </thead>

            <tbody>
            <?php

            $data = $structuredData_Diagram;

            $Prognose_Summe = 0;
            $Produktion_Summe = 0;
            foreach ($data as $zeitpunkt => $werteProQuelle) {
              $datum = substr($zeitpunkt, 0, 10);
              $aktuellesDatum = substr($zeitpunkt, 0, 10); // "YYYY-MM-DD"
              if ( $aktuellesDatum == $selectedDay ) {
                echo "<tr id='row-$zeitpunkt'><td>$zeitpunkt</td>";
                //  Prognosewerte je Quelle
                foreach ($quellen as $quelle) {
                    if (isset($werteProQuelle[$quelle])) {
                        $wert = (int)$werteProQuelle[$quelle]['wert'];
                        $gewicht = (int) $werteProQuelle[$quelle]['gewicht'];
                        $style = '';
                        if ($gewicht == 0) {
                            $style = "style='color: red;'";
                        } elseif ($gewicht > 1) {
                            $style = "style='color: blue;'";
                        }
                        if ($quelle == 'Produktion') {
                            $Produktion_Summe += $wert;
                            $style = "style='color: #4CAF50; font-weight: bold;'";
                        }
                        if ($quelle == 'Prognose') {
                            $Prognose_Summe += $wert;
                        }
                        echo "<td $style>$wert</td>";
                    } else {
                        echo "<td></td>";
                    }
                }
                echo "</tr>\n";
              }
            }
            ?>
            </tbody>
        </table>

<form method="post" action="?download=csv" style="margin-top: 30px; margin-left: 20px;">
<button type="submit" style="background-color: #4CAF50; color: white;">Daten als CSV herunterladen</button>
</form>

<!-- Formular zur Quellenlöschung -->
<form method="post" style="margin-top: 20px;">
    <fieldset>
        <legend><strong>Quellen zum Löschen auswählen:</strong></legend>
        <span style="color: red;"><b>ACHTUNG!!</b></span><span> Es werden alle Daten der ausgewählten Spalte gelöscht, für <b>Prognosen</b> ist die Historie nicht wiederherstellbar!!!</span>
        <br>
        <?php
        foreach ($quellen as $quelle) {
            $quelle_bg = '';
            if (!in_array($quelle, ['Produktion', 'Prognose', 'Basis'])) {
              $quelle_bg = 'style="color: red;"';
            }
            if ( $quelle != 'DUMMY') {
                echo "<label><input type='checkbox' name='delete_quellen[]' value='$quelle'>\n";
                echo "<span $quelle_bg><b> $quelle</b></span></label><br>";
            }
        }
        ?>
        <label><input type="checkbox" id="selectAll" onclick="toggleAll(this)"> Alle Quellen auswählen</label><br>
        <br>
        <label for="tage">Alle Daten der gewählten Quellen bis auf die letzten</label><br>
        <input type="number" name="tage" id="tage" value="8" min="0" max="35" required style="width: 30px; text-align: center;">
        <label for="tage"> Tage <b>löschen!!</b></label>
        <br>
        <button type="submit" style="background-color: red; color: white;" name="submit_delete" 
        onclick="return confirm('&#128721; Prognosequellen können nicht hergestellt werden! &#128721; \n \
\nQuellen können auch nur durch setzen von &quot;Gewicht=0&quot; in der &quot;weather_priv.ini&quot; aus der Berechnung der Prognose ausgeschlossen werden. \
Das neue Gewicht wird bei der nächsten Anforderung der Prognosequelle gesetzt!\n \
\n&#128721; Ausgewählte Quellen wirklich löschen? &#128721;');">Auswahl aus DB löschen</button>
    </fieldset>
</form>

<?php
// Quellen löschen, wenn Formular abgeschickt wurde
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['submit_delete']) && !empty($_POST['delete_quellen']) && isset($_POST['tage'])) {
    $toDelete = $_POST['delete_quellen'];
    $tage = intval($_POST['tage']);
    $grenzeDatum = date('Y-m-d 00:00:00', strtotime("-$tage days"));

    foreach ($toDelete as $quelle) {
        $stmt = $db->prepare("DELETE FROM weatherData WHERE Quelle = ? AND Zeitpunkt < ?");
        if ($stmt) {
            $stmt->bindValue(1, $quelle, SQLITE3_TEXT);
            $stmt->bindValue(2, $grenzeDatum, SQLITE3_TEXT);
            $stmt->execute();
        }
    }

    echo "<script>window.location.href=window.location.href;</script>";
}
?>
    </div>
    <script>
    function toggleAll(source) {
        checkboxes = document.getElementsByName('delete_quellen[]');
        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = source.checked;
        }
    }
    </script>

<?php
# Daten für Chartjs bilden
$chartData = []; // [datum][quelle] = array of [time, wert]

// Dann die Daten aufbereiten
foreach ($data as $zeitpunkt => $werteProQuelle) {
    $datum = substr($zeitpunkt, 0, 10);
    $uhrzeit = substr($zeitpunkt, 11, 5);

    foreach ($quellenListe as $quelle) {
        $wert = isset($werteProQuelle[$quelle]) ? $werteProQuelle[$quelle]['wert'] : NULL;
        $gewicht = isset($werteProQuelle[$quelle]['gewicht']) ? $werteProQuelle[$quelle]['gewicht']: '';

        $chartData[$datum][$quelle][] = [
            'time' => $uhrzeit,
            'wert' => $wert,
            'gewicht' => $gewicht
        ];
    }
}
?>

<script>
const chartData = <?php echo json_encode($chartData); ?>;
const selectedDay = <?= json_encode($selectedDay) ?>;
const daySelector = document.getElementById('daySelector');
const ctx = document.getElementById('dayChart').getContext('2d');

let lineChart = null;

// Definieren der Farbzuweisungen für jede Quelle
const sourceColors = {
    'Prognose': '#FF3300', //  Rot für Prognosewert
    'Basis': '#FF3300', //  Rot für Prognosewert
    'Produktion': '#4CAF50',    //  Grün für Produktion-Wert
    'solcast.com': '#3F51B5', // Blau
    'solarprognose': '#7B3F00', // Braun
    'akkudoktor': '#9C27B0', // Lila
    'forecast.solar': '#87CEFA', // Hellblau
    'openmeteo': '#696969', // dunkelgrau
};


function renderChart(date) {
    const dateData = chartData[date];
    const allTimes = new Set();
    const datasets = [];

    for (const quelle in dateData) {
        const data = dateData[quelle];
        const times = data.map(e => e.time);
        const werte = data.map(e => e.wert);
        const gewicht_array = data.map(e => e.gewicht);
        const gewicht = gewicht_array.find(e => typeof e === "number")
        times.forEach(t => allTimes.add(t));

        let fillOption = false;
        let backgroundColor = 'transparent';
        let hidden = false;
        if (quelle === 'Produktion') {
            backgroundColor = 'rgba(200, 200, 200, 0.3)';
            fillOption = true;
        } else if (quelle === 'Basis') {
            backgroundColor = 'rgba(255, 51, 0, 0.1)';
            fillOption = '1';
        }
        //Strichliert und blass bei Gewicht 0
        let borderDash = [7, 7];
        if (quelle === 'Produktion' || quelle === 'Prognose' ) {
            borderDash = [0, 0];
        } else if ((gewicht === 0) && (quelle !== 'Basis')) {
            //sourceColors[quelle] = '#CCCCCC';
            //borderDash = [5, 8];
            hidden = true;
        }


        datasets.push({
            label: quelle,
            data: werte,
            // Feste Farbzuweisung basierend auf dem Quellnamen
            borderColor: sourceColors[quelle] || '#CCCCCC', // Falls Quelle nicht definiert, Fallback-Farbe
            borderWidth: 3,
            // Anpassung der Strichart basierend auf Quelle
            borderDash: borderDash,
            pointRadius: 0,
            fill: fillOption,
            backgroundColor: backgroundColor,
            hidden: hidden,
            tension: 0.1
        });


    }

    const labels = Array.from(allTimes).sort();

    if (lineChart) lineChart.destroy();

    lineChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: datasets
    },
    options: {
        responsive: true,
        plugins: {
            legend: { position: 'top' },
            title: {
                display: false,
                text: `Prognosen am ${date}`
            },
            tooltip: {
                titleFont: { size: 20 },
                bodyFont: { size: 20 },
                footerFont: { size: 20 },
                enabled: true,
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: function(context) {
                        const label = context.dataset.label || '';
                        const value = context.parsed.y !== null ? context.parsed.y : '';
                        return `${label}: ${value} W`;
                    }
                }
            }
        },
        interaction: {
            mode: 'nearest',
            intersect: false
        },
        scales: {
            x: {
                title: { display: true, text: 'Prognose: <?php echo round($Prognose_Summe/1000,1); ?>kWh => Produktion: <?php echo round($Produktion_Summe/1000,1); ?>kWh' ,
                    font: {
                        size: 18 // Hier Schriftgröße Footer ändern
                    }
                },
                ticks: {
                    font: {
                        size: 18 // Schriftgröße für Achsenwerte (Tick-Beschriftung)
                    }
                }
            },
            y: {
                title: { display: false, text: 'Prognosewert (W)' 
                },
                ticks: {
                    font: {
                        size: 18 // Schriftgröße für Achsenwerte (Tick-Beschriftung)
                    }
                }
            },
        }
    }
});
}

// Initialisieren mit heute oder erstem Tag
window.addEventListener('load', function () {
    const todayRow = document.querySelector('tr.today');
    const container = document.querySelector('.table-container');
    // Chart anzeigen, sobald Seite geladen ist
    renderChart(selectedDay);
});
</script>
<script>
// Tabelle ein und ausklappen
function toggleTable() {
    const tableWrapper = document.getElementById("tableWrapper");
    const table = document.getElementById("Prognosetable");

    if (tableWrapper.style.display === "none") {
        tableWrapper.style.display = "block";
        setTimeout(() => {
            table.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100); // kleiner Delay, damit das DOM-Layout aktualisiert ist
    } else {
        tableWrapper.style.display = "none";
    }
}
</script>
</body>
</html>

