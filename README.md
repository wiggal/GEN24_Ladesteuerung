## :sunny: GEN24_Ladesteuerung :battery:
(getestet unter Python 3.8 und 3.9)

![Screenshot](pics/Steuerungstabellen.png)

- Ladesteuerung für  Fronius Symo GEN24 Plus um die Einspeisebegrenzung (bei mir 70%) zu umgehen,
und die Produktion über der AC-Ausgangsleistung des WR als DC in die Batterie zu laden.  
- Entladesteuerung, um die Entladung der Batterie bei großen Verbräuchen zu steuern.  

Die Ladung des Hausakkus erfolgt prognosebasiert und kann mit der Variablen „BatSparFaktor“ in der „config.ini“ gesteuert werden.  
Hier zwei Grafiken um die Auswirkung des „BatSparFaktor“ zu verdeutlichen:  
![Screenshot](pics/Ladewertverteilung.png)

## :floppy_disk: Installationshinweise: [(siehe auch)](https://github.com/wiggal/GEN24_Ladesteuerung/wiki/Installation-GEN24_Ladesteuerung-auf-einem-RaspberryPi)
Voraussetzung ist, dass "Slave als Modbus TCP" am GEN24 aktiv  
und auf "int + SF" gestellt ist, sonst passen die Register nicht.

Folgende Installationen sind nötig, damit die Pythonskripte funktionieren  
(getestet auf einem Ubuntu/Mint und auf einem Raspberry Pi mit Debian GNU/Linux 11)
```
sudo apt install python3
sudo apt install python3-pip
sudo pip install pyModbusTCP==v0.1.10   # mit Version 0.2.x nicht lauffähig
sudo pip install pickledb
sudo pip install pytz
sudo pip install xmltodict
sudo pip install NumPy==v1.23.1
sudo pip install requests
sudo pip install ping3
```
Mit start_PythonScript.sh können Pythonskripte per Cronjobs oder auf der Shell gestartet werden, die Ausgabe erfolgt dann in die Datei "Crontab.log".  
Als Erstes muss ein Prognoseskript aufgerufen werden, damit neue Prognosedaten in der Datei weatherData.json vorhanden sind!  

Beispiele für Crontabeinträge ("DIR" durch dein Installationverzeichnis ersetzen)  
Ausführrechte für das start_PythonScript.sh Skript setzen nicht vergessen (chmod +x start_PythonScript.sh)

```
*/5 06-16 * * * /DIR/start_PythonScript.sh SymoGen24Controller2.py schreiben
33 5,8,10,12,14,19 * * * /DIR/start_PythonScript.sh WeatherDataProvider2.py
8 5,7,9,11,13,15,17 * * * /DIR/start_PythonScript.sh Solarprognose_WeatherData.py
1 6,8,11,13,15 * * * /DIR/start_PythonScript.sh Solcast_WeatherData.py
#Crontab.log jeden Montag abräumen
0 5 * * 1 mv /DIR/Crontab.log /DIR/Crontab.log_weg
```

### :sun_behind_rain_cloud: WeatherDataProvider2.py

holt die Leistungsprognose von forecast.solar und schreibt sie in weatherData.json  
Damit die Wetterdaten aktuell bleiben ist es besser sie öfters am Tag abzurufen (bei mir alle 2-3 Std)

### :sun_behind_rain_cloud: Solarprognose_WeatherData.py 

Kann alternativ zu WeatherDataProvider2.py benutzt werden, ist etwas genauer, es ist aber ein Account erforderlich,
hier wird eine genauer Zeitpunkt für die Anforderung vorgegeben.  
Holt die Leistungsprognose von solarprognose.de und schreibt sie in weatherData.json.
Damit die Wetterdaten aktuell bleiben ist es besser sie öfter abzufragen (bei mir alle 2-3 Std)  

### :sun_behind_rain_cloud: Solcast_WeatherData.py

Kann auch alternativ zu WeatherDataProvider2.py benutzt werden, es ist ein "Home User" Account auf solcast.com erforderlich.  
Holt die Leistungsprognose von toolkit.solcast.com.au und schreibt sie in weatherData.json.
Leider kann Solcast_WeatherData.py nur 5x am Tag aufgerufen werden, da pro Lauf zwei Zugriffe erforderlich sind (10 pro Tag).  

### :chart_with_upwards_trend: SymoGen24Controller2.py

berechnet den aktuell besten Ladewert aufgrund der Werte in weatherData.json, den Akkustand und der tatsächlichen Einspeisung bzw Produktion und gibt sie aus.
Ist die Einspeisung über der Einspeisebegrenzung bzw. die Produktion über der AC-Kapazität der Wechselrichters, wird dies in der Ladewerteberechnung berücksichtigt.  
Mit dem Parameter "schreiben" aufgerufen (start_PythonScript.sh SymoGen24Controller2.py **schreiben**) schreibt er die Ladewerte auf den Wechselrichter  
falls Änderungen außerhalb der gesetzten Grenzen sind.

