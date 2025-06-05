<?php
# Download als CSV Funktion
if (isset($_GET['download']) && $_GET['download'] === 'csv') {
    $db = new PDO('sqlite:../weatherData.sqlite');
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC); // wichtig!

    $stmt = $db->query("SELECT * FROM weatherData ORDER BY Zeitpunkt ASC");

    // Richtige Header setzen
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="weatherData.csv"');
    header('Pragma: no-cache');
    header('Expires: 0');

    $output = fopen('php://output', 'w');

    // Kopfzeile schreiben
    $firstRow = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($firstRow) {
        fputcsv($output, array_keys($firstRow));
        fputcsv($output, array_values($firstRow));

        // Restliche Zeilen
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            fputcsv($output, $row);
        }
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
            background-color: #4CAF50;
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
    <p>(Der Median wird über alle vorhandenen Werte berechnet, Werte mit Gewicht 0 werden <span style="color: red;"><b>rot</b></span>, größer 1 <span style="color: blue;"><b>blau</b></span>, dargestellt!)</p>
    <?php
    $db = new PDO('sqlite:../weatherData.sqlite');
    // Verfügbare Tage aus DB lesen
    $tagesStmt = $db->query("SELECT DISTINCT substr(Zeitpunkt, 1, 10) AS Tag FROM weatherData ORDER BY Tag DESC");
    $tage = $tagesStmt->fetchAll(PDO::FETCH_COLUMN);

    // Aktuellen Tag bestimmen (POST hat Vorrang)
    $selectedDay = $_POST['selected_day'] ?? date('Y-m-d');
    // Index des aktuellen Tags im $tage-Array finden
    $currentIndex = array_search($selectedDay, $tage);
    $prevDay = $tage[$currentIndex + 1] ?? null;
    $nextDay = $tage[$currentIndex - 1] ?? null;
    
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
    foreach ($tage as $tag) {
        $selected = ($tag === $selectedDay) ? 'selected' : '';
        echo "<option value=\"$tag\" $selected>$tag</option>";
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
        <table id="Prognosetable">
            <thead>
            <tr>
                <th>Zeitpunkt</th>
                <th style="background-color: #ffa500;">Median (alle)</th> <!-- Orange für Median -->
                <?php
                // Quellenliste abrufen
                $quellenQuery = "SELECT DISTINCT Quelle FROM weatherData ORDER BY Quelle";
                $quellenResult = $db->query($quellenQuery);
                $quellen = [];
                foreach ($quellenResult as $row) {
                    $quellen[] = $row['Quelle'];
                    echo "<th>{$row['Quelle']}</th>";
                }
                ?>
            </tr>
            </thead>

            <tbody>
            <?php
            # Tag auslesen
            $stmt = $db->prepare("SELECT Zeitpunkt, Quelle, Prognose_W, Gewicht
                      FROM weatherData
                      WHERE DATE(Zeitpunkt) = :tag
                      ORDER BY Zeitpunkt ASC");
            $stmt->execute([':tag' => $selectedDay]);

            $data = [];
            foreach ($stmt as $row) {
                $zeit = new DateTime($row['Zeitpunkt']);
                $zeit->setTime((int)$zeit->format('H'), 0);
                $zeitpunkt = $zeit->format('Y-m-d H:00:00');
                $quelle = $row['Quelle'];
                $prognose = $row['Prognose_W'];
                $gewicht = $row['Gewicht'];

                // Speichere Wert und Gewicht
                $data[$zeitpunkt][$quelle] = ['wert' => $prognose, 'gewicht' => $gewicht];
            }

            ksort($data);

            $jetzt = new DateTime();
            $heute = $jetzt->format('Y-m-d');

            foreach ($data as $zeitpunkt => $werteProQuelle) {
                $datum = substr($zeitpunkt, 0, 10);
                $aktuellesDatum = substr($zeitpunkt, 0, 10); // "YYYY-MM-DD"

                echo "<tr id='row-$zeitpunkt'><td>$zeitpunkt</td>";
            
                // Median berechnen
                $werte = [];
                foreach ($werteProQuelle as $eintrag) {
                    $wert = $eintrag['wert'];
                    $gewicht = isset($eintrag['gewicht']) ? (int)$eintrag['gewicht'] : 0;
                    for ($i = 0; $i < $gewicht; $i++) {
                        $werte[] = $wert;
                    }
                }
                sort($werte);
                $count = count($werte);
                if ($count > 0) {
                    $middle = floor($count / 2);
                    $median = $count % 2 === 0
                        ? ($werte[$middle - 1] + $werte[$middle]) / 2
                        : $werte[$middle];
                     // NEU: Median als eigene „Quelle“ im Array speichern
                } else {
                    $median = '';
                }
                echo '<td><strong><span style="color: #4CAF50;">' . (int)$median . '</span></strong></td>';

                // Prognosewerte je Quelle
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
                        echo "<td $style>$wert</td>";
                    } else {
                        echo "<td></td>";
                    }
                }
                echo "</tr>\n";
                $data_median[$zeitpunkt]['Median'] = ['wert' => (int)$median, 'gewicht' => 1];
            }
            foreach ($data_median as $zeitpunkt => $werte) {
                foreach ($werte as $quelle => $eintrag) {
                    $data[$zeitpunkt][$quelle] = $eintrag;
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
        <?php
        foreach ($quellen as $quelle) {
            echo "<label><input type='checkbox' name='delete_quellen[]' value='$quelle'> $quelle</label><br>";
        }
        ?>
        <br>
        <button type="submit" style="background-color: red; color: white;" name="submit_delete" onclick="return confirm('Ausgewählte Quellen wirklich löschen?');">Auswahl aus DB löschen</button>
    </fieldset>
</form>

<?php
// Quellen löschen, wenn Formular abgeschickt wurde
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['submit_delete']) && !empty($_POST['delete_quellen'])) {
    $toDelete = $_POST['delete_quellen'];
    $placeholders = implode(',', array_fill(0, count($toDelete), '?'));
    $stmt = $db->prepare("DELETE FROM weatherData WHERE Quelle IN ($placeholders)");
    $stmt->execute($toDelete);

    // Nach dem Löschen neu laden, um Änderungen anzuzeigen
    echo "<script>window.location.href=window.location.href;</script>";
}
?>

    </div>
    <?php
