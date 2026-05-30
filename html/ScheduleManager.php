<?php
// ================================================
// ScheduleManager – CronJob-Verwaltung, aufrufbar aus Settings-Tab
// Liest/schreibt Jobs aus der Tabelle cron_jobs in Prog_Steuerung.sqlite
// ================================================

include 'SQL_steuerfunctions.php';

// -------------------------
// DB-Pfad (analog zur restlichen App anpassen)
// -------------------------
# config.ini parsen
require_once "config_parser.php";

global $PythonDIR;
$DB_PATH = $PythonDIR.'/CONFIG/Prog_Steuerung.sqlite';
$GEN24_DIR = realpath(__DIR__ . '/' .$PythonDIR);

// -------------------------
// Helper: DB-Verbindung + Tabelle anlegen falls nicht vorhanden
// -------------------------
function get_db($path, $GEN24_DIR) {
    try {
        $db = new PDO('sqlite:' . $path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

        // Prüfen ob Tabelle bereits existiert
        $exists = $db->query("SELECT name FROM sqlite_master WHERE type='table' AND name='cron_jobs'")->fetchColumn();

        // Tabelle anlegen falls nicht vorhanden
        $db->exec("CREATE TABLE IF NOT EXISTS cron_jobs (
            ID             INTEGER PRIMARY KEY AUTOINCREMENT,
            Name           TEXT    NOT NULL,
            Minute         TEXT    NOT NULL DEFAULT '*',
            Stunde         TEXT    NOT NULL DEFAULT '*',
            Tag_Monat      TEXT    NOT NULL DEFAULT '*',
            Monat          TEXT    NOT NULL DEFAULT '*',
            Tag_Woche      TEXT    NOT NULL DEFAULT '*',
            Befehl         TEXT    NOT NULL,
            Aktiv          INT     NOT NULL DEFAULT 1,
            Letzter_Lauf   TEXT,
            Letzter_Status INT,
            Notiz          TEXT,
            Angelegt_Am    TEXT
        )");

        // Nur beim erstmaligen Anlegen: Vorschläge deaktiviert eintragen
        if (!$exists) {
            $now = date('Y-m-d H:i:s');
            $defaults = [
                ['EnergyController',          '1-56/5',  '*',                    '*','*','*', $GEN24_DIR.'/start_PythonScript.sh EnergyController.py logging',1,                                'EnergyController nur logging'],
                ['Forecast Solar WeatherData','33',       '5,8,10,12,14',        '*','*','*', $GEN24_DIR.'/start_PythonScript.sh FORECAST/Forecast_solar__WeatherData.py',1,                    'Solar-Wetterprognose'],
                ['Solarprognose WeatherData', '8',        '5,7,9,11,13,15',      '*','*','*', $GEN24_DIR.'/start_PythonScript.sh FORECAST/Solarprognose_WeatherData.py',0,                      'Solarprognose'],
                ['Solcast WeatherData',       '0',        '6,8,11,13,15',        '*','*','*', $GEN24_DIR.'/start_PythonScript.sh FORECAST/Solcast_WeatherData.py',0,                            'Solcast'],
                ['Akkudoktor WeatherData',    '0',        '5,7,9,11,13,15,17,19','*','*','*', $GEN24_DIR.'/start_PythonScript.sh FORECAST/Akkudoktor__WeatherData.py',0,                        'Akkudoktor'],
                ['OpenMeteo WeatherData',     '35',       '5,7,9,11,13,15,17,19','*','*','*', $GEN24_DIR.'/start_PythonScript.sh FORECAST/OpenMeteo_WeatherData.py',0,                          'OpenMeteo'],
                ['DynamicPriceCheck',         '58',       '*',                   '*','*','*', $GEN24_DIR.'/start_PythonScript.sh -o DynPriceCheck.log DynamicPriceCheck.py schreiben',0,        'Dynamische Strompreise'],
                ['Rotate Crontab.log',        '0',        '5',                   '*','*','1', 'mv '.$GEN24_DIR.'/Crontab.log '.$GEN24_DIR.'/old_Crontab.log',1,                                       'Log-Rotation Mo'],
                ['Rotate DynPriceCheck.log',  '0',        '5',                   '*','*','1', 'mv '.$GEN24_DIR.'/DynPriceCheck.log '.$GEN24_DIR.'/old_DynPriceCheck.log',0,                           'Log-Rotation DynPrice Mo'],
            ];
            $stmt = $db->prepare("INSERT INTO cron_jobs
                (Name, Minute, Stunde, Tag_Monat, Monat, Tag_Woche, Befehl, Aktiv, Notiz, Angelegt_Am)
                VALUES (?,?,?,?,?,?,?,?,?,?)");
            foreach ($defaults as $j) {
                $stmt->execute([$j[0],$j[1],$j[2],$j[3],$j[4],$j[5],$j[6],$j[7],$j[8],$now]);
            }
        }

        return $db;
    } catch (Exception $e) {
        return null;
    }
}

// -------------------------
// Handle Actions (POST)
// -------------------------
if (isset($_POST['action'])) {
    $action = $_POST['action'];
    $db = get_db($DB_PATH, $GEN24_DIR);

    if ($db) {
        // --- Job speichern (neu oder update) ---
        if ($action === 'save_job') {
            $id      = isset($_POST['job_id']) && $_POST['job_id'] !== '' ? intval($_POST['job_id']) : null;
            $name    = trim($_POST['Name']    ?? '');
            $minute  = trim($_POST['Minute']  ?? '*');
            $stunde  = trim($_POST['Stunde']  ?? '*');
            $tag_m   = trim($_POST['Tag_Monat'] ?? '*');
            $monat   = trim($_POST['Monat']   ?? '*');
            $tag_w   = trim($_POST['Tag_Woche'] ?? '*');
            $befehl  = trim($_POST['Befehl']  ?? '');
            $aktiv   = isset($_POST['Aktiv']) ? 1 : 0;
            $notiz   = trim($_POST['Notiz']   ?? '');

            if ($name !== '' && $befehl !== '') {
                if ($id === null) {
                    // Neuer Job
                    $stmt = $db->prepare("INSERT INTO cron_jobs
                        (Name, Minute, Stunde, Tag_Monat, Monat, Tag_Woche, Befehl, Aktiv, Notiz, Angelegt_Am)
                        VALUES (?,?,?,?,?,?,?,?,?, datetime('now','localtime'))");
                    $stmt->execute([$name, $minute, $stunde, $tag_m, $monat, $tag_w, $befehl, $aktiv, $notiz]);
                } else {
                    // Bestehenden Job updaten
                    $stmt = $db->prepare("UPDATE cron_jobs SET
                        Name=?, Minute=?, Stunde=?, Tag_Monat=?, Monat=?, Tag_Woche=?,
                        Befehl=?, Aktiv=?, Notiz=?
                        WHERE ID=?");
                    $stmt->execute([$name, $minute, $stunde, $tag_m, $monat, $tag_w, $befehl, $aktiv, $notiz, $id]);
                }
            }
        }

        // --- Job aktivieren/deaktivieren (Toggle) ---
        if ($action === 'toggle_job') {
            $id = intval($_POST['job_id'] ?? 0);
            $db->prepare("UPDATE cron_jobs SET Aktiv = CASE WHEN Aktiv=1 THEN 0 ELSE 1 END WHERE ID=?")
               ->execute([$id]);
        }

        // --- Job löschen ---
        if ($action === 'delete_job') {
            $id = intval($_POST['job_id'] ?? 0);
            $db->prepare("DELETE FROM cron_jobs WHERE ID=?")->execute([$id]);
        }
    }

    // Redirect zurück zum Tab
    echo "<script>window.location.href = window.location.pathname + '?tab=ScheduleManager';</script>";
    exit;
}

// -------------------------
// AJAX: Jobs als JSON liefern
// -------------------------
if (isset($_GET['ajax'])) {
    header('Content-Type: application/json; charset=utf-8');
    $db = get_db($DB_PATH, $GEN24_DIR);
    $jobs = [];
    if ($db) {
        $jobs = $db->query("SELECT * FROM cron_jobs ORDER BY ID")->fetchAll();
    }
    echo json_encode(['jobs' => $jobs, 'timestamp' => time()]);
    exit;
}

// -------------------------
// Jobs laden für HTML-Ausgabe
// -------------------------
$db   = get_db($DB_PATH, $GEN24_DIR);
$jobs = [];
if ($db) {
    $jobs = $db->query("SELECT * FROM cron_jobs ORDER BY ID")->fetchAll();
}
$db_ok = ($db !== null);

?>
<style>
/* --- Grundlayout (identisch zu Wallbox-Tab) --- */
body { background: white; }

.card {
    background: white;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 8px;
}
.card h2 { margin: 0px; }
.card p  { margin: 4px 0; line-height: 1.1; }

button.ocpp {
    padding: 6px 12px;
    font-size: 14px;
    background-color: #4CAF50;
    color: black;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
button.ocpp.red     { background: #d9534f; }
button.ocpp.orange  { background: #e8a838; }
button.ocpp.schreiben { position: sticky; bottom: 10px; }
button.ocpp:disabled { background-color: #ccc; color: #666; cursor: not-allowed; }

select,
input[type="number"],
input[type="text"] {
    font-size: 1.1em;
    background-color: #F5F5DC;
    padding: 4px;
    border-radius: 4px;
    border: 1px solid #ccc;
}

.info  { background: #e9f7ef; padding: 10px; border-radius: 6px; margin-bottom: 10px; }
.small { font-size: 0.9em; color: #666; }

p, label {
    color: #000;
    font-size: 120%;
    padding: 2px 1px;
    line-height: 1.1;
}

.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    vertical-align: middle;
}

.row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    gap: 8px;
}
.label-inline  { width: 200px; flex-shrink: 0; }
.input-inline  { flex: 1; }
.input-inline select,
.input-inline input { width: 100%; max-width: 400px; }

/* --- Jobtabelle --- */
.job-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 1em;
    margin-bottom: 10px;
}
.job-table th {
    background: #4CAF50;
    color: white;
    padding: 6px 8px;
    text-align: left;
    font-size: 0.95em;
}
.job-table td {
    padding: 5px 8px;
    border-bottom: 1px solid #ddd;
    vertical-align: middle;
    font-size: 0.95em;
}
.job-table tr:hover { background: #f9f9f9; }
.job-table tr.inaktiv td { color: #aaa; }

.cron-badge {
    font-family: monospace;
    background: #f0f0f0;
    border-radius: 3px;
    padding: 1px 4px;
    font-size: 0.85em;
}
.befehl-cell {
    max-width: 260px;
    word-break: break-all;
    font-size: 0.82em;
    font-family: monospace;
}
.btn-row { display: flex; gap: 4px; }

/* --- Formular-Card --- */
#formCard { display: none; }
#formCard.open { display: block; }

@media (max-width: 600px) {
    .label-inline { width: 140px; }
    .input-inline input,
    .input-inline select { max-width: 100%; }
    .job-table th:nth-child(4),
    .job-table td:nth-child(4) { display: none; } /* Befehl auf Mobile ausblenden */
    .hilfe { margin: 0px; }
}
</style>

<?php
  $hilfe_link = "index.php?tab=Hilfe&file=ScheduleManager";
?>
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
  <div class="hilfe" style="text-align:right"><a href="index.php?tab=Settings"><b>Zurück</b></a></div>
</div>

<!-- ============================
     STATUS-CARD
     ============================ -->
<div class="card">
    <h2>⏱ CronJob-Verwaltung</h2>
    <p>
        <?php if ($db_ok): ?>
            <span class="status-dot" style="background:green"></span>
            <strong style="color:green">Datenbank verbunden</strong>
            &nbsp;–&nbsp; <span class="small"><?php echo count($jobs); ?> Jobs gesamt,
            <?php echo count(array_filter($jobs, fn($j) => $j['Aktiv'] == 1)); ?> aktiv</span>
        <?php else: ?>
            <span class="status-dot" style="background:red"></span>
            <strong style="color:red">Datenbank nicht erreichbar</strong>
            <span class="small">(<?php echo htmlspecialchars($DB_PATH); ?>)</span>
        <?php endif; ?>
    </p>
    <p class="small">
        Der Scheduler (<code>db_scheduler.py</code>) wird jede Minute per Crontab aufgerufen
        und führt fällige Jobs aus dieser Tabelle aus.
    </p>
</div>

<!-- ============================
     JOB-LISTE
     ============================ -->
<div class="card">
    <h2>Aktuelle Jobs</h2>
    <div style="overflow-x:auto;">
    <table class="job-table" id="jobTable">
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Cron-Zeit</th>
                <th>Befehl</th>
                <th>Letzter Lauf</th>
                <th>Status</th>
                <th>Aktionen</th>
            </tr>
        </thead>
        <tbody>
        <?php if (empty($jobs)): ?>
            <tr><td colspan="7" style="text-align:center;color:#aaa;">Keine Jobs vorhanden</td></tr>
        <?php else: ?>
        <?php foreach ($jobs as $job): ?>
            <tr class="<?php echo $job['Aktiv'] ? '' : 'inaktiv'; ?>">
                <td><?php echo htmlspecialchars($job['ID']); ?></td>
                <td>
                    <span class="status-dot" style="background:<?php echo $job['Aktiv'] ? 'green' : '#ccc'; ?>"></span>
                    <?php echo htmlspecialchars($job['Name']); ?>
                    <?php if ($job['Notiz']): ?>
                        <br><span class="small"><?php echo htmlspecialchars($job['Notiz']); ?></span>
                    <?php endif; ?>
                </td>
                <td>
                    <span class="cron-badge"><?php echo htmlspecialchars($job['Minute']); ?></span>
                    <span class="cron-badge"><?php echo htmlspecialchars($job['Stunde']); ?></span>
                    <span class="cron-badge"><?php echo htmlspecialchars($job['Tag_Monat']); ?></span>
                    <span class="cron-badge"><?php echo htmlspecialchars($job['Monat']); ?></span>
                    <span class="cron-badge"><?php echo htmlspecialchars($job['Tag_Woche']); ?></span>
                </td>
                <td class="befehl-cell"><?php echo htmlspecialchars($job['Befehl']); ?></td>
                <td class="small">
                    <?php echo $job['Letzter_Lauf'] ? htmlspecialchars(substr($job['Letzter_Lauf'], 0, 16)) : '—'; ?>
                </td>
                <td>
                    <?php if ($job['Letzter_Status'] === null): ?>
                        <span class="small">—</span>
                    <?php elseif ($job['Letzter_Status'] == 0): ?>
                        <span style="color:green">✓ OK</span>
                    <?php else: ?>
                        <span style="color:red">✗ <?php echo htmlspecialchars($job['Letzter_Status']); ?></span>
                    <?php endif; ?>
                </td>
                <td>
                    <div class="btn-row">
                        <!-- Bearbeiten -->
                        <button class="ocpp" onclick="editJob(<?php echo htmlspecialchars(json_encode($job)); ?>)" title="Bearbeiten">✎</button>

                        <!-- Aktiv/Inaktiv Toggle -->
                        <form method="post" style="display:inline">
                            <input type="hidden" name="action"  value="toggle_job">
                            <input type="hidden" name="job_id" value="<?php echo $job['ID']; ?>">
                            <button class="ocpp <?php echo $job['Aktiv'] ? 'orange' : ''; ?>"
                                    title="<?php echo $job['Aktiv'] ? 'Deaktivieren' : 'Aktivieren'; ?>">
                                <?php echo $job['Aktiv'] ? '⏸' : '▶'; ?>
                            </button>
                        </form>

                        <!-- Löschen -->
                        <form method="post" style="display:inline"
                              onsubmit="return confirm('Job \'<?php echo addslashes(htmlspecialchars($job['Name'])); ?>\' wirklich löschen?')">
                            <input type="hidden" name="action"  value="delete_job">
                            <input type="hidden" name="job_id" value="<?php echo $job['ID']; ?>">
                            <button class="ocpp red" title="Löschen">✕</button>
                        </form>
                    </div>
                </td>
            </tr>
        <?php endforeach; ?>
        <?php endif; ?>
        </tbody>
    </table>
    </div>

    <br>
    <button class="ocpp" onclick="newJob()">+ Neuer Job</button>
</div>

<!-- ============================
     FORMULAR: NEU / BEARBEITEN
     ============================ -->
<div class="card" id="formCard">
    <h2 id="formTitle">Job bearbeiten</h2>

    <form id="jobForm" method="post">
        <input type="hidden" name="action"  value="save_job">
        <input type="hidden" name="job_id"  id="fJobId">

        <div class="row">
            <span class="label-inline"><label for="fName">Name:</label></span>
            <span class="input-inline"><input type="text" id="fName" name="Name" required placeholder="z.B. EnergyController" style="width:100%;max-width:400px;"></span>
        </div>

        <hr>
        <p><b>Cron-Felder</b> &nbsp;<span class="small">(* = immer, Komma = Liste, a-b = Bereich, */n = Schritt)</span></p>

        <div class="row">
            <span class="label-inline"><label for="fMinute">Minute:</label></span>
            <span class="input-inline"><input type="text" id="fMinute" name="Minute" value="*" placeholder="* / 0 / 1-56/10 / 0,30" style="width:160px;"></span>
        </div>
        <div class="row">
            <span class="label-inline"><label for="fStunde">Stunde:</label></span>
            <span class="input-inline"><input type="text" id="fStunde" name="Stunde" value="*" placeholder="* / 5,8,10 / 0-23" style="width:160px;"></span>
        </div>
        <div class="row">
            <span class="label-inline"><label for="fTagMonat">Tag (Monat):</label></span>
            <span class="input-inline"><input type="text" id="fTagMonat" name="Tag_Monat" value="*" placeholder="* / 1 / 1-15" style="width:160px;"></span>
        </div>
        <div class="row">
            <span class="label-inline"><label for="fMonat">Monat:</label></span>
            <span class="input-inline"><input type="text" id="fMonat" name="Monat" value="*" placeholder="* / 1-12" style="width:160px;"></span>
        </div>
        <div class="row">
            <span class="label-inline"><label for="fTagWoche">Tag (Woche):</label></span>
            <span class="input-inline">
                <input type="text" id="fTagWoche" name="Tag_Woche" value="*" placeholder="* / 1=Mo / 1-5" style="width:160px;">
                <span class="small">&nbsp;1=Mo … 7=So</span>
            </span>
        </div>

        <hr>

        <div class="row">
            <span class="label-inline"><label for="fBefehl">Befehl:</label></span>
            <span class="input-inline"><input type="text" id="fBefehl" name="Befehl" required placeholder="/home/GEN24/start_PythonScript.sh mein_script.py" style="width:100%;max-width:500px;"></span>
        </div>
        <div class="row">
            <span class="label-inline"><label for="fNotiz">Notiz:</label></span>
            <span class="input-inline"><input type="text" id="fNotiz" name="Notiz" placeholder="Optionale Beschreibung" style="width:100%;max-width:400px;"></span>
        </div>
        <div class="row">
            <span class="label-inline"><label for="fAktiv">Aktiv:</label></span>
            <span class="input-inline">
                <input type="checkbox" id="fAktiv" name="Aktiv" value="1" checked style="width:auto;background:none;border:none;">
            </span>
        </div>

        <br>
        <button type="submit" class="ocpp schreiben">💾 Speichern</button>
        &nbsp;
        <button type="button" class="ocpp red" onclick="closeForm()">Abbrechen</button>
    </form>
</div>

<!-- ============================
     CRONTAB-HINWEIS
     ============================ -->
<div class="card">
    <details id="cronHinweis">
        <summary><b>Crontab-Eintrag für den Scheduler</b></summary>
        <div style="margin-top:8px;">
        <p class="small">In der System-Crontab (<code>crontab -e</code>) muss nur noch dieser eine Eintrag stehen:</p>
        <pre style="background:#f0f0f0;padding:8px;border-radius:4px;font-size:0.9em;overflow-x:auto;">* * * * * /usr/bin/python /home/GEN24/db_scheduler.py </pre>
        <p class="small">Der Scheduler liest jede Minute alle aktiven Jobs aus dieser Tabelle und führt fällige Jobs aus.</p>
        <p class="small"><b>Cron-Syntax Kurzreferenz:</b></p>
        <table style="font-size:0.85em;border-collapse:collapse;width:100%;">
            <tr><th style="text-align:left;padding:3px 8px;background:#eee;">Feld</th><th style="text-align:left;padding:3px 8px;background:#eee;">Bereich</th><th style="text-align:left;padding:3px 8px;background:#eee;">Beispiele</th></tr>
            <tr><td style="padding:2px 8px;">Minute</td><td style="padding:2px 8px;">0–59</td><td style="padding:2px 8px;font-family:monospace;">* &nbsp; 0 &nbsp; 1-56/10 &nbsp; 0,30</td></tr>
            <tr><td style="padding:2px 8px;">Stunde</td><td style="padding:2px 8px;">0–23</td><td style="padding:2px 8px;font-family:monospace;">* &nbsp; 5 &nbsp; 5,8,10,12,14</td></tr>
            <tr><td style="padding:2px 8px;">Tag (Monat)</td><td style="padding:2px 8px;">1–31</td><td style="padding:2px 8px;font-family:monospace;">* &nbsp; 1 &nbsp; 1-15</td></tr>
            <tr><td style="padding:2px 8px;">Monat</td><td style="padding:2px 8px;">1–12</td><td style="padding:2px 8px;font-family:monospace;">* &nbsp; 6-9</td></tr>
            <tr><td style="padding:2px 8px;">Tag (Woche)</td><td style="padding:2px 8px;">1–7 (Mo–So)</td><td style="padding:2px 8px;font-family:monospace;">* &nbsp; 1 &nbsp; 1-5</td></tr>
        </table>
        </div>
    </details>
</div>

<script src="jquery.min.js"></script>
<script>
// ===================================
// Formular: Neuer Job
// ===================================
function newJob() {
    document.getElementById('formTitle').textContent = '+ Neuer Job';
    document.getElementById('fJobId').value  = '';
    document.getElementById('fName').value   = '';
    document.getElementById('fMinute').value = '*';
    document.getElementById('fStunde').value = '*';
    document.getElementById('fTagMonat').value = '*';
    document.getElementById('fMonat').value  = '*';
    document.getElementById('fTagWoche').value = '*';
    document.getElementById('fBefehl').value = '';
    document.getElementById('fNotiz').value  = '';
    document.getElementById('fAktiv').checked = true;
    openForm();
}

// ===================================
// Formular: Bestehenden Job bearbeiten
// ===================================
function editJob(job) {
    document.getElementById('formTitle').textContent = '✎ Job bearbeiten (ID ' + job.ID + ')';
    document.getElementById('fJobId').value     = job.ID;
    document.getElementById('fName').value      = job.Name      || '';
    document.getElementById('fMinute').value    = job.Minute    || '*';
    document.getElementById('fStunde').value    = job.Stunde    || '*';
    document.getElementById('fTagMonat').value  = job.Tag_Monat || '*';
    document.getElementById('fMonat').value     = job.Monat     || '*';
    document.getElementById('fTagWoche').value  = job.Tag_Woche || '*';
    document.getElementById('fBefehl').value    = job.Befehl    || '';
    document.getElementById('fNotiz').value     = job.Notiz     || '';
    document.getElementById('fAktiv').checked   = (job.Aktiv == 1);
    openForm();
}

function openForm() {
    var card = document.getElementById('formCard');
    card.classList.add('open');
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeForm() {
    document.getElementById('formCard').classList.remove('open');
}

// ===================================
// Scroll-Position wiederherstellen
// ===================================
window.addEventListener("beforeunload", function() {
    sessionStorage.setItem("scrollPos", window.scrollY);
});
window.addEventListener("load", function() {
    var pos = sessionStorage.getItem("scrollPos");
    if (pos !== null) window.scrollTo(0, parseInt(pos));
});

// ===================================
// localStorage: Details-Status merken
// ===================================
(function() {
    var el = document.getElementById('cronHinweis');
    if (!el) return;
    if (localStorage.getItem('cronHinweisOpen') === '1') el.setAttribute('open','open');
    el.addEventListener('toggle', function() {
        localStorage.setItem('cronHinweisOpen', this.open ? '1' : '0');
    });
})();
</script>
