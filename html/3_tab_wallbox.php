<?php
// ================================================
// Wattpilot OCPP Control – Single File PHP UI (angepasst: Kein Fallback-ID, DB-Werte immer anzeigen)
// Erweiterung: zusätzliche Wallbox-Parameter (IDs 2-7) editierbar und in DB speicherbar
// Änderungen: Details-Bereich "Mehr Optionen" behält manuell gesetzten geöffnet/geschlossen-Status in localStorage
// ================================================
// Erkennt automatisch die IP des Servers (z.B. 192.168.178.4)
$server_ip = $_SERVER['HTTP_HOST'];
// Falls HTTP_HOST auch den Port enthält (z.B. :80), filtern wir nur die IP/Domain
$server_ip = explode(':', $server_ip)[0];
$API = "http://localhost:8886";
$API_PUBLIC = "http://" . $server_ip . ":8886";
$SERVER_PID_FILE = "/tmp/ocpp_server.pid";
# config.ini parsen
require_once "config_parser.php";
global $PythonDIR;
$GEN24_DIR = realpath(__DIR__ . '/' . $PythonDIR);
$PYTHON_SERVER_CMD = "nohup python3 -u $GEN24_DIR/ocpp_server.py > /tmp/ocpp.log 2>&1 & echo $!";

include 'SQL_steuerfunctions.php';
require_once '3_funktion_wallbox.php';

// -------------------------
// AJAX: Next-Trip-Ladediagramm live neu berechnen
// Wird gebraucht, weil der PV-Modus-Wechsel im Dropdown rein clientseitig (JS) passiert -
// ohne diesen Endpunkt gäbe es beim Umschalten von z.B. "Aus" auf "NextTrip" weder eine
// aktualisierte Vorschau noch korrekt berechnete Ladeslots zum Speichern.
// Nutzt die im Formular AKTUELL eingetragenen (ggf. noch ungespeicherten) Werte, nicht die DB-Werte.
// -------------------------
if (isset($_POST['ladeDiagrammAjax'])) {
    header('Content-Type: application/json; charset=utf-8');

    $ld_pv_mode       = (int)($_POST['pv_mode'] ?? 0);
    $ld_phases        = (int)($_POST['phases'] ?? 1);
    $ld_amp_max       = (float)($_POST['amp_max'] ?? 16);
    $ld_target_kwh    = (float)($_POST['target_kwh'] ?? 0);
    $ld_lz_von        = (string)($_POST['ladezeit_von'] ?? '12:00');
    $ld_lz_bis        = (string)($_POST['ladezeit_bis'] ?? '05:00');
    $ld_preisgrenze   = (string)($_POST['ladepreis_grenze'] ?? '');

    $ld_result = berechneNextTripLadeSlots(
        $ld_pv_mode, $ld_phases, $ld_amp_max, $ld_target_kwh,
        $ld_lz_von, $ld_lz_bis, $ld_preisgrenze
    );

    $ld_slots = $ld_result['slotZeiten'] ?? [];
    $ld_fenster_ende = ($ld_pv_mode === 4) ? berechneLadefensterEnde($ld_lz_von, $ld_lz_bis) : null;

    $ld_html = ($ld_pv_mode === 4)
        ? generateLadeDiagramm(
            $ld_pv_mode, $ld_phases, $ld_amp_max, $ld_target_kwh,
            $ld_lz_von, $ld_lz_bis, $ld_preisgrenze, null, 96, $ld_result
          )
        : '';

    echo json_encode([
        'html'  => $ld_html,
        'slots' => $ld_slots,
        'fensterEnde' => $ld_fenster_ende,
    ]);
    exit;
}

// -------------------------
// Helper Functions
// -------------------------
function server_is_running($pidfile) {
    if (!file_exists($pidfile)) return false;
    $pid = intval(@file_get_contents($pidfile));
    // Überprüfen, ob die PID gültig ist und der Prozess noch läuft
    return $pid > 0 && function_exists('posix_kill') && @posix_kill($pid, 0);
}

function api_post($endpoint, $data = []) {
    $options = [
        'http' => [
            'header'  => "Content-type: application/json\r\n",
            'method'  => 'POST',
            'content' => json_encode($data),
            'timeout' => 5
        ]
    ];
    $context = stream_context_create($options);
    $result = @file_get_contents($GLOBALS['API'].$endpoint, false, $context);
    return $result ? json_decode($result, true) : null;
}

// -------------------------
// Handle Actions (POST)
// -------------------------
if (isset($_POST['action'])) {
    $action = $_POST['action'];

    if ($action === 'start_server') {
        // Nur starten, wenn der Server noch nicht läuft
        if (!server_is_running($SERVER_PID_FILE)) {
            $pid = shell_exec($GLOBALS['PYTHON_SERVER_CMD']);
            $pid = trim($pid);
            if ($pid !== '') {
                file_put_contents($GLOBALS['SERVER_PID_FILE'], $pid);
            }
        }
    }

    if ($action === 'stop_server') {
        if (file_exists($GLOBALS['SERVER_PID_FILE'])) {
            $pid = intval(@file_get_contents($GLOBALS['SERVER_PID_FILE']));
            if ($pid > 0) {
                if (function_exists('posix_kill')) {
                    @posix_kill($pid, 9); // SIGKILL
                } else {
                    @shell_exec("kill -9 $pid");
                }
            }
            @unlink($GLOBALS['SERVER_PID_FILE']);
        }
    }

    // Beim Weiterleiten die aktuelle Client-ID beibehalten
        echo "
	<script>
    		const params = new URLSearchParams();
    		params.set('tab', " . json_encode('Wallbox') . ");";
    if (isset($_POST['cp_id']) && !empty($_POST['cp_id'])) {
    	echo "params.set('cp_id', " . json_encode($_POST['cp_id']) . ");";
    	}
    echo "window.location.href = window.location.pathname + '?' + params.toString();
	</script>
	";
    exit;
}

// -------------------------
// Fetch Status Data
// -------------------------
$server_running = server_is_running($SERVER_PID_FILE);
$status = null;
$meter_values = null;
$connected_list = [];

if ($server_running) {
    $status_json = @file_get_contents($API . "/list");
    $status = $status_json ? @json_decode($status_json, true) : null;
}

// Connected client check
if (is_array($status)) {
    if (isset($status['connected']) && is_array($status['connected'])) {
        $connected_list = $status['connected'];
    } else {
        $connected_list = $status;
    }
}

// --- Aktuell ausgewählten Client bestimmen ---
$selected_charge_point_id = null;
$client_connected = !empty($connected_list);