### SymoGen24Connector.py

Wird von SymoGen24Controller2.py aufgerufen und stellt die Verbindung zum Wechselrichter (GEN24 Plus) her.

**_NEU ab Version 0.10.4_**
### :bar_chart: Logging (optional)

Erfolgt nun beim Aufruf von SymoGen24Controller2.py, wenn in der "config.ini" Logging_ein = 1.
Das Logging schreibt Werte ins"Logging_file", im csv- oder sqlite-Format.  
**_ENDE NEU_**


#####################################################################

## Modul zur Reservierung von größeren Mengen PV-Leistung, manuelle Ladesteuerung bzw. Entladesteuerung
(z.B. E-Autos)

Das Modul ist in PHP programmiert und setzt einen entsprechend konfigurierten Webserver (z.B. Apache, ) voraus.  
Konfiguration muss eventuell in der "config.php" angepasst werden.  

Nur zum testen kann der PHPeigene Webserver benutzt werden. Einfach unter /DIR/html/ folgendes starten:  
php -S 0.0.0.0:7777  
Und im Browser localhost:7777 aufrufen.  

Webserver Apache z.B.:

### :floppy_disk: Installationshinweise: [(siehe auch)](https://github.com/wiggal/GEN24_Ladesteuerung/wiki/Installation-GEN24_Ladesteuerung-auf-einem-RaspberryPi)
**_NEU ab Version 0.11.0_**  
```
sudo apt install apache2 php
sudo apt install php-sqlite3
```
**_ENDE NEU_**  
In /etc/apache2/apache2.conf   
<Directory /srv/> durch <Directory /DIR/html/> ersetzen!  

In /etc/apache2/sites-available/000-default.conf  
DocumentRoot /var/www/html durch DocumentRoot /DIR/html/ ersetzen  

Apache neu starten  
sudo systemctl restart apache2  
Reservierung im Browser aufrufen (= IP oder localen Namen des RasberryPi).

ACHTUNG!! /DIR/ und /DIR/html/ muss Schreibrechte für den Webserver Apache haben!!  
Vorschlag:  
Den Apachewebserver unter demselben USER laufen lassen, unter dem man arbeitet bzw.auch die Crojobs laufen.
In der Datei `/etc/apache2/envvars` die Variablen `APACHE_RUN_USER` und `APACHE_RUN_GROUP` anpassen.  

Vorhandene Skripts:  
1_tab_LadeSteuerung.php    ==>> Reservierung von großen PV-Mengen und feste manuelle Ladesteuerung  
2_tab_EntladeSteuerung.php ==>>  EntladeSteuerung durch Eintrag in Tabelle und feste manuelle Entladesteuerung  
3_tab_Hilfe.html       ==>> Hile zu Reservierung von großen PV-Mengen  
4_tab_config_ini.php   ==>> Anzeigen und Editieren der config.ini  
5_tab_Crontab_log.php  ==>> Anzeigen der Logdatei Crontab.log  
6_tab_GEN24.php        ==>> lokaler Aufruf des GEN24  

Mit der Namenskonvention [1-9]_tab_xxxxxxx.[php|html] können eigene Skripts als "Tab" eingebunden werden.  


![Screenshot](pics/Ladesteuerung.png)
### Batterieladesteuerung ( TAB--> LadeSteuerung )

Alle eingetragenen Reservierungen werden in die Datei /DIR/Watt_Reservierung.json geschrieben.  
In der html/config.php müssen die Dateipfade und Variablen angepasst werden.   

Ist das Modul eingeschaltet (in /DIR/config.ini -->> PV_Reservierung_steuern = 1) wird die Reservierung  
beim nächsten Aufruf von SymoGen24Controller2.py in der Ladeberechnung berücksichtigt.

Mit einer gewählten Ladestufe (AUS, HALB, VOLL) unter Hausakkuladung wird die entsprechende Batterieladeleistung,
beim nächsten Aufruf von SymoGen24Controller2.py auf den Wechselrichter geschrieben.  
Die prognosebasierte Ladesteuerung ist dadurch deaktivieren, und kann mit der Option "AUTO" wieder aktiviert werden.  

Weitere Erklärungen stehen im Hilfetab 3_tab_Hilfe.html [Vorschau hier](pics/3_tab_Hilfe.pdf)

![Screenshot](pics/Entladesteuerung.png)
### BatterieENTladesteuerung ( TAB--> EntladeSteuerung )

Unter "Feste Entladegrenze " kann die maximale Entladeleistung
in den Schritten 0, 20, 40, 60, 80 oder 100 Prozent fest eingestellt werden.

In der Entladetabelle können Leistungen in KW zur Steuerung der Akkuentladung eingetragen werden.

Weitere Erklärungen stehen im Hilfetab 3_tab_Hilfe.html [Vorschau hier](pics/3_tab_Hilfe.pdf)

======================================================  
Das Programm wurde auf Grundlage von https://github.com/godfuture/SymoGen24Weather erstellt.  
Herzlichen Dank an "godfuture"

