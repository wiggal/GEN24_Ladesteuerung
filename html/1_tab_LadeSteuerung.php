  <script src="jquery.min.js"></script>
  <style>
  .box
  {
   max-width:600px;
   width:100%;
   margin: 0 auto;;
  }
  .center {
  margin-left: auto;
  margin-right: auto;
  }
  table, th, td, caption {
  border: thin solid #a0a0a0;
  }

  table {
  border-collapse: collapse;
  border-spacing: 0;
  border-width: thin 0 0 thin;
  margin: 0 0 1em;
  table-layout: auto;
  }
  th {
  position: sticky;
  top: 65px;
  z-index: 101; /* soll vor dem Button liegen */
  }
  th, td {
  font-size: 200%;
  font-weight: normal;
  text-align: right;
  padding: 4px;
  }
  th {
    text-align: center;
  }

  th, caption {
  background-color: #C1C0C0;
  font-weight: 700;
  }

  .speichern {
	background-color:#44c767;
	border-radius:28px;
	border:1px solid #18ab29;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-size:200%;
	padding:16px 31px;
	text-decoration:none;
    white-space: nowrap;
    position: fixed;
    transform: translate(-50%, 0);
    z-index: 100;  /* <-- sorgt dafür, dass der Button oben bleibt */
  }
  .speichern:hover {
	background-color:#5cbf2a;
  }
  .speichern:active {
	position:fixed;
  }

/* LADEGRENZBOX */
.flex-container {
  display: flex;
  width: 80%;
  max-width: 800px;
  margin: auto;
  background: #fff;
  align-items: center;
  padding: 5px 8px;
  box-shadow: 5px 5px 30px rgba(0,0,0,0.2);
}
.flex-container > div {
  background-color: #fff;
  margin: 5px;
  padding: 10px;
  font-size: 30px;
}
/* Zeilen-Wrapper der Auto-Options-Felder: eigene Regel, da die generische ".flex-container > div"-Regel
   (margin/padding) zusammen mit width:100% sonst über den Container hinausragt */
.flex-container > div.autooption-row {
  margin: 0;
  padding: 4px 0;
  box-sizing: border-box;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 1ch;
}
/* END LADEGRENZBOX */

/* CHECKBOX */
input[type="checkbox"] {
   position: relative;
   width: 20px;
   height: 25px;
   top: +.5em;
   accent-color: #44c767;
}
.dropdown {
  font-size: 2rem;
  line-height: 1.4;
  display: grid;
  justify-items: left;
  grid-template-columns: 1.3em auto;
}

/* Reines Textlabel (kein <select>) - ca. 30% kleiner als .dropdown, ohne dessen Grid-Layout */
.autooption-label {
  font-size: 1.4rem;
  line-height: 1.4;
  display: inline-block;
}

/* Prozent-Badge bei Auto-Options-Feldern ca. 30% kleiner als der normale .slider-Badge (90% -> 63%) */
label.slider.autooption-percent {
  font-size: 63%;
}

/* ENDE CHECKBOX */

label.slider {
	background-color:#44c767;
	border-radius:10px;
	border:1px solid #18ab29;
	display:inline-block;
	cursor:pointer;
	color:#000000;
	font-size:90%;
	padding:5px 10px;
	margin:0;
	text-decoration:none;
    flex-shrink: 0;
  }
input.slider {
   width: 100%;
   height: 35px;
   margin: 0;
   accent-color: #44c767;
  }

/* Auto-Options-Feld zeigt den Config-Wert (nicht den DB-Wert) - rot wie die Prognosebalken */
label.slider.autooption-fallback {
	background-color:#ff5733;
	border:1px solid #cc4020;
  }
input.slider.autooption-fallback {
   accent-color: #ff5733;
  }

/* Zahl-/Listen-Felder bei Auto Options (typ 'zahl'/'liste') - grün wie normale Werte, rot als Fallback */
.autooption-input {
	background-color:#44c767;
	border-radius:10px;
	border:1px solid #18ab29;
	color:#000000;
	font-size:90%;
	padding:5px 10px;
	width:100%;
	height:35px;
	box-sizing:border-box;
  }
.autooption-input.autooption-fallback {
	background-color:#ff5733;
	border:1px solid #cc4020;
  }

/* Ladeleistung-Feld: blau, wenn der Wert exakt dem MaxLadung-Wert entspricht (Vorrang vor rot) */
.autooption-input.autooption-maxladung {
	background-color:#58ACFA;
	border:1px solid #2f7fd1;
  }

/* Radio-Buttons-Gruppe: flexibles Layout statt fester Höhe wie bei Zahl-/Listenfeldern */
.autooption-input.autooption-radio-group {
	height: auto;
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 4px 16px;
  }
.autooption-input.autooption-radio-group input[type="radio"] {
	margin-right: 4px;
	vertical-align: middle;
  }

.sliderbeschriftung{
  font-weight: bold;
  font-size:120%;
  color: #000000;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin-top: 50px !important; /* Abstand nach oben zum Button */
  margin-bottom: 10px !important; /* Abstand nach unten zum Slider */
}
.checkbox-wrap {
  white-space: nowrap;
}
.gueltig {
  font-weight: normal;
  color: #555;
  font-size: 90%;
}

