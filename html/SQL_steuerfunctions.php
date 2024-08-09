<?php

function getSteuercodes($schluessel)
{
$SQLfile = '../CONFIG/Prog_Steuerung.sqlite';
/*
if (!file_exists($SQLfile)) {
    echo "\nSQLitedatei $SQLfile existiert nicht, leere Datenbank anlegen!";
    echo "</body></html>";
    $db = new SQLite3($SQLfile);
    $db->exec('CREATE TABLE IF NOT EXISTS steuercodes (
        ID TEXT,
        Schluessel TEXT,
        Zeit TEXT,
        Res_Feld1 INT,
        Res_Feld2 INT,
        Options text)');
    $db->exec('CREATE UNIQUE INDEX idx_positions_title ON steuercodes (ID, Schluessel)');
}
*/
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

?>
