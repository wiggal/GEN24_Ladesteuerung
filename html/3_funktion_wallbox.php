<?php
// Zeitzone wird zentral in config_parser.php gesetzt (Europe/Berlin, überschreibbar via
// config.ini [General]), das VOR dieser Datei in 3_tab_wallbox.php eingebunden wird.
/**
 * Generiert den HTML-Code für den Ladebalken basierend auf den übergebenen Werten.
 */
function generateLoadBar(float $solar, float $battery, float $grid, float $in_auto, float $in_haus): array
{
    // 1. Berechnung der Energiewerte
    $aus_battery = max(0.0, $battery);
    $aus_grid = max(0.0, $grid);
    $Q_total = $solar + $aus_battery + $aus_grid;

    $in_battery = max(0.0, -$battery);
    $in_grid = max(0.0, -$grid);
    $Z_total = $in_haus + $in_battery + $in_grid + $in_auto;

    if ($Q_total === 0.0) {
        return ['', 0.0, 0.0];
    }

    // 2. Erstellung eines Arrays für die Daten der Quellen
    $data_quelle = [
        'solar' => [
            'value' => $solar,
            'class' => 'solar',
            'label' => '☀️'
        ],
        'battery' => [
            'value' => $aus_battery,
            'class' => 'aus_battery',
            'label' => '🪫'
        ],
        'grid' => [
            'value' => $aus_grid,
            'class' => 'aus_grid',
            'label' => '⬇️'
        ]
    ];

    // 3. Erstellung eines Arrays für die Daten Ziele
    $data_ziel = [
        'haus' => [
            'value' => $in_haus,
            'class' => 'in_haus',
            'label' => '🏠'
        ],
        'auto' => [
            'value' => $in_auto,
            'class' => 'in_auto',
            'label' => '🚘'
        ],
        'battery' => [
            'value' => $in_battery,
            'class' => 'in_battery',
            'label' => '🔋'
        ],
        'grid' => [
            'value' => $in_grid,
            'class' => 'in_grid',
            'label' => '⬆️'
        ]
    ];

    $quelle_emoji_cells = ''; 
    $quelle_value_cells = ''; 
    $ziel_emoji_cells = ''; 
    $ziel_value_cells = ''; 

    // 3. Dynamische Generierung der Zellen Quelle
    foreach ($data_quelle as $item) {
        if ($item['value'] >= 0.1) {
            $pct = ($item['value'] / $Q_total) * 100;
            $width_style = "width: {$pct}%";
            
            // Emoji Zelle (Obere Reihe)
            $quelle_emoji_cells .= "<td style=\"{$width_style}\">{$item['label']}</td>";

            // Zelle für den Wert (Untere Reihe)
            $quelle_value_cells .= "<td class=\"{$item['class']}\" style=\"{$width_style}\">{$item['value']}</td>";
        }
    }

    // 4. Dynamische Generierung der Zellen Ziel
    foreach ($data_ziel as $item) {
        if ($item['value'] >= 0.1) {
            $pct = ($item['value'] / $Q_total) * 100;
            $width_style = "width: {$pct}%";
            
            // Emoji Zelle (Obere Reihe)
            $ziel_emoji_cells .= "<td style=\"{$width_style}\">{$item['label']}</td>";

            // Zelle für den Wert (Untere Reihe)
            $ziel_value_cells .= "<td class=\"{$item['class']}\" style=\"{$width_style}\">{$item['value']}</td>";
        }
    }


    // 4. Erzeugung des HTML-Strings mit den integrierten CSS-Styles
    $html = <<<HTML
    <div class="wrapper">
        <table class="bar-table">
            <tr class="load-bar-icons">
                {$quelle_emoji_cells}
            </tr>
            <tr class="load-bar-values">
                {$quelle_value_cells}
            </tr>
        </table>

        <table class="bar-table">
            <tr class="load-bar-values">
                {$ziel_value_cells}
            </tr>
            <tr class="load-bar-icons">
                {$ziel_emoji_cells}
            </tr>
        </table>
    </div>
    HTML;

    return [ $html, $Q_total, $Z_total ];
}

