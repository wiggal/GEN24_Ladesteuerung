<?php

$steuerung_value = isset($_POST['Steuerung']) ? $_POST['Steuerung'] : null;

//Steuerungsfile schreiben
if($steuerung_value !== null) {
    $steuerung_data['Steuerung'] =  $steuerung_value[0];
    file_put_contents('../Prog_Steuerung.json', json_encode($steuerung_data, JSON_PRETTY_PRINT));
}


?>
