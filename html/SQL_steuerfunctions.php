<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}

function getSteuercodes($schluessel)
{
global $PythonDIR;
$SQLfile = $PythonDIR.'/CONFIG/Prog_Steuerung.sqlite';
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

function getPrognose() {
    global $PythonDIR;
    $watts = [];

    try {
        $db = new SQLite3($PythonDIR.'/weatherData.sqlite');

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

function getPrstLadeStd() {
global $PythonDIR;
$SQLfile = $PythonDIR.'/CONFIG/Prog_Steuerung.sqlite';
$db = new SQLite3($SQLfile);
$SQL = "
        SELECT strftime('%H:00:00', Zeit) AS Stunde,
            MIN(Res_Feld2) AS Res_Feld2
        FROM steuercodes
        WHERE Res_Feld2 != 0
            AND Schluessel = 'Reservierung'
            AND ID LIKE '1%'
        GROUP BY strftime('%Y-%m-%d %H', Zeit)
        ORDER BY Stunde;
        ";


        $results = $db->query($SQL);
        $data = array();

        // Fetch Associated Array
        if($results != false){
            while ($row = $results->fetchArray(SQLITE3_ASSOC))
            {
                $stunde = $row['Stunde'];
                $data[$stunde] = array(
                    'Res_Feld2' => $row['Res_Feld2']
                );
            }
        }
        
$db->close();

return $data;
}
?>
