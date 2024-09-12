<!DOCTYPE html>
<html lang="de">
<head>
<title>PV_Planung</title>
  <link rel="icon" type="image/png" href="GEN24Ladesteuerung.png">
<style>
/**
 * Tabs
 */
.tabs {
    position:fixed; top:0px; width:100%;
	display: flex;
	flex-wrap: wrap; // make sure it wraps
    overflow: hidden;
}
.tabs label {
	order: 1; // Put the labels first
	display: block;
	padding: 15px 7px;
	*margin-right: 0.2rem;
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
}
.tabs .tab {
  order: 99; // Put the tabs last
  flex-grow: 1;
	width: 100%;
    height: 88dvh;
	display: none;
  padding: 1rem;
  background: #fff;
}
.tabs input[type="radio"] {
	display: none;
}
.tabs input[type="radio"]:checked + label {
	background: #fff;
}
.tabs input[type="radio"]:checked + label + .tab {
	display: block;
}

@media (max-width: 85em) {
  .tabs label {
    margin-right: 0;
    font-size: 20px;
  }
}

/**
 * Generic Styling
*/
body {
  background: #eee;
  min-height: 100vh;
	box-sizing: border-box;
	padding-top: 1vh;
  font-family: "HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif;
  font-weight: 300;
  line-height: 1.5;
  * max-width: 60rem;
  margin: 0 auto;
  font-size: 112%;
  overflow: hidden;
}


</style>
</head>
<body>

<?php
include "config.php";
if(file_exists("config_priv.php")){
  include "config_priv.php";
}
if (!isset($TAB_config) OR !is_array($TAB_config)) {
    echo '</br><center>ACHTUNG: Die Variable "TAB_config" ist in der config.php nicht (richtig) gesetzt!!</center></body></html>';
    exit();
}
$class_link='';
# Breite der Tabs in % rechnen
$anzahl_tabs = array_count_values(array_column($TAB_config, 'sichtbar'))['ein'];
$Tab_Proz = floor((100-($anzahl_tabs*2))/$anzahl_tabs);
$class_tab = '';

echo '<div class="tabs">';
foreach ($TAB_config as $files) {
    if ($files['sichtbar'] == 'ein' and file_exists($files['file'])){
        if($files['checked'] == 'ja') {
            $id_default = ' checked="checked"';
        } else {
            $id_default = '';
        }
            $class_tab .= '<input type="radio" name="tabs" id="'.$files['name'].'"'.$id_default.' onclick="reloadFrame(\''.$files['name'].'\')">'."\n";
            $class_tab .= '<label style="width: '.$Tab_Proz.'vw;" for="'.$files['name'].'">'.$files['name'].'</label>'."\n";
            $class_tab .= '<div class="tab"><iframe id="'.$files['name'].'" src="'.$files['file'].'" style="border:none;" height="100%" width="100%"></iframe></div>'."\n";
    }
}
$class_tab .= '</div>';
echo $class_tab;
?>
<script>
function reloadFrame(button){
  document.querySelectorAll("iframe").forEach(function(e){ 
  // nur Iframe des geklickten Tab neu laden
  if ( e.getAttribute("id") == button ) {
  e.src+=""; 
  }
  });
}
// Alle 5 Minuten alle Iframes neu laden
setInterval(function() {
  document.querySelectorAll("iframe").forEach(function(e){ e.src+=""; });
}, 900000);

</script>
</body>
</html>

