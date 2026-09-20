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
 * Lädt eine beliebige, per Parameter übergebene ini-Datei und merged
 * automatisch eine evtl. vorhandene "_priv"-Variante darüber
 * (z.B. "../CONFIG/charge.ini" -> "../CONFIG/charge_priv.ini").
 * Enthaltene Werte aus der priv-Datei überschreiben die Basis-Datei.
 */
function load_ini_auto($file) {
    $pathinfo = pathinfo($file);
    $ext = isset($pathinfo['extension']) ? '.' . $pathinfo['extension'] : '';
    $priv = $pathinfo['dirname'] . '/' . $pathinfo['filename'] . '_priv' . $ext;

    return load_ini_merged($file, $priv);
}

/**
 * Lädt eine ini-Datei (inkl. automatischem "_priv"-Merge via load_ini_auto())
 * und legt jede enthaltene Sektion als eigenes Array unter ihrem
 * Sektionsnamen in $GLOBALS ab, z.B. bei einer ini mit
 * [Ladeberechnung]
 * key = wert
 * landet das Ergebnis in $GLOBALS['Ladeberechnung']['key'].
 * Ini-Werte ohne Sektion (flach auf oberster Ebene) werden direkt unter
 * ihrem Key gesetzt.
 *
 * Enthält die Datei zusätzlich eine Sektion [monats_priv.ini], z.B.:
 *   [monats_priv.ini]
 *   uebergang_priv.ini = 09, 02
 *   winter_priv.ini = 10, 11, 12, 01
 * wird geprüft, ob der aktuelle Monat (zweistellig, z.B. "09") in der
 * Monatsliste einer der dort genannten Dateien enthalten ist. Trifft das
 * zu, wird diese Datei (im selben Verzeichnis wie $file erwartet)
 * zusätzlich geladen und ihre Sektionen überschreiben - Key für Key,
 * nicht die ganze Sektion - die bereits aus $file gesetzten Werte.
 *
 * Als eigenständiger Funktionsaufruf gedacht - NICHT über ein erneutes
 * require/require_once "config_parser.php";, sondern direkt:
 *
 *   require_once __DIR__ . '/config_parser.php'; // wie gehabt, lädt config.ini
 *   merge_config_into_globals(__DIR__ . '/../CONFIG/charge.ini');
 *   // Zugriff dann z.B. über $GLOBALS['Ladeberechnung']['key']
 */
function merge_config_into_globals($file) {
    $extra_ini = load_ini_auto($file);
    foreach ($extra_ini as $section => $values) {
        $GLOBALS[$section] = $values;
    }

    // Monatsabhängige Zusatz-Configs nur anwenden, wenn die geparste Datei
    // charge.ini ist (nicht bei anderen über diese Funktion geladenen Dateien)
    if (basename($file) === 'charge.ini' && isset($GLOBALS['monats_priv.ini']) && is_array($GLOBALS['monats_priv.ini'])) {
        $monats_config = $GLOBALS['monats_priv.ini'];
        $aktueller_monat = date('m'); // zweistellig, z.B. "09"
        $basis_dir = dirname($file);

        foreach ($monats_config as $monats_datei => $gueltige_monate) {
            $monate = array_map('trim', explode(',', $gueltige_monate));
            if (!in_array($aktueller_monat, $monate, true)) {
                continue;
            }

            $monats_ini_pfad = $basis_dir . '/' . $monats_datei;
            if (!file_exists($monats_ini_pfad)) {
                continue;
            }

            $monats_ini = parse_ini_file($monats_ini_pfad, true, INI_SCANNER_RAW);
            if ($monats_ini === false) {
                continue;
            }

            foreach ($monats_ini as $section => $values) {
                if (is_array($values) && isset($GLOBALS[$section]) && is_array($GLOBALS[$section])) {
                    // Sektionsweise mergen: nur die in der Monats-ini
                    // enthaltenen Keys überschreiben, Rest bleibt bestehen
                    $GLOBALS[$section] = array_replace_recursive($GLOBALS[$section], $values);
                } else {
                    $GLOBALS[$section] = $values;
                }
            }
        }
    }
}

/**
 * Generischer erster Schritt für alle numerisch-indizierten ini-Sektionen im "N.feld = wert"-
 * Format (z.B. [TAB_config], [AutoOptionsFelder]): gruppiert die flachen Keys zu einem Array
 * pro Index N, jeweils mit den enthaltenen Feldern als assoziatives Array. Index-Reihenfolge
 * bleibt über SORT_NATURAL erhalten (auch bei nachträglich eingeschobenen Indizes wie "3_5"
 * oder "3a").
 */
function group_indexed_ini_section(array $ini_section) {
    $result = [];

    foreach ($ini_section as $flatKey => $value) {
        if (strpos($flatKey, '.') === false) continue;

        [$index, $field] = explode('.', $flatKey, 2);

        if (!isset($result[$index])) {
            $result[$index] = [];
        }
        $result[$index][$field] = $value;
    }

    ksort($result, SORT_NATURAL);

    return $result;
}