/* Spezielle Anpassung für Mobilgeräte */
@media (max-width: 600px) {
  .gueltig {
    width: 100%;
    display: block;
  }

  th, td {
    font-size: 90%; /* Schrift auf Handys deutlich verkleinern */
  }

  .sliderbeschriftung{
    font-size:90%;
    margin-top: 15px !important; /* Abstand nach oben zum Button */
    margin-bottom: 10px !important; /* Abstand nach unten zum Slider */
  }

  .flex-container {
    width: 95% !important; /* Container fast volle Breite */
    padding: 5px 2px !important;
  }

  .flex-container > div {
    margin: 2px !important;      /* Abstand zwischen den Elementen im Block verringern */
    padding: 2px !important;     /* Inneres Padding der Divs verringern */
    font-size: 18px !important; /* Slider-Beschriftung kleiner */
  }

  .flex-container > div.autooption-row {
    margin: 0 !important;
    box-sizing: border-box !important;
    width: 100% !important;
  }

  .speichern {
    font-size: 100% !important; /* Speicher-Button verkleinern */
    padding: 8px 10px !important;
  }

  .dropdown {
    font-size: 1.2rem !important; /* Dropdown kleiner */
  }

  .autooption-label {
    font-size: 0.84rem !important; /* ca. 30% kleiner als .dropdown auf Mobilgeräten */
  }

  /* Tabelle zwingen, in die Breite zu passen */
  table.center {
    width: 90% !important;
    display: table; /* Stellt sicher, dass sie sich wie eine Tabelle verhält */
  }
}
</style>

<div class="weatherDataManager"> <a href="index.php?tab=WeatherMgr&file=<?php echo $activeTab; ?>"><b>FcastMgr</b></a></div>
<!-- Hilfeaufruf ANFANG -->
<?php
  $hilfe_link = "index.php?tab=Hilfe&file={$activeTab}";
?>
  <div class="hilfe"> <a href="<?php echo $hilfe_link; ?>"><b>Hilfe</b></a></div>
<!-- Hilfeaufruf ENDE -->
  <div align="center"><button type="button" id="import_data" class="speichern">Ladesteuerung speichern</button></div>
  <br />

<?php
# $PythonDIR/CONFIG/charge.ini parsen
merge_config_into_globals($PythonDIR . '/CONFIG/charge.ini');

include 'SQL_steuerfunctions.php';
# Zwei getrennte Aufrufe im bekannten, garantiert funktionierenden Ein-String-Format statt eines
# einzelnen Aufrufs mit zusammengesetztem Mehrfach-Schlüssel-String (dessen Verhalten unklar ist
# und vermutlich die Ursache dafür war, dass ChargeOption-Zeilen nicht zuverlässig gelesen wurden).
$EV_Reservierung_Zeit = getSteuercodes('Reservierung');
$EV_Reservierung_Options = getSteuercodes('ChargeOption');
$EV_Reservierung = array_merge($EV_Reservierung_Zeit, $EV_Reservierung_Options);
#print_r($EV_Reservierung);  #entWIGGlung
$PrstLadeStd = getPrstLadeStd();
$Prognose = getPrognose();

$Res_Feld1 = 'einmal';
$Res_Feld2 = 'laufend';
$DB_AutoOptions_selected = '';
$DB_Auto_selected = '';
$DB_Slider_selected = '';
$Akkuschon_check = '';
# Prüfen, ob Einträge für ManuelleSteuerung schon abgelaufen
# Wenn Feld in DB keine Zahl (oder die Zeile noch gar nicht existiert)
if (!isset($EV_Reservierung['ManuelleSteuerung']['Options']) || !is_numeric($EV_Reservierung['ManuelleSteuerung']['Options'])){
    $EV_Reservierung['ManuelleSteuerung']['Options'] = 0;
}

# Modus-Kennung: -1 = Auto, -3 = Slider/Ladeleistung, -4 = AutoOptions (Res_Feld1 enthält ab jetzt
# NUR die Kennung, keinen Prozentwert mehr). -2 (ehemals MaxLadung) ist als eigener Modus entfallen -
# ein evtl. noch in der DB stehender Altwert -2 fällt einfach mit in den Slider/Ladeleistung-Zweig.
$ManSteuerung_abgelaufen = ($EV_Reservierung['ManuelleSteuerung']['Options'] < time());

if ($ManSteuerung_abgelaufen) {
    $EV_Reservierung['ManuelleSteuerung']['Res_Feld1'] = -1;
    $gueltig_bis = '';
    } else {
    $gueltig_bis = "&nbsp;gültig bis " . date("Y-m-d H:i", $EV_Reservierung['ManuelleSteuerung']['Options']);
    }
$std_diff = ($EV_Reservierung['ManuelleSteuerung']['Options'] - time())/3600;
$std_diff = ($std_diff <= 0) ? 0 : round($std_diff,2);

