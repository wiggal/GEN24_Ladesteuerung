<?php
// ================================================
// Wattpilot OCPP Control – Single File PHP UI (angepasst)
// ================================================

$API = "http://127.0.0.1:8080"; // OCPP Server API
$SERVER_PID_FILE = "/tmp/ocpp_server.pid";
$PYTHON_SERVER_CMD = "nohup python3 ../FUNCTIONS/ocpp_legacy_server.py > /tmp/ocpp.log 2>&1 & echo $!";
$CHARGE_POINT_ID = "32162088";

include 'SQL_steuerfunctions.php';

// -------------------------
// Helper Functions
// -------------------------
function server_is_running($pidfile) {
    if (!file_exists($pidfile)) return false;
    $pid = intval(@file_get_contents($pidfile));
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
        $pid = shell_exec($GLOBALS['PYTHON_SERVER_CMD']);
        file_put_contents($GLOBALS['SERVER_PID_FILE'], trim($pid));
    }

    if ($action === 'stop_server') {
        if (file_exists($GLOBALS['SERVER_PID_FILE'])) {
            $pid = intval(@file_get_contents($GLOBALS['SERVER_PID_FILE']));
            if ($pid > 0) {
                if (function_exists('posix_kill')) {
                    @posix_kill($pid, 9);
                } else {
                    @shell_exec("kill -9 $pid");
                }
            }
            @unlink($GLOBALS['SERVER_PID_FILE']);
        }
    }

    // API calls (optional, falls gewünscht)
    if ($action === 'set_amp') api_post('/set_charging_profile', ['charge_point_id'=>$CHARGE_POINT_ID,'amp_min'=>intval($_POST['amp_min']),'amp_max'=>intval($_POST['amp_max'])]);
    if ($action === 'set_phases') api_post('/set_charging_profile', ['charge_point_id'=>$CHARGE_POINT_ID,'phases'=>$_POST['phases']]);
    if ($action === 'set_pv_mode') api_post('/set_pv_mode', ['charge_point_id'=>$CHARGE_POINT_ID,'mode'=>$_POST['pv_mode']]);

    header('Location: ' . $_SERVER['PHP_SELF']);
    exit;
}

// -------------------------
// Fetch Status Data
// -------------------------
$server_running = server_is_running($SERVER_PID_FILE);
$status = null;
$meter_values = null;

if ($server_running) {
    $status_json = @file_get_contents($API . "/list");
    $status = $status_json ? @json_decode($status_json, true) : null;

    $meter_values_json = @file_get_contents($API . "/meter_values?charge_point_id=$CHARGE_POINT_ID");
    $meter_values = $meter_values_json ? @json_decode($meter_values_json, true) : null;
}

// Connected client check
$connected_list = [];
if (is_array($status)) {
    if (isset($status['connected']) && is_array($status['connected'])) {
        $connected_list = $status['connected'];
    } else {
        $connected_list = $status;
    }
}
$client_connected = in_array($CHARGE_POINT_ID, $connected_list, true);