/**
 * Liefert die CSS-Styles für generateLadeDiagramm().
 * Einmal pro Seite (z.B. im <head> oder <style>-Block von 3_tab_wallbox.php) einbinden,
 * NICHT bei jedem Funktionsaufruf, da es sonst Duplikate im DOM gibt.
 */
function generateLadeDiagrammCSS(): string
{
    return <<<CSS
    <style>
        .chart-container {
            width: 100%;
            background: #fff;
            padding: 30px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            box-sizing: border-box;
        }
        .chart-container h2 {
            margin: 0 0 8px 0;
            font-weight: 600;
            font-size: 1.4rem;
        }
        .lademenge-anzeige {
            margin: 0 0 22px 0;
            font-size: 0.95rem;
            color: #444;
        }
        .chart-area {
            position: relative;
            height: 180px;
            border-bottom: 2px solid #555;
            padding-bottom: 5px;
            width: 100%;
            box-sizing: border-box;
        }
        .chart-area .column {
            position: absolute;
            bottom: 5px;
            background-color: #D1D1D1;
            border-radius: 2px 2px 0 0;
            transition: transform 0.2s, opacity 0.2s;
        }
        .chart-area .column.im-fenster {
            background-color: #e74c3c;
        }
        .chart-area .column.cheap {
            background-color: #2ecc71;
        }
        /* Zusätzliche, von der Live-Berechnung unabhängige Kennzeichnung: Slot ist
           tatsächlich in der DB gespeichert. Statt Rahmen (frisst bei schmalen Balken auf
           Mobile die komplette Breite) wird die UNTERE Hälfte blau eingefärbt - das braucht
           keine Breite, nur Höhe, und bleibt daher auch bei sehr schmalen Balken erkennbar.
           Je nach Status (cheap/im-fenster/default) behält die obere Hälfte ihre Farbe. */
        .chart-area .column.db-slot {
            background: linear-gradient(to bottom, #D1D1D1 0%, #D1D1D1 50%, #2980b9 50%, #2980b9 100%);
        }
        .chart-area .column.im-fenster.db-slot {
            background: linear-gradient(to bottom, #e74c3c 0%, #e74c3c 50%, #2980b9 50%, #2980b9 100%);
        }
        .chart-area .column.cheap.db-slot {
            background: linear-gradient(to bottom, #2ecc71 0%, #2ecc71 50%, #2980b9 50%, #2980b9 100%);
        }
        .legend-item .color-box.db-slot-legend {
            background: linear-gradient(to bottom, #D1D1D1 0%, #D1D1D1 50%, #2980b9 50%, #2980b9 100%);
        }
        .chart-area .column:hover {
            opacity: 0.8;
            transform: scaleY(1.02);
        }
        .chart-area .column:hover::after {
            content: attr(data-label);
            position: absolute;
            top: -40px;
            left: 50%;
            transform: translateX(-50%);
            background: #222;
            color: #fff;
            padding: 5px 10px;
            font-size: 11px;
            border-radius: 4px;
            white-space: nowrap;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .x-axis {
            position: relative;
            width: 100%;
            height: 30px;
            margin-top: 15px;
        }
        .x-axis .time-tick {
            position: absolute;
            transform: translateX(-50%);
            font-size: 12px;
            font-weight: bold;
            color: #666;
        }
        .x-axis .time-tick::before {
            content: '';
            position: absolute;
            top: -10px;
            left: 50%;
            width: 1px;
            height: 6px;
            background: #ccc;
        }
        /* Mobile: nur noch jede 2. Stunde beschriften, sonst zu eng/unleserlich */
        @media (max-width: 600px) {
            .x-axis .time-tick.tick-ungerade {
                display: none;
            }
            .chart-container h2 {
                font-size: 1.05rem;
                margin-bottom: 20px;
            }
        }
        .chart-container .legend {
            margin-top: 40px;
            display: flex;
            flex-wrap: wrap;
            row-gap: 10px;
            column-gap: 20px;
            font-size: 0.9rem;
        }
        .chart-container .legend-item { display: flex; align-items: center; gap: 8px; }
        .chart-container .color-box { width: 15px; height: 15px; border-radius: 3px; }
    </style>
    CSS;
}

/**
 * Extrahiert die bestehenden Next-Trip-Ladeslot-Zeiten aus dem von getSteuercodes('wallbox')
 * gelieferten Array (SQL_steuerfunctions.php).
 *
 * Schema: Ladeslot-Zeilen speichern ihre eigene (eindeutige) Anfangszeit im Feld 'Zeit' im
 * Format "HHMM" (z.B. "0515" für 05:15), statt eines gemeinsamen Markers wie früher "6".
 * Dadurch schlüsselt getSteuercodes() (das nach 'Zeit' gruppiert) jeden Slot unter seinem
 * eigenen eindeutigen Key ein - keine eigene direkte DB-Abfrage mehr nötig, im Gegensatz zu
 * vorher, als alle Slot-Zeilen denselben Zeit-Wert '6' teilten und sich dadurch gegenseitig
 * überschrieben hätten.
 * Basis-Konfigurationszeilen (ID 1-7) haben Zeit-Werte "1".."7" (1 Ziffer) und werden über
 * das Muster "genau 4 Ziffern" zuverlässig ausgeschlossen.
 *
 * @param array $steuercodesWallbox Rückgabe von getSteuercodes('wallbox')
 * @return string[] Liste von Anfangszeiten ("H:i"), z.B. ["05:15", "11:30", ...]
 */
function extrahiereLadeSlots(array $steuercodesWallbox): array
{
    $slots = [];
    foreach ($steuercodesWallbox as $zeitKey => $eintrag) {
        $zeitKey = (string)$zeitKey;
        if (preg_match('/^\d{4}$/', $zeitKey)) {
            $slots[] = substr($zeitKey, 0, 2) . ':' . substr($zeitKey, 2, 2);
        }
    }
    sort($slots);
    return $slots;
}

/**
 * Berechnet den Unix-Timestamp, an dem das aktuell konfigurierte Next-Trip-Ladezeit-Fenster
 * das nächste Mal endet (Uhrzeit == $bis). Wird beim Speichern (PV-Modus=NextTrip) in
 * ID=1/Res_Feld2 abgelegt, damit sowohl 3_tab_wallbox.php als auch ocpp.py nach Ablauf
 * dieses Zeitpunkts den PV-Modus automatisch auf "Aus" zurückfallen lassen können, statt
 * das Fenster (wie ein normales Ladezeit-Fenster) täglich zu wiederholen.
 *
 * Funktioniert unabhängig davon, ob das Fenster über Mitternacht geht (von > bis) oder
 * nicht (von < bis): gesucht wird schlicht der nächste Zeitpunkt ab $now, an dem die
 * Uhrzeit $bis erreicht wird.
 *
 * @param string   $von Ladezeit-Fenster Start "HH:MM" (nur zur Erkennung von "kein Fenster").
 * @param string   $bis Ladezeit-Fenster Ende "HH:MM".
 * @param int|null $now Basis-Zeitpunkt (Default: time()), für Tests überschreibbar.
 * @return int|null Unix-Timestamp des nächsten Fenster-Endes, oder null falls $von === $bis
 *                   (kein eingeschränktes Fenster -> kein definiertes "Ende").
 */
function berechneLadefensterEnde(string $von, string $bis, ?int $now = null): ?int
{
    if ($von === $bis) {
        // Kein eingeschränktes Fenster -> kein Fenster-Ende, kein Auto-Aus-Fallback.
        return null;
    }

    $now = $now ?? time();
    $heuteBis = strtotime(date('Y-m-d', $now) . ' ' . $bis . ':00', $now);
    if ($heuteBis === false) {
        return null;
    }

    return ($heuteBis > $now) ? $heuteBis : strtotime('+1 day', $heuteBis);
}

/**
 * Prüft, ob eine Uhrzeit (HH:MM) innerhalb eines Ladezeit-Fensters liegt.
 * Unterstützt Fenster, die über Mitternacht gehen (z.B. von "12:00" bis "05:00").
 */
function istInLadezeitfenster(string $zeit, string $von, string $bis): bool
{
    if ($von === $bis) {
        // Kein eingeschränktes Fenster (von == bis) -> ganzer Tag gültig
        return true;
    }
    if ($von < $bis) {
        // Normales Fenster ohne Mitternachts-Wrap, z.B. 08:00 - 18:00
        return $zeit >= $von && $zeit < $bis;
    }
    // Fenster geht über Mitternacht, z.B. 12:00 - 05:00
    return $zeit >= $von || $zeit < $bis;
}

/**
 * Liest die echten Strompreisdaten (Viertelstunden-Raster) aus PV_Daten.sqlite (Tabelle strompreise)
 * ab der nächsten vollen Viertelstunde.
 *
 * @return array{startTime:int, preise:float[]}|array{startTime:null, preise:array, fehler:string}
 */
function ladeStrompreise(string $dbPath, int $blockAnzahl): array
{
    // 1. Start-Zeitpunkt: nächste volle Viertelstunde
    $now = time();
    $minutes = (int)date('i', $now);
    $nextQuarterMinutes = (int)(floor($minutes / 15) * 15);
    $stundenStart = strtotime(date('Y-m-d H:00:00', $now));
    if ($nextQuarterMinutes >= 60) {
        $startTime = $stundenStart + 3600;
    } else {
        $startTime = $stundenStart + ($nextQuarterMinutes * 60);
    }

    if (!is_file($dbPath)) {
        error_log("ladeStrompreise: DB nicht gefunden unter {$dbPath}");
        return ['startTime' => null, 'preise' => [], 'fehler' => 'Preisdaten-Datenbank nicht gefunden.'];
    }

    // Zeitpunkt ist in der DB als TEXT "YYYY-MM-DD HH:MM:SS" gespeichert (kein Unix-
    // Timestamp) - deshalb hier ebenfalls als String binden, sonst vergleicht SQLite
    // einen INTEGER-Bind-Wert gegen eine TEXT-Spalte und liefert falsche/keine Treffer.
    $startTimeStr = date('Y-m-d H:i:s', $startTime);

    $preise = [];
    try {
        $db = new SQLite3($dbPath, SQLITE3_OPEN_READONLY);
        $stmt = $db->prepare(
            "SELECT Zeitpunkt, Bruttopreis FROM strompreise
             WHERE Zeitpunkt >= :start
             ORDER BY Zeitpunkt ASC
             LIMIT :limit"
        );
        $stmt->bindValue(':start', $startTimeStr, SQLITE3_TEXT);
        $stmt->bindValue(':limit', $blockAnzahl, SQLITE3_INTEGER);
        $result = $stmt->execute();
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $preise[] = (float)$row['Bruttopreis'];
        }
        $db->close();
    } catch (\Throwable $e) {
        error_log('ladeStrompreise: DB-Fehler - ' . $e->getMessage());
        return ['startTime' => null, 'preise' => [], 'fehler' => 'Preisdaten aktuell nicht verfügbar.'];
    }

    if (empty($preise)) {
        return ['startTime' => null, 'preise' => [], 'fehler' => 'Keine Preisdaten für die nächsten 24h gefunden.'];
    }

    return ['startTime' => $startTime, 'preise' => $preise];
}

/**
 * Ermittelt anhand der Next-Trip-Einstellungen (PV-Modus, Ladezeit-Fenster, Ladepreisgrenze,
 * Lademenge, Ladeleistung), welche Viertelstunden-Slots der nächsten 24h zum Laden genutzt
 * würden. Gemeinsame Berechnung für generateLadeDiagramm() (Anzeige) und getNextTripSlotZeiten()
 * (zum Speichern in steuercodes).
 *
 * @return array{anzeigeDaten:float[], startTime:int|null, topKeys:int[], hinweis:string}
 */
function berechneNextTripLadeSlots(
    int $pvMode,
    int $phases,
    float $ampMax,
    float $targetKwh,
    string $ladezeitVon,
    string $ladezeitBis,
    string $ladepreisGrenze = '',
    ?string $dbPath = null,
    int $blockAnzahl = 96
): array {
    if ($dbPath === null) {
        // Ein Verzeichnis über 3_funktion_wallbox.php
        $dbPath = __DIR__ . '/../PV_Daten.sqlite';
    }

    $preisDaten = ladeStrompreise($dbPath, $blockAnzahl);
    if ($preisDaten['startTime'] === null) {
        return [
            'anzeigeDaten' => [],
            'startTime' => null,
            'topKeys' => [],
            'hinweis' => '<p class="small">' . htmlspecialchars($preisDaten['fehler']) . '</p>',
        ];
    }

    $anzeigeDaten = $preisDaten['preise'];
    $startTime = $preisDaten['startTime'];

    $ladeAktiv = ($pvMode === 4);
    $ladepreisGrenzeAktiv = ($ladepreisGrenze !== '');
    $ladepreisGrenzeWert  = $ladepreisGrenzeAktiv ? (float)$ladepreisGrenze : null;

    // Phasen=0 bedeutet "Automatische Phasenwahl" - für die NextTrip-Berechnung wird das
    // wie in ocpp.py (compute_limits_from_global, PV-Mode 4) als 3-phasig behandelt.
    $phasenFuerBerechnung = ($phases === 0) ? 3 : $phases;

    // Maximale Ladeleistung -> Energie pro Viertelstunden-Slot
    $powerKw = ($phasenFuerBerechnung * $ampMax * 230) / 1000;
    $energieProSlot = $powerKw * 0.25; // kWh je 15-Minuten-Slot

    $topKeys = [];
    $hinweis = '';
    $lademengeErreichbar = true;
    $keineLademengeOderLeistung = false;
    $erreichteMenge = 0.0;

    if (!$ladeAktiv) {
        $hinweis = '<p class="small">PV-Modus ist nicht "Next Trip" (4) – aktuell ist keine Wallboxladung geplant.</p>';
    } elseif ($energieProSlot <= 0.0 || $targetKwh <= 0.0) {
        $keineLademengeOderLeistung = true;
        $lademengeErreichbar = false;
    } else {
        // Kandidaten: innerhalb Ladezeit-Fenster und (falls gesetzt) unter Ladepreisgrenze
        $kandidaten = [];
        foreach ($anzeigeDaten as $offset => $preis) {
            $slotTime = $startTime + ($offset * 900);
            $slotZeit = date('H:i', $slotTime);

            if (!istInLadezeitfenster($slotZeit, $ladezeitVon, $ladezeitBis)) {
                continue;
            }
            if ($ladepreisGrenzeAktiv && $preis > $ladepreisGrenzeWert) {
                continue;
            }
            $kandidaten[$offset] = $preis;
        }

        if (empty($kandidaten)) {
            $hinweis = '<p class="small">Keine Slots im Ladezeit-Fenster' . ($ladepreisGrenzeAktiv ? ' unterhalb der Ladepreisgrenze' : '') . ' gefunden.</p>';
            $lademengeErreichbar = false;
        } else {
            asort($kandidaten);
            // Lademenge wird immer mit 110% kalkuliert (Sicherheitspuffer, z.B. für Ladeverluste)
            $targetKwhMitPuffer = $targetKwh * 1.10;
            $neededSlots = (int)ceil($targetKwhMitPuffer / $energieProSlot);
            $verfuegbareSlots = count($kandidaten);
            $genutzteSlots = min($neededSlots, $verfuegbareSlots);
            $topKeys = array_slice(array_keys($kandidaten), 0, $genutzteSlots);

            // Wirklich erreichte Lademenge anhand der tatsächlich genutzten Slots.
            // Die Anzeige erfolgt immer auf 100%-Basis (Netto) - der 110%-Aufschlag oben
            // dient nur der Slot-Anzahl-Berechnung, um den angenommenen Ladeverlust
            // auszugleichen, und wird für die Anzeige wieder herausgerechnet.
            $erreichteMengeBrutto = $genutzteSlots * $energieProSlot;
            $erreichteMenge = $erreichteMengeBrutto / 1.10;
            $lademengeErreichbar = ($erreichteMenge >= $targetKwh - 0.0001);
        }
    }

    return [
        'anzeigeDaten' => $anzeigeDaten,
        'startTime' => $startTime,
        'topKeys' => $topKeys,
        'hinweis' => $hinweis,
        'targetKwh' => $targetKwh,
        'ladeAktiv' => $ladeAktiv,
        'lademengeErreichbar' => $lademengeErreichbar,
        'keineLademengeOderLeistung' => $keineLademengeOderLeistung,
        'erreichteMenge' => $erreichteMenge,
    ];
}

/**
 * Wandelt die von berechneNextTripLadeSlots() gelieferten Viertelstunden-Offsets (topKeys)
 * in Uhrzeiten ("H:i") um. Gemeinsame Hilfsfunktion für getNextTripSlotZeiten() sowie die
 * AJAX-/Initial-Render-Stellen in 3_tab_wallbox.php, die direkt mit dem Ergebnis von
 * berechneNextTripLadeSlots() weiterarbeiten - dessen Rückgabe-Array selbst KEINEN
 * 'slotZeiten'-Schlüssel enthält (nur 'topKeys' als Viertelstunden-Offsets).
 *
 * @param array $result Rückgabe von berechneNextTripLadeSlots()
 * @return string[] Liste von Uhrzeiten im Format "H:i", z.B. ["05:15", "05:30", ...]
 */
function nextTripTopKeysToZeiten(array $result): array
{
    if (($result['startTime'] ?? null) === null) {
        return [];
    }
    $zeiten = [];
    foreach ($result['topKeys'] ?? [] as $offset) {
        $zeiten[] = date('H:i', $result['startTime'] + ($offset * 900));
    }
    return $zeiten;
}

/**
 * Liefert die Uhrzeiten ("H:i") der Slots, die laut aktuellen Next-Trip-Einstellungen zum
 * Laden genutzt würden – zum Speichern als eigene Datensätze in steuercodes (ID = Anfangszeit,
 * Schluessel = "wallbox", Zeit = eigene Slot-Zeit "HHMM", s. extrahiereLadeSlots()). Nur
 * sinnvoll befüllt, wenn $pvMode === 4.
 *
 * @return string[] Liste von Uhrzeiten im Format "H:i", z.B. ["05:15", "05:30", ...]
 */
function getNextTripSlotZeiten(
    int $pvMode,
    int $phases,
    float $ampMax,
    float $targetKwh,
    string $ladezeitVon,
    string $ladezeitBis,
    string $ladepreisGrenze = '',
    ?string $dbPath = null,
    int $blockAnzahl = 96
): array {
    $result = berechneNextTripLadeSlots(
        $pvMode, $phases, $ampMax, $targetKwh, $ladezeitVon, $ladezeitBis,
        $ladepreisGrenze, $dbPath, $blockAnzahl
    );

    return nextTripTopKeysToZeiten($result);
}

/**
 * Erzeugt das 24h-Ladepreis-Diagramm mit echten Daten aus PV_Daten.sqlite (Tabelle strompreise)
 * und markiert die Slots grün, die laut den auf der Oberfläche eingestellten Next-Trip-Werten
 * tatsächlich für die Wallboxladung genutzt würden:
 *  - Nur aktiv, wenn PV-Modus == 4 (sonst keine Ladung geplant)
 *  - Nur innerhalb des Ladezeit-Fensters (Ladezeit-von / Ladezeit-bis)
 *  - Nur unterhalb der Ladepreisgrenze, falls eine gesetzt ist
 *  - Anzahl markierter Slots ergibt sich aus der Lademenge (kWh) und der maximal
 *    möglichen Ladeleistung (Phasen x Ampere-Max x 230V); es werden die günstigsten
 *    Slots aus den verbleibenden Kandidaten gewählt, bis die Lademenge gedeckt ist.
 *
 * WICHTIG - bitte vor Einsatz prüfen und ggf. anpassen:
 *  - $dbPath: Pfad zur PV_Daten.sqlite (aktuell ein Verzeichnis über dieser Datei angenommen)
 *  - Spaltennamen 'Zeitpunkt' (Unix-Timestamp) und 'Bruttopreis' in Tabelle "strompreise":
 *    bitte mit tatsächlichem Schema abgleichen (z.B. per `PRAGMA table_info(strompreise);`).
 *
 * @param int         $pvMode          Aktuell eingestellter PV-Modus (Next-Trip = 4).
 * @param int         $phases          Anzahl Ladephasen (Options aus ID=1).
 * @param float       $ampMax          Maximale Ladestromstärke in A.
 * @param float       $targetKwh       Gewünschte Lademenge in kWh (DEFAULT_TARGET_KWH).
 * @param string      $ladezeitVon     Ladezeit-Fenster Start "HH:MM".
 * @param string      $ladezeitBis     Ladezeit-Fenster Ende "HH:MM".
 * @param string      $ladepreisGrenze Ladepreisgrenze in € oder '' für kein Limit.
 * @param string|null $dbPath          Pfad zur SQLite-DB. Default: ein Verzeichnis über dieser Datei.
 * @param int         $blockAnzahl     Anzahl Viertelstunden-Blöcke, die angezeigt werden (96 = 24h).
 * @return string HTML-Fragment (ohne CSS - siehe generateLadeDiagrammCSS()).
 */
function generateLadeDiagramm(
    int $pvMode,
    int $phases,
    float $ampMax,
    float $targetKwh,
    string $ladezeitVon,
    string $ladezeitBis,
    string $ladepreisGrenze = '',
    ?string $dbPath = null,
    int $blockAnzahl = 96,
    ?array $presetResult = null, // Neu: Nimmt ein bereits berechnetes Ergebnis entgegen
    array $dbSlots = [] // Tatsächlich in der DB gespeicherte Ladeslots ("H:i"), s. extrahiereLadeSlots()
 ): string {
    // Falls das Ergebnis bereits vorliegt, nutze es. Ansonsten führe die Berechnung durch.
    $result = $presetResult ?? berechneNextTripLadeSlots(
        $pvMode, $phases, $ampMax, $targetKwh, $ladezeitVon, $ladezeitBis,
        $ladepreisGrenze, $dbPath, $blockAnzahl
    );

    if ($result['startTime'] === null) {
        return '<div class="chart-container">' . $result['hinweis'] . '</div>';
    }

    $anzeigeDaten = $result['anzeigeDaten'];
    $startTime = $result['startTime'];
    $lademengeErreichbar = $result['lademengeErreichbar'];
    $ladeAktivFuerAnzeige = $result['ladeAktiv'];
    $keineLademengeOderLeistung = $result['keineLademengeOderLeistung'];
    $erreichteMenge = $result['erreichteMenge'];
    $topKeys = $result['topKeys'];
    $hinweis = $result['hinweis'];

    // Schneller Lookup, ob eine Slot-Uhrzeit tatsächlich in der DB gespeichert ist -
    // unabhängig davon, ob die aktuelle Live-Berechnung (topKeys) sie (noch) auswählt.
    $dbSlotSet = array_flip($dbSlots);

    $maxPreis = max($anzeigeDaten);
    if ($maxPreis <= 0.0) {
        $maxPreis = 1.0;
    }

    $anzahlSlots = count($anzeigeDaten);
    $columns = '';
    $ticks = '';
    $slotBreitePercent = 100 / $anzahlSlots;

    foreach ($anzeigeDaten as $offset => $preis) {
        $currentSlotTime = $startTime + ($offset * 900);
        $zeitString = date('H:i', $currentSlotTime);

        if (in_array($offset, $topKeys, true)) {
            $classCheap = 'cheap';
        } elseif (istInLadezeitfenster($zeitString, $ladezeitVon, $ladezeitBis)) {
            $classCheap = 'im-fenster';
        } else {
            $classCheap = '';
        }

        // Zusätzliche, von der Live-Berechnung UNABHÄNGIGE Kennzeichnung: Ist dieser Slot
        // tatsächlich in der DB gespeichert? (z.B. nach Änderungen am Formular, die noch
        // nicht gespeichert wurden, kann das von "cheap" abweichen.)
        $dbClass = isset($dbSlotSet[$zeitString]) ? ' db-slot' : '';

        $hoehe = max(($preis / $maxPreis) * 100, 3);
        $preisFormatiert = number_format($preis, 2, ',', '.');
        $leftPercent = $offset * $slotBreitePercent;
        $dbHinweis = $dbClass !== '' ? ' [in DB gespeichert]' : '';

        // Balken werden absolut/prozentual positioniert (statt Flex+Gap), damit sie exakt
        // auf demselben Koordinatensystem wie die Zeitmarken im x-axis-Bereich liegen -
        // sonst laufen beide auf schmalen (mobilen) Bildschirmen auseinander.
        $columns .= "<div class=\"column {$classCheap}{$dbClass}\" style=\"left: {$leftPercent}%; width: calc({$slotBreitePercent}% - 1px); height: {$hoehe}%;\" data-label=\"{$zeitString} Uhr: {$preisFormatiert} ct{$dbHinweis}\"></div>";

        if (date('i', $currentSlotTime) === '00') {
            $stunde = (int)date('H', $currentSlotTime);
            $percent = ($offset / $anzahlSlots) * 100;
            $stundenClass = ($stunde % 2 === 0) ? 'tick-gerade' : 'tick-ungerade';
            $ticks .= "<span class=\"time-tick {$stundenClass}\" style=\"left: {$percent}%;\">{$stunde}</span>";
        }
    }

    $lademengeZeile = '';
    if ($ladeAktivFuerAnzeige && $keineLademengeOderLeistung) {
        $lademengeZeile = '<p class="lademenge-anzeige" style="color: #e74c3c; font-weight: bold;">Keine Lademenge hinterlegt – keine Ladeslots berechnet.</p>';
    } elseif ($ladeAktivFuerAnzeige) {
        $erreichtFormatiert = number_format($erreichteMenge, 1, ',', '.');
        if ($lademengeErreichbar) {
            $lademengeZeile = "<p class=\"lademenge-anzeige\">Lademenge: {$erreichtFormatiert} kWh</p>";
        } else {
            $zielFormatiert = number_format($targetKwh, 1, ',', '.');
            $lademengeZeile = "<p class=\"lademenge-anzeige\" style=\"color: #e74c3c; font-weight: bold;\">Lademenge: {$erreichtFormatiert} kWh (Ziel {$zielFormatiert} kWh nicht erreichbar!)</p>";
        }
    }

    $html = <<<HTML
    <div class="chart-container">
        <h2>Strompreis-Vorschau (nächste 24h)</h2>
        {$lademengeZeile}
        <div class="chart-area">
            {$columns}
        </div>
        <div class="x-axis">
            {$ticks}
        </div>
        <div class="legend">
            <div class="legend-item"><div class="color-box" style="background: #D1D1D1;"></div> Außerhalb Zeitfenster</div>
            <div class="legend-item"><div class="color-box" style="background: #e74c3c;"></div> Ungenutzter Ladeslot</div>
            <div class="legend-item"><div class="color-box" style="background: #2ecc71;"></div> Genutzter Ladeslot</div>
            <div class="legend-item"><div class="color-box db-slot-legend"></div> Ladeslot in DB</div>
        </div>
        {$hinweis}
    </div>
    HTML;

    return $html;
}
?>
