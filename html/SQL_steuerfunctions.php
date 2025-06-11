<?php

function getSteuercodes($schluessel)
{
$SQLfile = '../CONFIG/Prog_Steuerung.sqlite';
$db = new SQLite3($SQLfile);
$SQL = "SELECT
        Zeit, Res_Feld1, Res_Feld2, Options
        from steuercodes where Schluessel == '".$schluessel."'";
        $results = $db->query($SQL);
        $data = array();
        // Fetch Associated Array (1 for SQLITE3_ASSOC)
        if($results != false){
            while ($row = $results->fetchArray(1))
            {
            //insert row into array
            $data[$row['Zeit']] = array();
                foreach ($row as $key => $value) {
                    if($key != 'Zeit') {
                        $data[$row['Zeit']][$key] = $value;
                    }
                }
            }
        }
        
$db->close();

return $data;
}

function median($daten) {
    $werte = [];

    foreach ($daten as $eintrag) {
        $wert = $eintrag[0];
        $anzahl = $eintrag[1];

        for ($i = 0; $i < $anzahl; $i++) {
            $werte[] = $wert;
        }
    }

    sort($werte);
    $anzahl = count($werte);
    $mitte = (int) floor($anzahl / 2);

    if ($anzahl % 2 === 0) {
        // Gerade Anzahl: Mittelwert der beiden mittleren Zahlen
        $median = ($werte[$mitte - 1] + $werte[$mitte]) / 2;
    } else {
        // Ungerade Anzahl: Der mittlere Wert
        $median = $werte[$mitte];
    }

    return $median;
}


function getPrognose() {
    $watts = [];

    try {
        $db = new SQLite3('../weatherData.sqlite');

        $sql = "
            SELECT Zeitpunkt, Prognose_W
            FROM weatherData
            WHERE
                Prognose_W > 30 AND
                Quelle IS 'Prognose' AND
                DATE(Zeitpunkt) BETWEEN DATE('now') AND DATE('now', '+2 day')
            ORDER BY Zeitpunkt ASC
        ";

        $results = $db->query($sql);

        if (!$results) {
            // Abfragefehler (z. B. Tabelle existiert nicht)
            $db->close();
            echo("<center><b><h1>Datenbank weatherData.sqlite existiert nicht, oder ist nicht OK!</h1></b>");
            return ['result' => ['watts' => []]];
        }

        $stundenDaten = [];

        while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
            $zeit = new DateTime($row['Zeitpunkt']);
            $stunde = $zeit->format("Y-m-d H:00:00");

            $watts[$stunde] = (int)$row['Prognose_W'];
        }

        $db->close();
    } catch (Exception $e) {
        // Fehler bei Verbindungsaufbau oder Query
        return ['result' => ['watts' => []]];
    }

    return ['result' => ['watts' => $watts]];
}

?>