// -------------------------
// DB: Werte laden
// -------------------------
$EV_Reservierung = getSteuercodes('wallbox');
// Die Werte aus dem Unterarray auslesen
$pv_mode = $EV_Reservierung['1']['Res_Feld1'];
$phases = $EV_Reservierung['1']['Res_Feld2'];
list($amp_min, $amp_max) = explode(",", $EV_Reservierung['1']['Options']);

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
        'charge_point_id' => $CHARGE_POINT_ID,
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
body{font-family:Arial;background:#f2f2f2;padding:20px;}
.card{background:white;padding:20px;margin-bottom:20px;border-radius:8px;}
button{padding:10px 20px;border:none;background:#007bff;color:white;border-radius:6px;cursor:pointer;margin-right:10px;}
button[disabled]{opacity:0.5;cursor:not-allowed;}
.red{background:#d9534f;}
.green{background:#5cb85c;}
.info{background:#e9f7ef;padding:10px;border-radius:6px;margin-bottom:10px;}
.small{font-size:0.9em;color:#666;}
form { display: inline-block; margin-right:6px; }
pre{background:#f8f8f8;padding:10px;border-radius:6px;overflow:auto;max-height:300px;}
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
    <p id="clientStatus" class="small">
        <?php if ($client_connected): ?>
            <span class="status-dot" style="background:green"></span>
            <strong style="color:green">OCPP-Client <?php echo htmlspecialchars($CHARGE_POINT_ID); ?>: Verbunden</strong>
        <?php else: ?>
            <span class="status-dot" style="background:red"></span>
            <strong style="color:red">OCPP-Client <?php echo htmlspecialchars($CHARGE_POINT_ID); ?>: Nicht verbunden</strong>
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
    <h2>Optionen konfigurieren</h2>
     <!-- Aktuelle Werte von der Wallbox -->
    <p>Aktuelle Stromstärke: <strong id="currentAmp"><?php echo htmlspecialchars($meter_values['current_limit'] ?? '—'); ?> A</strong></p>
    <p>Aktive Phasen: <strong id="currentPhases"><?php echo htmlspecialchars($meter_values['phases'] ?? '—'); ?></strong></p>

    <form id="formOptions">
        <label>PV-Modus:
            <select id="pvMode" name="pv_mode">
                <option value="0" <?php if($pv_mode=='0') echo 'selected'; ?>>Aus</option>
                <option value="1" <?php if($pv_mode=='1') echo 'selected'; ?>>PV</option>
                <option value="2" <?php if($pv_mode=='2') echo 'selected'; ?>>MIN+PV</option>
                <option value="3" <?php if($pv_mode=='3') echo 'selected'; ?>>MAX</option>
            </select>
        </label>
        <label>Phasen:
            <select id="phases" name="phases">
                <option value="0" <?php if($phases=='0') echo 'selected'; ?>>Auto</option>
                <option value="1" <?php if($phases=='1') echo 'selected'; ?>>1 Phase</option>
                <option value="3" <?php if($phases=='3') echo 'selected'; ?>>3 Phasen</option>
            </select>
        </label>
        <label>Stromstärke MIN:
            <select id="ampMin" name="amp_min">
                <?php for($i=6;$i<=16;$i++): ?>
                    <option value="<?php echo $i; ?>" <?php if($i==$amp_min) echo 'selected'; ?>><?php echo $i; ?> A</option>
                <?php endfor; ?>
            </select>
        </label>
        <label>Stromstärke MAX:
            <select id="ampMax" name="amp_max">
                <?php for($i=6;$i<=16;$i++): ?>
                    <option value="<?php echo $i; ?>" <?php if($i==$amp_max) echo 'selected'; ?>><?php echo $i; ?> A</option>
                <?php endfor; ?>
            </select>
        </label>
        <br><br>
        <button type="button" id="btnSave" class="green">Speichern</button>
    </form>
</div>

<script src="jquery.min.js"></script>
<script>
// Einträge Prog_Steuerung.sqlite
//ID,Schluessel,Zeit,Res_Feld1,Res_Feld2,Options
//  ,          ,    ,PV-Modus ,Phasen   ,A-MIN;MAX
//1 ,   wallbox,  1 ,AUS=0    ,AUTO=0   ,6,16
//  ,          ,    ,PV=1     ,1        ,
//  ,          ,    ,MIN+PV=2 ,3        ,
//  ,          ,    ,MAX=3    ,         ,
$(document).ready(function(){
    $('#btnSave').click(function(){
        var amp_min = $('#ampMin').val();
        var amp_max = $('#ampMax').val();
        var phases = $('#phases').val();
        var pv_mode = $('#pvMode').val();

        $.ajax({
            url: "SQL_speichern.php",
            method: "post",
            data: {
                ID: ["1"],
                Schluessel: ["wallbox"],
                Tag_Zeit: ["1"],
                Res_Feld1: [pv_mode],
                Res_Feld2: [phases],
                Options: [amp_min + "," + amp_max]
            },
            success: function(data){
                //alert("Optionen gespeichert!");
                location.reload();
            }
        });
    });
});
</script>
<script>
// Seite alle 30 Sekunden automatisch neu laden
setInterval(function() {
    location.reload();
}, 10000); // 10000 ms = 10 Sekunden
</script>


</body>
</html>

