
## ☀️ GEN24_Ladesteuerung 🔋 
(getestet unter Python 3.8 und 3.9)  
![new](pics/new.png)  
Ab Version: **0.20**  
[:chart_with_downwards_trend: http_SymoGen24Controller2.py](https://github.com/wiggal/GEN24_Ladesteuerung/#chart_with_downwards_trend-http_symogen24controller2py) `Maximale Ladeleistung` **per HTTP-Request** im Batteriemanagement setzen.  
Ab Version: **0.21.1**  
Zur Ermittlung der gesamten Produktion können auch mehrere GEN24 eingebunden werden.  
Ab Version: **0.21.2**  
Bei aktivierter EntladeSteuerung auch die `Maximale Entladeleistung` **per HTTP-Request** im Batteriemanagement setzen.  
![new](pics/new2.png)  

- Prognosebasierte Ladesteuerung für  Fronius Symo GEN24 Plus um eine Einspeisebegrenzung (bei mir 70%) zu umgehen,
und eine Produktion über der AC-Ausgangsleistungsgrenze des WR als DC in die Batterie zu laden.  
Über die Tabelle [Ladesteuerung](https://github.com/wiggal/GEN24_Ladesteuerung/#batterieladesteuerung--tab---ladesteuerung-) können große, geplante Verbräuche bei der Ladeplanung berücksichtigt werden.  
- [Entladesteuerung,](https://github.com/wiggal/GEN24_Ladesteuerung/#batterieentladesteuerung--tab---entladesteuerung-) um die Entladung der Batterie bei großen Verbräuchen zu steuern.  
- [Logging](https://github.com/wiggal/GEN24_Ladesteuerung/#bar_chart-logging) und grafische Darstellung von Produktion und Verbrauch.  
- Akkuschonung: Um eine LFP-Akku zu schonen, wird die Ladeleistung ab 80% auf 0,2C und ab 90% auf 0,1C beschränkt.  

Die Ladung des Hausakkus erfolgt prognosebasiert und kann mit der Variablen „BatSparFaktor“ in der „config.ini“ gesteuert werden.  
Hier zwei Grafiken um die Auswirkung des „BatSparFaktor“ zu verdeutlichen:  
![Auswirkung des BatSparFaktor](pics/Ladewertverteilung.png)

## 💾 Installationshinweise: [(siehe auch Wikibeitrag)](https://github.com/wiggal/GEN24_Ladesteuerung/wiki/Installation-GEN24_Ladesteuerung-auf-einem-RaspberryPi)
Bei Verwendung von **SymoGen24Controller2.py** ist Voraussetzung, dass "Slave als Modbus TCP" am GEN24 aktiv 
und auf "int + SF" gestellt ist.  
Bei Verwendung von **http_SymoGen24Controller2.py** wird Modbus nicht benötigt.

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
Als Erstes muss ein Prognoseskript aufgerufen werden, damit aktuelle Prognosedaten in der Datei weatherData.json vorhanden sind!  

Beispiele für Crontabeinträge ("DIR" durch dein Installationsverzeichnis ersetzen).  
Ausführrechte für das start_PythonScript.sh Skript setzen nicht vergessen (chmod +x start_PythonScript.sh).  
SymoGen24Controller2.py bzw. http_SymoGen24Controller2.py durchgehend (wegen Logging) alle 5/10 Minuten starten  
(Häufigerer Aufruf für Logging nicht sinnvoll, da der Gen24 die Zähler nur alle 5 Minuten aktualisiert!).  
Da bei der HTTP-Methode der WR die Einspeisebegrenzung regelt, reicht hier auch ein Aufruf alle 10 Minuten (1-59/10).  

```
1-59/5 * * * * /DIR/start_PythonScript.sh SymoGen24Controller2.py schreiben
```
**ODER!!**
```
1-59/10 * * * * /DIR/start_PythonScript.sh http_SymoGen24Controller2.py schreiben
```
**ACHTUNG:** nur den Wetterdienst eintragen, den ihr verwenden wollt.
```
33 5,8,10,12,14 * * * /DIR/start_PythonScript.sh WeatherDataProvider2.py
8 5,7,9,11,13,15 * * * /DIR/start_PythonScript.sh Solarprognose_WeatherData.py
0 6,8,11,13,15 * * * /DIR/start_PythonScript.sh Solcast_WeatherData.py
```
**Crontab.log jeden Montag abräumen**
```
0 0 * * 1 mv /DIR/Crontab.log /DIR/Crontab.log_weg
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

berechnet den aktuell besten Ladewert aufgrund der Prognosewerte in weatherData.json, dem Akkustand und der tatsächlichen Einspeisung bzw. Produktion und gibt sie aus.
Ist die Einspeisung über der Einspeisebegrenzung bzw. die Produktion über der AC-Kapazität der Wechselrichters, wird dies in der Ladewerteberechnung berücksichtigt.  
Mit dem Parameter "schreiben" aufgerufen (start_PythonScript.sh SymoGen24Controller2.py **schreiben**) schreibt er die Ladewerte **per Modbus** auf den Wechselrichter, 
falls die Änderung über der gesetzten Grenze ist.

### FUNCTIONS/SymoGen24Connector.py
Wird von SymoGen24Controller2.py aufgerufen und stellt die Verbindung **per Modbus** zum Wechselrichter (GEN24 Plus) her.

### :chart_with_downwards_trend: http_SymoGen24Controller2.py

berechnet den aktuell besten Ladewert aufgrund der Prognosewerte in weatherData.json und dem Akkustand und gibt sie aus. 
Ist die Produktion über der AC-Kapazität der Wechselrichters, wird dies in der Ladewerteberechnung berücksichtigt. 
Mit dem Parameter "schreiben" aufgerufen (start_PythonScript.sh http_SymoGen24Controller2.py **schreiben**) setzt es die `Maximale Ladeleistung` **per HTTP-Request** 
im Batteriemanagement des Wechselrichter, falls die Änderung über der gesetzten Grenze ist.
Die **Einspeisebegrenzung** muss hier nicht berücksichtigt werden, da dies das Batteriemanagement des GEN24 selber regelt (auch über der definierten `Maximale Ladeleistung`!)

## Webserver Installation (WebUI):  
Nicht zwingend erforderlich, die prognosebasierte Ladesteuerung funktioniert auch ohne WebUI (Webserver)  

**PHP installieren:**
```
sudo apt update && sudo apt upgrade
sudo apt install php php-sqlite3
```
Wenn PHP installiert ist, kann durch die Variable `Einfacher_PHP_Webserver = 1` in der config.ini beim ersten Start von  `start_PythonScript.sh` automatisch der einfache PHP-Webserver gestartet werden. Die Webseite ist dann auf Port:2424 erreichbar (z.B.: raspberrypi:2424). **Ab Version 0.21**


**_Alternativ kann auch der Webserver Apache installiert werden:_**  
[(siehe Wikibeitrag)](https://github.com/wiggal/GEN24_Ladesteuerung/wiki/Installation-GEN24_Ladesteuerung-auf-einem-RaspberryPi)

### :bar_chart: Logging

Wenn in der "config.ini" Logging_ein = 1 gesetzt ist, werden die Werte im "Logging_file" im sqlite-Format gespeichert.  
Beim Aufruf von `SymoGen24Controller2.py schreiben` oder `http_SymoGen24Controller2.py schreiben` wird die Ladesteuerung und das Logging ausgeführt. 
Beim Aufruf mit dem Parameter ` logging` wird nur das Logging ausgeführt, es erfolgt keine Ladesteuerung.  
Aus der SQLite-Datei werden dann in html/7_tab_Diagram.php Diagramme erzeugt.  
Hier z.B. das Liniendiagramm zur Tagesproduktion:  
![Grafik zur Tagesproduktion](pics/Tagesproduktion.png)
oder das Balkendiagramm zum Tagesverbrauch:  
![Grafik zur Tagesproduktion](pics/Tagesverbrauch.png)

html/8_tab_Diagram.php erzeugt ein Diagramm nach Quelle (wo kommt die Energie her) und Ziel (wo geht die Energie hin).  
Dadurch soll z.B. ein Laden der Batterie aus dem Netz ersichtlich bzw. gezählt werden.  
![Grafik zur Tagesproduktion](pics/QZ_Tag.png)

## Modul zur Reservierung von größeren Mengen PV-Leistung, manuelle Ladesteuerung bzw. Entladesteuerung (z.B. E-Autos)

### Batterieladesteuerung ( TAB--> LadeSteuerung )
![Tabelle zur Ladesteuerung](pics/Ladesteuerung.png)

Alle eingetragenen Reservierungen werden in die Datei /DIR/Watt_Reservierung.json geschrieben.  
In der html/config.php können die Variablen angepasst werden (z.B. $PV_Leistung_KWp) .   

Ist das Modul eingeschaltet (in /DIR/config.ini -->> PV_Reservierung_steuern = 1) wird die Reservierung  
beim nächsten Aufruf von SymoGen24Controller2.py in der Ladeberechnung berücksichtigt.

Mit einer gewählten Ladestufe (AUS, HALB, VOLL) unter Hausakkuladung wird die entsprechende Batterieladeleistung,
beim nächsten Aufruf von SymoGen24Controller2.py auf den Wechselrichter geschrieben.  
Die prognosebasierte Ladesteuerung ist dadurch deaktivieren, und kann mit der Option "AUTO" wieder aktiviert werden.  

Weitere Erklärungen stehen in der verlinkten Hilfe oder im Wiki.  

### BatterieENTladesteuerung ( TAB--> EntladeSteuerung )
![Tabelle zur Entladesteuerung](pics/Entladesteuerung.png)

Unter "Feste Entladegrenze " kann die maximale Entladeleistung
in den Schritten 0, 20, 40, 60, 80 oder 100 Prozent fest eingestellt werden.

In der Entladetabelle können Leistungen in KW zur Steuerung der Akkuentladung eingetragen werden.

Weitere Erklärungen stehen in der verlinkten Hilfe oder im Wiki.  

=======================================================  


