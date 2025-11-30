<?php
// ================================================
// Wattpilot OCPP Control – Single File PHP UI (angepasst: Kein Fallback-ID, DB-Werte immer anzeigen)
// ================================================

$API = "http://127.0.0.1:8080"; // OCPP Server API
$SERVER_PID_FILE = "/tmp/ocpp_server.pid";
$PYTHON_SERVER_CMD = "cd ..; nohup python3 -u ocpp_server.py > /tmp/ocpp.log 2>&1 & echo $!";

include 'SQL_steuerfunctions.php';

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
    $redirect_url = $_SERVER['PHP_SELF'];
    if (isset($_POST['cp_id']) && !empty($_POST['cp_id'])) {
        $redirect_url .= '?cp_id=' . $_POST['cp_id'];
    }
    
    header('Location: ' . $redirect_url);
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
// Die Werte aus dem Unterarray auslesen
$pv_mode = $EV_Reservierung['1']['Res_Feld1'] ?? 0;
$phases  = $EV_Reservierung['1']['Res_Feld2'] ?? 1;
$amp_options = $EV_Reservierung['1']['Options'] ?? '6,6';
list($amp_min, $amp_max) = explode(",", $amp_options);

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
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Wattpilot – OCPP Steuerung</title>
<style>
body{font-family:Arial;background:white;padding:20px;}
.card{background:white;padding:20px;margin-bottom:20px;border-radius:8px;}
button { padding: 6px 12px; font-size: 14px; font-size: 1.3em; background-color: #4CAF50; }
select { font-size: 1.1em; background-color: #F5F5DC; }
.red{background:#d9534f;}
.green{background:#5cb85c;}
.info{background:#e9f7ef;padding:10px;border-radius:6px;margin-bottom:10px;}
.small{font-size:0.9em;color:#666;}
form { display: inline-block; margin-right:6px; }
p, label { color:#000000; font-family:Arial; font-size: 150%; padding:2px 1px; }
.status-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;vertical-align:middle;}
</style>
</head>
<body>
<h1>Wattpilot – OCPP Steuerung</h1>

<div class="card">
    <h2>Python OCPP Server</h2>
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
            **OCPP Client auswählen:**
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
            <form method="post"><input type="hidden" name="action" value="stop_server"><button class="red" id="btnStopServer">Server stoppen</button></form>
        <?php else: ?>
            <form method="post"><input type="hidden" name="action" value="start_server"><button class="green" id="btnStartServer">Server starten</button></form>
        <?php endif; ?>
    </div>
</div>

<div class="card">
    <h2>Optionen konfigurieren (DB-Werte) <?php if ($client_connected) echo 'für Client: ' . htmlspecialchars($selected_charge_point_id); ?></h2>
    
    <?php if ($client_connected): ?>
        <p>Stromstärke Wallbox (0=AUS): <strong id="currentAmp"><?php echo htmlspecialchars($meter_values['current_limit'] ?? '—'); ?> A</strong></p>
        <p>Aktive Phasen Wallbox:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong id="currentPhases"><?php echo htmlspecialchars($meter_values['phases'] ?? '—'); ?></strong></p>
        <p>Ladedauer in Std:Min:Sek: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong id="currentPhases"><?php echo gmdate("H:i:s", htmlspecialchars($meter_values['charging_duration_s'] ?? 0)); ?></strong></p>
        <hr>
    <?php else: ?>
        <p class="small">Live-Daten der Wallbox (Aktuelle Stromstärke/Phasen) sind nur sichtbar, wenn ein Client verbunden ist.</p>
    <?php endif; ?>

    <form id="formOptions">
        <input type="hidden" id="selectedCpId" name="cp_id" value="<?php echo htmlspecialchars($selected_charge_point_id ?? ''); ?>">
        
        <label>PV-Modus (DB=<?php echo($pv_mode); ?>):
            <select id="pvMode" name="pv_mode">
                <option value="0" <?php if($pv_mode=='0') echo 'selected'; ?>>Aus</option>
                <option value="1" <?php if($pv_mode=='1') echo 'selected'; ?>>PV</option>
                <option value="2" <?php if($pv_mode=='2') echo 'selected'; ?>>MIN+PV</option>
                <option value="3" <?php if($pv_mode=='3') echo 'selected'; ?>>MAX</option>
            </select>
        </label>
        <label>Phasen (DB=<?php echo($phases); ?>):
            <select id="phases" name="phases">
                <option value="0" <?php if($phases=='0') echo 'selected'; ?>>Auto</option>
                <option value="1" <?php if($phases=='1') echo 'selected'; ?>>1 Phase</option>
                <option value="3" <?php if($phases=='3') echo 'selected'; ?>>3 Phasen</option>
            </select>
        </label>
        <br><br><br>
        <label>Stromstärke MIN (DB=<?php echo($amp_min); ?>):
            <select id="ampMin" name="amp_min">
                <?php for($i=6;$i<=16;$i++): ?>
                    <option value="<?php echo $i; ?>" <?php if($i==$amp_min) echo 'selected'; ?>><?php echo $i; ?> A</option>
                <?php endfor; ?>
            </select>
        </label>
        <label>Stromstärke MAX (DB=<?php echo($amp_max); ?>):
            <select id="ampMax" name="amp_max">
                <?php for($i=6;$i<=16;$i++): ?>
                    <option value="<?php echo $i; ?>" <?php if($i==$amp_max) echo 'selected'; ?>><?php echo $i; ?> A</option>
                <?php endfor; ?>
            </select>
        </label>
        <br><br>
        <button type="button" id="btnSave" class="green">Speichern</button>
        <p class="small">Diese Einstellungen werden in der SQLite-Datenbank gespeichert und von der Steuerung (ocpp_server.py) verwendet, um OCPP-Befehle an die Wallbox zu senden.</p>
    </form>
</div>

<script src="jquery.min.js"></script>
<script>
// Einträge Prog_Steuerung.sqlite
//ID,Schluessel,Zeit,Res_Feld1,Res_Feld2,Options
//  ,          ,    ,PV-Modus ,Phasen   ,A-MIN;MAX
//1 ,   wallbox,  1 ,AUS=0    ,AUTO=0   ,6,16
//  ,          ,    ,PV=1     ,1        ,
//  ,          ,    ,MIN+PV=2 ,3        ,
//  ,          ,    ,MAX=3    ,         ,

// --- FUNKTIONEN ZUM SPEICHERN/LADEN MIT localStorage ---

// Speichert den aktuellen Wert eines Select-Elements im localStorage
function saveToLocalStorage(id) {
    localStorage.setItem(id, $('#' + id).val());
}

// Lädt den Wert aus dem localStorage und setzt ihn im Select-Element,
// wenn ein gespeicherter Wert existiert.
function loadFromLocalStorage(id) {
    var storedValue = localStorage.getItem(id);
    if (storedValue !== null) {
        $('#' + id).val(storedValue);
    }
}

$(document).ready(function(){
    
    // 1. Dropdown-Werte aus localStorage laden, um Änderungen beim Reload zu erhalten
    loadFromLocalStorage('pvMode');
    loadFromLocalStorage('phases');
    loadFromLocalStorage('ampMin');
    loadFromLocalStorage('ampMax');
    
    // 2. Event-Listener hinzufügen, um Änderungen sofort im localStorage zu speichern
    $('#pvMode').on('change', function() { saveToLocalStorage('pvMode'); });
    $('#phases').on('change', function() { saveToLocalStorage('phases'); });
    $('#ampMin').on('change', function() { saveToLocalStorage('ampMin'); });
    $('#ampMax').on('change', function() { saveToLocalStorage('ampMax'); });


    $('#btnSave').click(function(){
        var amp_min = $('#ampMin').val();
        var amp_max = $('#ampMax').val();
        var phases = $('#phases').val();
        var pv_mode = $('#pvMode').val();
        var cp_id = $('#selectedCpId').val(); // Ausgewählte Client-ID (kann leer sein)

        $.ajax({
            url: "SQL_speichern.php",
            method: "post",
            data: {
                ID: ["1"], // Speichern auf dem festen Eintrag 1
                Schluessel: ["wallbox"], 
                Tag_Zeit: ["1"],
                Res_Feld1: [pv_mode],
                Res_Feld2: [phases],
                Options: [amp_min + "," + amp_max]
            },
            success: function(data){
                // WICHTIG: NACH ERFOLGREICHEM SPEICHERN DIE LOKALEN WERTE LÖSCHEN
                // damit beim nächsten Neuladen die NEUEN DB-Werte angezeigt werden.
                localStorage.removeItem('pvMode');
                localStorage.removeItem('phases');
                localStorage.removeItem('ampMin');
                localStorage.removeItem('ampMax');

                // Nach dem Speichern auf die Seite des ausgewählten Clients neu laden
                var redirect_url = '<?php echo $_SERVER['PHP_SELF']; ?>';
                if (cp_id) {
                     redirect_url += '?cp_id=' + cp_id;
                }
                location.href = redirect_url; 
            }
        });
    });
});
</script>
<script>
// Seite alle 30 Sekunden automatisch neu laden (Behält die Client-ID bei, falls gesetzt)
setInterval(function() {
    var current_cp_id = "<?php echo htmlspecialchars($selected_charge_point_id ?? ''); ?>";
    var reload_url = '<?php echo $_SERVER['PHP_SELF']; ?>';
    if (current_cp_id) {
        reload_url += '?cp_id=' + current_cp_id;
    }
    window.location.href = reload_url;
}, 10000); // 10000 ms = 10 Sekunden
</script>


</body>
</html>
