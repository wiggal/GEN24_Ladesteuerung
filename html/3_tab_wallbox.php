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
    $redirect_url = $_SERVER['PHP_SELF'] . '?tab=Wallbox'; // NEU: Tab hier fest anfügen
    if (isset($_POST['cp_id']) && !empty($_POST['cp_id'])) {
        $redirect_url .= '?cp_id=' . $_POST['cp_id'];
    }
    
    // header('Location: ' . $redirect_url);
    // NEU (funktioniert auch nach HTML-Ausgabe)
    echo "<script type='text/javascript'>window.location.href='{$redirect_url}';</script>";
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
    font-family: Arial;
    background: white;
}

.card {
    background: white;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 8px;
}

.card h2 { margin-bottom: 6px; }
.card p { margin: 4px 0; line-height: 1.1; }

button.ocpp {
    padding: 6px 12px;
    font-size: 14px;
    background-color: #4CAF50;
    color: white;
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
    font-family: Arial;
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
    font-family: sans-serif;
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
// Aktuelle Live-Werte berechnen
$solar_current   = round(($meter_values['Produktion_W'] ?? 0) / 1000, 1);
$battery_current = round(($meter_values['Batteriebezug_W'] ?? 0) / 1000, 1);
$grid_current    = round(($meter_values['Netzbezug_W'] ?? 0) / 1000, 1);
$wallbox_Ampere  = ($meter_values['current_limit'] ?? 0);
$wallbox_Phase   = ($meter_values['phases'] ?? 0);
$car_power       = round((($wallbox_Ampere * $wallbox_Phase * 230) / 1000), 1);
$Hausverbrauch   = round(($meter_values['Hausverbrauch'] ?? 0) / 1000, 1);

// Neue Berechnung der Bar
[ $html, $Q_new, $Z_new ] = generateLoadBar($solar_current, $battery_current, $grid_current, $car_power, $Hausverbrauch);

$QZnew_Diff = abs($Q_new - $Z_new); 

// Wenn Abweichung zu groß, wegen zeitlich versetzten Werten, generiere Bar mit den alten Werten aus dem POST
// Prüfen, ob alte Werte per POST übergeben wurden
if ($QZnew_Diff > 0.2 or $Hausverbrauch <= 0) {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['old_Q'], $_POST['old_Z'])) {
        $solar_current   = floatval($_POST['old_solar']);
        $battery_current = floatval($_POST['old_batt']);
        $grid_current    = floatval($_POST['old_grid']);
        $car_power     = floatval($_POST['old_total']);
        $Hausverbrauch   = floatval($_POST['old_haus']);
        // Neue Berechnung der Bar
        [ $html, $Q_new, $Z_new ] = generateLoadBar($solar_current, $battery_current, $grid_current, $car_power, $Hausverbrauch);
    }
}
echo $html;  # Balkendiagramm ausgeben

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

        <hr>
        <details id="moreOptions">
            <summary><b>Erweiterte Optionen:</b></summary>
        <h3>Timing Einstellungen:</h3>

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

        <hr>
        <h3>Sonstige Zielwerte:</h3>

        <div class="row">
            <span class="label-inline">Verbleibende Leistung(W) (DB=<?php echo htmlspecialchars($residualPower); ?>):</span>
            <span class="input-inline"><input id="residualPower" type="number" step="100" value="<?php echo htmlspecialchars($residualPower); ?>"></span>
        </div>

        <div class="row">
            <span class="label-inline">Lademenge(kWh) (DB=<?php echo htmlspecialchars($default_target_kwh); ?>):</span>
            <span class="input-inline"><input id="defaultTargetKwh" type="number" step="1" min="0" value="<?php echo htmlspecialchars($default_target_kwh); ?>"></span>
        </div>

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
    var ls_ids = ['pvMode','phases','ampMin','ampMax','autoSyncInterval','minPhaseDur','minChargeDur','phaseChangeConfirm','residualPower','defaultTargetKwh'];

    // Load saved values
    ls_ids.forEach(function(id){ loadFromLocalStorage(id); });

    // Save on change
    ls_ids.forEach(function(id){ 
        $('#' + id).on('change input', function(){ saveToLocalStorage(id); });
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

    $('#btnSave').click(function(){
        var amp_min = $('#ampMin').val();
        var amp_max = $('#ampMax').val();
        var phases = $('#phases').val();
        var pv_mode = $('#pvMode').val();
        var cp_id = $('#selectedCpId').val(); // Ausgewählte Client-ID (kann leer sein)

        // Neue Parameter (ID=2)
        var auto_sync_interval = $('#autoSyncInterval').val();
        var min_phase_dur = $('#minPhaseDur').val();
        var min_charge_dur = $('#minChargeDur').val();

        // Neue Parameter (ID=3)
        var phase_change_confirm = $('#phaseChangeConfirm').val();
        var residual_power = $('#residualPower').val();
        var default_target_kwh = $('#defaultTargetKwh').val();

        $.ajax({
            url: "SQL_speichern.php",
            method: "post",
            data: {
                ID: ["1","2","3"],
                Schluessel: ["wallbox","wallbox","wallbox"],
                Tag_Zeit: ["1","2","3"],
                // Res_Feld1 for each ID:
                // ID=1 -> pv_mode
                // ID=2 -> MIN_PHASE_DURATION_S
                // ID=3 -> residualPower
                Res_Feld1: [pv_mode, min_phase_dur, residual_power],
                // Res_Feld2 for each ID:
                // ID=1 -> phases
                // ID=2 -> MIN_CHARGE_DURATION_S
                // ID=3 -> DEFAULT_TARGET_KWH
                Res_Feld2: [phases, min_charge_dur, default_target_kwh],
                // Options for each ID:
                // ID=1 -> amp_min,amp_max
                // ID=2 -> AUTO_SYNC_INTERVAL
                // ID=3 -> PHASE_CHANGE_CONFIRM_S
                Options: [amp_min + "," + amp_max, auto_sync_interval, phase_change_confirm]
            },
            success: function(data){
                // Nach erfolgreichem Speichern die lokalen Werte löschen,
                // damit beim nächsten Neuladen die NEUEN DB-Werte angezeigt werden.
                ls_ids.forEach(function(id){ localStorage.removeItem(id); });

                // Hinweis: Den Zustand von "Mehr Optionen" NICHT löschen, damit Benutzer-Einstellung erhalten bleibt.

                // Nach dem Speichern auf die Seite des ausgewählten Clients neu laden
                refreshData();
            },
            error: function(xhr, status, err) {
                alert("Fehler beim Speichern: " + err);
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
// Allgemeine Funktion zum Neuladen mit POST-Feldern
// ===================================
function refreshData() {
    var current_cp_id = "<?php echo htmlspecialchars($selected_charge_point_id ?? ''); ?>";

    var form = $('<form method="post"></form>');
    var url = window.location.pathname + (current_cp_id ? '?cp_id=' + encodeURIComponent(current_cp_id) : '');
    form.attr("action", url);

    // PHP-Variablen direkt im JS zugewiesen
    var params = {
        'tab': 'Wallbox',   // damit index weiß von welchem TAB der reload kam
        'old_Q': '<?php echo $Q_new; ?>',
        'old_Z': '<?php echo $Z_new; ?>',
        'old_solar': '<?php echo $solar_current; ?>',
        'old_batt': '<?php echo $battery_current; ?>',
        'old_grid': '<?php echo $grid_current; ?>',
        'old_total': '<?php echo $car_power; ?>',
        'old_haus': '<?php echo $Hausverbrauch; ?>'
    };

    $.each(params, function(key, value) {
        form.append($('<input type="hidden">').attr("name", key).attr("value", value));
    });

    $(document.body).append(form);
    form.submit();
}

// ===================================
// Automatisches Neuladen
// ===================================
// Die benannte Funktion wird alle 20 Sekunden ausgeführt
setInterval(refreshData, 20000); // 20000 ms = 20 Sekunden

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