# Modus zuerst bestimmen, da Res_Feld2 nur noch bei Modus "Slider" ein Prozentwert ist
# (bei Auto/AutoOptions steht dort -1)
if (isset($EV_Reservierung['ManuelleSteuerung']['Res_Feld1'])) {
    $Modus_wert = $EV_Reservierung['ManuelleSteuerung']['Res_Feld1'];

    if ($Modus_wert == -1){
    $DB_Auto_selected = 'selected';
    } elseif ($Modus_wert == -4) {
    $DB_AutoOptions_selected = 'selected';
    } else {
    $DB_Slider_selected = 'selected';
    }
}

// Ausgelesenen Wert für das Select-Feld vorbereiten (standardmäßig 0)
$DB_Akkuschon_wert = isset($EV_Reservierung['Akkuschonung']['Res_Feld2']) ? (int)$EV_Reservierung['Akkuschonung']['Res_Feld2'] : 0;

# Stundenfeld bleibt immer aktiv/vorbelegt (echter Wert bzw. 1 Stunde als Default, wenn nichts aus
# der DB kommt) - auch bei Auto, statt hier auf 0 gezwungen zu werden. Beim Speichern wird das Feld
# für Auto ohnehin ignoriert (Options wird dort fest auf 0 gesetzt), das betrifft nur die Anzeige.
$std_diff_anzeige = $std_diff;
if ($DB_Auto_selected) {
    $DB_Akkuschon_wert = 0;
}

# Auto Options: die Feldliste kommt jetzt aus der Sektion [AutoOptionsFelder] von
# config.ini/config_priv.ini (siehe dort für Format/Beispiele) und wird von config_parser.php
# beim Einbinden bereits als $GLOBALS['AutoOptionsFelder'] bereitgestellt - hier nur defensiv
# gegen ein fehlendes/leeres Ergebnis absichern, falls die Sektion (noch) nicht existiert.
$AutoOptionsFelder = $GLOBALS['AutoOptionsFelder'] ?? [];

# Werte je Auto-Options-Feld berechnen: Config-Wert (aus charge.ini/charge_priv.ini, via
# merge_config_into_globals bereits zusammengeführt, Schlüssel = Feldname) wird angezeigt - und das
# Feld rot markiert - wenn die Zeile zeitlich abgelaufen ist, kein DB-Wert existiert, oder der
# DB-Wert ohnehin identisch mit dem Config-Wert ist. Bei 'liste' wird als String verglichen, sonst
# als Zahl.
$AutoOptionsWerte = [];
foreach ($AutoOptionsFelder as $Feld_Schluessel => $Feld) {
    $typ = $Feld['typ'] ?? 'prozent';
    $ist_numerisch = !in_array($typ, ['liste', 'radio'], true);
    $section = $Feld['section'] ?? 'Ladeberechnung';

    $config_wert_roh = isset($GLOBALS[$section][$Feld_Schluessel]) ? $GLOBALS[$section][$Feld_Schluessel] : null;
    $db_wert_roh = isset($EV_Reservierung[$Feld_Schluessel]['Res_Feld2']) ? $EV_Reservierung[$Feld_Schluessel]['Res_Feld2'] : null;

    $config_wert = $ist_numerisch ? (int) $config_wert_roh : (string) $config_wert_roh;
    $db_wert = is_null($db_wert_roh) ? null : ($ist_numerisch ? (int) $db_wert_roh : (string) $db_wert_roh);

    $options = isset($EV_Reservierung[$Feld_Schluessel]['Options']) ? (int) $EV_Reservierung[$Feld_Schluessel]['Options'] : 0;
    $abgelaufen = ($options < time());
    $ist_fallback = $abgelaufen || is_null($db_wert) || ($db_wert === $config_wert);

    $AutoOptionsWerte[$Feld_Schluessel] = [
        'typ'            => $typ,
        'anzeige_wert'   => $ist_fallback ? $config_wert : $db_wert,
        'config_wert'    => $config_wert,
        'fallback_class' => $ist_fallback ? 'autooption-fallback' : '',
        'input_id'       => 'autooption_' . $Feld_Schluessel . '_input',
        'label_id'       => 'autooption_' . $Feld_Schluessel . '_label',
        'radio_name'     => 'autooption_' . $Feld_Schluessel . '_radio',
    ];
}