if ($client_connected) {
    if (isset($_GET['cp_id']) && in_array($_GET['cp_id'], $connected_list, true)) {
        // 1. Priorität: Client-ID aus dem GET-Parameter, falls sie in der Liste ist
        $selected_charge_point_id = $_GET['cp_id'];
    } else {
        // 2. Priorität: Nimm den ersten Client in der Liste als Standard
        $selected_charge_point_id = reset($connected_list);
    }
    
    // Meter Values für den aktuell ausgewählten Client abfragen
    if ($server_running) {
        $meter_values_json = @file_get_contents($API . "/meter_values?charge_point_id=$selected_charge_point_id");
        $meter_values = $meter_values_json ? @json_decode($meter_values_json, true) : null;
    }
} 

// -------------------------
// DB: Werte laden (immer laden, da es die Konfiguration ist)
// -------------------------
$EV_Reservierung = getSteuercodes('wallbox'); // Fester DB-Schlüssel

// ID=1 (Basis-Einstellungen)
$pv_mode = $EV_Reservierung['1']['Res_Feld1'] ?? 0;
$nexttrip_fenster_ende = $EV_Reservierung['1']['Res_Feld2'] ?? '';        // Unix-Timestamp Fenster-Ende (NextTrip)
$phases  = $EV_Reservierung['1']['Options'] ?? 1;

// Next-Trip-Fenster bereits abgelaufen? -> PV-Modus für Anzeige/weitere Logik wie "Aus"
// behandeln (Dropdown, Next-Trip-Details, Diagramm) - das eigentliche Zurückschreiben in
// die DB passiert unten per Auto-Save (siehe $nextTripAbgelaufen im <script>-Bereich).
$nextTripAbgelaufen = (
    (int)$pv_mode === 4
    && $nexttrip_fenster_ende !== ''
    && (int)$nexttrip_fenster_ende <= time()
);
if ($nextTripAbgelaufen) {
    $pv_mode = 0;
}

// ID=2 (Ampere-Grenzen)
$amp_min = $EV_Reservierung['2']['Res_Feld1'] ?? 6;                       // A-MIN
$amp_max = $EV_Reservierung['2']['Res_Feld2'] ?? 16;                      // A-MAX

// ID=3 (Lademenge / Ladepreisgrenze)
$default_target_kwh = $EV_Reservierung['3']['Res_Feld1'] ?? 0.0;          // DEFAULT_TARGET_KWH (Lademenge)
$ladepreis_grenze   = $EV_Reservierung['3']['Res_Feld2'] ?? '';           // Leer = keine Ladepreisgrenze aktiv

// ID=4 (Zeitintervalle)
$auto_sync_interval    = $EV_Reservierung['4']['Res_Feld1'] ?? 20;        // AUTO_SYNC_INTERVAL (Wallboxaktualisierung)
$min_charge_duration_s = $EV_Reservierung['4']['Res_Feld2'] ?? 600;       // MIN_CHARGE_DURATION_S (Mindestladezeit)
$phase_change_confirm_s = $EV_Reservierung['4']['Options'] ?? 300;        // PHASE_CHANGE_CONFIRM_S (Phasen-Delay)

// ID=5 (Leistung)
$residualPower   = $EV_Reservierung['5']['Res_Feld1'] ?? 100;             // residualPower (Watt, Verbleibende Leistung)
$max_leistung_ha = $EV_Reservierung['5']['Res_Feld2'] ?? "-0.1";          // Höchster Akkuladewert kW

// ID=6 (Ladezeit-Fenster)
$ladezeit_von = $EV_Reservierung['6']['Res_Feld1'] ?? "12:00";
$ladezeit_bis = $EV_Reservierung['6']['Res_Feld2'] ?? "05:00";

// ID=7 (Preise)
$strompreis_fest = $EV_Reservierung['7']['Res_Feld1'] ?? 0.30;
$einspeise_verg  = $EV_Reservierung['7']['Res_Feld2'] ?? 0.07;

// Bestehende Next-Trip-Ladeslots (Zeit="HHMM" = eigene Slot-Zeit, ID=Anfangszeit "HH:MM")
// aus $EV_Reservierung (bereits oben per getSteuercodes('wallbox') geladen) extrahieren.
// Diese werden beim Speichern unverändert mitgeschickt, solange NICHT neu mit
// PV-Modus=NextTrip gespeichert wird - sonst würden sie durch den vollständigen
// DELETE+REPLACE in SQL_speichern.php sonst verloren gehen.
$bestehende_lade_slots = extrahiereLadeSlots($EV_Reservierung);

// -------------------------
// AJAX poll
// -------------------------
if (isset($_GET['ajax'])) {
    header('Content-Type: application/json; charset=utf-8');

    // Ladebalken-HTML für AJAX berechnen
    $solar_current_a   = round(($meter_values['Produktion_W'] ?? 0) / 1000, 1);
    $battery_current_a = round(($meter_values['Batteriebezug_W'] ?? 0) / 1000, 1);
    $grid_current_a    = round(($meter_values['Netzbezug_W'] ?? 0) / 1000, 1);
    $Hausverbrauch_a   = round(($meter_values['Hausverbrauch'] ?? 0) / 1000, 1);
    $car_power_ist_a   = round(($meter_values['power_w_ist']  ?? 0) / 1000, 1);
    $car_power_soll_a  = round(($meter_values['power_w_soll'] ?? 0) / 1000, 1);

    $Q_sum_a    = $solar_current_a + max(0, $battery_current_a) + max(0, $grid_current_a);
    $in_batt_a  = max(0, -$battery_current_a);
    $in_grid_a  = max(0, -$grid_current_a);
    $basis_a    = $Hausverbrauch_a + $in_batt_a + $in_grid_a;
    $abw_ist_a  = abs($Q_sum_a - ($basis_a + $car_power_ist_a));
    $abw_soll_a = abs($Q_sum_a - ($basis_a + $car_power_soll_a));
    $car_power_a = ($abw_ist_a <= $abw_soll_a) ? $car_power_ist_a : $car_power_soll_a;
    if ($car_power_a < 0.2) $car_power_a = 0;
    if ($Hausverbrauch_a < 0.1) $Hausverbrauch_a = 0.2;

    [ $html_ajax, $Q_ajax, $Z_ajax ] = generateLoadBar(
        $solar_current_a, $battery_current_a, $grid_current_a, $car_power_a, $Hausverbrauch_a
    );
    $diff_ajax = abs($Q_ajax - $Z_ajax);

    $cl_ajax = (float)($meter_values['current_limit'] ?? 0);
    $ph_ajax = (int)($meter_values['phases'] ?? 0);
    $kw_ajax = round($ph_ajax * $cl_ajax * 230 / 1000, 2);

    echo json_encode([
        'server_running'   => $server_running,
        'pid'              => $server_running && file_exists($SERVER_PID_FILE) ? intval(@file_get_contents($SERVER_PID_FILE)) : null,
        'connected_list'   => array_values($connected_list),
        'client_connected' => $client_connected,
        'meter_values'     => $meter_values ?? new stdClass(),
        'charge_point_id'  => $selected_charge_point_id,
        'timestamp'        => time(),
        'loadbar_html'     => $html_ajax,
        'loadbar_diff'     => $diff_ajax,
        'wallbox_amp'      => $cl_ajax,
        'wallbox_phases'   => $ph_ajax,
        'wallbox_kw'       => $kw_ajax,
    ]);
    exit;
}

