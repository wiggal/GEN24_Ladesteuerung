<?php
# config.ini parsen und $TAB_config lesen
require_once "config_parser.php";

$tabs = [];

foreach ($TAB_config as $tab) {
    if ($tab['sichtbar'] === 'ein') {
        $tabs[$tab['name']] = $tab['file'];
    }
}

$activeTab = $_POST['tab'] ?? $_GET['tab'] ?? $TAB_config['0']['name'];

$sonder_tabs = [
  'WeatherMgr'  => 'weatherDataManager.php',
  'Hilfe'  => 'Hilfe_Ausgabe.php'
];
$all_files = $tabs + $sonder_tabs;

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
/* ===== BASIS & NAV-HÖHE ===== */
/* ===== BASIS & NAV-STRUKTUR ===== */
body { margin: 0; font-family: Arial, sans-serif; }

.header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: #90CAF9;
  z-index: 1000;
  height: 50px;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 50px;
}

.nav-visible {
  display: flex;
  overflow: hidden;
  height: 100%;
  flex-grow: 1;
}

.nav-item {
  margin: 0;
  display: flex;
}

/* Standard: 50px Padding & 17px Schrift */
.nav-item button, .nav-item .wiki-btn {
  border: none;
  padding: 0 50px;   /* Maximales padding 50 wenn Platz*/
  background: #90CAF9;
  font-weight: bold;
  font-size: 17px;
  white-space: nowrap;
  cursor: pointer;
  height: 50px;
  box-sizing: border-box;
  text-align: center;
}

/* Kompakt-Modus: Reduzierung auf 2px */
.nav-container.compact .nav-item button,
.nav-container.compact .nav-item .wiki-btn {
  padding: 0 8px;
}

.nav-item button.active {
  background: #fff;
}

/* ===== OVERFLOW / HAMBURGER ===== */
.hamburger {
  padding: 0 15px;
  font-size: 30px;
  cursor: pointer;
  line-height: 50px;
  display: none;
  background: #90CAF9;
}

.overflow-menu {
  display: none;
  position: absolute;
  right: 0;
  top: 50px;
  background: #90CAF9;
  box-shadow: -2px 5px 10px rgba(0,0,0,0.2);
  min-width: 200px;
  flex-direction: column;
}

.overflow-menu.open {
  display: flex;
}

/* Im Menü gute Lesbarkeit */
.overflow-menu .nav-item button {
  width: 100%;
  text-align: left;
  padding: 0 15px !important;
  border-top: 1px solid rgba(0,0,0,0.1);
}

.hilfe a {
  font-family: Arial; font-size: 130%; position: absolute;
  right: 15px; text-decoration: none;
}

.weatherDataManager a {
  font-family: Arial; font-size: 130%; position: absolute;
  left: 8px; white-space: nowrap; text-decoration: none;
}

.content {
  background: #fff; 
  padding: 5px; 
  margin-left: 8px;
  margin-top: 50px;
  height: calc(100vh - 50px);
  overflow: auto;
}

iframe {
  width: 100%;
  height: calc(100vh - 80px);
  border: none;
  display: block;
}

/* Mobile Scrollbar-Handling */
@media (max-width: 600px) {
  html, body, .content {
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
  }
  html::-webkit-scrollbar, body::-webkit-scrollbar, .content::-webkit-scrollbar {
    display: none !important;
  }
.header {
  height: 40px;
  visibility: visible;
}
.nav-container {
  height: 40px;
}
.nav-item button, .nav-item .wiki-btn {
  height: 40px;
}
.hamburger {
  line-height: 40px;
}
.overflow-menu {
  top: 40px;
}
/* ===== CONTENT ===== */
.hilfe, .weatherDataManager {
   font-size: 80% !important;
   margin-top: 20px;
}
.content {
  margin-top: 40px;
  height: calc(100vh - 40px);
}
</style>
</head>

<body>

<div class="header">
  <div class="nav-container">
    <div class="nav-visible" id="navVisible">
      <?php foreach ($tabs as $key => $file): ?>
        <form method="post" class="nav-item">
          <input type="hidden" name="tab" value="<?= $key ?>">
          <button type="submit" class="<?= $activeTab === $key ? 'active' : '' ?>">
            <?= htmlspecialchars($key) ?>
          </button>
        </form>
      <?php endforeach; ?>
      
      <div class="nav-item">
        <button class="wiki-btn" onclick="openWiki()" style="background: #44c767;">WIKI</button>
      </div>
    </div>

    <div class="nav-overflow">
      <div class="hamburger" id="hamburgerBtn" onclick="toggleMenu()">☰</div>
      <div class="overflow-menu" id="overflowMenu"></div>
    </div>
  </div>
</div>

<script>
// Globale Funktionen für Events
function toggleMenu() {
    const menu = document.getElementById('overflowMenu');
    menu.classList.toggle('open');
}

function openWiki() {
    window.open('https://wiggal.github.io/GEN24_Ladesteuerung/', '_blank');
}

(function () {
  const updateNavigation = () => {
    const container = document.querySelector('.nav-container');
    const visible = document.getElementById('navVisible');
    const overflow = document.getElementById('overflowMenu');
    const hamburger = document.getElementById('hamburgerBtn');
    const items = Array.from(document.querySelectorAll('.nav-item'));

    // Reset
    container.classList.remove('compact');
    hamburger.style.display = 'none';
    overflow.classList.remove('open');
    items.forEach(item => visible.appendChild(item));

    const availableWidth = visible.offsetWidth - 60;
    let widths = items.map(item => item.getBoundingClientRect().width);
    let totalWidth = widths.reduce((a, b) => a + b, 0);

    // Kompakt-Check
    if (totalWidth > availableWidth) {
      container.classList.add('compact');
      widths = items.map(item => item.getBoundingClientRect().width);
    }

    // Overflow-Check
    let used = 0;
    items.forEach((item, i) => {
      used += widths[i];
      if (used > availableWidth) {
        hamburger.style.display = 'block';
        overflow.appendChild(item);
      }
    });
  };

  // Sofort ausführen
  updateNavigation();
  window.addEventListener('resize', updateNavigation);
  window.addEventListener('load', updateNavigation);
})();
</script>

<div class="content">
  <?php
    $target = $all_files[$activeTab];
    if (substr($target, 0, 4) === 'http' || substr($target, 0, 7) === 'iframe:') {
        $url = (substr($target, 0, 7) === 'iframe:') ? explode(":", $target, 2)[1] : $target;
        echo '<iframe src="' . htmlspecialchars($url) . '"></iframe>';
    } else {
        // Hier wird die lokale PHP-Datei geladen
        if (file_exists($target)) {
            include $target;
        } else {
            echo "Datei $target nicht gefunden.";
        }
    }
  ?>
</div>
</body>
</html>