# FesteLadeleistung: eigenständig für den Dropdown-Modus "Slider" (Ladeleistung W) verdrahtet -
# bewusst NICHT Teil von $AutoOptionsFelder, da es fest an diesen Hauptmodus gebunden ist statt an
# das Auto-Options-Panel. Gleiche Fallback-Logik wie bei den Auto-Options-Feldern (Config-Wert +
# rote Markierung, wenn Zeile abgelaufen/kein DB-Wert/DB-Wert==Config-Wert).
$FesteLadeleistung_Config_Wert = isset($Ladeberechnung['FesteLadeleistung']) ? (int) $Ladeberechnung['FesteLadeleistung'] : 0;
$FesteLadeleistung_DB_Wert = isset($EV_Reservierung['FesteLadeleistung']['Res_Feld2']) ? (int) $EV_Reservierung['FesteLadeleistung']['Res_Feld2'] : null;
$FesteLadeleistung_Options = isset($EV_Reservierung['FesteLadeleistung']['Options']) ? (int) $EV_Reservierung['FesteLadeleistung']['Options'] : 0;
$FesteLadeleistung_abgelaufen = ($FesteLadeleistung_Options < time());
$FesteLadeleistung_ist_fallback = $FesteLadeleistung_abgelaufen || is_null($FesteLadeleistung_DB_Wert) || ($FesteLadeleistung_DB_Wert === $FesteLadeleistung_Config_Wert);
$DB_FesteLadeleistung_wert = $FesteLadeleistung_ist_fallback ? $FesteLadeleistung_Config_Wert : $FesteLadeleistung_DB_Wert;
# Entspricht der angezeigte Wert exakt dem MaxLadung-Wert, hat Blau Vorrang vor der roten Fallback-Farbe
$MaxLadung_Config_Wert = isset($Ladeberechnung['MaxLadung']) ? (int) $Ladeberechnung['MaxLadung'] : 0;
$FesteLadeleistung_ist_maxladung = ($DB_FesteLadeleistung_wert === $MaxLadung_Config_Wert);
$FesteLadeleistung_Fallback_Class = $FesteLadeleistung_ist_maxladung ? 'autooption-maxladung' : ($FesteLadeleistung_ist_fallback ? 'autooption-fallback' : '');
?>

<!-- SLIDER -->
<div style='text-align: center;'>
    <p class="sliderbeschriftung">Ladegrenze mit Akkuschonung:
    <span class="checkbox-wrap">
    <select name="akkuschonung" id="akkuschonung" style="font-size: 1rem; padding: 2px 5px;">
        <option value="0" <?php echo ($DB_Akkuschon_wert === 0) ? 'selected' : ''; ?>>0 - Aus</option>
        <option value="1" <?php echo ($DB_Akkuschon_wert === 1) ? 'selected' : ''; ?>>1 - Ein</option>
        <option value="2" <?php echo ($DB_Akkuschon_wert === 2) ? 'selected' : ''; ?>>2 - Zell-U</option>
    </select>
    </span>
  <span class="gueltig" ><?php echo $gueltig_bis ?></span></p>
  <p class="sliderbeschriftung" style="margin-top:0 !important;">Gültigkeitsstunden bis "Auto":
  <input type="number" id="gueltigkeitsstunden" name="gueltigkeitsstunden" min="0" max="100" step="0.25" value="<?php echo $std_diff_anzeige ?>" style="width:80px; font-size:100%;">
  </p>
<div class="flex-container">
    <div>
  <select id="modus" class="dropdown" name="hausakkuladung" >
    <option value="Auto" <?php echo $DB_Auto_selected ?>>Auto</option>
    <option value="AutoOptions" <?php echo $DB_AutoOptions_selected ?>>AutoOptions</option>
    <option value="Slider" <?php echo $DB_Slider_selected ?>>Ladeleistung</option>
  </select>
</div>
    <div id="slider_wrapper" style="flex-grow: 1; <?php echo $DB_Slider_selected ? '' : 'display:none;' ?>">
<input class="autooption-input <?php echo $FesteLadeleistung_Fallback_Class ?>" id="feste_ladeleistung_feld" data-typ="zahl" data-config-wert="<?php echo htmlspecialchars($FesteLadeleistung_Config_Wert) ?>" data-maxladung-wert="<?php echo htmlspecialchars($MaxLadung_Config_Wert) ?>" type="number" value="<?php echo htmlspecialchars($DB_FesteLadeleistung_wert) ?>" oninput="autoOptionInput(this, null);">
    </div>
    <div id="maxladung_button_wrapper" style="<?php echo $DB_Slider_selected ? '' : 'display:none;' ?>">
<button type="button" id="maxladung_setzen_btn" class="speichern" style="position:static; transform:none; font-size:70%; padding:8px 14px; background-color:#58ACFA; border-color:#2f7fd1;" onclick="feste_ladeleistung_feld.value = <?php echo (int) ($Ladeberechnung['MaxLadung'] ?? 0); ?>; autoOptionInput(feste_ladeleistung_feld, null);">MaxLadung</button>
    </div>
</div>

<details id="auto_options_details" <?php echo $DB_AutoOptions_selected ? 'open' : '' ?>>
  <summary class="sliderbeschriftung" style="margin-top:0 !important; display:list-item; cursor:pointer;">Auto Options</summary>

<div class="flex-container" style="flex-direction: column; align-items: stretch;">
<?php foreach ($AutoOptionsFelder as $Feld_Schluessel => $Feld):
    $w = $AutoOptionsWerte[$Feld_Schluessel];
?>
<div class="autooption-row">
    <div>
      <label class="autooption-label" style="cursor:default;"><?php echo htmlspecialchars($Feld_Schluessel) ?></label>
    </div>
