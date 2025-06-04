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
    <div class="table-container">
        <table>
            <thead>
            <tr>
                <th>Zeitpunkt</th>
                <th style="background-color: #ffa500;">Median (alle)</th> <!-- Orange für Median -->
                <?php
                // Quellenliste abrufen
                $db = new PDO('sqlite:../weatherData.sqlite');
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
            $stmt = $db->query("SELECT Zeitpunkt, Quelle, Prognose_W, Gewicht FROM weatherData");
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

            $erstesDatum = null;
            $letztesDatum = null;

            $jetzt = new DateTime();
            $heute = $jetzt->format('Y-m-d');

            foreach ($data as $zeitpunkt => $werteProQuelle) {
                $datum = substr($zeitpunkt, 0, 10);
                $isPast = ($datum < $heute);
                $class = $isPast ? "class='past'" : "";
                $aktuellesDatum = substr($zeitpunkt, 0, 10); // "YYYY-MM-DD"
                $scrollDone = false;
                $id = ($datum == $heute && !$scrollDone) ? "id='today'" : "";
                if ($datum == $heute && !$scrollDone) {
                    $class = "class='today'";
                    $scrollDone = true;
                }

                // Wenn sich das Datum geändert hat, füge eine Trennzeile ein
                if ($letztesDatum !== null && $aktuellesDatum !== $letztesDatum) {
                    echo "<tr><td colspan='" . (count($quellen) + 2) . "' style='border-top: 4px solid black;'></td></tr>\n";
                }

                // Erstes Datum ermitteln für Produktions-SELECT
                if ($erstesDatum == null || $aktuellesDatum < $erstesDatum) {
                    $erstesDatum = $aktuellesDatum;
                }

                echo "<tr id='row-$zeitpunkt' $class><td>$zeitpunkt</td>";
            
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
                $letztesDatum = $aktuellesDatum;
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
        <div style="margin: 20px;">
    <label for="daySelector"><strong>Tag auswählen:</strong></label>
    <select id="daySelector"></select>
</div>
<canvas id="dayChart" height="100"></canvas>

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
$stmt = $db->query("
    WITH Alle_PVDaten AS (
        SELECT MIN(Zeitpunkt) AS Zeitpunkt, DC_Produktion
        FROM pv_daten
        WHERE Zeitpunkt BETWEEN '".$erstesDatum."' AND '".$letztesDatum."'
        GROUP BY STRFTIME('%Y-%m-%d %H', Zeitpunkt)
        UNION
        SELECT MAX(Zeitpunkt) AS Zeitpunkt, DC_Produktion
        FROM pv_daten
        WHERE Zeitpunkt BETWEEN '".$erstesDatum."' AND '".$letztesDatum."'
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
</script>


<script>
window.addEventListener('load', function () {
    const todayRow = document.querySelector('tr.today');
    const container = document.querySelector('.table-container');

    if (todayRow && container) {
        const offsetTop = todayRow.offsetTop;
        container.scrollTo({
            top: offsetTop - 40, // Höhe deines sticky-Headers
            behavior: 'smooth'
        });
    }
});
</script>
<script>
const daySelector = document.getElementById('daySelector');
const ctx = document.getElementById('dayChart').getContext('2d');

// Dropdown füllen
Object.keys(chartData).forEach(date => {
    const option = document.createElement('option');
    option.value = date;
    option.textContent = date;
    daySelector.appendChild(option);
});

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
            borderWidth: quelle === 'Median' ? 6 : 2,
            borderDash: quelle === 'Median' ? [5, 5] : [0, 0],
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
                }
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
const today = new Date().toISOString().split('T')[0];
const firstAvailable = Object.keys(chartData)[0];
daySelector.value = chartData[today] ? today : firstAvailable;
renderChart(daySelector.value);

daySelector.addEventListener('change', () => {
    renderChart(daySelector.value);
});
</script>
</body>
</html>

