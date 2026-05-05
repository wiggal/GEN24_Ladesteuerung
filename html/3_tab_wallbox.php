<?php
// ================================================
// Wattpilot OCPP Control – Single File PHP UI (angepasst: Kein Fallback-ID, DB-Werte immer anzeigen)
// Erweiterung: zusätzliche Wallbox-Parameter (IDs 2 und 3) editierbar und in DB speicherbar
// Änderungen: Details-Bereich "Mehr Optionen" behält manuell gesetzten geöffnet/geschlossen-Status in localStorage
// ================================================
// Erkennt automatisch die IP des Servers (z.B. 192.168.178.4)
$server_ip = $_SERVER['HTTP_HOST'];
// Falls HTTP_HOST auch den Port enthält (z.B. :80), filtern wir nur die IP/Domain
$server_ip = explode(':', $server_ip)[0];
$API = "http://" . $server_ip . ":8886";
$SERVER_PID_FILE = "/tmp/ocpp_server.pid";
$PYTHON_SERVER_CMD = "cd ..; nohup python3 -u ocpp_server.py > /tmp/ocpp.log 2>&1 & echo $!";

include 'SQL_steuerfunctions.php';
require_once '3_funktion_wallbox.php';

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

// Bestehende ID=1 (bestehende Einstellungen)
$pv_mode = $EV_Reservierung['1']['Res_Feld1'] ?? 0;
$phases  = $EV_Reservierung['1']['Res_Feld2'] ?? 1;
$amp_options = $EV_Reservierung['1']['Options'] ?? '6,16';
list($amp_min, $amp_max) = array_map('trim', explode(",", $amp_options . ","));

// Neue Einstellungen ID=2
$min_phase_duration_s = $EV_Reservierung['2']['Res_Feld1'] ?? 180;       // MIN_PHASE_DURATION_S
$min_charge_duration_s = $EV_Reservierung['2']['Res_Feld2'] ?? 600;       // MIN_CHARGE_DURATION_S
$auto_sync_interval   = $EV_Reservierung['2']['Options']    ?? 20;        // AUTO_SYNC_INTERVAL

// Neue Einstellungen ID=3
$residualPower        = $EV_Reservierung['3']['Res_Feld1'] ?? -300;      // residualPower (Watt)
$default_target_kwh   = $EV_Reservierung['3']['Res_Feld2'] ?? 0.0;        // DEFAULT_TARGET_KWH
$phase_change_confirm_s = $EV_Reservierung['3']['Options'] ?? 30;        // PHASE_CHANGE_CONFIRM_S

// Neue Einstellungen ID=4 (Ladezeiten)
$ladezeit_von = $EV_Reservierung['4']['Res_Feld1'] ?? "12:00";
$ladezeit_bis = $EV_Reservierung['4']['Res_Feld2'] ?? "05:00";
$max_leistung_ha = $EV_Reservierung['4']['Options'] ?? "-0.1";

// Neue Einstellungen ID=5 (Preise)
$strompreis_fest = $EV_Reservierung['5']['Res_Feld1'] ?? 0.30;
$einspeise_verg  = $EV_Reservierung['5']['Res_Feld2'] ?? 0.07;