<?php if ($w['typ'] === 'prozent'): ?>
    <div style="display:flex; align-items:center; flex-grow: 1; gap: 0;"><label class="slider autooption-percent <?php echo $w['fallback_class'] ?>" id="<?php echo $w['label_id'] ?>" for="<?php echo $w['input_id'] ?>"><?php echo $w['anzeige_wert'] ?>%</label><input class="slider <?php echo $w['fallback_class'] ?>" id="<?php echo $w['input_id'] ?>" data-typ="prozent" data-config-wert="<?php echo htmlspecialchars($w['config_wert']) ?>" type="range" min="0" max="100" step="5" value="<?php echo $w['anzeige_wert'] ?>" oninput="autoOptionInput(this, '<?php echo $w['label_id'] ?>');" style="flex-grow: 1;">
    </div>
<?php elseif ($w['typ'] === 'zahl'): ?>
    <div style="flex-grow: 1">
<input class="autooption-input <?php echo $w['fallback_class'] ?>" id="<?php echo $w['input_id'] ?>" data-typ="zahl" data-config-wert="<?php echo htmlspecialchars($w['config_wert']) ?>" type="number" value="<?php echo htmlspecialchars($w['anzeige_wert']) ?>" oninput="autoOptionInput(this, null);">
    </div>
<?php elseif ($w['typ'] === 'liste'): ?>
    <div style="flex-grow: 1">
<select class="autooption-input <?php echo $w['fallback_class'] ?>" id="<?php echo $w['input_id'] ?>" data-typ="liste" data-config-wert="<?php echo htmlspecialchars($w['config_wert']) ?>" onchange="autoOptionInput(this, null);">
<?php foreach (($Feld['optionen'] ?? []) as $opt_wert => $opt_label): ?>
      <option value="<?php echo htmlspecialchars($opt_wert) ?>" <?php echo ((string) $opt_wert === (string) $w['anzeige_wert']) ? 'selected' : '' ?>><?php echo htmlspecialchars($opt_label) ?></option>
<?php endforeach; ?>
</select>
    </div>
<?php elseif ($w['typ'] === 'radio'): ?>
    <div style="flex-grow: 1">
<span class="autooption-input autooption-radio-group <?php echo $w['fallback_class'] ?>" id="<?php echo $w['input_id'] ?>" data-typ="radio" data-config-wert="<?php echo htmlspecialchars($w['config_wert']) ?>">
<?php foreach (($Feld['optionen'] ?? []) as $opt_wert => $opt_label): ?>
      <label style="white-space:nowrap; cursor:pointer; font-weight:normal;">
        <input type="radio" name="<?php echo $w['radio_name'] ?>" value="<?php echo htmlspecialchars($opt_wert) ?>" <?php echo ((string) $opt_wert === (string) $w['anzeige_wert']) ? 'checked' : '' ?> onchange="autoOptionInput(this, null, '<?php echo $w['input_id'] ?>');">
        <?php echo htmlspecialchars($opt_label) ?>
      </label>
<?php endforeach; ?>
</span>
    </div>
<?php endif; ?>
</div>
<?php endforeach; ?>
</div>
</details>
</div>
<!-- ENDE SLIDER -->

<br /> <div id="csv_file_data">

<?php
echo "<table class=\"center\"><tbody><tr><th>Tag und Zeit</th><th style=\"display:none\" >Tag,Zeit zum Dateieintrag noetig, versteckt</th><th>Prognose(KW)</th><th>Rest</th><th>$Res_Feld1</th><th>$Res_Feld2</th></tr>";
echo "\n";

// Variablen definieren
$Prognosewert_Sum = 0;
$Rest_KW_Sum = 0;
$Res_Feld1_Watt_Sum = 0;
$Res_Feld2_Watt_Sum = 0;
$Prognosewert = 0;
$Rest_KW = 0;
$Res_Feld1_Watt = 0;
$Res_Feld2_Watt = 0;
// Variablen definieren ENDE