# tatsächliche Produktion
$db = new PDO('sqlite:../PV_Daten.sqlite');
$db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC); // wichtig!

$pvData = [];
$letztesDatum_tmp = new DateTime($selectedDay);
$letztesDatum_tmp->modify('+1 day +5 minutes');
$letztesDatum = $letztesDatum_tmp->format('Y-m-d H:i:s');
$stmt = $db->query("
    WITH Alle_PVDaten AS (
        SELECT MIN(Zeitpunkt) AS Zeitpunkt, DC_Produktion
        FROM pv_daten
        WHERE Zeitpunkt BETWEEN '".$selectedDay."' AND '".$letztesDatum."'
        GROUP BY STRFTIME('%Y-%m-%d %H', Zeitpunkt)
        UNION
        SELECT MAX(Zeitpunkt) AS Zeitpunkt, DC_Produktion
        FROM pv_daten
        WHERE Zeitpunkt BETWEEN '".$selectedDay."' AND '".$letztesDatum."'
        ORDER BY Zeitpunkt
    ),
    Alle_PVDaten2 AS (
        SELECT Zeitpunkt, LEAD(DC_Produktion) OVER (ORDER BY Zeitpunkt) - DC_Produktion AS Produktion
        FROM Alle_PVDaten
    )
    SELECT Zeitpunkt, Produktion FROM Alle_PVDaten2 ORDER BY Zeitpunkt
");

foreach ($stmt as $row) {
    $zeit = (new DateTime($row['Zeitpunkt']))->format('Y-m-d H:00:00');
    $pvData[$zeit] = (float)$row['Produktion'];
}
foreach ($pvData as $zeitpunkt => $produktion) {
    $data[$zeitpunkt]['Ist'] = ['wert' => $produktion, 'gewicht' => 1];
}

# Daten für Chartjs bilden
$chartData = []; // [datum][quelle] = array of [time, wert]

foreach ($data as $zeitpunkt => $werteProQuelle) {
    $datum = substr($zeitpunkt, 0, 10);
    $uhrzeit = substr($zeitpunkt, 11, 5);
    foreach ($werteProQuelle as $quelle => $eintrag) {
        if ($eintrag['wert'] > 10)
            $chartData[$datum][$quelle][] = [
                'time' => $uhrzeit,
                'wert' => $eintrag['wert']
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

function getColor(index) {
    const colors = ['#4CAF50', '#FF5722', '#3F51B5', '#FFC107', '#9C27B0', '#009688', '#E91E63'];
    return colors[index % colors.length];
}

function renderChart(date) {
    const dateData = chartData[date];
    const allTimes = new Set();
    const datasets = [];

    let sourceIndex = 0;
    for (const quelle in dateData) {
        const data = dateData[quelle];
        const times = data.map(e => e.time);
        const werte = data.map(e => e.wert);
        times.forEach(t => allTimes.add(t));

        datasets.push({
            label: quelle,
            data: werte,
            borderColor: quelle === 'Median' ? '#FF9800' : 
                         quelle === 'Ist' ? '#FF9500' : getColor(sourceIndex),
            borderWidth: 3,
            borderDash: quelle === 'Median' || quelle === 'Ist' ? [0, 0] : [5, 5],
            pointRadius: 0,
            fill: quelle === 'Ist' ? true : false,
            tension: 0.1
        });

        sourceIndex++;
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
                display: true,
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
                title: { display: true, text: 'Uhrzeit' }
            },
            y: {
                title: { display: true, text: 'Prognosewert (W)' }
            }
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

