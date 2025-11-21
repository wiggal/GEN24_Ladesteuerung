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
    $tabs = [];

    // 1) transformiere flat keys "5.name" / "5_1.name" / "5a.name" usw.
    foreach ($ini_section as $flatKey => $value) {
        // flatKey z.B. "5.name" oder "5_1.name"
        if (strpos($flatKey, '.') === false) continue;
        list($index, $field) = explode('.', $flatKey, 2);

        // Bewahre index als string (nicht casten!)
        if (!isset($tabs[$index])) $tabs[$index] = [];
        $tabs[$index][$field] = $value;
    }

    // 2) Erzeuge ein Array zum Sortieren: extrahiere numeric prefix und suffix
    $sortKeys = [];
    foreach ($tabs as $idx => $data) {
        // versuche numeric prefix zu finden
        if (preg_match('/^(\d+)(?:[_\-]?(\d+|[A-Za-z]+))?$/', $idx, $m)) {
            $main = (int)$m[1];
            $suffix = isset($m[2]) ? $m[2] : null;
            $isSuffixNumeric = $suffix !== null && preg_match('/^[0-9]+$/', $suffix);
        } else {
            // kein führendes nummerisches Präfix — setze große Hauptnummer, sortiere nach idx string
            $main = PHP_INT_MAX;
            $suffix = $idx;
            $isSuffixNumeric = false;
        }

        $sortKeys[$idx] = [
            'main' => $main,
            'suffix' => $suffix,
            'isSuffixNumeric' => $isSuffixNumeric
        ];
    }

    // 3) Sortiere die Indices: zuerst nach main (int), dann falls beide main gleich,
    //    numerische Suffixe zuerst (numerisch), sonst lexikographisch nach suffix string,
    //    zuletzt nach original idx as fallback.
    uasort($tabs, function($a, $b) use ($sortKeys) {
        // diese Closure bekommt Werte, wir brauchen deren keys => workaround:
        return 0; // dummy, wir sortieren weiter unten nach keys
    });

    // wir sortieren anhand der sortKeys array: get list of indices, usort with comparator
    $indices = array_keys($tabs);
    usort($indices, function($ia, $ib) use ($sortKeys) {
        $sa = $sortKeys[$ia];
        $sb = $sortKeys[$ib];

        if ($sa['main'] < $sb['main']) return -1;
        if ($sa['main'] > $sb['main']) return 1;

        // mains gleich -> handle suffix
        if ($sa['suffix'] === null && $sb['suffix'] === null) {
            // keine suffix -> sortiere nach original index string (numerische ohne suffix bleiben in Reihenfolge)
            return strcmp($ia, $ib);
        }

        if ($sa['suffix'] === null) return -1; // kein suffix kommt vor suffix
        if ($sb['suffix'] === null) return 1;

        // beide haben suffix
        if ($sa['isSuffixNumeric'] && $sb['isSuffixNumeric']) {
            // numerische comparison
            $na = (int)$sa['suffix'];
            $nb = (int)$sb['suffix'];
            if ($na < $nb) return -1;
            if ($na > $nb) return 1;
            return 0;
        }

        if ($sa['isSuffixNumeric'] && !$sb['isSuffixNumeric']) {
            return -1; // numerische suffix vor alphabetischen
        }
        if (!$sa['isSuffixNumeric'] && $sb['isSuffixNumeric']) {
            return 1;
        }

        // beide alphabetisch -> lexikographisch
        return strcmp($sa['suffix'], $sb['suffix']);
    });

    // 4) Baue das final sortierte numerische-index-Array (0..n) oder behalte string-keys
    //    Hier bauen wir numerisch neu auf (0..n) — das entspricht typischerweise der alten Struktur.
    $result = [];
    foreach ($indices as $k) {
        $result[] = $tabs[$k];
    }

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