// -------------------------
// AJAX poll
// -------------------------
if (isset($_GET['ajax'])) {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'server_running' => $server_running,
        'pid' => $server_running && file_exists($SERVER_PID_FILE) ? intval(@file_get_contents($SERVER_PID_FILE)) : null,
        'connected_list' => array_values($connected_list),
        'client_connected' => $client_connected,
        'meter_values' => $meter_values ?? new stdClass(),
        'charge_point_id' => $selected_charge_point_id,
        'timestamp' => time()
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
<?php
  $current_url = urlencode($_SERVER['REQUEST_URI']);
  $hilfe_link = "index.php?tab=Hilfe&file={$activeTab}";
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
            <select id="chargePointSelect" onchange="window.location.href='<?php echo $_SERVER['PHP_SELF']; ?>?cp_id=' + this.value">
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
            <button class="ocpp green" id="btnStartServer">Server starten</button></form>
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
$diff = abs($Q_final - $Z_final);

// Differenz und neue Werte als data-Attribute ausgeben — JavaScript entscheidet anhand localStorage
echo "<div id=\"loadbar-container\" data-diff=\"{$diff}\" data-html=\"" . htmlspecialchars($html_neu) . "\">";
echo $html_neu;
echo "</div>";
?>
<div class="card">
    <div class="wallboxwerte">
    <?php if ($client_connected): ?>
        <p>Wallboxwerte(0A=AUS): <strong id="currentAmp"><?php echo htmlspecialchars($meter_values['current_limit'] ?? '—'); 
            echo 'A / ';
            echo htmlspecialchars($meter_values['phases'] ?? '—'); 
            echo 'PH / ';
            echo htmlspecialchars($meter_values['phases'] * $meter_values['current_limit'] * 230 / 1000); ?>kW</strong></p>
        <p>Ladedauer (Std:Min:Sek): <strong><?php echo gmdate("H:i:s", intval($meter_values['charging_duration_s'] ?? 0)); ?></strong></p>
        <p>Geladene kWh: <strong><?php echo htmlspecialchars($meter_values['charged_energy_kwh'] ?? 0); ?></strong>
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
        </details>
        <hr>
        <details id="moreOptions">
            <summary><b>Erweiterte Optionen:</b></summary>

        <div class="row">
            <span class="label-inline">Wallboxaktualisierung(s) (DB=<?php echo htmlspecialchars($auto_sync_interval); ?>):</span>
            <span class="input-inline"><input id="autoSyncInterval" type="number" min="10" step="10" value="<?php echo htmlspecialchars($auto_sync_interval); ?>"></span>
        </div>

        <div class="row">
            <span class="label-inline">Phasen-Intervall(s) (DB=<?php echo htmlspecialchars($min_phase_duration_s); ?>):</span>
            <span class="input-inline"><input id="minPhaseDur" type="number" min="60" step="60" value="<?php echo htmlspecialchars($min_phase_duration_s); ?>"></span>
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
// --- FUNKTIONEN ZUM SPEICHERN/LADEN MIT localStorage ---

function saveToLocalStorage(id) {self.Netzbezug
    var el = $('#' + id);
    if (el.length) localStorage.setItem(id, el.val());
}

function loadFromLocalStorage(id) {
    var storedValue = localStorage.getItem(id);
    if (storedValue !== null) {
        $('#' + id).val(storedValue);
    }
}

$(document).ready(function(){
    // IDs, die wir im localStorage zwischenhalten möchten
    var ls_ids = ['pvMode','phases','ampMin','ampMax','autoSyncInterval','minPhaseDur','minChargeDur','phaseChangeConfirm','residualPower','defaultTargetKwh', 'MaxLeistHAkW'];

    // Load saved values
    ls_ids.forEach(function(id){ loadFromLocalStorage(id); });

    // Save on change
    ls_ids.forEach(function(id){ 
        $('#' + id).on('change input', function(){ saveToLocalStorage(id); });
    });

    // --- Logik für Next Trip Optionen Sichtbarkeit ---
    function toggleNextTripVisibility() {
        var selectedMode = $('#pvMode').val();
        var nextTripDetails = document.getElementById('nextTripOptions');

        if (selectedMode === '4') { // '4' ist NextTrip
            nextTripDetails.setAttribute('open', 'open');
        } else {
            nextTripDetails.removeAttribute('open');
        }
    }

    // Bei Änderung des PV-Modus umschalten
    $('#pvMode').on('change', toggleNextTripVisibility);

    // --- Bestehende Logik für "Erweiterte Optionen" (moreOptions) ---
    // Diese bleibt unverändert, da sie bereits den User-Status via localStorage speichert
    var moreOptionsKey = 'moreOptionsOpen';
    var moreOptionsEl = document.getElementById('moreOptions');
    if (moreOptionsEl) {
        var stored = localStorage.getItem(moreOptionsKey);
        if (stored === '1') {
            moreOptionsEl.setAttribute('open', 'open');
        } else {
            moreOptionsEl.removeAttribute('open');
        }
        moreOptionsEl.addEventListener('toggle', function(){
            localStorage.setItem(moreOptionsKey, this.open ? '1' : '0');
        });
    }

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
            } else {
                nextTripDetails.removeAttribute('open');
            }
        }
    }

    // Sofort beim Laden der Seite ausführen
    updateNextTripVisibility();

    // Bei jeder Änderung des PV-Modus-Dropdowns ausführen
    $('#pvMode').on('change', function() {
        updateNextTripVisibility();
    });
    // =========================================================================

    $('#btnSave').click(function(){
    // --- Daten sammeln ---

    // ID 1: Basis-Einstellungen
    var pv_mode = $('#pvMode').val();
    var phases = $('#phases').val();
    var amp_min = $('#ampMin').val();
    var amp_max = $('#ampMax').val();

    // ID 2: Zeitintervalle
    var auto_sync_interval = $('#autoSyncInterval').val();
    var min_phase_dur = $('#minPhaseDur').val();
    var min_charge_dur = $('#minChargeDur').val();

    // ID 3: Leistung & Target
    var phase_change_confirm = $('#phaseChangeConfirm').val();
    var residual_power = $('#residualPower').val();
    var default_target_kwh = $('#defaultTargetKwh').val();

    // ID 4: Next Trip Zeiten (aus Grafik)
    var lz_von = $('#ladezeitVon').val();
    var lz_bis = $('#ladezeitBis').val();
    var max_leistung_ha = $('#MaxLeistHAkW').val();

    // ID 5: Preise (aus Grafik)
    var s_preis = $('#strompreisFest').val();
    var e_verg  = $('#einspeiseVerg').val();

    // --- AJAX Request ---
    $.ajax({
        url: "SQL_speichern.php",
        method: "post",
        data: {
            // Die Arrays müssen exakt gleich lang sein (5 Einträge)
            ID:         ["1", "2", "3", "4", "5"],
            Schluessel: ["wallbox", "wallbox", "wallbox", "wallbox", "wallbox"],
            Tag_Zeit:   ["1", "2", "3", "4", "5"],

            // Zuordnung Res_Feld1
            Res_Feld1: [
                pv_mode,           // ID 1
                min_phase_dur,     // ID 2
                residual_power,    // ID 3
                lz_von,            // ID 4
                s_preis            // ID 5
            ],

            // Zuordnung Res_Feld2
            Res_Feld2: [
                phases,            // ID 1
                min_charge_dur,    // ID 2
                default_target_kwh,// ID 3
                lz_bis,            // ID 4
                e_verg             // ID 5
            ],

            // Zuordnung Options
            Options: [
                amp_min + "," + amp_max, // ID 1
                auto_sync_interval,      // ID 2
                phase_change_confirm,    // ID 3
                max_leistung_ha,         // ID 4
                ""                       // ID 5
            ]
        },
        success: function(response){
            // LocalStorage aufräumen, damit beim Refresh die neuen DB-Werte geladen werden
            var ls_ids = [
                'pvMode','phases','ampMin','ampMax','autoSyncInterval',
                'minPhaseDur','minChargeDur','phaseChangeConfirm','residualPower',
                'defaultTargetKwh', 'ladezeitVon', 'ladezeitBis', 'strompreisFest', 'einspeiseVerg',
                'MaxLeistHAkW'
            ];

            ls_ids.forEach(function(id){
                localStorage.removeItem(id);
            });

            // Seite neu laden (mit Scroll-Position-Erhalt durch deinen bestehenden Listener)
            refreshData();
        },
        error: function(xhr, status, err) {
            alert("Fehler beim Speichern in die Datenbank: " + err);
        }
     });
    });
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
// Ladebalken-Cache via localStorage
// ===================================
(function() {
    var container = document.getElementById('loadbar-container');
    if (!container) return;

    var diff = parseFloat(container.dataset.diff);
    var htmlNeu = container.dataset.html;

    if (diff <= 0.3) {
        // Plausibel → als letzten gültigen Stand speichern
        localStorage.setItem('loadbar_cache', htmlNeu);
    } else {
        // Abweichung zu groß → gecachten Stand wiederherstellen
        var cached = localStorage.getItem('loadbar_cache');
        if (cached) {
            container.innerHTML = cached;
        }
    }
})();

