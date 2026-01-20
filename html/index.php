<?php
# config.ini parsen und $TAB_config lesen
require_once "config_parser.php";

$tabs = [];
$file_checked = null;

foreach ($TAB_config as $tab) {
    // nur sichtbare Tabs übernehmen
    if ($tab['sichtbar'] === 'ein') {
        // name => file
        $tabs[$tab['name']] = $tab['file'];
        // ersten checked => ja merken (NAME!)
        if ($file_checked === null && $tab['checked'] === 'ja') {
            $file_checked = $tab['name'];
        }
    }
}
// Fallbacks, falls kein checked => ja
if ($file_checked === null) {
    if (!empty($tabs)) {
        $file_checked = array_key_first($tabs); // erster sichtbarer Tab
    } else {
        $file_checked = 'LadeStrg'; // Standard
    }
}

// Sucht erst in POST, dann in GET, sonst Standard 'LadeStrg'
$activeTab = $_POST['tab'] ?? $_GET['tab'] ?? $file_checked;

$sonder_tabs = [
  'WeatherMgr'  => 'weatherDataManager.php',
  'Hilfe'  => 'Hilfe_Ausgabe.php'
];
// Neues Array für alle Dateien erzeugen, ohne $tabs zu verändern
$all_files = $tabs + $sonder_tabs;

// Sicherheitskontrolle um unbefugte Files auszuschießen
if (!isset($all_files[$activeTab])) {
    $activeTab = 'LadeStrg';
    }

?>
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>PV_Planung</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/png" href="GEN24Ladesteuerung.png">
<style>
/* ===== NAV ===== */
.nav {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  background: #90CAF9;
  z-index: 1000;
}

.nav form {
  margin: 0;
  display: block;
}

.nav button, .nav .wiki {
  display: block;
  border: none;
  padding: 15px 7px;
  margin-right: 0.2%;
  cursor: pointer;
  background: #90CAF9;
  font-weight: bold;
  font-size: 17px;
  white-space: nowrap;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background ease 0.2s;
  width: 9vw;
  box-sizing: border-box;
}

.nav button.active {
  background: #fff;
  cursor: default;
}

.nav button.wiki {
  background: #44c767;
  width: 9vw; /* Wiki Button gleiche Breite */
  color: black;
  text-decoration: none;
}
/* ===== CONTENT ===== */
.content {
  background: #fff;
  padding: 5px;
  margin-top: 30px;
  /*height: calc(100vh - 80px);   #entWIGGlung*/
  height: 100vh
  overflow-y: auto;
  overflow-x: auto;
}

.hilfe a {
  font-family:Arial;
  font-size:130%;
  position: absolute;
  right: 15px;
  text-decoration: none;
}

.weatherDataManager a {
  font-family:Arial;
  font-size:130%;
  position: absolute;
  left: 8px;
  white-space: nowrap;
  text-decoration: none;
}
/* Der Iframe füllt den Content komplett aus */
iframe {
  width: 100%;
  height: calc(100vh - 80px);
  border: none;
  display: block;
}

/* ===== MOBILE ANPASSUNG ===== */
/* Spezifisches Handy-Menü beibehalten */
@media (max-width: 600px) {
  /* Scrollbalken für das gesamte Dokument UND den Content-Container ausblenden */
  html, body, .content {
    scrollbar-width: none !important; /* Firefox */
    -ms-overflow-style: none !important; /* IE/Edge */
  }
  /* Für Chrome, Safari und Opera */
  html::-webkit-scrollbar,
  body::-webkit-scrollbar,
  .content::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
  }

  .hamburger {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1001;
    background: #90CAF9;
    width: 100%;
    height: 35px;        /* Höhe des blauen Balkens */
    line-height: 35px;   /* Zentriert die Striche vertikal */
    font-size: 30px;     /* Die drei Striche deutlich größer */
    padding-left: 15px;  /* Rückt nur die Striche von links ein */
    cursor: pointer;
    box-sizing: border-box;
    overflow: hidden;    /* Verhindert, dass das große Icon den Balken sprengt */
  }
  .nav {
    top: 35px;
    flex-direction: column;
    display: none;
    width: auto;
    max-width: 80%; /* Optional: Verhindert, dass das Menü zu breit wird */
    background: #90CAF9;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
  }
  .nav.open {
    display: flex;
  }
  .nav button, .nav .wiki {
    text-align: left;
    /* Geändert: width: 100% entfernt, damit es nur so breit wie der Text ist */
    width: auto !important;
    min-width: 150px; /* Optional: Damit schmale Wörter nicht zu winzig wirken */
    border-bottom: 1px solid rgba(0,0,0,0.1);
    padding: 12px 20px; /* Mehr Platz links/rechts für bessere Optik */
  }

/* ===== CONTENT ===== */
  .hilfe, .weatherDataManager {
    font-size: 80% !important;
    margin-top: 20px;
  }
}
</style>
</head>

<body>

<!-- ===== HEADER ===== -->
<div class="header">
  <div class="hamburger" onclick="toggleMenu()">☰</div>

  <div class="nav" id="nav">
    <?php foreach ($tabs as $key => $file): ?>
      <form method="post">
        <input type="hidden" name="tab" value="<?= $key ?>">
        <button
          type="submit"
          class="<?= $activeTab === $key ? 'active' : '' ?>"
          onclick="closeMenu()">
          <?= htmlspecialchars($key) ?>
        </button>
      </form>
    <?php endforeach; ?>

    <button class="wiki" onclick="openWiki()">WIKI</button>
  </div>
</div>

<!-- ===== CONTENT ===== -->
<div class="content">
  <?php
    $target = $all_files[$activeTab];

    // Externe Seiten laden: prüfen, ob der Pfad mit http:// oder https:// beginnt
    if (substr($target, 0, 4) === 'http') {
        // Externe Seite per Iframe einbinden
        echo '<iframe src="' . htmlspecialchars($target) . '"></iframe>';
    } elseif (substr($target, 0, 7) === 'iframe:') {
        // PHP-Script in Iframe laden, z.B. iframe:6_tab_GEN24.php
        $teile = explode(":", $target, 2);
        // Externe Seite per Iframe einbinden
        echo '<iframe src="' . htmlspecialchars($teile[1]) . '"></iframe>';
    } else {
        // Lokale Datei wie gewohnt includen
        include $target;
    }
  ?>
</div>

<script>
function toggleMenu() {
  document.getElementById('nav').classList.toggle('open');
}

function closeMenu() {
  document.getElementById('nav').classList.remove('open');
}

function openWiki() {
  window.open(
    'https://wiggal.github.io/GEN24_Ladesteuerung/',
    '_blank'
  );
}
</script>

</body>
</html>