foreach($Prognose['result']['watts'] AS $date => $Watt) {

// Summenbildung
$Prognosewert_Sum = number_format($Prognosewert_Sum + $Prognosewert,1);
$Rest_KW_Sum = number_format($Rest_KW_Sum + (float) $Rest_KW,1);
$Res_Feld1_Watt_Sum = number_format($Res_Feld1_Watt_Sum + (float) $Res_Feld1_Watt,1);
$Res_Feld2_Watt_Sum = number_format($Res_Feld2_Watt_Sum + (float) $Res_Feld2_Watt,1);
// Stunde aus $date extrahieren
$stunde = date('H:00:00', strtotime($date));
$datum = date('Y-m-d', strtotime($date));
$heute = date('Y-m-d');
# Wenn  Res_Feld2 = 'laufend' gesetzt dann zuweisen
if (isset($PrstLadeStd[$stunde]) and $datum == $heute) {
    if ($PrstLadeStd[$stunde]['Res_Feld2'] !== '0') $EV_Reservierung[$date]['Res_Feld2'] = $PrstLadeStd[$stunde]['Res_Feld2'];
}
if (isset($EV_Reservierung[$date]['Res_Feld1'])){
    $Res_Feld1_wert = (float) $EV_Reservierung[$date]['Res_Feld1']/1000;
} else {
    $Res_Feld1_wert = 0;
}

if ($Res_Feld1_wert <> 0) {
$Res_Feld1_Watt = number_format($Res_Feld1_wert, 1);
} else  { 
$Res_Feld1_Watt = "" ;
}

if (isset($EV_Reservierung[$date]['Res_Feld2'])){
    $Res_Feld2_wert = (float) $EV_Reservierung[$date]['Res_Feld2']/1000;
} else {
    $Res_Feld2_wert = 0;
}
if ($Res_Feld2_wert <> 0) {
$Res_Feld2_Watt = number_format($Res_Feld2_wert, 1);
} else  { 
$Res_Feld2_Watt = "" ;
}
$Prognosewert =number_format($Watt/1000, 1);
$Rest_KW = number_format($Prognosewert - (float) $Res_Feld2_Watt - (float) $Res_Feld1_Watt, 1);

// Hintergrund heute bzw. morgen 
$Tag_akt_Schl = substr($date,0,10);
$Tag_heute = date("Y-m-d");
$Hintergrund_Tag = '#FFFFFF';
if ($Tag_akt_Schl != $Tag_heute) $Hintergrund_Tag = '#F1F3F4';

// Hintergrund Rest
if ($Rest_KW >= 0) {
$Hintergrund_Rest = '#CCFFCC';
} else {
$Hintergrund_Rest = '#ff9090';
}
// Prognose in % von $PV_Leistung_KWp
$ProgProzent = $Prognosewert / $PV_Leistung_KWp * 100;

// Ausgabe der Summen
if (isset($Tag_vor_Schl) and $Tag_akt_Schl != $Tag_vor_Schl) {
echo "<tr bgcolor=#C1C0C0><td>Summen: </td><td style=\"display:none\" >Tag,Zeit zum Dateieintrag noetig, versteckt</td><td>$Prognosewert_Sum</td><td>$Rest_KW_Sum</td><td>$Res_Feld1_Watt_Sum</td><td>$Res_Feld2_Watt_Sum</td></tr>\n";
$Prognosewert_Sum = 0;
$Rest_KW_Sum = 0;
$Res_Feld1_Watt_Sum = 0;
$Res_Feld2_Watt_Sum = 0;
}

$Tag_vor_Schl = $Tag_akt_Schl;
# Wochentag in Deutsch ausgeben
$wochentage = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
$timestamp = strtotime($date);
$tagIndex = date('w', $timestamp); // 0 (So) bis 6 (Sa)

echo '<tr><td style="white-space: nowrap; text-align: left;" bgcolor='.$Hintergrund_Tag.' class="Tag_Zeit_lesbar" contenteditable="false">';
echo $wochentage[$tagIndex] . ' ' . date('d.m. H:i', $timestamp);
echo '</td><td style="white-space: nowrap; display:none" class="Tag_Zeit" contenteditable="false">';
echo $date;
echo '</td><td style="background: linear-gradient(90deg,  #ff5733 '.$ProgProzent.'%, '.$Hintergrund_Tag.' 0%)" class="Prognose" contenteditable="false">';
echo $Prognosewert;
echo '</td><td bgcolor='.$Hintergrund_Rest.' class="Rest" contenteditable="false">';
echo $Rest_KW;
echo '</td><td bgcolor='.$Hintergrund_Tag.' class="Res_Feld1" contenteditable="true">';
echo $Res_Feld1_Watt;
echo '</td><td bgcolor='.$Hintergrund_Tag.' class="Res_Feld2" contenteditable="true">';
echo $Res_Feld2_Watt;
echo "</td></tr>\n";

} //foreach($Prognose....

echo "<tr bgcolor=#C1C0C0><td>Summen: </td><td style=\"display:none\" >Tag,Zeit zum Dateieintrag noetig, versteckt</td><td>$Prognosewert_Sum</td><td>$Rest_KW_Sum</td><td>$Res_Feld1_Watt_Sum</td><td>$Res_Feld2_Watt_Sum</td></tr>";
echo "</tbody></table>\n";
?>
   <br />
  </div>
<script>
// Auto-Options-Felder (aus dem PHP-Array $AutoOptionsFelder) - auf Script-Top-Level, da sowohl der
// DOMContentLoaded-Block als auch der separate Speichern-Handler weiter unten darauf zugreifen.
// Neue Felder werden automatisch mitgenommen, ohne dass hier oder im Speichern-Handler etwas
// geändert werden muss - einfach in PHP im Array $AutoOptionsFelder ergänzen.
const AutoOptionsFelder = <?php echo json_encode(array_map(function ($Feld_Schluessel, $Feld) use ($AutoOptionsWerte) {
    $w = $AutoOptionsWerte[$Feld_Schluessel];
    return [
        'key'         => $Feld_Schluessel,
        'db_id'       => $Feld['db_id'],
        'input_id'    => $w['input_id'],
        'typ'         => $w['typ'],
        'radio_name'  => $w['radio_name'],
        'config_wert' => $w['config_wert'],
    ];
}, array_keys($AutoOptionsFelder), $AutoOptionsFelder)); ?>;

