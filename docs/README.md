![License](https://img.shields.io/github/license/wiggal/GEN24_Ladesteuerung)
![Debian](https://img.shields.io/badge/Debian-supported-A81D33?logo=debian)
![Alpine Linux](https://img.shields.io/badge/Alpine%20Linux-3.x-0D597F?logo=alpinelinux)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)
![PHP](https://img.shields.io/badge/PHP-8.x-777BB4?logo=php)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?logo=chartdotjs)<br>
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-compatible-C51A4A?logo=raspberrypi)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1%2B-41BDF5?logo=homeassistant)
![Fronius](https://img.shields.io/badge/Fronius-GEN24-E2001A?logo=data:image/svg+xml;base64,...)
![Wattpilot](https://img.shields.io/badge/Fronius-Wattpilot-E2001A)
![OCPP](https://img.shields.io/badge/OCPP-1.6J-00A651)
![MQTT](https://img.shields.io/badge/MQTT-green)

## ⚡☀️ EnergyWIGGAL mit MQTT🔋🚘

<h1>GEN24_Ladesteuerung mit MQTT</h1>

<p>Dieser Fork hat zusätzlich 2 Addons, die MQTT-Statusmeldungen senden und MQTT-Befehle entgegenehmen können</p>

<h2>Installation</h2>
Die 2 Addons mqtt_prognose.py und mqtt_steuerung.py in /ADDONS ablegen, die mqtt.ini unter /CONFIG und nach mqtt_priv.ini kopieren und Einstellungen anpassen.
Dann 2 Cronjobs über den Scheduler (Settings - Scheduler) eintragen:
MQTT Statusmeldungen ausgeben:
Minuten: 0,15,30,45   (auch andere Intervalle gehen)
Befehl: [Webserververzeichnis]/start_PythonScript.sh ADDONS/mqtt_prognose.py

MQTT Statusmeldungen empfangen:
Minuten: * (jede Minute)
Befehl: [Webserververzeichnis]/start_PythonScript.sh ADDONS/mqtt_steuerung.py

[Webserververzeichnis] entsprechend dem eigenen Server anpassen, damit start_PythonScript.sh aufgerufen wird, analog zu den anderen cronjobs

<h2>Überblick MQTT Topics</h2>

<p>Alle Topics liegen unter dem Basistopic <code>gen24</code> (Einstellung <code>Topic_Base</code> in <code>CONFIG/mqtt.ini</code> bzw. <code>mqtt_priv.ini</code>). Drei Skripte senden oder lesen sie.</p>

<table>
<thead>
<tr><th>Zweig</th><th>Richtung</th><th>Quelle</th><th>Wann</th><th>Retained</th></tr>
</thead>
<tbody>
<tr><td><code>gen24/stunden/&lt;tag&gt;</code></td><td>Programm → Broker</td><td><code>ADDONS/mqtt_prognose.py</code></td><td>Scheduler, z. B. alle 5 Minuten, und nach jedem geschriebenen Set-Befehl</td><td>nach <code>Retain</code> (Standard 1)</td></tr>
<tr><td><code>gen24/&lt;serie&gt;/&lt;tag&gt;/sum/wert</code></td><td>Programm → Broker</td><td><code>ADDONS/mqtt_prognose.py</code></td><td>wie oben</td><td>nach <code>Retain</code></td></tr>
<tr><td><code>gen24/status/&lt;name&gt;</code></td><td>Programm → Broker</td><td>Hook in <code>EnergyController.py</code></td><td>bei jedem Lauf der Batteriesteuerung, wenn <code>Status_senden = 1</code></td><td>nach <code>Retain</code></td></tr>
<tr><td><code>gen24/set/...</code></td><td>Broker → Programm</td><td><code>ADDONS/mqtt_steuerung.py</code></td><td>Scheduler jede Minute, wenn <code>Steuerung_empfangen = 1</code></td><td>muss retained gesendet werden</td></tr>
<tr><td><code>gen24/ack/...</code></td><td>Programm → Broker</td><td><code>ADDONS/mqtt_steuerung.py</code></td><td>nur nach neuem Set-Befehl</td><td>nach <code>Retain</code></td></tr>
</tbody>
</table>

<p>Platzhalter: <code>&lt;tag&gt;</code> ist <code>heute</code>, <code>morgen</code> oder <code>uebermorgen</code>. <code>&lt;HH&gt;</code> ist die Stunde zweistellig von <code>00</code> bis <code>23</code>.</p>

<p>Scheduler-Einträge:</p>
<pre><code>start_PythonScript.sh ADDONS/mqtt_prognose.py     (z. B. alle 5 Minuten)
start_PythonScript.sh ADDONS/mqtt_steuerung.py    (jede Minute)</code></pre>

<h2>Prognose und Planung</h2>

<p>Je Tag gibt es ein JSON mit allen Stundenwerten und vier Tagessummen, also 15 Topics für heute, morgen und übermorgen. Stunden ohne Wert werden mit 0 gefüllt.</p>

<table>
<thead>
<tr><th>Topic</th><th>Inhalt</th><th>Einheit</th></tr>
</thead>
<tbody>
<tr><td><code>gen24/stunden/&lt;tag&gt;</code></td><td>JSON mit <code>datum</code> (YYYY-MM-DD) und je Stunde <code>forecast_&lt;HH&gt;h</code>, <code>geplant_&lt;HH&gt;h</code>, <code>laufend_&lt;HH&gt;h</code>, <code>diff_&lt;HH&gt;h</code></td><td>kW, 3 Nachkommastellen</td></tr>
<tr><td><code>gen24/prognose/&lt;tag&gt;/sum/wert</code></td><td>Tagessumme der PV-Prognose</td><td>kWh</td></tr>
<tr><td><code>gen24/planung_einmal/&lt;tag&gt;/sum/wert</code></td><td>Tagessumme geplanter Verbrauch einmal</td><td>kWh</td></tr>
<tr><td><code>gen24/planung_laufend/&lt;tag&gt;/sum/wert</code></td><td>Tagessumme geplanter Verbrauch laufend</td><td>kWh</td></tr>
<tr><td><code>gen24/differenz/&lt;tag&gt;/sum/wert</code></td><td>Tagessumme Rest (Prognose − einmal − laufend)</td><td>kWh</td></tr>
</tbody>
</table>

<p>Beispiel für einen Ausschnitt aus <code>gen24/stunden/heute</code> (Zahlen ausgedacht):</p>
<pre><code>{"datum": "2026-10-21", "forecast_12h": 3.2, "diff_12h": 1.2, "geplant_12h": 2.0, "laufend_12h": 0.0, ...}</code></pre>

<p><code>laufend</code> ist der Wert der Zeile selbst, sonst der letzte Wert früherer Tage zur gleichen Uhrzeit (Regel aus <code>SQLall.py</code>).</p>

<h2>Statuswerte der Batteriesteuerung</h2>

<p>Bei jedem Lauf von <code>EnergyController.py</code> gehen 14 Einzelwerte unter <code>gen24/status/</code> raus, dieselben Werte wie auf der Seite Logfiles.</p>

<table>
<thead>
<tr><th>Topic</th><th>Inhalt</th><th>Einheit</th></tr>
</thead>
<tbody>
<tr><td><code>gen24/status/zeit</code></td><td>Zeitpunkt des Laufs (YYYY-MM-DD HH:MM:SS)</td><td></td></tr>
<tr><td><code>gen24/status/pv_produktion</code></td><td>aktuelle PV-Produktion</td><td>W</td></tr>
<tr><td><code>gen24/status/einspeisung</code></td><td>aktuelle Einspeisung, positiv = Einspeisung</td><td>W</td></tr>
<tr><td><code>gen24/status/batterie_power</code></td><td>aktuelle Batterieleistung</td><td>W</td></tr>
<tr><td><code>gen24/status/verbrauch_haus</code></td><td>Gesamtverbrauch Haus</td><td>W</td></tr>
<tr><td><code>gen24/status/batterie_soc</code></td><td>Ladestand</td><td>%</td></tr>
<tr><td><code>gen24/status/batterie_freie_kapazitaet</code></td><td>freie Batteriekapazität (im Log „aktuelleBattKapazität“)</td><td>Wh</td></tr>
<tr><td><code>gen24/status/ladewert_alt</code></td><td>bisheriger Ladewert</td><td>W</td></tr>
<tr><td><code>gen24/status/ladewert_neu</code></td><td>neuer Ladewert</td><td>W</td></tr>
<tr><td><code>gen24/status/ladewert_grund</code></td><td>Begründung für den Ladewert</td><td>Text</td></tr>
<tr><td><code>gen24/status/batt_voll_um</code></td><td>erwartete Uhrzeit Batterie voll</td><td>Uhr</td></tr>
<tr><td><code>gen24/status/prognose_aktuell</code></td><td>aktuelle Prognose</td><td>W</td></tr>
<tr><td><code>gen24/status/prognose_tag</code></td><td>Tagesprognose gesamt</td><td>Wh</td></tr>
<tr><td><code>gen24/status/grundlast_summe</code></td><td>Summe Grundlast</td><td>Wh</td></tr>
</tbody>
</table>

<h2>Set-Befehle und Rückmeldungen</h2>

<p>Befehle werden retained an <code>gen24/set/...</code> gesendet. Zu jedem neuen Befehl meldet das Addon unter <code>gen24/ack/&lt;gleicher Pfad&gt;</code> zurück, z. B. <code>gen24/ack/stunden</code> mit <code>ok ...</code> oder <code>fehler ...</code>.</p>

<table>
<thead>
<tr><th>Topic</th><th>Seite</th><th>Erlaubte Werte</th><th>Hinweis</th></tr>
</thead>
<tbody>
<tr><td><code>gen24/set/geplant/&lt;tag&gt;/&lt;HH&gt;h</code></td><td>Planung einmal</td><td>kW, 0 bis <code>Geplant_Max_kW</code> (Standard 20)</td><td><code>&lt;tag&gt;</code> auch als Datum YYYY-MM-DD; 0 löscht den Eintrag</td></tr>
<tr><td><code>gen24/set/laufend/&lt;HH&gt;h</code></td><td>Planung laufend</td><td>kW, 0 bis <code>Geplant_Max_kW</code></td><td>gilt ab heute jeden Tag zur gleichen Uhrzeit; 0 löscht</td></tr>
<tr><td><code>gen24/set/modus</code></td><td>LadeStrg</td><td><code>auto</code>, <code>autooptions</code>, <code>ladeleistung</code></td><td><code>auto</code> beendet alle Übersteuerungen</td></tr>
<tr><td><code>gen24/set/stunden</code></td><td>LadeStrg</td><td>0 bis 100</td><td>„Stunden bis Auto“; 0 = keine Wirkung</td></tr>
<tr><td><code>gen24/set/akkuschonung</code></td><td>LadeStrg</td><td>0, 1, 2</td><td>wirkt nur bei <code>autooptions</code> und <code>ladeleistung</code></td></tr>
<tr><td><code>gen24/set/ladeleistung</code></td><td>LadeStrg</td><td>W, −1 bis MaxLadung aus <code>charge.ini</code></td><td>wirkt nur bei <code>ladeleistung</code></td></tr>
<tr><td><code>gen24/set/autooptions/&lt;Schlüssel&gt;</code></td><td>LadeStrg</td><td>je nach Feldtyp, <code>prozent</code> = 0 bis 100</td><td>Felder aus <code>[AutoOptionsFelder]</code> in <code>html/config.ini</code>/<code>config_priv.ini</code>, z. B. <code>autooptions/MindBattLad</code>; Feld muss in <code>charge.ini</code> stehen</td></tr>
<tr><td><code>gen24/set/betrieb</code></td><td>Settings</td><td><code>webui_aus</code>, <code>aus_loeschen</code>, <code>aus_belassen</code>, <code>analyse</code>, <code>ladesteuerung</code> oder 0 bis 4</td><td><code>aus_loeschen</code> löscht beim nächsten Lauf die zeitabhängigen Batterie-Einträge im Wechselrichter</td></tr>
<tr><td><code>gen24/set/betrieb_optionen</code></td><td>Settings</td><td>Liste aus <code>logging</code>, <code>laden</code>, <code>entladen</code>, <code>optimierung</code>, <code>notstrom</code>, <code>dynamicprice</code></td><td>nur bei <code>betrieb</code> = <code>ladesteuerung</code>, z. B. <code>logging,laden,entladen</code></td></tr>
</tbody>
</table>

<p>Das Addon übernimmt einen Befehl nur, wenn sich der Wert am Broker seit dem letzten Abruf geändert hat (gemerkt in <code>ADDONS/mqtt_steuerung_last.json</code>). Die Weboberfläche bleibt so parallel bedienbar, die letzte Änderung gilt.</p>

<h2>Hinweise</h2>

<p>Nicht mehr gesendet werden die Einzel-Topics der ersten Version (<code>gen24/&lt;serie&gt;/&lt;tag&gt;/&lt;HH&gt;/wert</code> und <code>gen24/&lt;serie&gt;/&lt;tag&gt;/datum</code>). Am Broker werden sie mit <code>start_PythonScript.sh ADDONS/mqtt_prognose.py aufraeumen</code> gelöscht.</p>

<p>Wer in <code>gen24/set/#</code> schreiben darf, kann die Ladesteuerung abschalten. Zugriffsrechte am Broker sind deshalb sinnvoll.</p>
