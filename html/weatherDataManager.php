<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Prognose Tabelle</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            font-family: Arial, sans-serif;
            background: #f7f7f7;
        }

        h1, p {
            margin: 20px;
        }

        .table-container {
            height: calc(100vh - 80px); /* Fensterhöhe minus Header etc. */
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
    </style>
</head>
<body>
<div class="hilfe" align="right"> <a href="1_tab_LadeSteuerung.php"><b>Zurück</b></a></div>
    <h1>Solarprognosen aus weatherData</h1>
    <p>(Der Median wird über alle vorhandenen Werte berechnet, Werte mit Gewicht 0 werden rot dargestellt!)</p>
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

            foreach ($data as $zeitpunkt => $werteProQuelle) {
                echo "<tr><td>$zeitpunkt</td>";
            
                // Median berechnen
                $werte = [];
                foreach ($werteProQuelle as $eintrag) {
                    $werte[] = $eintrag['wert'];
                }
                sort($werte);
                $count = count($werte);
                if ($count > 0) {
                    $middle = floor($count / 2);
                    $median = $count % 2 === 0
                        ? ($werte[$middle - 1] + $werte[$middle]) / 2
                        : $werte[$middle];
                } else {
                    $median = '';
                }
                echo "<td><strong>" . (int)$median . "</strong></td>";

                // Prognosewerte je Quelle
                foreach ($quellen as $quelle) {
                    if (isset($werteProQuelle[$quelle])) {
                        $wert = (int)$werteProQuelle[$quelle]['wert'];
                        $gewicht = $werteProQuelle[$quelle]['gewicht'];
                        $stil = ($gewicht == 0) ? "style='color: red;'" : "";
                        echo "<td $stil>$wert</td>";
                    } else {
                        echo "<td></td>";
                    }
                }
                echo "</tr>";
            }

            ?>
            </tbody>
        </table>
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
        <button type="submit" name="submit_delete" onclick="return confirm('Ausgewählte Quellen wirklich löschen?');">Löschen</button>
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
</body>
</html>

