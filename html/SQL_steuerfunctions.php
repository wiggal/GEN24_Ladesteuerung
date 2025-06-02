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

function gewichteterMedian(array $werteMitGewicht): ?float {
    if (empty($werteMitGewicht)) return null;

    usort($werteMitGewicht, fn($a, $b) => $a[0] <=> $b[0]);

    $gesamtGewicht = array_sum(array_column($werteMitGewicht, 1));
    $halbGewicht = $gesamtGewicht / 2;

    $kumuliert = 0;
    foreach ($werteMitGewicht as [$wert, $gewicht]) {
        $kumuliert += $gewicht;
        if ($kumuliert >= $halbGewicht) {
            return $wert;
        }
    }

    return null;
}

function median(array $werte): ?float {
    if (empty($werte)) return null;

    sort($werte);
    $n = count($werte);
    $mid = (int) floor($n / 2);

    if ($n % 2 === 1) {
        return $werte[$mid];
    } else {
        return ($werte[$mid - 1] + $werte[$mid]) / 2;
    }
}


function getPrognose() {
    $watts = [];

    try {
        $db = new SQLite3('../weatherData.sqlite');

        $sql = "
            SELECT Zeitpunkt, Prognose_W, Gewicht
            FROM weatherData
            WHERE
                Prognose_W IS NOT NULL AND
                Gewicht > 0 AND
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


      /*
      // Nur für gewichteten Median
      //$stundenDaten[$stunde][] = [(float)$row['Prognose_W'], (float)$row['Gewicht']];
      // Gewichteten Median berechnen
      // Aktuell nur einfachen Median verwenden  #entWIGGlung
      $watts = [];
    
      foreach ($stundenDaten as $stunde => $werte) {
          $watts[$stunde] = gewichteterMedian($werte);
      }
      */

        while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
            $zeit = new DateTime($row['Zeitpunkt']);
            $stunde = $zeit->format("Y-m-d H:00:00");

            if (!isset($stundenDaten[$stunde])) {
                $stundenDaten[$stunde] = [];
            }

            $stundenDaten[$stunde][] = (float)$row['Prognose_W'];
        }

        foreach ($stundenDaten as $stunde => $werte) {
            $watts[$stunde] = median($werte);
        }

        $db->close();
    } catch (Exception $e) {
        // Fehler bei Verbindungsaufbau oder Query
        return ['result' => ['watts' => []]];
    }

    return ['result' => ['watts' => $watts]];
}

?>