// Live-Farbumschaltung (rot = Config-Wert, grün = eigener Wert) für jedes Auto-Options-Feld.
// el ist je nach Feldtyp ein <input type="range">, <input type="number">, <select> oder ein
// einzelnes <input type="radio"> einer Gruppe. labelId ist nur bei typ 'prozent' gesetzt (das
// dortige %-Badge). farbZielId wird nur bei typ 'radio' gebraucht: dort trägt nicht das einzelne
// Radio-Element die Farbe, sondern der umschließende Gruppen-Container.
function autoOptionInput(el, labelId, farbZielId) {
  const farbZiel = farbZielId ? document.getElementById(farbZielId) : el;
  if (labelId) {
    document.getElementById(labelId).innerText = el.value + '%';
  }
  const typ = farbZiel.dataset.typ;
  const istConfigWert = (typ === 'liste' || typ === 'radio')
    ? (String(el.value) === String(farbZiel.dataset.configWert))
    : (parseInt(el.value, 10) === parseInt(farbZiel.dataset.configWert, 10));
  // Entspricht der Wert exakt dem MaxLadung-Wert (nur beim Ladeleistung-Feld gesetzt), hat Blau
  // Vorrang vor der roten Fallback-Farbe
  const istMaxLadungWert = (farbZiel.dataset.maxladungWert !== undefined)
    && (parseInt(el.value, 10) === parseInt(farbZiel.dataset.maxladungWert, 10));
  farbZiel.classList.toggle('autooption-maxladung', istMaxLadungWert);
  farbZiel.classList.toggle('autooption-fallback', istConfigWert && !istMaxLadungWert);
  if (labelId) {
    const labelEl = document.getElementById(labelId);
    labelEl.classList.toggle('autooption-maxladung', istMaxLadungWert);
    labelEl.classList.toggle('autooption-fallback', istConfigWert && !istMaxLadungWert);
  }
}

/* Auto-Options-Panel und Dropdown-Sichtbarkeit steuern */
  document.addEventListener('DOMContentLoaded', function () {
    // Ursprünglicher Gültigkeitsstunden-Wert aus der DB (vor jeglicher Live-Umschaltung im Dropdown)
    const DB_Std_Diff = <?php echo json_encode((float) $std_diff); ?>;

    function toggleSliderBereich(zeigen) {
      document.getElementById('slider_wrapper').style.display = zeigen ? '' : 'none';
      document.getElementById('maxladung_button_wrapper').style.display = zeigen ? '' : 'none';
    }

    document.getElementById('modus').addEventListener('change', function () {
      toggleSliderBereich(this.value === 'Slider');
      document.getElementById('auto_options_details').open = (this.value === 'AutoOptions');

      // Gültigkeitsstunden immer auf den echten DB-Wert setzen, außer bei Auto (dort 0) -
      // FesteLadeleistung (Ladeleistung) ist eine eigene, vom Modus unabhängige DB-Zeile und
      // braucht daher keinen eigenen Restore-Mechanismus mehr wie früher der Prozent-Slider.
      if (this.value !== 'Auto') {
        document.getElementById('gueltigkeitsstunden').value = DB_Std_Diff;
      }
    });
  });

