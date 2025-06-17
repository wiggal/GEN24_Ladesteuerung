(**ACHTUNG:** Die Beschreibung kann in Einzelpunkten abweichend sein.)  
Stand 01.06.2025
# :floppy_disk: Installation GEN24_Ladesteuerung auf einem RaspberryPi

## Von folgenden Voraussetzungen wird ausgegangen:  
* Die Grundinstallation des RaspberryPi auf der SD-Karte erfolgt auf einem Debian-Linux.  
* Der Benutzer auf dem RaspberryPi ist der Standard-USER „pi“  
* Die Scripte von https://github.com/wiggal/GEN24_Ladesteuerung werden unter /home/GEN24/ abgelegt  
* Zu Fehlern und Problemen siehe auch [Tipps-und-Tricks](https://github.com/wiggal/GEN24_Ladesteuerung/wiki/Tipps-und-Tricks)
  
## Installation System:  
* Raspberry Pi Imager installieren  
`sudo apt install rpi-imager`  
* Micro-SD Karte einlegen  
* Raspberry Pi Imager starten  
Betriebssystem auswählen → Raps Pi OS (other) → Rasp Pi OS Lite (64-bit)
SD-Karte wählen  
* Erweiterte Optionen   
x	Hostname „raspberrrypi.local“  
x	SSH aktivieren → Password zur Authentifizierung verwenden  
x	Wifi einrichten → SSID = "WLAN-Name" → Password "XXX" → Wifi-Land = DE  
x	Spracheinstellungen → Zeitzone=Berlin → Tastaturlayout=de  
Speichern  
SCHREIBEN → alles löschen → JA  
* MicroSD in Raspberry einlegen und warten bis er hochgefahren ist  

## Python Installationen  
```
sudo apt install python3
sudo apt install python3-pip
sudo pip install requests
``` 
## Skripte GEN24_Ladesteuerung installieren  
Am besten die Scripte mit `git` holen, dann könen sie einfach upgedatet werden, ohne geänderte Dateien zu überschreiben.  

```
# Erstinstallation Verzeichnis /home/GEN24 erzeugen:
git clone https://github.com/wiggal/GEN24_Ladesteuerung.git .
# Die CONFIG/XY.ini's nach CONFIG/XY_priv.ini's und die html/config.php nach html/config_priv.php kopieren.
# Anpassungen in den CONFIG/XY_priv.ini's und in html/config_priv.php machen.
# Nun können die Neuerungen immer mit git geholt werden, ohne die Änderungen zu überschreiben
# Update mit git
git pull
# Tipp: Dateien die zukünftig nicht mehr überschieben werden sollen (z.B. weatherData.json) in die Datei .gitignore aufnehmen.
```
**Alternativ:**
* Verzeichnis /home/GEN24 erzeugen, Scripte downloaden, entpacken und Rechte setzen.  
  Die Befehle müssen mit `sudo` ausgeführt werden, da unter `/home/` nur `root` Schreibrechte hat.
```
cd /home/
sudo wget https://github.com/wiggal/GEN24_Ladesteuerung/archive/refs/heads/main.zip
sudo unzip main.zip
sudo rm main.zip
sudo mv GEN24_Ladesteuerung-main GEN24
sudo chown -R pi:pi /home/GEN24
sudo chmod +x /home/GEN24/start_PythonScript.sh
```
**Konfiguration:**
* Konfiguration der Ladesteuerung  
Die jeweilige CONFIG/XY.ini nach CONFIG/XY_priv.ini und die html/config.php nach html/config_priv.php kopieren.
Anpassungen in den CONFIG/XY_priv.ini's und in html/config_priv.php machen, siehe auch die jeweils verlinkte Hilfe in der WebUI, bzw. hier im Wiki

* Crontabeinträge  
`crontab -e`  # Editor wählen und folgende Einträge machen.  
http_SymoGen24Controller2.py immer eine Minute nach vollen zehn Minuten ausführen (1-56/10), da der GEN24 die Daten immer etwa zur vollen fünften Minute bereitstellt. Da das Smartmeter die Daten aktuell hat, kann beim Ausführen zur vollen fünften Minute passieren, dass die Daten vom GEN24 noch nicht zur Verfügung stehen. Dadurch entstehen unschöne Zacken in der Tagesgrafik.

```
1-56/10 * * * * /DIR/start_PythonScript.sh http_SymoGen24Controller2.py schreiben
```
**ACHTUNG:** nur den Wetterdienst eintragen, den ihr verwenden wollt, bzw. die als Backup dienen nur einmal am Tag.
```
33 5,8,10,12,14 * * * /DIR/start_PythonScript.sh FORECAST/Forecast_solar__WeatherData.py
8 5,7,9,11,13,15 * * * /DIR/start_PythonScript.sh FORECAST/Solarprognose_WeatherData.py
0 6,8,11,13,15 * * * /DIR/start_PythonScript.sh FORECAST/Solcast_WeatherData.py
0 5,7,9,11,13,15,17,19 * * * /DIR/start_PythonScript.sh FORECAST/Akkudoktor__WeatherData.py
```
**Crontab.log jeden Montag abräumen**
```
0 5 * * 1 mv /DIR/Crontab.log /DIR/Crontab.log_weg
```

* Editor mit schreiben beenden, folgende Meldung muss erscheinen, damit die Conjobs aktiv sind:  
„crontab: installing new crontab“

## Webserver Installation:  
  
**PHP installieren:**
```
sudo apt update && sudo apt upgrade
sudo apt install php php-sqlite3
```
Wenn PHP installiert ist, wird durch die Variable `Einfacher_PHP_Webserver = 1` (Standard) in der CONFIG/default_priv.ini beim ersten Start von  `start_PythonScript.sh` automatisch der einfache PHP-Webserver gestartet werden. Die Webseite ist dann auf Port:2424 erreichbar (z.B.: raspberrypi:2424).


**_Alternativ kann auch der Webserver Apache installiert werden:_**  
(dann `Einfacher_PHP_Webserver = 0` setzen)  
**Apache installieren und konfigurieren:**
```
sudo apt update && sudo apt upgrade
sudo apt install apache2
```
Änderungen der Apachekonfiguration unter /etc/apache2/:  
ApacheUser auf „pi“ und DokumetRoot auf /home/GEN24/html/ ändern

* /etc/apache2/apache2.conf `<Directory /var/www/>` nach `<Directory /home/GEN24/html/>` ändern.  
* /etc/apache2/envvars `export APACHE_RUN_USER=www-data` nach `export APACHE_RUN_USER=pi` ändern.  
* /etc/apache2/envvars `export APACHE_RUN_GROUP=www-data` nach `export APACHE_RUN_GROUP=pi` ändern.   
* /etc/apache2/sites-enabled/000-default.conf `DocumentRoot /var/www/html` nach `DocumentRoot /home/GEN24/html` ändern.  

Apache neu starten  
`sudo service apache2 restart`

**Vorhandene Skripts:**  
1_tab_LadeSteuerung.php    ==>> Reservierung von großen PV-Mengen und feste manuelle Ladesteuerung  
2_tab_EntladeSteuerung.php ==>>  EntladeSteuerung durch Eintrag in Tabelle und feste manuelle Entladesteuerung  
4_tab_config_ini.php       ==>> Anzeigen und Editieren der CONFIG/XY_priv.ini's  
5_tab_Crontab_log.php      ==>> Anzeigen der Logdatei Crontab.log  
6_tab_GEN24.php            ==>> lokaler Aufruf des GEN24  
7_tab_Diagram.php          ==>> Diagramme der Strompreise (nur wenn DynamicPriceCheck.py läuft)  
8_tab_Diagram.php          ==>> Diagramm Quelle und Ziel der Energie  
9_tab_settigs.php          ==>> Settings, ändern der Startparameter der Ladesteuerung  

In der `html/config_priv.php` können die tab_Skripte unter `$TAB_config` konfiguriert werden. Man kann den Namen ändern, Tab's die nicht benötigt werden ausblenden, den Tab der beim Start geladen wird auswählen und eigene Skripts als "Tab" einbinden. 