?>
<style>
/* --- Grundlayout --- */
body {
    background: white;
}

.card {
    background: white;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 8px;
}

.card h2 { margin: 0px; }
.card p { margin: 4px 0; line-height: 1.1; }

button.ocpp {
    padding: 6px 12px;
    font-size: 14px;
    background-color: #4CAF50;
    color: black;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button.ocpp.red { background: #d9534f; }
button.ocpp.schreiben { position: sticky; bottom: 10px;}
button.ocpp:disabled {
    background-color: #ccc;
    color: #666;
    cursor: not-allowed;
}


select,
input[type="number"],
input[type="text"] {
    font-size: 1.1em;
    background-color: #F5F5DC;
    padding: 4px;
    border-radius: 4px;
    border: 1px solid #ccc;
}

.info {
    background: #e9f7ef;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 10px;
}

.small {
    font-size: 0.9em;
    color: #666;
}

p, label {
    color: #000;
    font-size: 120%;
    padding: 2px 1px;
    line-height: 1.1;
}

.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    vertical-align: middle;
}

/* --- Flexbox für Einstellungszeilen --- */
.row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    gap: 8px;
}

.label-inline {
    width: 300px;     /* Einheitliche Label-Spalte */
    flex-shrink: 0;   /* verhindert Zusammenstauchen */
}

.input-inline {
    flex: 1;
}

.input-inline select,
.input-inline input {
    width: 120px;     /* oder auto / oder 100% */
    max-width: 100%;
}

.kein-limit-label {
    white-space: nowrap;
    font-size: 0.9em;
    display: inline-flex;
    align-items: center;
    gap: 3px;
}

.kein-limit-label input[type="checkbox"] {
    width: auto;
    margin: 0;
}

/* --- Balkentabelle (PV/Lastenanzeige) --- */
.wrapper {
    width: 99%;
    margin: 10px 0;
}

.bar-table {
    width: 100%;
    border-collapse: collapse;
}

.load-bar-icons td {
    padding: 0;
    text-align: center;
    vertical-align: middle;
    font-size: 1.2em;
    border-left: 2px solid #999;
    border-right: 2px solid #999;
}

.load-bar-values td {
    padding: 2px;
    text-align: center;
    font-weight: 600;
}

