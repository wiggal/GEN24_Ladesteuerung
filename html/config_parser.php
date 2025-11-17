<?php

function load_ini_merged($base, $priv) {
    $default = parse_ini_file($base, true, INI_SCANNER_TYPED);
    $private = file_exists($priv) ? parse_ini_file($priv, true, INI_SCANNER_TYPED) : [];

    // Merge der beiden Ebenen
    return array_replace_recursive($default, $private);
}

function parse_config_variables($ini) {

    //
    // 1) Einzelne Variablen aus [General]
    //
    foreach ($ini['General'] as $key => $value) {
        $GLOBALS[$key] = $value;   // z.B. $PythonDIR
    }

    //
    // 2) TAB_config rekonstruieren
    //
    $TAB_config = [];

    if (isset($ini['TAB_config'])) {
        foreach ($ini['TAB_config'] as $flatKey => $value) {

            // Beispiel: "0.name" → index=0, field=name
            list($index, $field) = explode('.', $flatKey, 2);

            if (!isset($TAB_config[(int)$index])) {
                $TAB_config[(int)$index] = [];
            }

            $TAB_config[(int)$index][$field] = $value;
        }
    }

    // globale Variable erzeugen
    $GLOBALS['TAB_config'] = $TAB_config;
}

// -----------------------------------------
// Automatisch laden und Variablen bereitstellen
// -----------------------------------------

$ini = load_ini_merged('config.ini', 'config_priv.ini');
parse_config_variables($ini);

