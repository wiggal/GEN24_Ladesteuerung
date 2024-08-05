<?php

function getSteuercodes($schluessel)
{
$SQLite_file = '../CONFIG/Prog_Steuerung.sqlite';
if (!file_exists($SQLite_file)) {
    echo "\nSQLitedatei $filename existiert nicht, keine Grafik verfügbar!";
    echo "</body></html>";
    exit();
}
$db = new SQLite3($SQLite_file);
$SQL = "SELECT
        Zeit, Res_Feld1, Res_Feld2 
        from steuercodes where Schluessel == '".$schluessel."'";
        $results = $db->query($SQL);
        $data = array();
        // Fetch Associated Array (1 for SQLITE3_ASSOC)
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
        
$db->close();

return $data;
}

?>
