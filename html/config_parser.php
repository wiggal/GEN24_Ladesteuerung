<?php
/**
 * Lädt config.ini + config_priv.ini, merged und rekonstruiert $TAB_config
 * ohne Indexverlust (z.B. "5_5" bleibt "5a" und wird korrekt einsortiert).
 */

function load_ini_merged($base = 'config.ini', $priv = 'config_priv.ini') {
    if (!file_exists($base)) {
        throw new Exception("Basis-Konfig '$base' fehlt");
    }
    $default = parse_ini_file($base, true, INI_SCANNER_RAW);
    $private = file_exists($priv) ? parse_ini_file($priv, true, INI_SCANNER_RAW) : [];
    // array_replace_recursive reicht hier; wir wollen die Keys aus priv zusätzlich haben
    return array_replace_recursive($default, $private);
}

/**
 * Rekonstruiert $TAB_config aus dem Abschnitt [TAB_config]
 * und sortiert die Tabs nach (hauptindex, suffix).
 */
function build_tab_config(array $ini_section) {
    // 1) transformiere flat keys 
    $tabs = [];

    foreach ($ini_section as $flatKey => $value) {
        if (strpos($flatKey, '.') === false) continue;
    
        [$index, $field] = explode('.', $flatKey, 2);
    
        // Index bewusst als STRING behalten
        if (!isset($tabs[$index])) {
            $tabs[$index] = [];
        }

        $tabs[$index][$field] = $value;
    }
    // 2) Erzeuge sortierten Array  wie $TAB_config
    $result = [];

    foreach ($tabs as $tab) {
        $index = (int)$tab['sort'];
        $result[$index] = $tab;
    }

    ksort($result);
    // 2. Neu indizieren von 0 aufwärts
    $result = array_values($result);

    return $result;
}

// --------------------
// Anwendung
// --------------------
try {
    $ini = load_ini_merged('config.ini', 'config_priv.ini');

    // General als Variablen setzen
    if (isset($ini['General'])) {
        foreach ($ini['General'] as $k => $v) {
            $GLOBALS[$k] = $v;
        }
    }

    // TAB_config rekonstruieren und $TAB_config global setzen
    $TAB_config = [];
    if (isset($ini['TAB_config'])) {
        $TAB_config = build_tab_config($ini['TAB_config']);
    }
    $GLOBALS['TAB_config'] = $TAB_config;

} catch (Exception $e) {
    die("Config-Fehler: " . $e->getMessage());
}