/* Lesen und speichern der Daten */
$(document).ready(function(){

 $(document).on('click', '#import_data', function(){
  var ID = [];
  var tagzahler = 0;
  var tag_old = 0;
  var Schluessel = [];
  var Tag_Zeit = [];
  var Res_Feld1 = [];
  var Res_Feld2 = [];
  var Options = [];
  $('.Tag_Zeit').each(function(){
   var datum = new Date($(this).text());
    if (tag_old != datum.getDate()) {
        tagzahler++;
        tag_old = datum.getDate();
    }
   var std = String(tagzahler) + "-" + (String(datum.getHours()).padStart(2, "0") + ":" + String(datum.getMinutes()).padStart(2, "0"));
   ID.push(std);
   Schluessel.push('Reservierung');
   Options.push('');
   Tag_Zeit.push($(this).text());
  });
  // Nur Zahlen in den Feldern Res_Feldx erlauben
  $('.Res_Feld1').each(function(){
    let val = parseFloat($(this).text().replace(",", ".")) * 1000;
    Res_Feld1.push(Number.isFinite(val) ? val : 0);
  });
  $('.Res_Feld2').each(function(){
    let val = parseFloat($(this).text().replace(",", ".")) * 1000;
    Res_Feld2.push(Number.isFinite(val) ? val : 0);
  });

  const modus = document.querySelector('select[name="hausakkuladung"]').value;
  let js_value = (modus === "Slider") ? -3 : (modus === "AutoOptions" ? -4 : -1);
  let manuellesteuerung_options;

  if (modus == "Auto") {
      // Auto braucht keine Gültigkeitsstunden -> Options fest auf 0
      manuellesteuerung_options = 0;
    } else {
      // AutoOptions / Slider: Gültigkeitsstunden direkt aus dem Eingabefeld lesen
      let eingabe = document.getElementById('gueltigkeitsstunden').value;
      let parsed = parseFloat(String(eingabe).replace(",", "."));
      let hours = (eingabe !== "" && !isNaN(parsed) && parsed >= 0 && parsed <= 100) ? parsed : 0;
      // Bei 0 Stunden explizit 0 speichern (statt "jetzt"), damit AutoOptions und der davon
      // abgeleitete MindBattLad-Timestamp konsistent 0 bekommen
      manuellesteuerung_options = (hours === 0) ? 0 : Math.floor(Date.now() / 1000) + hours * 3600;
    }

  // Akkuschonung (0, 1 oder 2) auslesen – bei Modus "Auto" fest 0 speichern
  let as_modus = (modus === "Auto") ? 0 : (parseInt(document.querySelector('select[name="akkuschonung"]').value, 10) || 0);

  // Res_Feld2 hängt vom Modus ab:
  // Auto/AutoOptions -> fest -1 (analog zur Kennung in CONFIG/charge_priv.ini)
  // Slider ("Ladeleistung") -> ungenutzt (0); der eigentliche Watt-Wert steht in der eigenständigen
  // FesteLadeleistung-Zeile (weiter unten gespeichert) - für die Steuerung reicht Res_Feld1=-3 als
  // Moduskennung, ein zusätzlicher Wert hier wird von der Oberfläche nicht (mehr) gelesen
  let res_feld2_wert;
  if (modus === "Auto" || modus === "AutoOptions") {
    res_feld2_wert = -1;
  } else {
    res_feld2_wert = 0;
  }

  ID.push("23:59");
  Schluessel.push("ChargeOption");
  Tag_Zeit.push("ManuelleSteuerung");
  Res_Feld1.push(js_value);
  Res_Feld2.push(res_feld2_wert);
  Options.push(manuellesteuerung_options);

  // Akkuschonung als eigene, von der ManuelleSteuerung-Gültigkeit unabhängige Zeile
  // Eigene ID (nicht "23:59"), da sonst die gleiche ID wie die ManuelleSteuerung-Zeile
  // beim Speichern zu einem Überschreiben statt zwei getrennten Zeilen führt
  ID.push("23:58");
  Schluessel.push("ChargeOption");
  Tag_Zeit.push("Akkuschonung");
  Res_Feld1.push(0);
  Res_Feld2.push(as_modus);
  Options.push(manuellesteuerung_options);

  // Alle Auto-Options-Felder (z.B. MindBattLad) generisch speichern - vom Dropdown-Modus
  // unabhängige, eigene Zeilen. Timestamp wird nur übernommen, wenn "AutoOptions" gewählt ist
  // (identisch zum ManuelleSteuerung-Timestamp), sonst 0. Neue Felder in $AutoOptionsFelder (PHP)
  // werden hier automatisch mitgespeichert, ohne dass dieser Code geändert werden muss.
  AutoOptionsFelder.forEach(function (feld) {
    let feld_wert;
    if (feld.typ === 'radio') {
      let checkedEl = document.querySelector('input[name="' + feld.radio_name + '"]:checked');
      feld_wert = checkedEl ? (parseInt(checkedEl.value) || 0) : 0;
    } else {
      let inputEl = document.getElementById(feld.input_id);
      feld_wert = parseInt(inputEl.value) || 0;
    }
    // Entspricht der Wert ohnehin dem Config-Wert (ini), ist kein eigener Timestamp nötig -> 0
    let istConfigWert = (String(feld_wert) === String(feld.config_wert));
    ID.push(feld.db_id);
    Schluessel.push("ChargeOption");
    Tag_Zeit.push(feld.key);
    Res_Feld1.push(0);
    Res_Feld2.push(feld_wert);
    Options.push((modus === "AutoOptions" && !istConfigWert) ? manuellesteuerung_options : 0);
  });

  // FesteLadeleistung: eigenständig für Modus "Slider" (Ladeleistung W) verdrahtet, nicht Teil
  // von AutoOptionsFelder. Timestamp nur bei Modus Slider UND wenn der Wert vom Config-Wert abweicht.
  const FesteLadeleistungConfigWert = <?php echo (int) $FesteLadeleistung_Config_Wert; ?>;
  let feste_ladeleistung_wert = parseInt(document.getElementById('feste_ladeleistung_feld').value) || 0;
  let FesteLadeleistung_istConfigWert = (feste_ladeleistung_wert === FesteLadeleistungConfigWert);
  ID.push("23:56");
  Schluessel.push("ChargeOption");
  Tag_Zeit.push("FesteLadeleistung");
  Res_Feld1.push(0);
  Res_Feld2.push(feste_ladeleistung_wert);
  Options.push((modus === "Slider" && !FesteLadeleistung_istConfigWert) ? manuellesteuerung_options : 0);
  //alert(js_value);

  $.ajax({
   url:"SQL_speichern.php",
   method:"post",
   data:{ID:ID, Schluessel:Schluessel, Tag_Zeit:Tag_Zeit, Res_Feld1:Res_Feld1, Res_Feld2:Res_Feld2, Options:Options},
   success:function(data)
   {
    //alert(data);
    window.location.href = "index.php?tab=<?php echo $activeTab; ?>";
   }
  })
 });
});
</script>