// ===================================
// Einfaches Neuladen der Seite
// ===================================
function refreshData() {
    var current_cp_id = "<?php echo htmlspecialchars($selected_charge_point_id ?? ''); ?>";

    // Wir bauen die URL nur mit der Charge Point ID zusammen
    var url = window.location.pathname + "?tab=Wallbox";
    if (current_cp_id) {
        url += '&cp_id=' + encodeURIComponent(current_cp_id);
    }

    // Einfaches Neuladen per GET (keine POST-Felder mehr nötig)
    window.location.href = url;
}

// ===================================
// Automatisches Neuladen
// ===================================
// Die benannte Funktion wird alle 20 Sekunden ausgeführt
setInterval(refreshData, 15000); // 20000 ms = 20 Sekunden

// ===================================
// Zähler-Reset Logik 
// ===================================
$('#btnResetCounter').click(function(){
    var cp_id = '<?php echo htmlspecialchars($selected_charge_point_id ?? ''); ?>';

    if (!cp_id) {
        alert("Fehler: Die Charge Point ID ist leer.");
        return;
    }

    if (!confirm("Wollen Sie den Ladezähler (Geladene kWh) für " + cp_id + " wirklich auf 0 zurücksetzen?")) {
        return;
    }

    $.ajax({
        url: "<?php echo $API; ?>/reset_counter",
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

</script>