/**
 * Rekonstruiert $TAB_config aus dem Abschnitt [TAB_config]
 * und sortiert die Tabs nach (hauptindex, suffix).
 */
function build_tab_config(array $ini_section) {
    $tabs = group_indexed_ini_section($ini_section);

    // Nach dem "sort"-Feld sortieren und numerisch von 0 an neu indizieren
    $result = [];
    foreach ($tabs as $tab) {
        $index = (int) $tab['sort'];
        $result[$index] = $tab;
    }
    ksort($result);
    $result = array_values($result);

    return $result;
}

/**
 * Rekonstruiert $AutoOptionsFelder aus dem Abschnitt [AutoOptionsFelder] von config.ini/config_priv.ini,
 * analog zu build_tab_config(). Jeder Eintrag "N.*" wird zu einem Feld, dessen "key" der
 * eigentliche Array-Schlüssel wird (z.B. "0.key = MindBattLad" -> $AutoOptionsFelder['MindBattLad']).
 * Erwartete Unter-Keys je Eintrag:
 * - key:      Pflicht - Anzeigename/Config-Schlüssel/DB-"Zeit" (identisch zum bisherigen PHP-Array-Schlüssel)
 * - typ:      'prozent' (Default), 'zahl', 'liste' oder 'radio'
 * - db_id:    eigene, kollisionsfreie ID (Spalte "ID") für den Speichervorgang
 * - section:  optional, ini-Sektion für den Config-Wert (Default 'Ladeberechnung')
 * - optionen: optional, nur bei typ 'liste'/'radio' - kommaseparierte "wert:Label"-Paare,
 *             z.B. "0:Aus,1:Ein,2:Automatik"
 */
function build_auto_options_felder(array $ini_section) {
    $felder_roh = group_indexed_ini_section($ini_section);

    // Auf das von 1_tab_LadeSteuerung.php erwartete Format bringen: key => [typ, db_id, ...]
    $result = [];
    foreach ($felder_roh as $eintrag) {
        if (!isset($eintrag['key']) || $eintrag['key'] === '') continue;

        $feld = [
            'typ'   => $eintrag['typ'] ?? 'prozent',
            'db_id' => $eintrag['db_id'] ?? '',
        ];
        if (isset($eintrag['section']) && $eintrag['section'] !== '') {
            $feld['section'] = $eintrag['section'];
        }
        if (isset($eintrag['optionen']) && $eintrag['optionen'] !== '') {
            $optionen = [];
            foreach (explode(',', $eintrag['optionen']) as $paar) {
                $paar = trim($paar);
                if ($paar === '') continue;
                $teile = explode(':', $paar, 2);
                $opt_wert = trim($teile[0]);
                $opt_label = isset($teile[1]) ? trim($teile[1]) : $opt_wert;
                $optionen[$opt_wert] = $opt_label;
            }
            $feld['optionen'] = $optionen;
        }

        $result[$eintrag['key']] = $feld;
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

    // Zeitzone zentral für ALLE Skripte setzen, die config_parser.php einbinden - ohne das
    // fällt PHP je nach Server-/php.ini-Konfiguration auf UTC zurück, während z.B. die
    // Strompreis-Daten in PV_Daten.sqlite in lokaler Zeit befüllt werden. Überschreibbar
    // über einen "Zeitzone"- oder "timezone"-Key in [General] von config.ini/config_priv.ini,
    // Default Europe/Berlin, falls dort nichts (oder ein ungültiger Wert) hinterlegt ist.
    $zeitzone = $GLOBALS['Zeitzone'] ?? $GLOBALS['timezone'] ?? 'Europe/Berlin';
    if (!@date_default_timezone_set($zeitzone)) {
        date_default_timezone_set('Europe/Berlin');
    }

    // TAB_config rekonstruieren und $TAB_config global setzen
    $TAB_config = [];
    if (isset($ini['TAB_config'])) {
        $TAB_config = build_tab_config($ini['TAB_config']);
    }
    $GLOBALS['TAB_config'] = $TAB_config;

    // AutoOptionsFelder (1_tab_LadeSteuerung.php) rekonstruieren und global setzen
    $AutoOptionsFelder = [];
    if (isset($ini['AutoOptionsFelder'])) {
        $AutoOptionsFelder = build_auto_options_felder($ini['AutoOptionsFelder']);
    }
    $GLOBALS['AutoOptionsFelder'] = $AutoOptionsFelder;

    // $ini selbst wird nicht mehr gebraucht - da es auf oberster Skriptebene
    // deklariert ist, würde es sonst als $GLOBALS['ini'] liegen bleiben und
    // die rohe, unverarbeitete [TAB_config]-Sektion doppelt neben der
    // aufbereiteten $GLOBALS['TAB_config'] sichtbar machen.
    unset($ini);

} catch (Exception $e) {
    die("Config-Fehler: " . $e->getMessage());
}