/* Farben für Energiefluss */
.solar         { background: #FFC800; color: black; }
.aus_battery   { background: #2DB42D; color: black; }
.aus_grid      { background: #6E6E6E; color: black; }
.in_haus       { background: #d9534f; color: black; }
.in_auto       { background: #FB5555; color: black; }
.in_battery    { background: #3CD73C; color: black; }
.in_grid       { background: #949494; color: black; }

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
    .label-inline {
      width: 180px;     /* Einheitliche Label-Spalte */
      flex-shrink: 0;   /* verhindert Zusammenstauchen */
    }
    .input-inline select,
    .input-inline input {
      width: 70px;     /* oder auto / oder 100% */
      max-width: 100%;
    }
    #ladePreisGrenze {
      width: 55px;     /* schmaler, damit "kein Limit" daneben passt */
    }
    .kein-limit-label {
      font-size: 0.8em;
    }
   .wallboxwerte {
     font-size: 14px;
   }
   .hilfe {
      margin: 0px;
   }
   .content {
        height: auto; /* Erlaubt dem Body zu scrollen */
        overflow: visible;
    }

} /* @media ENDE */

</style>
<?php echo generateLadeDiagrammCSS(); ?>
<?php
  $current_url = urlencode($_SERVER['REQUEST_URI']);
  $hilfe_link = "index.php?tab=Hilfe&file=" . ($activeTab ?? basename(__FILE__, '.php'));
?>
<div class="hilfe"> <a href="<?php echo $hilfe_link; ?>"><b>Hilfe</b></a></div>
<div class="card">
    <h2>OCPP Server</h2>
    <p id="serverStatus">
        <?php if ($server_running): ?>
            <span class="status-dot" style="background:green"></span>
            <strong style="color:green">Server läuft</strong>
            (PID: <span id="serverPid"><?php echo intval(@file_get_contents($SERVER_PID_FILE)); ?></span>)
        <?php else: ?>
            <span class="status-dot" style="background:red"></span>
            <strong style="color:red">Server gestoppt</strong>
        <?php endif; ?>
    </p>

    <?php if (count($connected_list) > 1): ?>
    <p>
        <label>
            OCPP Client auswählen:
            <select id="chargePointSelect" onchange="var u=window.location.pathname+'?tab=Wallbox&cp_id='+encodeURIComponent(this.value); window.location.href=u;">
                <?php foreach ($connected_list as $cp_id): ?>
                    <option value="<?php echo htmlspecialchars($cp_id); ?>" <?php if ($cp_id === $selected_charge_point_id) echo 'selected'; ?>>
                        <?php echo htmlspecialchars($cp_id); ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </label>
    </p>
    <?php endif; ?>

    <p id="clientStatus">
        <?php if ($client_connected): ?>
            <span class="status-dot" style="background:green"></span>
            <strong style="color:green">Client <?php echo htmlspecialchars($selected_charge_point_id); ?>: Verbunden</strong>
            <?php if (count($connected_list) > 1): ?>
                <span class="small">(Ausgewählt)</span>
            <?php endif; ?>
        <?php else: ?>
            <span class="status-dot" style="background:red"></span>
            <strong style="color:red">Kein Client verbunden</strong>
        <?php endif; ?>
    </p>
    
    <div style="margin-top:10px;">
        <?php if ($server_running): ?>
            <form method="post">
            <input type="hidden" name="action" value="stop_server">
            <input type="hidden" name="tab" value="Wallbox">
            <button class="ocpp red" id="btnStopServer">Server stoppen</button></form>
        <?php else: ?>
            <form method="post">
            <input type="hidden" name="action" value="start_server">
            <input type="hidden" name="tab" value="Wallbox">
            <button class="ocpp green" id="btnStartServer" onclick="this.disabled=true;this.textContent='Server startet…';this.form.submit();">Server starten</button></form>
        <?php endif; ?>
    </div>
</div>

<?php
// 1. Inverter-Werte (Quellen) vorbereiten
$solar_current   = round(($meter_values['Produktion_W'] ?? 0) / 1000, 1);
$battery_current = round(($meter_values['Batteriebezug_W'] ?? 0) / 1000, 1);
$grid_current    = round(($meter_values['Netzbezug_W'] ?? 0) / 1000, 1);
$Hausverbrauch    = round(($meter_values['Hausverbrauch'] ?? 0) / 1000, 1);

// 2. Ladeleistung — Ist- und Sollwert aus OCPP
$car_power_ist  = round(($meter_values['power_w_ist']  ?? 0) / 1000, 1);
$car_power_soll = round(($meter_values['power_w_soll'] ?? 0) / 1000, 1);

// Quellbilanz: welcher Wert passt besser zur Inverter-Summe?
$Q_sum      = $solar_current + max(0, $battery_current) + max(0, $grid_current);
$in_battery = max(0, -$battery_current);
$in_grid    = max(0, -$grid_current);
$basis      = $Hausverbrauch + $in_battery + $in_grid;

$abw_ist  = abs($Q_sum - ($basis + $car_power_ist));
$abw_soll = abs($Q_sum - ($basis + $car_power_soll));

$car_power = ($abw_ist <= $abw_soll) ? $car_power_ist : $car_power_soll;
if ($car_power < 0.2) $car_power = 0;

// 3. Hausverbrauch-Mindestlast
if ($Hausverbrauch < 0.1) $Hausverbrauch = 0.2;

// 4. Balkendiagramm generieren
[ $html_neu, $Q_final, $Z_final ] = generateLoadBar($solar_current, $battery_current, $grid_current, $car_power, $Hausverbrauch);
// $diff nicht mehr benötigt (war für localStorage-Cache)

echo "<div id=\"loadbar-container\">";
echo $html_neu;
echo "</div>";
?>
<div class="card">
    <div class="wallboxwerte">
    <?php if ($client_connected): ?>
        <p>Wallboxwerte(0A=AUS): <strong id="currentAmp"><?php
            $cl = (float)($meter_values['current_limit'] ?? 0);
            $ph = (int)($meter_values['phases'] ?? 0);
            echo htmlspecialchars($cl) . 'A / ' . htmlspecialchars($ph) . 'PH / ';
            echo htmlspecialchars(round($ph * $cl * 230 / 1000, 2));
            ?>kW</strong></p>
        <p>Ladedauer (Std:Min): <strong><?php echo gmdate("H:i", intval($meter_values['charging_duration_s'] ?? 0)); ?></strong></p>
        <p>Geladene kWh: <strong><?php echo htmlspecialchars(round($meter_values['charged_energy_kwh'] ?? 0, 1)); ?></strong>
            &nbsp; Soll: <?php echo htmlspecialchars($meter_values['target_energy_kwh'] ?? '—'); ?>
        <?php
        // Button nur anzeigen, wenn Server läuft und Client verbunden ist.
        $charged_energy = (float)($meter_values['charged_energy_kwh'] ?? 0.0);
        if ($server_running && $client_connected) {
            $disabled = ($charged_energy <= 0) ? 'disabled' : '';

            echo '<button type="button" id="btnResetCounter" class="ocpp red" ' . $disabled . '>Reset</button>';
        }
        ?>
        </p>
        <p>Hausakku SOC: <strong><?php echo ($meter_values['BattStatusProz'] ?? '—'); ?>%</strong></p>
    <?php else: ?>
        <p class="small">Live-Daten sind nicht vorhanden, da kein OCPP-Client (Wallbox) verbunden ist.</p>
    <?php endif; ?>
        <hr>
    </div>

    <h3>Optionen einstellen und speichern!</h3>
    <form id="formOptions">
        <input type="hidden" id="selectedCpId" name="cp_id" value="<?php echo htmlspecialchars($selected_charge_point_id ?? ''); ?>">
        
        <div class="row">
            <span class="label-inline">PV-Modus (DB=<?php echo htmlspecialchars($pv_mode); ?>):</span>
            <span class="input-inline">
            <select id="pvMode" name="pv_mode">
                <option value="0" <?php if($pv_mode=='0') echo 'selected'; ?>>Aus</option>
                <option value="1" <?php if($pv_mode=='1') echo 'selected'; ?>>PV</option>
                <option value="2" <?php if($pv_mode=='2') echo 'selected'; ?>>MIN+PV</option>
                <option value="3" <?php if($pv_mode=='3') echo 'selected'; ?>>MAX</option>
                <option value="4" <?php if($pv_mode=='4') echo 'selected'; ?>>NextTrip</option>
            </select>
            </span>
        </div>

        <div class="row">
            <span class="label-inline">Phasen (DB=<?php echo htmlspecialchars($phases); ?>):</span>
            <span class="input-inline">
            <select id="phases" name="phases">
                <option value="0" <?php if($phases=='0') echo 'selected'; ?>>Auto</option>
                <option value="1" <?php if($phases=='1') echo 'selected'; ?>>1Ph</option>
                <option value="3" <?php if($phases=='3') echo 'selected'; ?>>3Ph</option>
            </select>
            </span>
        </div>

        <div class="row">
            <span class="label-inline">Stromstärke MIN (DB=<?php echo htmlspecialchars($amp_min); ?>):</span>
            <span class="input-inline">
            <select id="ampMin" name="amp_min">
                <?php for($i=6;$i<=16;$i++): ?>
                    <option value="<?php echo $i; ?>" <?php if($i==$amp_min) echo 'selected'; ?>><?php echo $i; ?> A</option>
                <?php endfor; ?>
            </select>
            <span id="powerMin" class="small" style="margin-left: 10px;">(— kW)</span> </span>
        </div>

        <div class="row">
            <span class="label-inline">Stromstärke MAX (DB=<?php echo htmlspecialchars($amp_max); ?>):</span>
            <span class="input-inline">
            <select id="ampMax" name="amp_max">
                <?php for($i=6;$i<=16;$i++): ?>
                    <option value="<?php echo $i; ?>" <?php if($i==$amp_max) echo 'selected'; ?>><?php echo $i; ?> A</option>
                <?php endfor; ?>
            </select>
            <span id="powerMax" class="small" style="margin-left: 10px;">(— kW)</span> </span>
        </div>
        <div class="row">
            <span class="label-inline">Lademenge(kWh) (DB=<?php echo htmlspecialchars($default_target_kwh); ?>):</span>
            <span class="input-inline"><input id="defaultTargetKwh" type="number" step="1" min="0" value="<?php echo htmlspecialchars($default_target_kwh); ?>"></span>
        </div>

        <div class="row">
            <span class="label-inline">Ladepreisgrenze (€) (DB=<?php echo htmlspecialchars($ladepreis_grenze !== '' ? $ladepreis_grenze : 'kein Limit'); ?>):</span>
            <span class="input-inline" style="display:flex; align-items:center; gap:4px;">
                <input id="ladePreisGrenze" type="number" step="0.01" placeholder="kein Limit"
                    value="<?php echo htmlspecialchars($ladepreis_grenze); ?>"
                    <?php echo ($ladepreis_grenze === '') ? 'disabled' : ''; ?>>
                <label class="kein-limit-label">
                    <input type="checkbox" id="ladePreisGrenzeKeinLimit" <?php echo ($ladepreis_grenze === '') ? 'checked' : ''; ?>>
                    kein Limit
                </label>
            </span>
        </div>
        <hr>

        <details id="nextTripOptions" <?php echo ($pv_mode == '4') ? 'open' : ''; ?>>
            <summary><b>Next Trip Optionen:</b></summary>

            <div class="row">
                <span class="label-inline">Ladezeit-von (DB=<?php echo htmlspecialchars($ladezeit_von); ?>):</span>
                <span class="input-inline">
                    <input id="ladezeitVon" type="text"
                        value="<?php echo htmlspecialchars($ladezeit_von); ?>"
                        placeholder="HH:MM"
                        style="cursor: s-resize;">
                </span>
            </div>

            <div class="row">
                <span class="label-inline">Ladezeit-bis (DB=<?php echo htmlspecialchars($ladezeit_bis); ?>):</span>
                <span class="input-inline">
                    <input id="ladezeitBis" type="text"
                        value="<?php echo htmlspecialchars($ladezeit_bis); ?>"
                        placeholder="HH:MM"
                        style="cursor: s-resize;">
                </span>
            </div>

            <div class="row">
                <span class="label-inline">Strompreis-fest (€) (DB=<?php echo htmlspecialchars($strompreis_fest); ?>):</span>
                <span class="input-inline"><input id="strompreisFest" type="number" step="0.001" value="<?php echo htmlspecialchars($strompreis_fest); ?>"></span>
            </div>

            <div class="row">
                <span class="label-inline">Einspeisevergütung (€) (DB=<?php echo htmlspecialchars($einspeise_verg); ?>):</span>
                <span class="input-inline"><input id="einspeiseVerg" type="number" step="0.001" value="<?php echo htmlspecialchars($einspeise_verg); ?>"></span>
            </div>

            <div class="row" style="display:block;" id="ladeDiagrammContainer">
            <?php if ((int)$pv_mode === 4): ?>
                <?php
                    $next_trip_result = berechneNextTripLadeSlots(
                        (int)$pv_mode,
                        (int)$phases,
                        (float)$amp_max,
                        (float)$default_target_kwh,
                        $ladezeit_von,
                        $ladezeit_bis,
                        (string)$ladepreis_grenze
                    );

                    $neue_lade_slots = $next_trip_result['slotZeiten'] ?? [];

                    echo generateLadeDiagramm(
                        (int)$pv_mode,
                        (int)$phases,
                        (float)$amp_max,
                        (float)$default_target_kwh,
                        $ladezeit_von,
                        $ladezeit_bis,
                        (string)$ladepreis_grenze,
                        null,
                        96,
                        $next_trip_result
                    );
                ?>
            <?php else: ?>
                <?php $neue_lade_slots = []; ?>
            <?php endif; ?>
            </div>
        </details>
        <hr>
        <details id="moreOptions">
            <summary><b>Erweiterte Optionen:</b></summary>

        <div class="row">
            <span class="label-inline">Wallboxaktualisierung(s) (DB=<?php echo htmlspecialchars($auto_sync_interval); ?>):</span>
            <span class="input-inline"><input id="autoSyncInterval" type="number" min="10" step="10" value="<?php echo htmlspecialchars($auto_sync_interval); ?>"></span>
        </div>


        <div class="row">
            <span class="label-inline">Mindestladezeit(s) (DB=<?php echo htmlspecialchars($min_charge_duration_s); ?>):</span>
            <span class="input-inline"><input id="minChargeDur" type="number" min="60" step="60" value="<?php echo htmlspecialchars($min_charge_duration_s); ?>"></span>
        </div>

        <div class="row">
            <span class="label-inline">Phasen-Delay(s) (DB=<?php echo htmlspecialchars($phase_change_confirm_s); ?>):</span>
            <span class="input-inline"><input id="phaseChangeConfirm" type="number" min="0" step="30" value="<?php echo htmlspecialchars($phase_change_confirm_s); ?>"></span>
        </div>

        <div class="row">
            <span class="label-inline">Verbleibende Leistung(W) (DB=<?php echo htmlspecialchars($residualPower); ?>):</span>
            <span class="input-inline"><input id="residualPower" type="number" step="100" value="<?php echo htmlspecialchars($residualPower); ?>"></span>
        </div>

        <div class="row">
            <span class="label-inline">Ladebegr. Hausakku(kW) (DB=<?php echo htmlspecialchars($max_leistung_ha); ?>):</span>
            <span class="input-inline"><input id="MaxLeistHAkW" type="number" step="0.1" min="-0.1" value="<?php echo htmlspecialchars($max_leistung_ha); ?>"></span>
        </div>

        <hr>
        </details>
        <br>
        <button type="button" id="btnSave" class="ocpp schreiben">Speichern</button>
        <p class="small">Diese Einstellungen werden in der SQLite-Datenbank gespeichert und von der Steuerung (ocpp_server.py) verwendet, um OCPP-Befehle an die Wallbox zu senden.</p>
    </form>
</div>

<script src="jquery.min.js"></script>

<script>
// Next-Trip-Ladeslots (ID=Anfangszeit "HH:MM", Zeit=eigene Slot-Zeit ohne Doppelpunkt "HHMM"):
// - bestehendeLadeSlots: aktuell in der DB gespeicherte Slots (werden beim Speichern
//   unverändert mitgeschickt, solange NICHT neu mit PV-Modus=NextTrip gespeichert wird)
// - neueLadeSlots: frisch berechnete Slots auf Basis der aktuellen Next-Trip-Einstellungen
//   (nur befüllt, wenn die Seite mit PV-Modus=NextTrip geladen wurde)
var bestehendeLadeSlots = <?php echo json_encode(array_values($bestehende_lade_slots)); ?>;
var neueLadeSlots = <?php echo json_encode(array_values($neue_lade_slots ?? [])); ?>;
var fensterEndeBestehend = <?php echo json_encode($nexttrip_fenster_ende !== '' ? (int)$nexttrip_fenster_ende : ''); ?>;

$(document).ready(function(){

    // --- Zentrale Funktion zum Formatieren & Runden ---
    function formatAndRoundTime(inputVal) {
        // Entferne alles außer Zahlen und Doppelpunkt
        var clean = inputVal.replace(/[^0-9:]/g, '');

        // Falls nur Zahlen eingegeben wurden (z.B. 1200 -> 12:00)
        if (clean.length === 4 && clean.indexOf(':') === -1) {
            clean = clean.substr(0, 2) + ':' + clean.substr(2, 2);
        }

        var parts = clean.split(':');
        var h = parseInt(parts[0], 10) || 0;
        var m = parseInt(parts[1], 10) || 0;

        // Stunden auf 0-23 begrenzen
        h = Math.min(Math.max(h, 0), 23);

        // Minuten auf das nächste 15er Intervall runden
        m = Math.round(m / 15) * 15;
        if (m >= 60) {
            m = 0;
            h = (h + 1) % 24;
        }

        return (h < 10 ? '0' + h : h) + ":" + (m < 10 ? '0' + m : m);
    }

    // --- Blätter-Funktion (wie zuvor) ---
    function scrollTime(input, direction) {
        var current = formatAndRoundTime($(input).val());
        var parts = current.split(':');
        var totalMinutes = parseInt(parts[0]) * 60 + parseInt(parts[1]) + (direction * 15);

        if (totalMinutes < 0) totalMinutes += 1440;
        if (totalMinutes >= 1440) totalMinutes -= 1440;

        var newH = Math.floor(totalMinutes / 60);
        var newM = totalMinutes % 60;
        var formatted = (newH < 10 ? '0' + newH : newH) + ":" + (newM < 10 ? '0' + newM : newM);
        $(input).val(formatted).trigger('change');
    }

    // --- EVENTS ---

    // 1. Manuelle Eingabe korrigieren beim Verlassen des Feldes
    $('#ladezeitVon, #ladezeitBis').on('blur', function() {
        var corrected = formatAndRoundTime($(this).val());
        $(this).val(corrected);
    });

    // 2. Mausrad-Blättern
    $('#ladezeitVon, #ladezeitBis').on('wheel', function(e) {
        e.preventDefault();
        var direction = e.originalEvent.deltaY < 0 ? 1 : -1;
        scrollTime(this, direction);
    });

    // 3. Tastatur-Blättern (Pfeiltasten)
    $('#ladezeitVon, #ladezeitBis').on('keydown', function(e) {
        if (e.which === 38) { // Hoch
            e.preventDefault();
            scrollTime(this, 1);
        } else if (e.which === 40) { // Runter
            e.preventDefault();
            scrollTime(this, -1);
        }
    });
    
// ===================================
// NEU: Berechnung der Leistung bei Änderung
// ===================================
/**
 * Berechnet die Leistung (P = U * I * n_Phase) basierend auf den
 * ausgewählten Phasen (phases) und Stromstärken (ampMin/ampMax) und 
 * aktualisiert die Anzeigefelder.
 */
function calculatePower() {
    // Standard-Spannung
    const VOLTAGE = 230; // Volt
    
    // Aktuell ausgewählte Werte
    let phases_selection = parseInt($('#phases').val());
    let amp_min = parseFloat($('#ampMin').val());
    let amp_max = parseFloat($('#ampMax').val());
    
    let phases_min;
    let phases_max;
    
    if (phases_selection === 0) {
        // 'Auto' ist gewählt: MIN gilt für 1 Phase, MAX gilt für 3 Phasen
        phases_min = 1;
        phases_max = 3;
    } else {
        // 1 oder 3 Phasen sind fest gewählt
        phases_min = phases_selection;
        phases_max = phases_selection;
    }
    
    // Berechnung der Leistung (Watt)
    let power_min_w = VOLTAGE * amp_min * phases_min;
    let power_max_w = VOLTAGE * amp_max * phases_max;
    
    // Umwandlung in kW und Runden auf 2 Dezimalstellen
    let power_min_kw = (power_min_w / 1000).toFixed(2);
    let power_max_kw = (power_max_w / 1000).toFixed(2);
    
    // Aktualisierung der Anzeige
    $('#powerMin').text('(' + power_min_kw + ' kW)');
    $('#powerMax').text('(' + power_max_kw + ' kW)');
}

    // Listener hinzufügen: Führt die Berechnung aus, sobald einer der Werte geändert wird
    $('#phases, #ampMin, #ampMax').on('change', calculatePower);
    
    // Einmalige Berechnung beim Laden der Seite
    calculatePower();

    // --- Details "Mehr Optionen" öffnen/geschlossen Zustand persistieren ---
    var moreOptionsKey = 'moreOptionsOpen';
    var moreOptionsEl = document.getElementById('moreOptions');
    if (moreOptionsEl) {
        // Bei Laden wiederherstellen
        var stored = localStorage.getItem(moreOptionsKey);
        if (stored === '1') {
            moreOptionsEl.setAttribute('open', 'open');
        } else {
            moreOptionsEl.removeAttribute('open');
        }
        // Auf Toggle reagieren und Zustand speichern (Details-Element feuert 'toggle' Event)
        moreOptionsEl.addEventListener('toggle', function(){
            try {
                localStorage.setItem(moreOptionsKey, this.open ? '1' : '0');
            } catch(e) {
                // ignore storage errors
            }
        });
    }
    // =========================================================================
    // NEU: Sichtbarkeit der Next Trip Optionen steuern
    // =========================================================================
    function updateNextTripVisibility() {
        var selectedMode = $('#pvMode').val();
        var nextTripDetails = document.getElementById('nextTripOptions');

        if (nextTripDetails) {
            // Nur wenn Modus "4" (NextTrip) gewählt ist, aufklappen
            if (selectedMode === '4') {
                nextTripDetails.setAttribute('open', 'open');
                refreshLadeDiagramm();
            } else {
                nextTripDetails.removeAttribute('open');
                neueLadeSlots = [];
            }
        }
    }

    // Berechnet das Ladediagramm live neu (aktuelle Formularwerte, nicht DB-Werte) und
    // ersetzt den Container-Inhalt; aktualisiert neueLadeSlots für den Save-Handler.
    function refreshLadeDiagramm() {
        var container = document.getElementById('ladeDiagrammContainer');
        $.ajax({
            url: "<?php echo htmlspecialchars(basename(__FILE__)); ?>",
            method: "post",
            dataType: "json",
            data: {
                ladeDiagrammAjax: 1,
                pv_mode: $('#pvMode').val(),
                phases: $('#phases').val(),
                amp_max: $('#ampMax').val(),
                target_kwh: $('#defaultTargetKwh').val(),
                ladezeit_von: $('#ladezeitVon').val(),
                ladezeit_bis: $('#ladezeitBis').val(),
                ladepreis_grenze: $('#ladePreisGrenzeKeinLimit').is(':checked') ? '' : $('#ladePreisGrenze').val()
            },
            success: function(response) {
                neueLadeSlots = response.slots || [];
                if (container) {
                    container.innerHTML = response.html || '';
                }
            }
            // Bei Fehler bewusst nichts überschreiben - alter Stand von neueLadeSlots/HTML bleibt erhalten
        });
    }

    // Sofort beim Laden der Seite ausführen
    updateNextTripVisibility();

    // Bei jeder Änderung des PV-Modus-Dropdowns ausführen
    $('#pvMode').on('change', function() {
        updateNextTripVisibility();
    });

    // Bei Änderung der Next-Trip-relevanten Felder das Diagramm ebenfalls live neu berechnen,
    // solange NextTrip aktuell ausgewählt ist (sonst wären gespeicherte Slots sonst veraltet)
    $('#phases, #ampMax, #defaultTargetKwh, #ladezeitVon, #ladezeitBis, #ladePreisGrenze, #ladePreisGrenzeKeinLimit').on('change', function() {
        if ($('#pvMode').val() === '4') {
            refreshLadeDiagramm();
        }
    });
    // =========================================================================

    // =========================================================================
    // NEU: "kein Limit" Checkbox für Ladepreisgrenze
    // =========================================================================
    function updateLadePreisGrenzeState() {
        var keinLimit = $('#ladePreisGrenzeKeinLimit').is(':checked');
        $('#ladePreisGrenze').prop('disabled', keinLimit);
    }
    updateLadePreisGrenzeState();
    $('#ladePreisGrenzeKeinLimit').on('change', function() {
        updateLadePreisGrenzeState();
    });
    // =========================================================================

    $('#btnSave').click(function(){
    // --- Daten sammeln ---

    // ID 1: Basis-Einstellungen
    var pv_mode = $('#pvMode').val();
    var phases = $('#phases').val();

    // ID 2: Ampere-Grenzen
    var amp_min = $('#ampMin').val();
    var amp_max = $('#ampMax').val();

    // ID 3: Lademenge & Ladepreisgrenze
    var default_target_kwh = $('#defaultTargetKwh').val();
    var ladepreis_grenze = $('#ladePreisGrenzeKeinLimit').is(':checked') ? '' : $('#ladePreisGrenze').val();

    // ID 4: Zeitintervalle
    var auto_sync_interval = $('#autoSyncInterval').val();
    var min_charge_dur = $('#minChargeDur').val();
    var phase_change_confirm = $('#phaseChangeConfirm').val();

    // ID 5: Leistung
    var residual_power = $('#residualPower').val();
    var max_leistung_ha = $('#MaxLeistHAkW').val();

    // ID 6: Next Trip Zeiten (aus Grafik)
    var lz_von = $('#ladezeitVon').val();
    var lz_bis = $('#ladezeitBis').val();

    // ID 7: Preise (aus Grafik)
    var s_preis = $('#strompreisFest').val();
    var e_verg  = $('#einspeiseVerg').val();

    // --- Next-Trip-Ladeslots (ID=Anfangszeit, Zeit=eigene Slot-Zeit "HHMM") anhängen ---
    // SQL_speichern.php löscht + ersetzt ALLE "wallbox"-Datensätze bei jedem Speichern -
    // daher müssen bestehende Ladeslots hier immer mitgeschickt werden, sonst gehen sie
    // verloren. Nur bei PV-Modus=NextTrip (4) werden sie durch die frisch berechneten
    // Slots überschrieben; sonst bleiben die zuletzt gespeicherten Slots unverändert
    // erhalten (werden von ocpp.py bei anderem PV-Modus ohnehin nicht verwendet).
    // --- Next-Trip-Ladeslots bestimmen und dann speichern ---
    function speichereMitSlots(ladeSlots, fensterEnde) {
        var saveID         = ["1", "2", "3", "4", "5", "6", "7"];
        var saveSchluessel = ["wallbox", "wallbox", "wallbox", "wallbox", "wallbox", "wallbox", "wallbox"];
        var saveTagZeit     = ["1", "2", "3", "4", "5", "6", "7"];
        var saveRes_Feld1 = [
            pv_mode,                 // ID 1: PV-Modus
            amp_min,                 // ID 2: A-MIN
            default_target_kwh,      // ID 3: Lademenge
            auto_sync_interval,      // ID 4: Wallboxaktualisierung
            residual_power,          // ID 5: Verbleibende Leistung
            lz_von,                  // ID 6: Ladezeit-von
            s_preis                  // ID 7: Strompreis-fest
        ];
        var saveRes_Feld2 = [
            fensterEnde || "",  // ID 1: Unix-Timestamp Fenster-Ende (nur bei NextTrip gesetzt)
            amp_max,            // ID 2: A-MAX
            ladepreis_grenze,   // ID 3: LadePreisGrenze €
            min_charge_dur,     // ID 4: Mindestladezeit
            max_leistung_ha,    // ID 5: Max Akku-ladewert kW
            lz_bis,             // ID 6: Ladezeit-bis
            e_verg              // ID 7: Einspeisevergütung
        ];
        var saveOptions = [
            phases,                 // ID 1: Phasen
            "",                     // ID 2: unbenutzt
            "",                     // ID 3: unbenutzt
            phase_change_confirm,   // ID 4: Phasen-Delay
            "",                     // ID 5: unbenutzt
            "",                     // ID 6: unbenutzt
            ""                      // ID 7: unbenutzt
        ];

        ladeSlots.forEach(function(zeit){
            saveID.push(zeit);
            saveSchluessel.push("wallbox");
            saveTagZeit.push(zeit.replace(":", "")); // z.B. "05:15" -> "0515"
            saveRes_Feld1.push("");
            saveRes_Feld2.push("");
            saveOptions.push("");
        });

        $.ajax({
            url: "SQL_speichern.php",
            method: "post",
            data: {
                ID:         saveID,
                Schluessel: saveSchluessel,
                Tag_Zeit:   saveTagZeit,
                Res_Feld1:  saveRes_Feld1,
                Res_Feld2:  saveRes_Feld2,
                Options:    saveOptions
            },
            success: function(response){
                // Seite neu laden (mit Scroll-Position-Erhalt durch deinen bestehenden Listener)
                refreshData();
            },
            error: function(xhr, status, err) {
                alert("Fehler beim Speichern in die Datenbank: " + err);
            }
        });
    }

    if (pv_mode === '4') {
        // Formularwerte können sich seit dem letzten Diagramm-Refresh geändert haben (z.B.
        // Ladezeit-Feld editiert, aber "change" noch nicht gefeuert) - daher hier nochmal
        // synchron live neu berechnen, BEVOR gespeichert wird.
        $.ajax({
            url: "<?php echo htmlspecialchars(basename(__FILE__)); ?>",
            method: "post",
            dataType: "json",
            data: {
                ladeDiagrammAjax: 1,
                pv_mode: pv_mode,
                phases: phases,
                amp_max: amp_max,
                target_kwh: default_target_kwh,
                ladezeit_von: lz_von,
                ladezeit_bis: lz_bis,
                ladepreis_grenze: ladepreis_grenze
            },
            success: function(resp) {
                neueLadeSlots = resp.slots || [];
                speichereMitSlots(neueLadeSlots, resp.fensterEnde);
            },
            error: function() {
                // Fallback: letzten bekannten Stand verwenden statt Speichern ganz abzubrechen
                speichereMitSlots(neueLadeSlots, fensterEndeBestehend);
            }
        });
    } else {
        // Kein NextTrip -> kein Fenster-Ende relevant, ID=1/Res_Feld2 leeren.
        speichereMitSlots(bestehendeLadeSlots, "");
    }
    });

    <?php if ($nextTripAbgelaufen): ?>
    // Next-Trip-Zeitfenster ist laut Server bereits abgelaufen (ID=1/Res_Feld2 <= jetzt).
    // Automatisch wie ein manuelles Speichern mit PV-Modus=Aus auslösen, damit der
    // zurückgefallene Zustand (PV-Modus=0, Fenster-Ende geleert) auch tatsächlich in der
    // DB persistiert wird - #pvMode steht dank $pv_mode-Override serverseitig oben
    // bereits auf "0". Nutzt exakt denselben, bereits getesteten Save-Pfad wie der Button.
    $('#btnSave').trigger('click');
    <?php endif; ?>
});

  // Scroll-Position speichern
  window.addEventListener("beforeunload", () => {
    sessionStorage.setItem("scrollPos", window.scrollY);
  });

  // Scroll-Position nach dem Laden wiederherstellen
  window.addEventListener("load", () => {
    const scrollPos = sessionStorage.getItem("scrollPos");
    if (scrollPos !== null) {
      window.scrollTo(0, parseInt(scrollPos));
    }
  });

// ===================================
// Einfaches Neuladen der Seite
// ===================================
function refreshData() {
    var params = new URLSearchParams(window.location.search);
    params.set('tab', 'Wallbox');
    // cp_id aus der aktuellen URL übernehmen, falls vorhanden
    var url = window.location.pathname + '?' + params.toString();
    window.location.href = url;
}

// ===================================
// Ladebalken per AJAX aktualisieren
// ===================================
var lastValidLoadbar = null;

// Einmalig alten localStorage-Cache übernehmen und bereinigen
(function() {
    var old = localStorage.getItem('loadbar_cache');
    if (old) {
        lastValidLoadbar = old;
        localStorage.removeItem('loadbar_cache');
    }
})();

function pollLoadbar() {
    var cp_id = new URLSearchParams(window.location.search).get('cp_id') || "";
    var url = "<?php echo htmlspecialchars(basename(__FILE__)); ?>?ajax=1";
    if (cp_id) url += '&cp_id=' + encodeURIComponent(cp_id);

    $.getJSON(url, function(data) {
        var container = document.getElementById('loadbar-container');
        if (!container) return;

        if (typeof data.loadbar_html !== 'undefined' && data.loadbar_html !== '') {
            if (data.loadbar_diff <= 0.3) {
                // Plausibel → anzeigen und merken
                lastValidLoadbar = data.loadbar_html;
                container.innerHTML = data.loadbar_html;
            } else if (lastValidLoadbar) {
                // Abweichung zu groß → letzten gültigen Stand anzeigen
                container.innerHTML = lastValidLoadbar;
            }
        }

        // Wallboxwerte aktualisieren
        var ampEl = document.getElementById('currentAmp');
        if (ampEl && typeof data.wallbox_amp !== 'undefined') {
            ampEl.textContent = data.wallbox_amp + 'A / ' + data.wallbox_phases + 'PH / ' + data.wallbox_kw + 'kW';
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.warn('pollLoadbar AJAX-Fehler:', textStatus, errorThrown, url);
    });
}

// Ladebalken alle 10s per AJAX (kein Seitenflackern)
setInterval(pollLoadbar, 10000);
// Erster Poll nach 5s (initiales HTML ist bereits korrekt gerendert)
setTimeout(pollLoadbar, 5000);

// Full-Reload alle 60s (aktualisiert Konfigurationsfelder und Wallboxwerte) -
// wird ausgesetzt, solange ein Feld vom beim Laden angezeigten DB-Stand abweicht, damit
// eine gerade getroffene Auswahl (z.B. PV-Modus-Wechsel) nicht durch den automatischen
// Reload überschrieben wird. Wird ein Feld wieder auf seinen Original-Wert zurückgestellt,
// greift der Reload sofort wieder ganz normal (kein Timer, direkter Wertvergleich).
// Die Live-Ladeleistungs-Anzeige (pollLoadbar, alle 10s) ist davon NICHT betroffen -
// die läuft unabhängig per eigenem AJAX-Polling weiter.
var ueberwachteFelder = ['#pvMode', '#phases', '#ampMin', '#ampMax', '#autoSyncInterval',
    '#minChargeDur', '#phaseChangeConfirm', '#residualPower', '#defaultTargetKwh',
    '#ladezeitVon', '#ladezeitBis', '#MaxLeistHAkW', '#strompreisFest', '#einspeiseVerg',
    '#ladePreisGrenze', '#ladePreisGrenzeKeinLimit'];
var originalFeldWerte = {};

function feldWert($el) {
    return $el.is(':checkbox') ? $el.is(':checked') : $el.val();
}

$(document).ready(function(){
    ueberwachteFelder.forEach(function(sel){
        var $el = $(sel);
        if ($el.length) {
            originalFeldWerte[sel] = feldWert($el);
        }
    });
});

function hatUngespeicherteAenderung() {
    return ueberwachteFelder.some(function(sel){
        var $el = $(sel);
        if (!$el.length || !(sel in originalFeldWerte)) return false;
        return feldWert($el) !== originalFeldWerte[sel];
    });
}

function autoRefreshData() {
    if (hatUngespeicherteAenderung()) {
        // Aktueller Wert weicht vom DB-Stand ab - Reload überspringen, in 60s erneut prüfen
        return;
    }
    refreshData();
}
setInterval(autoRefreshData, 60000);

// ===================================
// Zähler-Reset Logik 
// ===================================
$(document).ready(function(){
$('#btnResetCounter').click(function(){
    var cp_id = new URLSearchParams(window.location.search).get('cp_id') || '<?php echo htmlspecialchars($selected_charge_point_id ?? ''); ?>';

    if (!cp_id) {
        alert("Fehler: Die Charge Point ID ist leer.");
        return;
    }

    if (!confirm("Wollen Sie den Ladezähler (Geladene kWh) für " + cp_id + " wirklich auf 0 zurücksetzen?")) {
        return;
    }

    $.ajax({
        url: "<?php echo $API_PUBLIC; ?>/reset_counter",
        method: "GET", // Wichtig: GET nutzen
        data: { charge_point_id: cp_id },
        dataType: 'json',
        success: function(response){
            console.log("Erfolg!");
            refreshData();
        },
        error: function(xhr, status, err) {
            // Falls es immer noch 'error' anzeigt, schauen wir in die Konsole
            console.error("Apache-Fehler:", status, err);
            refreshData();
        }
    });
});
});

</script>
