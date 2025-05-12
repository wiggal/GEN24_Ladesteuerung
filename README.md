
## ☀️ GEN24_Ladesteuerung 🔋 
  
**Programmfunktionen:**  
- Prognosebasierte Ladesteuerung für  Fronius Symo GEN24 Plus um eine Einspeisebegrenzung (bei mir 70%) zu umgehen,
und eine Produktion über der AC-Ausgangsleistungsgrenze des WR als DC in die Batterie zu laden.  
Über die Tabelle [Ladesteuerung](https://github.com/wiggal/GEN24_Ladesteuerung/#batterieladesteuerung--tab---ladesteuerung-) können große, geplante Verbräuche bei der Ladeplanung berücksichtigt werden.  
- [Entladesteuerung,](https://github.com/wiggal/GEN24_Ladesteuerung/#batterieentladesteuerung--tab---entladesteuerung-) um die Entladung der Batterie bei großen Verbräuchen zu steuern.  
- [Logging](https://github.com/wiggal/GEN24_Ladesteuerung/#bar_chart-logging) und grafische Darstellung von Produktion und Verbrauch.  
- Akkuschonung: Um einen LFP-Akku zu schonen, wird die Ladeleistung ab 80% auf 0,2C und ab 90% auf 0,1C (optional ab 95% weniger) beschränkt (anpassbar).  
- [Dynamischen Strompreis](https://github.com/wiggal/GEN24_Ladesteuerung/#heavy_dollar_signelectric_plug-dynamicpricecheckpy) nutzen um bei niedrigen Preisen den Akku zu laden und grafische Darstellung.  
- **NEU:** [Grafana](https://github.com/wiggal/GEN24_Ladesteuerung/#grafana-beispiele) Beschreibung zu Auswertungen mit Grafana inklusive fertige Dashboards von [@Manniene](https://github.com/Manniene).  

![new](pics/new.png)  
Ab Version: **0.28.1**  
Neues Prognoseskripte Akkudoktor__WeatherData.py für https://api.akkudoktor.net/ von @tz8  
**ACHTUNG:** Umfangreiche Änderungen in CONFIG/weather_priv.ini nötig!!  
Ab Version: **0.28.0**  
**ACHTUNG:** Die Prognoseskripte wurden ins Verzeichnis FORECAST verschoben.  
**Cronjobs müssen angepasst werden!!** (siehe Cortabeinträge Wetterdienste).  
![new](pics/new2.png)  

Die Ladung des Hausakkus erfolgt prognosebasiert und kann mit der Variablen „BatSparFaktor“ in der „CONFIG/charge_priv.ini“ gesteuert werden.  
Hier eine schematische Darstellung um die Auswirkung des „BatSparFaktor“ zu verdeutlichen:  
![Auswirkung des BatSparFaktor](pics/Ladewertverteilung.png)

## 💾 Installationshinweise: [(siehe Wikibeitrag)](https://github.com/wiggal/GEN24_Ladesteuerung/wiki/1\)-Installation-GEN24_Ladesteuerung-auf-einem-RaspberryPi)

Folgende Installationen sind nötig, damit die Pythonskripte funktionieren  
```
sudo apt install python3
sudo apt install python3-pip
sudo pip install requests
```
Mit start_PythonScript.sh können Pythonskripte per Cronjobs oder auf der Shell gestartet werden, die Ausgabe erfolgt dann in die Datei "Crontab.log". 
Als Erstes muss ein Prognoseskript aufgerufen werden, damit aktuelle Prognosedaten in der Datei weatherData.json vorhanden sind!  

Beispiele für Crontabeinträge ("DIR" durch dein Installationsverzeichnis ersetzen).  
Ausführrechte für das start_PythonScript.sh Skript setzen nicht vergessen (chmod +x start_PythonScript.sh).  
http_SymoGen24Controller2.py durchgehend (wegen Logging) alle 10 Minuten starten  
(Häufigerer Aufruf für Logging nicht sinnvoll, da der Gen24 die Zähler nur alle 5 Minuten aktualisiert!).  
Da bei der HTTP-Methode der WR die Einspeisebegrenzung regelt, reicht hier auch ein Aufruf alle 10 Minuten (1-59/10).  

```
1-59/10 * * * * /DIR/start_PythonScript.sh http_SymoGen24Controller2.py schreiben
```
**ACHTUNG: ab v0.28.0 Prognoseskripte ins Verzeichnis FORECAST verschoben!!**  
**ACHTUNG:** nur den Wetterdienst eintragen, den ihr verwenden wollt.
```
33 5,8,10,12,14 * * * /DIR/start_PythonScript.sh FORECAST/Forecast_solar__WeatherData.py
8 5,7,9,11,13,15 * * * /DIR/start_PythonScript.sh FORECAST/Solarprognose_WeatherData.py
0 6,8,11,13,15 * * * /DIR/start_PythonScript.sh FORECAST/Solcast_WeatherData.py
0 5,7,9,11,13,15,17,19 * * * /DIR/start_PythonScript.sh FORECAST/Akkudoktor__WeatherData.py
```
**Crontab.log jeden Montag abräumen**
```
0 0 * * 1 mv /DIR/Crontab.log /DIR/Crontab.log_weg
```

### :sun_behind_rain_cloud: Prognoseskripte in FORECAST/

Holen von den jeweiligen API-Urls die Prognosedaten und bereiten sie auf für GEN24_Ladesteuerung. 

Besonderheiten:  
- Bei forecast.solar kann mit einem Account die Prognose mit den Werten der Produktion aus der DB angepasst werden.  
- Bei solarprognose.de ist ein Account erforderlich, hier wird ein genauer Zeitpunkt für die Anforderung vorgegeben.  
- Bei solcast.com.au ist ein "Home User" Account erforderlich. Leider kann nur 5x am Tag aufgerufen werden, da pro Lauf zwei Zugriffe erforderlich sind (10 pro Tag).  
- Bei api.akkudoktor.net können Abschattungen und weitere Parameter angegeben werden.  

### :chart_with_downwards_trend: http_SymoGen24Controller2.py

Berechnet den aktuell besten Ladewert aufgrund der Prognosewerte in weatherData.json und dem Akkustand und gibt sie aus. 
Mit dem Parameter "schreiben" aufgerufen (start_PythonScript.sh http_SymoGen24Controller2.py **schreiben**) setzt es die `Maximale Ladeleistung` **per HTTP-Request** 
im Batteriemanagement des Wechselrichters. 
Die **Einspeisebegrenzung** und die **AC-Kapazität der Wechselrichters** muss hier nicht berücksichtigt werden,
da dies das Batteriemanagement des GEN24 selber regelt (auch über der definierten `Maximale Ladeleistung`!)

### :heavy_dollar_sign::electric_plug: DynamicPriceCheck.py
Es werden die günstigsten Stunden zum Laden des Akkus aus dem Netz, bzw. eines Akku Entladestopps ermittelt (siehe schematische Darstellung). Der Aufruf von DynamicPriceCheck.py sollte einmal stündlich am besten zwei Minuten vor der vollen Stunde erfolgen.  
**Crontab Beispiel** (-o = alternatives Logfile):
```
58 * * * * /DIR/start_PythonScript.sh -o LOG_DynamicPriceCheck.log DynamicPriceCheck.py schreiben
```
Die Werte werden in die Tabelle EntladeSteuerung eingetragen, und beim nächsten Aufruf von http_SymoGen24Controller2.py auf den GEN24 geschrieben.  
Hier das Diagramm zu den dynamischen Strompreisen:
![Beispiel einer Zwangsladeberechnung](pics/Dyn_Strompreis.png)

## Webserver Installation (WebUI):  
Nicht zwingend erforderlich, die prognosebasierte Ladesteuerung funktioniert auch ohne WebUI (Webserver)  

**PHP installieren:**
```
sudo apt update && sudo apt upgrade
sudo apt install php php-sqlite3
```
Wenn PHP installiert ist, kann durch die Variable `Einfacher_PHP_Webserver = 1` in der CONFIG/default_priv.ini beim nächsten Start von `start_PythonScript.sh`
automatisch der einfache PHP-Webserver gestartet werden. Die Webseite ist dann auf Port:2424 erreichbar (z.B.: raspberrypi:2424).  

**_Alternativ kann auch der Webserver Apache installiert werden:_**  
[(siehe Wikibeitrag)](https://github.com/wiggal/GEN24_Ladesteuerung/wiki/1\)-Installation-GEN24_Ladesteuerung-auf-einem-RaspberryPi)

### :bar_chart: Logging

Beim Aufruf von `http_SymoGen24Controller2.py schreiben` wird die Ladesteuerung und das Logging ausgeführt.  
Beim Aufruf mit dem Parameter `logging` wird nur das Logging ausgeführt, es erfolgt keine Ladesteuerung.  
Aus der SQLite-Datei `PV_Daten.sqlite` wird dann mit html/8_tab_Diagram.php ein Diagramm nach Quelle (wo kommt die Energie her) und Ziel (wo geht die Energie hin) erzeugt. 
![Grafik zur Quelle/Ziel](pics/QZ_Tag.png)

## Modul zur Reservierung von größeren Mengen PV-Leistung, manuelle Ladesteuerung bzw. Entladesteuerung (z.B. E-Autos)

### Batterieladesteuerung ( TAB--> LadeSteuerung )
![Tabelle zur Ladesteuerung](pics/Ladesteuerung.png)

Alle eingetragenen Reservierungen werden in die DB-Datei CONFIG/Prog_Steuerung.sqlite geschrieben.  

Ist das Modul eingeschaltet (in CONFIG/charge_priv.ini -->> PV_Reservierung_steuern = 1) wird die Reservierung 
beim nächsten Aufruf von http_SymoGen24Controller2.py in der Ladeberechnung berücksichtigt.

Ist nicht AUTO gewählt, erfolgt eine Batterieladung mit der eingestellten Prozentzahl der **maximalen Ladeleistung des GEN24**,
ab dem nächsten Aufruf von http_SymoGen24Controller2.py.  
Die prognosebasierte Ladesteuerung ist dadurch deaktiviert, und kann mit der Option "AUTO" wieder aktiviert werden.  

Weitere Erklärungen stehen in der verlinkten Hilfe oder im Wiki.  

### BatterieENTladesteuerung ( TAB--> EntladeSteuerung )
![Tabelle zur Entladesteuerung](pics/Entladesteuerung.png)

Unter "Feste Entladegrenze" kann die maximale Entladeleistung in Prozent der WR-Entladeleistung fest eingestellt werden.

In der Entladetabelle können Leistungen in kW zur Steuerung der Akkuentladung, bzw. zum Laden des Akkus aus dem Netz bei niedrigen Strompreisen, eingetragen werden. 
Durch einen negativen Wert in "Feste Entladegrenze" erfolgt die Zwangsladung des Akkus.

Weitere Erklärungen stehen in der verlinkten Hilfe oder im Wiki.  

### Settings ( TAB--> Settings )
![Tabelle zu den Settings](pics/Settings.png)
Programmfunktionen
Unter Settings kann das Programm zusätzlich gesteuert werden.  

Weitere Erklärungen stehen in der verlinkten Hilfe oder im Wiki.    

### Grafana Beispiele  
![Beispiele](pics/Grafana.png)

Eine [Beschreibung](GRAFANA/Grafana_Installation_readme.pdf) und Dashboarddateien liegen im Verzeichnis GRAFANA.

----------

**News History:**  
Ab Version: **0.26.9**  
Diagramm zur Darstellung der dynamischen Strompreise.  
Ab Version: **0.26.8**  
Beschreibung zu Auswertungen mit Grafana inklusive fertige Dashboards von @Manniene  
Ab Version: **0.26.1**  
Dynamischer Strompreis: Akku laden bei günstigen Strompreisen in Tabelle ENTLadeStrg eintragen durch DynamicPriceCheck.py.  
Ab Version: **0.25.1**  
Prognosebegrenzung auf Höchstwerte der historischen Produktion.  
Ab Version: **0.25.0**  
Zwangsladung durch Eintragen von negativen kW in die Tabelle ENTLadeStrg  
Ab Version: **0.24.8**  
Werte für Akkuschonung frei konfigurierbar.  
Ab Version: **0.24.5**  
Notstrom Reserverkapazität (Entladebegrenzung) höher setzen, wenn schlechte Prognose morgen.   
Netzdienliches Laden durch Prognosekappung, wenn BatSparFaktor = 0.  
Ab Version: **0.24.4**  
Auslagerung der jahreszeitenabhängingen Konfiguration in zusätzliche config-files.  
Änderung in der CONFIG/charge.ini und charge_priv.ini, neuen Block [monats_priv.ini] eingefügt, usw.  
Ab Version: **0.24.1**  
Einbindung von Fronius-Symos.  
Änderung in der CONFIG/default.ini `IP_weitere_Symo = no` in CONFIG/default_priv.ini einfügen.  
Ab Version: **0.24.0**  
Alle Daten aus den Steuerungs.json Dateien in SQLite-Datenbankdatei CONFIG/Prog_Steuerung.sqlite abgelegt.
Änderungen in WebUI: Reiter Settings neu konzipiert, Schieberegler bei den Prozentangaben der Ladesteuerungen.  
Ab Version: **0.22.0**  
Die config.ini ins Verzeichnis CONFIG verschoben und aufgeteilt auf `default.ini, charge.ini weather.ini`.
Zur jeweiligen `xy.ini` kann eine `xy_priv.ini` mit den persönlichen Anpassungen erstellt werden.  
Ab Version: **0.21.4**  
BattVollUm als Delta der ersten Prognosestunde, die kleiner als 1 % der maximalen PV-Leistung ist.  
Ab Version: **0.21.3**  
In der HTTP-Version kann nun im Energiemanagement, ein Einspeisezielwert der Eigenverbrauchs-Optimierung automatisch geschrieben werden.  
Ab Version: **0.21.2**  
Bei aktivierter EntladeSteuerung auch die `Maximale Entladeleistung` **per HTTP-Request** im Batteriemanagement setzen.  
Ab Version: **0.21.1**  
Zur Ermittlung der gesamten Produktion können auch mehrere GEN24 eingebunden werden.  
Ab Version: **0.20**  
[:chart_with_downwards_trend: http_SymoGen24Controller2.py](https://github.com/wiggal/GEN24_Ladesteuerung/#chart_with_downwards_trend-http_symogen24controller2py) `Maximale Ladeleistung` **per HTTP-Request** im Batteriemanagement setzen.  

