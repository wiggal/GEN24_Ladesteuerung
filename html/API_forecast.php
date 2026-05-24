<?php
header('Content-Type: application/json; charset=utf-8');

# config.ini parsen
require_once "config_parser.php";

$now     = new DateTime('now', new DateTimeZone($Timezone ?? 'Europe/Berlin'));
$now_utc = new DateTime('now', new DateTimeZone('UTC'));

# Daten aus DB lesen
$SQLite_file = $PythonDIR . "/weatherData.sqlite";

if (!file_exists($SQLite_file)) {
    echo json_encode([
        'result'  => null,
        'message' => [
            'code' => 1,
            'type' => 'error',
            'text' => "SQLite-Datei $SQLite_file nicht gefunden.",
        ]
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit();
}

$db = new SQLite3($SQLite_file);

// Nur Prognose-Einträge ab Beginn des heutigen Tages
$heute = $now->format('Y-m-d 00:00:00');
$stmt  = $db->prepare(
    "SELECT Zeitpunkt, Prognose_W
       FROM weatherData
      WHERE Quelle = 'Prognose'
        AND Zeitpunkt >= :heute
      ORDER BY Zeitpunkt ASC"
);
$stmt->bindValue(':heute', $heute, SQLITE3_TEXT);
$queryResult = $stmt->execute();

$result = [];
while ($row = $queryResult->fetchArray(SQLITE3_ASSOC)) {
    $result[$row['Zeitpunkt']] = (int) $row['Prognose_W'];
}

if (empty($result)) {
    echo json_encode([
        'result'  => null,
        'message' => [
            'code' => 2,
            'type' => 'error',
            'text' => 'Keine Prognosedaten gefunden.',
        ]
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit();
}

$output = [
    'result'  => $result,
    'message' => [
        'code' => 0,
        'type' => 'success',
        'text' => '',
        'info' => [
            'latitude'  => (float) ($Latitude  ?? 0),
            'longitude' => (float) ($Longitude ?? 0),
            'distance'  => 0,
            'place'     => $Place    ?? '',
            'timezone'  => $Timezone ?? 'Europe/Berlin',
            'time'      => $now->format(DateTime::ATOM),
            'time_utc'  => $now_utc->format(DateTime::ATOM),
        ],
        'ratelimit' => [
            'zone'      => $RatelimitZone      ?? '',
            'period'    => (int) ($RatelimitPeriod    ?? 3600),
            'limit'     => (int) ($RatelimitLimit     ?? 12),
            'remaining' => (int) ($RatelimitRemaining ?? 0),
        ],
    ],
];

echo json_encode($output, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
