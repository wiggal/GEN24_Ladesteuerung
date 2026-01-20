**[0.41.1] – 2026-XX-XX**  

- **Neukonzeption der WebUI um die Oberfläche besser an kleine Bildschirme anpassen zu können.**
- **Änderung in html/config.ini**  Externe Seiten werden anders eingebunden, in `priv.ini` nachziehen. z.B.:
    `4.file = iframe:6_tab_GEN24.php`
    `4.file = http://192.168.178.50`

FIX-Docker: ModuleNotFoundError: No module named 'yaml'
FIX: name AkkuschonungLadewert is not defined

**[0.41.0] – 2026-01-09**  

- Verbesserungen der Wattpilotsteuerung, und Dokumentierung in der README.  
- ForecastMgr bei allen Linien auch die Nullwerte darstellen.  

**[0.40.9] – 2026-01-03**  

- Stabilisierung des OCPP-Servers, hauptsächlich im PV-Überschussladen.  
- DynamicPrice: Keine Entladesperre (-1W), wenn der Akku bereits leer ist.  

**[0.40.8] – 2025-12-12**  

- CHANGELOG.md im Tab config und im WIKI verlinkt.  
- **Änderung in CONFIG/default.ini** Block `[wallbox]` für die Tests der Wattpilotanbindung eingefügt, in `priv.ini` nachziehen.  
- **Änderung in html/config.ini**  Block für Wallbox eingefügt, in `priv.ini` nachziehen.  
- In start_PythonScript.sh Start des OCPP_Servers eingefügt.  

**[0.40.7] – 2025-12-02**  

- Logfiles vor Download von HTML in ASCII umwandeln.  
- FIX: priv.ini wurde aus dem TAB-config nach dem Editieren/Updaten nicht mehr geschrieben.  

**[0.40.6] – 2025-11-27**  

- Updatemeldung, wenn keine ini_Dateien verändert wurden angepasst.  
  ✅ Configdateien seit dem letzten Update, ohne Veränderung!✅   

- Im ENTLadeStrg-TAb immer aktuelle Stunde oben anzeigen.  

- SQLs für Diagramme mit KI optimiert, da Strompreistatistik zu lange Laufzeit hatte.  

**[0.40.5] – 2025-11-22**  

- API-Anpassung ab Firmware 1.39.5-1 `BAT_VALUE_STATE_OF_CHARGE_RELATIVE_U16` nun `BAT_VALUE_STATE_OF_CHARGE_RELATIVE_F32`.  
  Die API components/readable wurde umfangreich geändert, die Konten wurden mit aussagekräftigen Namen versehen anstelle von Nummern (z.B. 0 => Fronius_Inverter_8e31d3b462cd).  

**[0.40.4] – 2025-11-21**  

- **Änderung in html/config.ini** Überflüssige Varaible `Faktor_PVLeistung_Prognose` entfernt, in html/config_priv.ini nachziehen.  

- **DOCKER**
  Umstellung von html/config.php auf html/config.ini auch für Docker dokumentiert und `DOCKER/docker-compose.yml` angepasst

**[0.40.3] – 2025-11-18**  

- **Änderung html/config.php in html/config.ini** 
  Bitte html/config.ini nach html/config_priv.ini kopieren und eventuell eigene Einstellungen übernehmen.  
  Durch die Änderung können nun auch die Einstellungen der html/config_priv.ini im TAB config editiert werden.  

- **DOCKER**
  in `docker-compose.yml` die html/config.ini bereitstellen,
  `./CONFIGS/config_priv.ini:/home/GEN24/html/config_priv.ini`

**[0.40.2] – 2025-11-17**  

**NEU**  
- Updatefunktion im TAB `config`, wenn das Quellverzeichnis ein Git-Repository ist, also mit `git clone ..` erzeugt wurde,  
  und sich auf dem Hauptzweig `main` befindet. Updatemeldungen werden in `Update.log` geschrieben, Einträge älter 1 Monat werden automatisch gelöscht.  

- **Änderung in der html/config.php** Bezeichnung des TAB `Logfile` in `Logfiles` geändert, evtl. in **html/config_priv.php**.  

- 🐳 Die Quellen im Dockerimage sind nun auch ein Clone des Repo. Damit kann ein Update auch im TAB `config` gemacht werden.  
  Neue Dockerimages wird es daher nur mehr für größere Release geben.  

**[0.40.1] – 2025-11-13**  

- Anpassung Diagramm QZ-Bilanz: Immer ganzen Wertebereich (z.B. ganzen Monat) darstellen, auch ohne Daten.  

**[0.40.0] – 2025-11-08 ⚠️  ACHTUNG: umfangreiche Änderungen ⚠️**  

- Programm von GEN24 auf Generic Inverter angepasst, um später auch andere Inverter steuern zu können.  
  **Umfangreiche Änderungen, längere Testes erforderlich**  

- **⚠️  ACHTUNG:**  
  Es ändert sich der Skriptname `http_SymoGen24Controller2.py` in `EnergyController.py`.  
  Die **Cronjobs** müssen angepasst werden!!  

- **Änderung in default.ini** Block `[gen24]` in `[inverter]` umbenannt.  
  **Neuer Parameter in default.ini [inverter]** `InverterTyp`, definiert nun den Inverter und dessen Klassen (aktuell nur gen24).  
  Die Klassen `InverterApi` und `InverterInterface` werden nun dynamisch in Abhängigkeit von `InverterTyp` geladen.  

  **⚠️  ACHTUNG: defaulti_priv.ini anpassen!!**  

**[0.38.8] – 2025-10-27**  

- CONFIG/dynprice.ini und evtl. CONFIG/dynprice_priv.ini tippfehler beseitigt: smart_api => smard_api

- FIX: sqlite3.IntegrityError: UNIQUE constraint failed: priceforecast.Zeitpunkt Durch Zeitumstellung entstehen doppelte Zeitpunkte.
- AWATTAR als Strompreisquelle für Börsenpreise hinzugefügt.

**[0.38.7] – 2025-10-23**  

- FIX: sqlite3.OperationalError: no such table: priceforecast, FUNCTIONS/DynamicPrice.py", line 644
- FIX: install_gen24.sh Cronjob für DynamicPriceCheck.py fehlte

- Erweiterung install_gen24.sh um bei einem Update weniger Entscheidungen eingeben zu müssen.  
- Versionsnummer in Logfiles ausgeben.

**[0.38.6] – 2025-10-17**  

- https://smard.api.bund.dev/ liefert nun auch viertelstündliche Strompreise.  
  In CONFIG/dynprice.ini entsprechend beschrieben.

- Bei Batteriekapazität den STATE_OF_HEALTH (Akku-Degradation) anbringen.

**NEU:** Alle in DIR vorhandenen `.log` Dateien zum Anzeigen bzw. Downloaden verlinken.

**[0.38.5] – 2025-10-06**  

- FIX: Eintrag viertelstündlicher Werte aus DynamicPriceCheck.py mit führender Null wird in PHP7 nicht richtig ausgelesen.  
- `Akku_MindestSOC = 5` in CONFIG/dynprice.ini eingefügt, damit kann ein höherer MIN-SOC als im GEN24 eingestellt werden, um mehr Reserve zu haben.   
- Einige Anpassungen durch die Umstellung der Datenquellen auf viertelstündliche Strompreise.  

**NEU** 
Nachdem nun die Strompreise viertelstündlich kommen, wurde auch der Tageszeit abhängiger Preisanteil in Euro (z.B. Netzentgelte nach $14a BRD) auf viertelstündlich umgestellt.  
- Anpassung auf Minutentakt in `CONFIG/dynprice_priv.ini` und `CONFIG/dynprice_priv.ini` an `Tageszeit_Preisanteil` nötig.  

**[0.38.4] – 2025-09-28**  

- FIX: Änderung der API `components/readable` wenn der Akku aus oder in Standby ist.  
- FIX: In den Strompreischarts wurde der Verbrauch bei stündlichen Strompreisen nur viertelstündlich berechnet.  

**[0.38.3] – 2025-09-25**  

- FIX: Login schlägt fehl, wenn der USER groß geschrieben wird.  
- FIX: DynamicPrice wird nicht mehr geloggt.  

**[0.38.2] – 2025-09-25**  

- BatSparFaktor < 0 (0=-1): Ladung hauptsächlich an den Prognosespitzen kann nun durch den Faktor beeinflusst werden.  
  Der errechnete Ladewert wird nun mit dem absoluten BatSparFaktor multipliziert.  

- GEN24_API.py liest die API-Daten nun vom Smartmeter mit label="<primary>".  
- An ADDONS/Fremd_API_priv.py werden nun die API-Daten des GEN24 übergeben (`def get_API(API_data)`).  

**[0.38.1] – 2025-09-10**  

- Parameter für Abschattungen in Akkudoktor__WeatherData.py angepasst.  

- Mit eigenem Skript ADDONS/Fremd_API_priv.py können Produktionswerte von fremden Erzeugern geholt und der GEN24_API.py übergeben werden.  
  Die Werte werden dann zu den Werten der GEN24_API.py addiert (siehe auch ADDONS/Fremd_API_priv.readme).  

- Dockerdateien ins Verzeichnis DOCKER übernommen, Github-Repository `wiggal/Docker_gen24_ladesteuerung` fällt weg.  
  **ACHTUNG:** das Dockerrepository ändert sich ab dieser Version von `wiggal/gen24_ladesteuerung_php` auf `wiggal/gen24_ladesteuerung`  

**[0.38.0] – 2025-09-07**  

**Umfangreiche Änderungen durch Firmwareupdate auf 1.38.6-1**  
- Firmwareversionen kleiner 1.36.6-1 werden zwar unterstützt, sind aber noch nicht getestet.  
- Nach einem Firmwareupdate auf 1.38.6-1 muss das Kennwort für `customer` neu gesetzt werden.  

**[0.31.5] – 2025-09-02**  

Neukonzipierung von FUNCTIONS/GEN24_API.py:
Nachdem sich die Node-Nummern der components/readable API auf verschiedenen Systemen bzw. Firmwareversionen unterscheiden,
werden nun die benötigten API-Schlüssel unabhängig der Node-Nummern bzw. Ebenen gelesen.

**[0.31.4] – 2025-08-30**  

FIX DynamicPriceCheck: TypeError: get_API() missing 1 required positional argument: 'self'

**[0.31.3] – 2025-08-30**  

FIX: Bei neuen Installationen wird die DB CONFIG/Prog_Steuerung.sqlite nicht mehr angelegt.

**[0.31.2] – 2025-08-30**  

**Änderung in der LadeStrg:**
- Die Spalten zur Reservierung von PV-Leistungen können nicht mehr frei benannt werden.  
  Die Variablen $Res_Feld1 und $Res_Feld2 wurden aus der `html/config.php` entfernt und sollten auch aus der `html/config_priv.php` entfernt werden.  
- Die Spalten heißen nun `einmal` und `laufend`  
  - Die Werte der Spalte einmal gelten nur für den Tag, bei dem sie eingetragen wurden, und fallen dann weg.  
  - Die Werte der Spalte laufend werden jeden Tag wiederholt, bis sie geändert oder gelöscht werden.  

- Im install_gen24.sh kann nun das Installationsverzeichnis verändert werden.  
- Fallback in GEN24_API, falls die Nodenummern 1 und 3 anders sind.  

**[0.31.1] – 2025-08-20**  

FIX: Im `ForecastMgr` konnten Quellen nicht mehr vollständig gelöscht werden.

**[0.31.0] – 2025-08-01**  

- **NEU** Updatefunktion in config-TAB:
  damit können `_priv.ini` Files mit den original ini-Files abgeglichen und upgedatet werden.
- `_priv.ini` Dateien werden nun bei einem Programmlauf von der `.ini` kopiert, wenn sie nicht vorhanden sind.
- In LadeStrg kann für die Punkte Slider oder MaxLadung nun Akkuschonung aktiviert werden.

- **NEU** Mit dem install_gen24.sh kann GEN24_Ladesteuerung auf Debian- und Alpine-linuxsystemen installiert/upgedatet werden.  

#### ACHTUNG Änderung in der html/config.php:  
- in html/config.php wurde `$PrognoseFile = "../weatherData.json";` durch `$PythonDIR = "..";` ersetzt, evtl. auch in html/config_priv.php ersetzen.  

**[0.30.7] – 2025-07-16**  

- Hilfe für den TAB LadeStrg angepasst.
- Skript html/make_config_help.php um Hilfe zu den Configs automatisch zu erstellen.

- Anpassung der prozentualen Lade- und Entladeleistung bei Einstellung über den Slider an die tatsächliche Ladeleistung des Systems.

**[0.30.6] – 2025-07-07**  

- Überarbeitung der Dokumentation abschließen.

- FIX: unsupported operand type, wenn in CONFIG/Prog_Steuerung.sqlite keine Zahlen.

**[0.30.5] – 2025-07-04**  

- Die Optimierung der Prognose mit gespeicherten Produktionsdaten kann nun für jede `ForecastCalcMethod` eingestellt werden.  
  **ACHTUNG:** `ForecastCalcMethod` `median_opt` nicht mehr gültig muss nun `median+` heißen.  

- Im `ForecastMgr` können nun ältere Prognosedaten gelöscht werden, falls sie nicht mehr repräsentativ sind. 
  Einträge die älter als 35 Tage sind, werden programmtechnisch gelöscht.

**[0.30.4] – 2025-06-29**  

- Für den Wetterdienst von `Akkudoktor` können nun auch mehr als 2 Strings konfiguriert werden.  

- **NEU:** Neues Prognoseskript FORECAST/OpenMeteo_WeatherData.pyi auch mit mehr als 2 Strings konfigurierbar.  
  Damit können PV-Prognosen von https://open-meteo.com/ abgerufen werden.  
  **ACHTUNG:** Neuer Block `[openmeteo]` in `CONFIG/weather.ini` bitte bei Bedarf in `CONFIG/weather_priv.ini` einarbeiten!!

- Im Diagramm `Strompreis` die Durchschnittspreise nicht standardmäßig anzeigen, da Auswertung zu langsam ist.  

**[0.30.3] – 2025-06-25**  

- Einheiten in Labels der QZ-Bilanz richtig gestellt.

- Die Einstellungen im TAB `LadeStrg` werden nun immer berücksichtigt.  
**ACHTUNG:** Der Block `[Reservierung]` in `CONFIG/charge.ini` ist weggefallen, auch aus `CONFIG/charge_priv.ini` entfernen!!  

- Die Funktion `MaximalPrognosebegrenzung` wurde entfernt, da sie nun durch `ForecastCalcMethod = median_opt` ersetzt wird.
**ACHTUNG:** Die Variablen `MaximalPrognosebegrenzung`, `MaxProGrenz_Faktor` und `MaxProGrenz_Dayback` aus dem Block `[env]`   
in `CONFIG/weather.ini` ist weggefallen, auch aus `CONFIG/weather_priv.ini` entfernen!!  

- Bei der Berechnung der Produktion für weatherData die Werte 30 Minuten vor und nach der vollen Stunde verwenden.  
  
**[0.30.2] – 2025-06-22**  

- Neue Methode zur Prognoseberechnung `ForecastCalcMethod` kann nun auch `median_opt` sein.  
  Damit wird aus den bisher gespeicherten  Daten in `weatherData.sqlite` mit einem Faktor aus 
  Median/Produktion eine Verbesserung der Prognose berechnet.  

- Nach Änderung des Gewichtes zu einem Prognosedienst, 
  werden bei dem nächsten Aufruf des Prognosedienstes in der DB alle Gewichte des Dienstes neu gesetzt.    

- Konsolidierung der Dokumentation:  
  - Hilfen nach docs/WIKI verschoben  
  - Wiki-Dateien nach HTML konvertiert und nach docs/WIKI übernommen.  

**[0.30.1] – 2025-06-12**  

- Im `ForecastMgr` beim Download die tatsächliche Produktion hinzugefügt, und Ausgabe als Kreuztabelle.  
- Speicherung der Produktion in weatherData.sqlite, damit sie leichter abgefragt werden kann.  
- Prognose (je nach Einstellung in `ForecastCalcMethod`) und Median werden nun im `ForecastMgr` dargestellt.  

**[0.30.0] – 2025-06-08**  

**Große Änderungen bei Prognosespeicherung**  
- Alle abgerufenen Prognosedaten werden nun in der SQLitedatei `weatherData.sqlite` gespeichert.  
- Die Methode zur Prognoseberechnung kann nun in der `CONFIG/weather_priv.ini` mit `ForecastCalcMethod` eingestellt werden.  
  Gültige Methoden sind `median | mean | min | max`  
  (Werte mit Gewicht 0 werden nicht berücksichtigt).  
- Durch die Prognoseskripte wird das Ergebnis aus allen Prognosedaten nach `ForecastCalcMethod` in `weatherData.sqlite` gespeichert.  
- Es können also alle vorhandenen Prognosedienste abgerufen und gleichzeitig verwendet werden, soweit gewollt.  
- Neues Tool `ForecastMgr` um die gespeicherten Prognosedaten zu sichten und evtl. zu löschen.

  **ACHTUNG:** Neue Variable `ForecastCalcMethod` in `CONFIG/weather.ini` bitte evtl. in `CONFIG/weather_priv.ini` einarbeiten!!  

**[0.29.1] – 2025-06-01**  

- Akkuschonung und Akku SOC-Begrenzung wird nicht mehr angewendet, wenn eine manuelle Ladegrenze eingestellt ist.
- Variable 'Einfacher_PHP_Webserver = 1' in CONFIG/default.ini als Standard gesetzt.

FIX: Nach Eingabe von Buchstaben in der Abfrage `Gültigkeit in Stunden` funktioniert das Programm nicht mehr.

**[0.29.0] – 2025-05-30**  

- DynamicPriceCheck.py: Vorbereitung auf viertelstündliche Strompreise. Umfangreiche Umbauten im Code.  

- Neue Funktion für die Akkuschonung.   
  Der Akku kann nun bei entsprechend großer Prognose für den Folgetag nur bis XX% geladen werden.  
  XX ist der erste Wert aus dem String Akkuschonung_Werte.  
  **ACHTUNG:** Neue Variable `PrognoseLimit_SOC` in `CONFIG/charge.ini` bitte in `CONFIG/charge_priv.ini` einarbeiten!!  

- Neue Funktion: Beim Speichern der LadeStrg mit der Auswahl "Slider/MaxLadung" kann eine Gültigkeit in Stunden angegeben werden.
  Ist der Zeitbereich abgelaufen, wird automatisch auf "Auto" zurückgeschaltet.

- in html/config.php wurde Zeile 21 entfernt `$Strompreis_Dia_optionen = array();` bitte evtl. auch in html/config_priv.php entfernen.  

**[0.28.5] – 2025-05-19**  

LadeStrg:  
- Wochentagkürzel hinzugefügt  
- Dopdown mit Optionen Auto, Slider und MaxLadung eingeführt. Damit kann die MaxLadung aus der charge.ini als fester Ladewert eingestellt werden.  

Eigenverbrauchs-Optimierung: Genauigkeit zu AkkuZielProz am Morgen verbessert  
**ACHTUNG** Neue Variable `RundungEinspeisewert` in `CONFIG/charge.ini` bitte in `CONFIG/charge_priv.ini` einarbeiten!!  
Dadurch kann die Häufigkeit der Schreibzugriffe auf den GEN24 gesteuert werden.

Strompreisdiagramm: Börsenpreis und Bruttopreis nebeneinander darstellen.  

**[0.28.4] – 2025-05-07**  

FIX: Fehler in getSQLlastProduktion  bei leerer PV_Daten.sqlite, wenn api_key gesetzt und forecastactual = ja.  
     Dadurch startet der Dockercontainer nicht, wenn die PV_Daten.sqlite leer ist.

**[0.28.3] – 2025-05-05**  

- Quick FIX: Fehler in Prognoseskripten wenn MaximalPrognosebegrenzung = 1

**[0.28.2] – 2025-04-30**  

- Quick fix: 2. string bei Akkudoktor las falsche Config Werte  

**[0.28.1] – 2025-04-29**  

**NEU** Prognoseskript FORECAST/Akkudoktor__WeatherData.py von @tz8:
die API unterstützt neue Eigenschaften:
- Horizont / Verschattung mit prozentualer Transparenz
- Albedo (reflektierende Oberfläche)
- Wechselrichter Effizienz
- Modul Effizienz

**ACHTUNG** Umfangreiche Änderungen in `CONFIG/weather.ini` bitte in `CONFIG/weather_priv.ini` einarbeiten!!

**[0.28.0] – 2025-04-27**  

**Konsolidierung der Wetterdienste**  
- Prognoseskripte wurden ins Verzeichnis FORECAST/ verschoben, **Crontabs** müssen angepasst werden, z.B.:  
  `8 5,7,9,11,13,15 * * * /DIR/start_PythonScript.sh FORECAST/Solarprognose_WeatherData.py`  
  WeatherDataProvider2.py umbenannt in Forecast_solar__WeatherData.py  
- Entfernen der Prognoseoptimierung über sklearn  

Änderung in Forecast_solar__WeatherData.py  durch @tz8:
- neue Variablen **forecastactual**, **forecastdamping** und **horizon** in `weather.ini`,
  dadurch können die entsprechenden Funktionen von https://doc.forecast.solar/api genutzt werden.

CONFIG/default.ini:  
- Block [Logging] entfernt, da nicht mehr nötig. Funktion durch Parameter `logging` gesteuert.  
  SQLitefile `PV_Daten.sqlite` in Skripten hart eingebaut.  


**[0.27.2] – 2025-04-25**  

**Anpassungen für Firmware 1.36.5-1**
- Pfad im httprequest hat sich von /config/... auf /api/config/... geändert

- Änderung in 5_tab_Crontab_log.php
  Die DEBUG-Zeilen werden nun beim Aufruf ausgeblendet, können aber eingeblendet werden.


**[0.27.1] – 2025-04-13**  

DynamicPriceCheck.py:
- **Neuer Parameter in CONFIG/dynprice.ini** `netzlade_preisschwelle`.   
  Bei einem Strompreis unter diesem Preis, wird immer versucht den Akku voll zuladen (z.B. negative Strompreise, oder unter Einspeisevergütung).  

- Strompreis-Chart: Hier wird nun auch der reine Börsenpreis dargestellt.

FIX: Erste node in response von /components/readable statt fest auf '0' gehen, da auch '1' als erster Node vorkommen kann.  

**[0.27.0] – 2025-04-07**  

- Weiterentwicklung der Grafana Dashboards und der Beschreibung von @Manniene

FIX: Fehler in DynamicPriceCheck.py, wenn keine Daten von api.energy-charts.info kommen:
     Nun werden in diesem Fall die Strompreise aus der DB verwendet, falls vorhanden.
     Wenn eingeschaltet, wird eine PushMeldung gesendet.

- Strompreis-Chart: Auch manuell eingetragene Zwangsladungen darstellen
  Prognose darstellen, auch in die Zukunft.
  FIX: Darstellung bei negativen Strompreisen

**[0.26.9] – 2025-03-24**  

- Weiterentwicklung der Grafana Dashboards und der Beschreibung von @Manniene

- **NEU** Strompreis-Chart:
  Zum Aktivieren, folgende Zeile in html/config_priv.php bei der Definition des TAB_config Array einfügen:
  `array ( 'name' => 'Strompreis','file' => '7_tab_Diagram.php','checked' => 'nein','sichtbar' => 'ein')`
  Werden die Daten des Array `$Strompreis_Dia_optionen` aus der `html/config.php` in die `html/config_priv.php` übernommen,
  kann die Darstellung der Charts auch verändert werden.

DynamicPriceCheck.py:
- **Neuer Parameter in CONFIG/dynprice.ini** `Tageszeit_Preisanteil`, für tageszeitabhängige Preisanteile (z.B. Netzentgelte nach $14a)

FIX: QZ-Bilanz für Balkendiagramm SQL angepasst und blättern durch Monate auf Anfang und Ende begrenzt.

**[0.26.8] – 2025-03-09**  

**NEU** Im Verzeichnis GRAFANA werden Beschreibungen und fertige Dashboards zum Import für Grafana von @Manniene bereitgestellt.

FIX: Entladeeintrag wurde mit Ladeeintrag mitgeschrieben, auch wenn kein Eintrag erforderlich.  

**[0.26.7] – 2025-03-01**  

**NEU** Im Verzeichnis ADDONS wird ein Skript Solcast_WeatherData_from_HA_file.py von @roethigj bereitgestellt,
mit dem eine Solcastfile von Homeassistant für GEN24_Ladesteuerung bereitgestellt werden kann. 
In Solcast_WeatherData_from_HA_file.readme wird eine Beschreibung bereitgestellt.  

DynamicPriceCheck.py:
Neue Variable `Lade_Verbrauchs_Faktor` in CONFIG/dynprice.ini eingefügt.  
Mit dem Faktor wird der Verbrauch aus dem Lastprofil multipliziert, damit kann ein Ladestandpuffer für ungenaue
Verbräuche aus dem Lastprofil, bzw. ungenaue Prognosen individuell eingestellt werden.

**[0.26.6] – 2025-02-23**  

DynamicPriceCheck.py:
- Die Strompreise werden nun in PV_Daten.sqlite in einer neuen Tabelle `strompreise` gespeichert.

Erweiterung der DB PV_Daten.sqlite um die Spalte AC_to_DC, der die Energie vom Netz zum Akku abbildet.

FIX: DISCHARGE_MAX wurde gelöscht, wenn sich nur CHARGE_MAX geändert hat.  

**[0.26.5] – 2025-02-16**  

DynamicPriceCheck.py:
- Weiterentwicklung durch neue Algorithmen

DynamicPriceCheck.py: Steuerung über WebUI-Settings eingebaut

GEN24-API: Anpassungen an Firmwareversion 1.35-4

**[0.26.4] – 2025-01-31**  

FIX: DynamicPriceCheck.py: Strompreisabfrage dauert zu lange, Timeout 10 Sekunden gesetzt.  
FIX: Prognoseskripte schreiben falsche Zeit in Crontab.log.

**[0.26.3] – 2025-01-30**  

Änderung in WeatherDataProvider2.py
- Einführen eines API_Key für `Personal` oder `Personal Plus` Accounts
**Änderung in weather.ini** unter [forecast.solar] Parameter für die API_Keys eingeführt:
  api_key = kein
  api_pers_plus = nein

Die Prognoseskripte schreiben nun auch bei erfolgreicher Anforderung in die Crontab.log.

FIX: Fehler beim Download von Crontab.log im Docker

**[0.26.2] – 2025-01-26**  

- Downloadlink für Crontab.log eingebaut

DynamicPriceCheck.py: 
- Ladeverlust beim Berechnen des Akuu-SOC berücksichtigen
- Manuelle Einträge zur Zwangsladung werden nicht mehr überschrieben.  
  Einträge von DynamicPriceCheck.py erhalten im Feld `Options` den Eintrag `DynPrice` und nur diese werden überschrieben.  
  **Achtung:** Beim Update auf diese Version müssen Eiträge zur Zwangsladung manuell gelöscht werden.

Änderung in http_SymoGen24Controller2.py
- Akkuschonung auch bei Zwangsladung möglich durch `Batterieentlandung_steuern = 2`
- Alle möglichen Programmoptionen aus den WebUI-Settings sind nun auch als Aufrufparameter möglich.

Diagramme:  
- FIX: Verbrauch in Kopfzeile der Diagramme auf Netzladen angepasst  
- FIX: Akkuladen aus dem Netz in den Diagrammen richtig darstellen.  
- Im Balkendiagramm Werte VonBatterie ausgeblendet hinzugefügt.  
- 7_tab_Diagram.php => PV-Bilanz entfernt, da es nicht mehr gepflegt wird.  
  Folgende Zeile aus html/config.php entfernt, bitte auch aus html/config_priv.php entfernen:  
  `array ( 'name' => 'PV-Bilanz','file' => '7_tab_Diagram.php','checked' => 'nein','sichtbar' => 'aus'),`  

**[0.26.1] – 2025-01-12**  

Dynamischer Strompreis Weiterentwicklung:  
- Laden und Ladestops nach Bedarf mischen in einer Berechnung.
- **Parameter aus CONFIG/dynprice.ini entfernt** `minimum_price_difference`.    
- **Parameter aus CONFIG/dynprice.ini entfernt** `minimum_batterylevel_Prozent`, Wert wird nun vom GEN24 gelesen.    
- **Neuer Parameter in CONFIG/dynprice.ini** `max_batt_dyn_ladung`, bis zu wieviel Prozent darf der Akku aus dem Netz geladen werden.  
- Wiederherstellung manueller Einträge in der Tabelle ENTLadeStrg deaktiviert.

FIX: Teilweise None als Verbrauch im Lastprofil.
FIX: Bei "Entladeeintrag löschen!" wurde die Batteriesteuerung auch gelöscht, wenn die optionen `Ladesteuerung` und `Ent- und Zwangsladesteuerung` nicht gesetzt waren.

**[0.26.0] – 2024-12-15**  

Dynamischer Strompreis:  
- Um Lade- und Abschreibungsverluste des Hausakku zu berücksichtigen, wurde eine Variable Akku_Verlust_Prozent in CONFIG/dynprice.ini eingeführt.    
- **Neuer Parameter in CONFIG/dynprice.ini** `Gewinnerwartung_kW`, damit kann ein Abstand der Kosten von Laden zu Entladung stoppen eingestellt werden.  
- **Neuer Parameter in CONFIG/dynprice.ini** `Daysback`, Einstellung, wie viele Tage zurück sollen für das Lastprofil verwendet werden.  
  Die Verbrauchsdaten für das Lastprofil werden so gewichtet, dass aktuelle Daten ein höheres Gewicht bekommen.  
- Manuelle Einträge in der Tabelle ENTLadeStrg werden, falls sie überschrieben werden, gesichert und später wiederhergestellt.  
- Die Steuecodes werden nur bei Veränderung in die Tabelle ENTLadeStrg geschrieben.  
- Im Debug-Modus wird eine DEBUG.csv erzeugt.  
- **Neuer Parameter in default.ini [gen24]** `battery_capacity_Wh`, wird benötigt, damit das Programm auch läuft, wenn Akku offline ist!!

CONFIG/Prog_Steuerung.sqlite wurde aus den Quellen entfernt, da inzwischen sehr viele Infos drin stecken, die sonst überschrieben werden.  
- Die Prog_Steuerung.sqlite wird, wenn sie fehlt, beim ersten Lauf von http_SymoGen24Controller2.py erzeugt.  
- Zugriffe von DynamicPriceCheck.py bei fehlender Prog_Steuerung.sqlite wurden abgefangen.  

**[0.25.5] – 2024-11-24**  

- ping3.ping ersetzt durch requests.get, da ping nur mit Adminrechte ausführbar ist,
  und bei manchen Installationen zu einem `PermissionError: [Errno 1]` führt.

Dynamischer Strompreis: 
- Abstand für Erneuerung des Lastprofils einstellbar.
  CONFIG/dynprice_priv.ini ==>> LastprofilNeuTage
- Wenn weniger als 7 Tage in der Logging-DB, werden die Werte im Lastprofil mit 600 Watt aufgefüllt.
  Damit kann das Tool DynamicPriceCheck.py immer getestet werden.
- CONFIG/dynprice.ini überarbeitet und in Hilfe aufgenommen

Neue Option in CONFIG/charge.ini im Block [Entladung]:
- Damit kann ab einem bestimmten Verbrauch die Entladung des Hausakkus begrenz werden.
```
; Feste Entladebegrenzung ab einem bestimmten Verbrauch (Angaben in Watt)
; Funktion nur aktiv, wenn Verbrauch_Feste_Entladegrenze > 0 (z.B. 10000 Watt für Wallbox)
Verbrauch_Feste_Entladegrenze = 0 # Wert Null bedeutet Funktion ist **AUS**
Feste_Entladegrenze = 300
```

Notstromprüfung erfolgt nun eine Stunde nach Sonnenuntergang (= Prognose < 1% PV-Leistung)

**[0.25.4] – 2024-11-17**  

**Modbusversion entfernt, da nicht mehr lauffähig!!**

Neukonzeption der Notstromreservesteuerung:
- Neuer Block [Notstrom] in charge.ini eingefügt, Einträge tlw. aus dem Block [Entladung] übernommen und umbenannt.
- Die Werte zur Steuerung der Notstromreserve können nun in mehreren Stufen konfiguriert werden:  
  z.B. Notstrom_Werte = {"5": "30", "9": "15"} (Bei 5kWh Prognose morgen auf 30% setzen usw.)

Bitte die Einträche in CONFIG/charge_priv.ini entsprechend anpassen

**[0.25.3] – 2024-11-13**  

Vorbereitungen für ein Dockerupdate und Wegfall der Modbusvariante und des Apacheimage:  
-Fallback Variablen entfernt

Dynamischer Strompreis: dyn_print_level mit Debug eingeführt.  

start_PythonScript.sh: Schalter "-o Logfile" erzeugt alterenative Logdatei (z.B. zu Analyse von DynamicPrice.py)

Hysterese bei Notstromfunktion hinzugefügt

**[0.25.2] – 2024-11-10**  

Weitere Prognoseoptimierungen:

- Prognosebegrenzung durch Maximalwert aus der DB PV_Daten.sqlite: Sommerzeit berücksichtigt

- Prognoseoptimierung mit scikit-learn (Machine Learning in Python) eingebaut (MaximalPrognosebegrenzung = 2)
  Erforderliche Pakete:
  `pip install pandas numpy scikit-learn`

In CONFIG/default.ini standardmäßig Logging_ein = 1 gesetzt, da die Loggingdaten immer häufiger Verwendung finden.

FIX: Fehler Prognosebegrenzung wenn keine Loggingdaten vorhanden.

**[0.25.1] – 2024-11-03**  

- Da bei bestimmten Konstellationen die Prognose eventuell zu hoch ausfällt (z.B. Abschattung durch Wald ab 15:00 Uhr),  
kann nun die Prognose auf den Höchstwert der Produktion der jeweiligen Stunde aus den letzten XX Tage begrenzt werden.
Der Höchstwert wird aus der DB PV_Daten.sqlite ermittelt.

Änderungen in den Prognoseskripten.
Änderung in **CONFIG/weather.ini**, folgende Zeilen eingefügt (evtl in CONFIG/weather_priv.ini einbauen):  

```
[env]
; 0 = aus, 1 = ein: damit wird die Prognose auf den höchsten Wert je Stunde der Produktion der letzten MaxProGrenz_Dayback Tage begrenzt
MaximalPrognosebegrenzung = 0
; MaxProGrenz_Faktor wird mit dem Werd aus der DB multipilziert
MaxProGrenz_Faktor = 1
MaxProGrenz_Dayback = 35
```

FIX: Solcast_WeatherData.py erkannte bei no_history = 1 nicht wenn die Anzahl der erlaubtem Zugriffe erreicht war.
FIX: Wird eine Zwangsladung geschrieben, muss die Ladegrenze immer höher als die Zwangsladung sein, sonst funktionierts nicht.

**[0.25.0] – 2024-10-24**  

- Zwangsladung durch Eintragen von negativen kW in die Tabelle ENTLadeStrg  

- Ein Lastprofil erzeugen (Loggin DB erforderlich), um damit bei dynamischen Strompreisen zu steuern.  
  - **Neue Skripte:**
    - DynamicPriceCheck.py  
    - FUNCTIONS/DynamicPrice.py  
  - **Neue Config:**  
    - CONFIG/dynprice.ini  
    - bei Benutzung CONFIG/dynprice_priv.ini anlegen  

**[0.24.9] – 2024-10-19**  

- FIX: Schreibverzögerung bei Eigenverbrauchs-Optimierung 

Da ich die Modbusversion nicht mehr weiterentwickeln werde,
Hinweis ``WIRD AB VERSION 0.25 nicht mehr gepflegt!!!`` in Modbusversion eingefügt.

**[0.24.8] – 2024-10-13**  

- Akkuschonung frei konfigurierbar machen:  
Änderung in CONFIG/charge.ini, folgende Zeilen eingefügt:  
```
; Akkuschonung_Werte = {"Ladestand%" : "LadewertC", ...}
Akkuschonung_Werte = {"80": "0.2", "90": "0.1", "95": "0.05"}
```
Bitte in CONFIG/charge.ini übernehmen und anpassen. Es können auch mehr Akkuladepunkte eingefügt werden.

- Fix: Eigenverbrauchs-Optimierung konnte unter tags nicht unter 50 Watt sein.

**[0.24.7] – 2024-10-06**  

Notstromprüfung nur zwischen 22:00 und 24:00 Uhr.  
Wetterdienste FIX: json.decoder.JSONDecodeError wenn keine Daten ankommen  

**[0.24.6] – 2024-09-29**  

- FIX: Schreibverzögerung bei Eigenverbrauchs-Optimierung funktioniert nicht bei MaxEinspeisung < 100W   
- Fix: Prognose holen mit WeatherDataProvider2.py von forecast.solar funktionierte nicht mehr.  

**[0.24.5] – 2024-09-22**  

- WebUI automatischer reload alle 5 Minuten, und beim wechseln des Tab.  
  Logfile springt beim Öffnen ans Ende.

- Notstrom Reserverkapazität (Entladebegrenzung) höher setzen, wenn schlechte Prognose in nächsten 24 Stunden (HTTP-Version)

- Netzdienliches Laden durch Prognosekappung, wenn BatSparFaktor = 0.  

**[0.24.4] – 2024-09-08**  

Auslagerung der jahreszeitenabhängingen Konfiguration in zusätzliche config-files  
Vorteil: Man kann dort alle Definitionen, die in der charge.ini, bzw. charge_priv.ini enthalten sind, 
Monats abhängig machen. Nicht nur aus dem Block [Ladeberechnung], sondern auch z.B. aus `[Entladung]`oder `[EigenverbOptimum]`.


#### ACHTUNG Änderung in der CONFIG/charge.ini und charge_priv.ini:  
- Definition der Zusatz_Ladebloecke und Zeilen mit Zusatz_Ladebloecke **entfernt**.
- Neuen Block [monats_priv.ini] eingefügt, hier zusätzliche config-files mit Monaten eintragen  
  Beispielconfig winter_priv.ini = 11, 12, 01 eingefügt und Protofile winter.ini eingefügt.

Aktivieren z.B. in CONFIG/charge_priv.ini  
- Kommentar bei `winter_priv.ini = 11, 12, 01` entfernen und winter.ini nach winter_priv.ini umbenennen, und enthaltene Werte anpassen.

**[0.24.3] – 2024-09-01**  

Vereinfachung des Programmcodes zur Ermittlung des Ladewertes.  
Akkuzustand in Prozent aus API ausgeben.  

**Neuerungen bei Ladewertberechnung**  
Bei BatSparFaktor < 1 wird morgens bei folgender Bedingung die Ladung auf 0 gestellt:  
Prognoseladewert < Grenze_nachOben*0.7"  

Wenn der Ladewert ohne BatSparFaktor größer MaxLadung, dann MaxLadung setzen, damit der Akku auch voll wird.  

**Neuerungen bei Eigenverbrauchs-Optimierung**  
Durch EigenverbOpt_steuern = 2, in der CONFIG/charge_priv.ini wird die Einspeisung am Tag auf Null gesetzt.  

#### ACHTUNG Änderung in der html/config.php:  
Eine neu Variable $Diagrammgrenze = 25000; wurde eingefügt, bitte in html/config_priv.php einfügen.  
Dadurch wird die Y-Achse des Tagesdiagramms in der QZ-Bilanz auf diese Größe begrenzt, um große Ausreißer
in dem Diagramm abzufangen, die durch längeren Loggingausfall entstehen können.

**[0.24.2] – 2024-08-25**  

FIX: Symos sind nachts evtl. im Standby und liefern keine Daten.  

Name des Wetterdienstes in LadeStrg-Tab ausgeben.  
Änderung: BattVollUm als Delta der ersten Prognosestunde, die kleiner als **2%** der maximalen PV-Leistung ist.  
Genauere Fehlerangabe bei Fehler in config-Files. #97    

**[0.24.1] – 2024-08-13**  

Einbindung von Fronius-Symos
- Änderung in der CONFIG/default.ini `IP_weitere_Symo = no` in CONFIG/default_priv.ini einfügen

**[0.24.0] – 2024-08-11**  

**Umfangreiche Änderungen in der Steuerung des Ladeprogramms**  

Alle Daten aus den Steuerungs.json Dateien ( Prog_Steuerung.json, Akku_EntLadeSteuerFile.json, Watt_Reservierung.json, html/EV_Reservierung.json ) in SQLite-Datenbankdatei CONFIG/Prog_Steuerung.sqlite ablegen. 

In der html/config.php wurden folgende Einträge entfernt, auch in der config_priv.php entfernen:
- $ReservierungsFile = "EV_Reservierung.json";
- $WattReservierungsFile = "../Watt_Reservierung.json";
- $EntLadeSteuerFile = "../Akku_EntLadeSteuerFile.json";

In der Ladesteuerung bezieht sich die feste Ladegrenze in Prozent **nicht** mehr auf `MaxLadung` sondern auf die **maximale Ladeleistung** des GEN24.

Änderung in CONFIG/charge.ini, auch in der CONFIG/charge_priv.ini ändern:
- FesteLadeleistung = -1, Ladesteuerung steht auf AUTO (0 ist ab jetzt Ladeleistung Null, -1 ist automatische Ladewertberechnung)

Folgende Einträge entfernt:
- PV_ReservieungsDatei = Watt_Reservierung.json
- Akku_EntladeSteuerungsFile = Akku_EntLadeSteuerFile.json

**Laden und Entladen des Akkus in Settings getrennt voneinander ein- bzw. ausschalten**


**[0.23.1] – 2024-08-05**  

FIX: RuntimeError: Server XXXX returned 400 in der Eigenverbrauchsoptimierung.

**[0.23.0] – 2024-08-04**  

**Umfangreiche Neukonzipierung der Ladewertberechnung**

Dies soll die Ladewertberechnung wieder stärker durch den `BatSparFaktor` beeinflussbar machen.  
- Der Einfluss der Prognose auf den Ladewert wurde entfernt.  
- Der Ladewert wird nun linear durch den Platz im Akku und der bis `BattVollUm` zur Verfügung stehenden Zeit definiert.  
- Der linear berechnete Wert wird dann mit dem `BatSparFaktor` multipliziert.  

Code aufräumen und auf Klassen umstellen.
- Der neue Code wurde zwar getestet, aber da ich nur die HTTP-Version benutze kann es vor allem in der Modbus-Version nicht zu Fehlern kommen.  

Änderung der Eigenverbrauchs-Optimierung  
- Der Einspeisewert wird nun auf 0 gesetzt, wenn der Akkustand unter `MindBattLad` fällt.

**[0.22.0] – 2024-07-20**  

**NEU ->>** Die config.ini in Verzeichnis CONFIG verschoben und aufgeteilt:  
- Dateinamen: default.ini, charge.ini, weather.ini  
- Zur jeweiligen xy.ini eine xy_priv.ini lesen, die nicht verteilt wird, aber mit angepassten Daten selbst erstellt werden kann.  
- Dadurch sollen die Updates einfacher und die Config Einstellungen übersichtlicher werden.  

**NEU ->>** Es kann auch eine html/config_priv.php angelegt werden, die eigene Einstellungen enthält und nicht ausgeliefert und überschrieben wird.  

**NEU ->>  In den jeweiligen xy_priv.ini Dateien müssen nur die Variablen definiert werden, deren Wert gegenüber den ausgelieferten INI_Dateien geändert werden sollen!**  

### ACHTUNG: Umfangreiche Änderungen der Konfiguration (Docker anpassen):  

Änderung bei der Akkuschonung:
- Der Wert `Akkuschonung` in der charge.ini kann nun auch auf einen Wert zwischen 0 und 1 gesetzt werden.
  Dadurch wird der Ladewert bei einem Akkustand ab 95% um den gesetzten Faktor vermindert, 
  z.B:: 0.1C = 1100W, Akkuschonung = 0.5, Dann ist der Ladewert 550W (= 0.1 x 0.5)

**[0.21.4] – 2024-07-18**

**NEU** BattVollUm als Delta der ersten Prognosestunde, die kleiner als 1 % der maximalen PV-Leistung ist.
- Positiver Wert in BattVollUm ist Zeitpunkt wie bisher
- Null oder negativer Wert in BattVollUm ist Differenz von der ersten Prognosestunde, die kleiner als 1 % der maximalen PV-Leistung ist.
- Damit verschiebt sich der Zeitpunkt BattVollUm automatisch im Winter nach vorne.

Änderung Eigenverbrauchs-Optimierung  
- Tagesentladung wird nur gesetzt, wenn Akkustand höher AkkuZielProz ist

Änderung in Solarprognose_WeatherData.py
- durch die Variable `Zeitversatz` kann die Prognose stundenweise verschoben werden.
#### ACHTUNG Änderung in der config.ini:  
- neue Variable `Zeitversatz` im Block [solarprognose]

**[0.21.3] – 2024-07-14**

**NEU** Automatisches setzen eines Einspeisewertes als `Zielwert am Einspeisepunkt` unter Eigenverbrauchs-Optimierung (nur HTTP)  
- durch das Setzen dieses Wertes kann ein Netzbezug trotz genügend eigene Energie, der durch die Einschwingzeit verursacht wird, minimiert werden.
- der Speicher kann je nach Prognose auf einen Zielstand entladen werden, um am nächsten Tag Kapazität zur Verfügung zu haben.

#### ACHTUNG Änderung in der config.ini:  
- neuer Block `[EigenverbOptimum]`

Änderung in http_SymoGen24Controller2.py
- Da der GEN24 die Energie, die über der AC Kapazität des Wechselrichters liegt automatisch in den Akku speichern,
  wurde die Begrenzung auf WR_Kapazitaet in der HTTP-Version entfernt.

Änderung in README.md:
- Crontab.log jeden Montag abräumen auf 0:00 Uhr verlegt.

- Fehlerbereinigungen siehe commits

**[0.21.2] – 2024-06-30**

Änderung in http_SymoGen24Controller2.py
- Entladesteuerung eingebaut

Änderung in FUNCTIONS/fun_API.py
- FUNCTIONS/fun_API.py API_Schlüssel von 16711680 nach 16252928 geändert.  
  Der Schlüssel 16711680 scheint bei manchen GEN24 zu fehlen.  
  Vermutlich durch Firmwareupdate auf 1.32.5-1 verursacht. 

Änderung in SymoGen24Controller2.py, bei Settings = AUS, wird die Steuerung deaktiviert.  
  - AUS         -->> die Skripte werden beendet , die bisherigen Steuerungswerte werden deaktiviert.  

FIX: Fehler bei HTTP-Zugang wenn 'user' groß geschrieben

#### ACHTUNG bitte html/config.php anpassen!!!  
Zeile `array ( 'name' => 'Hilfe','file' => '3_tab_Hilfe.html...` entfernt.  
html/3_tab_Hilfe.html entfernt, und die Hilfen direkt in den entsprechenden Seiten eingebunden.

**[0.21.1] – 2024-06-23**

**NEU** es können mehrere GEN24 eingebunden werden  
Dadurch wird die Produktion mehrerer GEN24 aufaddiert  

#### ACHTUNG Änderung in der config.ini:  
- neue Variablen 'IP_weitere_Gen24' in [gen24]   

FIX Batterieentladebegrenzung: TypeError: unsupported operand type  
FIX: DEBUG-Meldungen aus Funktionen ausgeben  
FIX: bei Prognosen im Diagramm wurden die Reservierungen abgezogen  

**[0.21.0] – 2024-06-17**

**NEU** Automatischer Start des eingebauten PHP-Webservers:  

#### ACHTUNG Änderung in der config.ini:
- neue Variable 'Einfacher_PHP_Webserver' in [env]
Durch setzen Einfacher_PHP_Webserver = 1 wird durch start_PythonScript.sh der einfache PHP_Webserver auf Port 2424 gestartet.  
Damit die Apachekonfiguration nicht gemacht werden, dies vereinfacht die Installation.
Erreichbar ist die Oberfläche dann mit name_oder_IP:2424

**NEU:** html/9_tab_settigs.php  

Durch die Optionen auf dem Tab, können die SymoGen24Controller-Skripte gesteuert werden:  
(Damit kann die Steuerung auch kurz mal abgeschaltet werden, ohne das Logging zu unterbrechen usw.)

  - unverändert lassen       -->> die Skripte laufen mit den Parametern, mit denen die aufgerufen wurden (z.B.: logging, schreiben)
  - AUS                      -->> die Skripte werden ohne jegliche Funktion beendet #Änderung in 0.21.2
  - Analyse in Crontab.log  -->> die Skripte berechnen die Ladewerte geben die Ergebnisse nur aus.
  - NUR Logging              -->> die Skripte führen nur das Logging für die Diagramme durch
  - WR-Steuerung und Logging -->> die Skripte schreiben die Ladesteuerung auf den WR und machen das Logging

Änderung in WeatherDataProvider2.py
- da es Probleme gibt, wenn zwischen  [forecast.solar] und  [forecast.solar2] verschiedene Koordinaten verwendet werden,
  werden nun nur noch die Werte `lat` und `lon` aus [forecast.solar] verwendet.

#### ACHTUNG Änderung in der config.ini:
- `lat` und `lon` aus dem Block [forecast.solar2] entfernt.

**[0.20.2] – 2024-06-13**

FIX: NameError: name 'WRSchreibGrenze_nachOben' is not defined

**[0.20.1] – 2024-06-11**

#### Ab dieser Version kann die Batteriesteuerung auch per HTTP über die Wechselrichteroberfläche erfolgen.  
Dies hat den Vorteil, dass die Leistung über der Einspeisegrenze automatisch in den Akku fließt,  
dadurch genauer gesteuert wird und damit der Platz im Akku besser ausgenutzt werden kann.  
Ausserdem sind weniger Schreibvorgänge am WR erforderlich.

Dies bedingt umfangreiche Änderungen, hier einige:
- Alle Funktionsdateien nach FUNCTIONS/ verschoben
- Funktionen zur Ermittlung des Ladewertes in FUNCTIONS/fun_Ladewert.py ausgelagert

#### ACHTUNG Änderung in der config.ini:
- neue Variable 'GrenzwertGroestePrognose' in [Ladeberechnung]
- neue Variablen 'user'und 'password' in [gen24]  (Zugangsdaten zum WR)

**Zur Umstellung von Modbus zu HTTP-Request bitte Modbussteuerung deaktivieren:**
- Am WR Modbus ausschalten und speichern, wenn andere Anwendungen Modbus brauchen wieder einschalten.

Da bei niedrigen Prognosen oft die Ladesteuerung ein bisschen untersteuert,
wird nun mit MaxLadung geladen, wenn die größte Prognose des Tages unter 
dem Wert in 'GrenzwertGroestePrognose' liegt.

Fehlerbereinigungen:  
FIX: fest codierte IP_Adresse in FUNCTIONS/fun_http.py beseitigt  
FIX: reservierungdata is not defined  

**[0.14.0] – 2024-05-25**

**NEU Konzeptionierung der Ladewertberechnung nach Prognose:**
Umfangreiche Änderung in SymoGen24Controller2.py
- genauere Berechnung der Ladedewerte aus den Prognosen.
- Vermeidung von Sprüngen in der Prognosenberechnung

Ladewerte_Vergleichtabelle.ods entfernt, da nicht mehr aktuell und nötig


**[0.13.3] – 2024-04-30**

Änderung in SymoGen24Controller2.py
- Bei Akkuschonung Schaltverzögerung (hysterese) eingebaut
- Bei zu geringer Prognose Akkuschonung nicht ausführen:  
  ``aktuelleVorhersage - (Grundlast /2) > AkkuschonungLadewert``
- Fix: Einspeisegrenzprüfung teilweise falsch.

**Berechnung der Ladewerte durch die Prognose neu konzipiert:**  
  **!!ACHTUNG noch Entwicklungsstand!!!**
- aktuell nur zum testen in der Datei neu_SymoGen24Controller2.py.  
  neu_SymoGen24Controller2.py ersetzt ab Version 0.14.0 die aktuelle SymoGen24Controller2.py
  Der Quellcode soll dadurch einfacher und übersichtlicher werden.

**[0.13.2] – 2024-04-07**

Änderung in SymoGen24Controller2.py
- die Akkuschonung wird jetzt immer ausgeführt, wenn die Variable "Akkuschonung = 1" ist. 
- Ladekurve durch Mittelung mit vorherigem Ladewert glätten

Änderung in Solcast_WeatherData.py
- hier kann nun auch eine zweite Ausrichtung, die in solcast.com mir 1km Entfernung 
  konfiguriert werden kann, abgerufen werden. 
  [pv.strings] anzahl auf 2 setzen.

- damit die freien 10 Abrufe nicht zu schnell verbraucht werden, 
  kann das Abrufen der Historie durch no_history = 1 abgestellt werden.
  Die Historie und die aktuelle Stunde werden dann aus der weatherData.json übernommen.

Änderung in functions.py  
- Beim lesen der Variablen, bei Zahlen Komma in Punkt umwandeln, falls in der config.ini ein Komma steht.

#### ACHTUNG Änderung in der config.ini:
- Im Block [solcast.com] wurde "no_history = 0" hinzugefügt
- ein neuer Block [solcast.com2] wurde hinzugefügt.

**[0.13.1] – 2024-03-17**

Änderung in 8_funktion_Diagram.php
-  Diagram Sortierungen angepasst  
-  Diagram Ausreisser minimieren (Ausgabe nur alle 10 Minuten)  

Änderung auch in SymoGen24Controller2.py  
- Fix: Ladewert wird nachts um 0:00 auf 0 gesetzt, da die Prognose hier 0 Watt ist.  
  Neuen Ladewert nicht mehr schreiben, wenn Prognose 0 Watt beträgt.  
- Gleitender Mittelwert für Prognose eingeführt, um starke Sprünge in den Prognosen zu glätten.

#### ACHTUNG Änderung in der config.ini:  Tippfehler in Variablen beseitigt  
  EntlageGrenze_steuern ==> EntladeGrenze_steuern  
  EntlageGrenze_Min     ==> EntladeGrenze_Min  
  EntlageGrenze_Max     ==> EntladeGrenze_Max  

Neue Funktion: Akkuschonung  
#### ACHTUNG Änderung in der config.ini: Variable Akkuschonung eingefügt  
Änderung auch in SymoGen24Controller2.py  
- ist die Variable "Akkuschonung = 1" wird der Akku zwischen 80 und 100% mit 0,2C bzw. 0,1C geladen,  
  ausser die Einspeisebegrenzung bzw. die AC-Leistung des Wechselrichters wird überschritten.   

**[0.13.0] – 2024-02-04**

Neue Funktion: Batteriereservekapazität mit Prognose von morgen anpassen.

#### ACHTUNG Änderung in der config.ini: Zusätzliche Parameter im Block [Entladung] 
- EntlageGrenze_steuern, ProgGrenzeMorgen, EntlageGrenze_Min, EntlageGrenze_Max

Änderung auch in SymoGen24Controller2.py, SymoGen24Connector.py
- Batteriereservekapazität Anpassung eingebaut
- PushMeldung angepasst 

Anpassungen in Solcast_WeatherData.py
- zuerst Vorhersage abrufen und dann die Vergangenheit, da Vergangenheit nicht für Berechnung nötig

**[0.12.6] – 2024-01-20**

Änderung in Solarprognose_WeatherData.py, Solcast_WeatherData.py, WeatherDataProvider2.py  
- Meldung wenn die definierten "dataAgeMaxInMinutes" noch nicht abgelaufen ist
  nur ausgeben, wenn "print_level" ungleich 0
- timeout bei http_request verlängert, da Solcast teilweise sehr langsam antwortet.

**[0.12.5] – 2024-01-01**

#### ACHTUNG bitte html/config.php anpassen!!!  
Änderung in html/config.php  

- Umbenennung der Diagrammregister:
  Diagramm  -->> PV-Bilanz = Produktions- und Verbrauchsbilanz
  Diagramm2 -->> QZ-Bilanz = Quellen- und Zielbilanz

FIX: html/8_funktion_Diagram.php 
     Einheit für BattStatus auf "%" geändert

#### ACHTUNG Änderung in der config.ini in den Zusatz_Ladebloecke
FIX: in der config.ini müssen die Monate der in den Zusatz_Ladebloecken immer  
     **zweistellig** sein (z.B.: 01, 02 )


**[0.12.4] – 2023-12-25**

Änderungen in html/funktion_Diagram.php
-  Batterieladung vom Netz im Liniendiagramm darstellen
-  FIX: Falscher Eigenverbrauch bei Balkendiagramm Verbrauch

html/funktion_Diagram.php umbenannt in html/7_funktion_Diagram.php

NEU: 
html/8_tab_Diagram.php
html/8_funktion_Diagram.php

Diagramm Aufbereitung nach EnergieQuelle und EnergieZiel,
um Laden aus dem Netz und Einspeisen aus Batterie besser abbilden zu können.
 
**[0.12.3] – 2023-12-05**

Änderungen in html/funktion_Diagram.php
- FIX: Datumsübergänge Monat und Jahr in Optionen

Änderungen in functions.py
- Zusatz_Ladebloecke können nun abgeschaltet werden, bisher lief das Programm ohne Zusatz_Ladebloecke auf einen Fehler.  
  Folgende Variablenbelegung schaltet die Zusatz_Ladebloecke ab:  
  Zusatz_Ladebloecke = aus  

- FIX: Darstellung falsch, wenn der Akku aus dem Netz geladen wird.

Änderungen in html/3_tab_Hilfe.html
- Versionsnummer eingefügt

**[0.12.2] – 2023-11-28**
 
Screenshots aktualisiert und Readme angepasst

Änderungen in html/7_tab_Diagram.php und html/funktion_Diagram.php
- Footer: Element "bis ..." weglassen wen von und bis gleich.
- Tooltip: Summenbildung hinzugefügt

**[0.12.1] – 2023-11-25**

Änderungen in html/7_tab_Diagram.php und html/funktion_Diagram.php
- Balkendiagramme, Optionsauswahl usw. hinzugefügt.

**[0.12.0] – 2023-11-18**

## ACHTUNG: Umfangreiche Änderungen im Logging

Logging erfolgt nun mit den "lifetime Zählerständen" aus der API: /components/readable  
**Bitte evtl. alte SQLite-Datei löschen**  

Das Logging in eine CSV_Datei fällt weg.  

Änderung in SymoGen24Controller2.py
Das Scribt kann nun auch mit dem Parameter "logging" aufgerufen werden, dann regelt die Ladesteuerung den WR nicht.  
Es werden nur Werte gelesen und in die SQLite Datei zur Auswertung geschrieben.  

### ACHTUNG Änderung in der config.ini im Block [Logging]
- Variable Logging_file erhält vollständigen Namen
- Variable Logging_type entfernt 

**[0.11.1] – 2023-11-11**

Änderung in SymoGen24Connector.py
- FIXED: Wenn nur ein MPPT angeschlossen ist, wurde der Wert für die PV-Produktion stark verfälscht.  
  Siehe Diskusion https://github.com/wiggal/GEN24_Ladesteuerung/discussions/35  

Änderung in SymoGen24Controller2.py  
- FIXED: Die Einträge in der Tabelle "EntladeSteuerung" wurden nicht berücksichtigt.
  Minimalwert bei Einträgen in die Tabelle "EntladeSteuerung" ist 0,1(KW = 100Watt). Hilfe ergänzt

**[0.11.0] – 2023-11-07**

## ACHTUNG diese Version beinhaltet umfangreiche Änderungen in den config-Dateien!!!  
**Bitte CHANGELOG.md genau lesen und alle Anpassungen in den config-Dateien durchführen**  
**Oder: eigene Anpassungen in die mitgelieferten config-Dateien übernehen!**   

Änderung in html/index.php:  
- Navigation ohne Javascript und mehr responsive  

#### ACHTUNG bitte html/config.php anpassen!!!  
Änderung in html/config.php  
Die NavigationsTABs werden nun in dem Array `$TAB_config` konfiguriert (Tabname, Dateiname, Startauswahl, ein/aus-blenden)  
Die config.ini aus dem Pythonverzeichnis wir gelesen um auf die Variablen zugreifen zu können.  
Variable $SQLite_file  entfernt, sie wird nun aus der config.ini ermittelt  

**NEU:** 7_tab_Diagram.php (noch Prototyp)  
Damit werden die Daten aus der SQLite Datei graphisch aufbereitet.  
Erforderlich php-sqlite3:  
`sudo apt install php-sqlite3`  

Änderung in html/1_tab_LadeSteuerung.php  
- Am Ende der Seite wird der Anforderungszeitpunkt der Prognose ausgeben.  

Änderung in Solarprognose_WeatherData.py, Solcast_WeatherData.py, WeatherDataProvider2.py  
- Meldung eingefügt, wenn die definierten "dataAgeMaxInMinutes" noch nicht abgelaufen sind,  
  und deshalb keine Prognose angefordert wird.  

Änderung in SymoGen24Controller2.py  
- Logging wird nur geschrieben, wenn der Parameter "schreiben" übergeben wurde.  

### ACHTUNG umfangreiche Änderungen in config.ini, bitte anpassen!!!  
**NEU Zusatzkonfigurationen für die Ladeberechnung möglich (z.B. für Wintermonate usw.)  
- neu Variable `Zusatz_Ladebloecke` im Block `[Ladeberechnung]`  
- neue Blöcke `[Winter]`  und `[Uebergang]`  
- In den Blöcken `[Winter]`  und `[Uebergang]` zusätzliche Werte für bestimmte Monate definiert werden,  
  diese überschreiben die Werte im Block `[Ladeberechnung]`, im den entsprechenden Monaten.  
  Es können auch noch mehrere Blöcke definiert werden.  

** Kommentare in config.ini von "#" auf ";" umgestellt!!  
- die Kommentierung musste von "#" auf ";" umgestellt werden, um die Datei in PHP parsen zu können.  
  Dadurch kann man einfach in PHP auf die config.ini von Python zugreifen.  

**[0.10.5] – 2023-10-29**

Änderung in Solcast_WeatherData.py und config.ini
- Zeitzone in config.ini auf +1 geändert, und in Solcast_WeatherData.py auf automatische Sommer-, Winterzeitumstellung geändert.

**[0.10.4] – 2023-10-26**

Änderung in SymoGen24Controller2.py, config.ini und functions.py
- Logging als "csv" oder "sqlite" eingebaut
- LoggingSymoGen24.py ist überflüssig und wird entfernt

### ACHTUNG bitte evtl. in config.ini anpassen!!!
- neuer Block [Logging]

**[0.10.3] – 2023-10-24**

- Alte start_skripte gelöscht

Änderung in html/4_tab_Crontab_log.php
- Anzeigen der "config.ini" ähnlich der Editierseite dargestellt und dadurch lesbarer.

Änderung in Solcast_WeatherData.py
- Fix: Wenn solcast.com nicht erreichbar fällt skript auf die Nase.

Neue Datei functions.py
- Häufig genutzte Funktionen in die Datei "functions.py" ausgelagert.
  Neue Funktion um alle Variablen beim Lesen aus der config.ini zu prüfen. 
  Angepasst in SymoGen24Connector.py, SymoGen24Controller2.py, WeatherDataProvider2.py, Solarprognose_WeatherData.py und Solcast_WeatherData.py

**[0.10.2] – 2023-10-15**

- in html/config.php relative Pfade eingeführt, dadurch müssen sie nicht mehr angepasst werden.

Neue Prognoseabfrage von solcast.com erstellt. Kann mit Solcast_WeatherData.py abgerufen werden.  
Hierfür ist ein neuer Block "[solcast.com]" in der config.ini nötig. Crontabeintrag siehe README.  
Leider kann Solcast_WeatherData.py nur 5x am Tag aufgerufen werden, 
da pro Lauf zwei Zugriffe erforderlich sind und insgesamt nur 10 pro Tag möglich sind.   

- Alle Pythonskripte werden ab jetzt mit "start_PythonScript.sh skriptname" in der "crontab" gestartet
### ACHTUNG bitte Crontabeinträge anpassen!!!
  z.B.: 
  */5 06-16 * * * /home/GEN24/start_PythonScript.sh SymoGen24Controller2.py schreiben
  1 6,8,11,13,15 * * * /home/GEN24/start_PythonScript.sh Solcast_WeatherData.py

Alte start_skripte fallen mit der nächsten Version weg!!!

**[0.10.1] – 2023-10-10**

- html/1_tab_LadeSteuerung.php: Schreibfehler in Mouseover beseitigt
- html/3_tab_Hilfe.html: Beschreibung LadeSteuerung präzisiert
- Beschreibungen in der README angepasst
- Prognosekalkulationstabelle "Ladewerte_Vergleichtabelle.ods" angepasst

- Die Werte "WRSchreibGrenze_nachUnten" und "WRSchreibGrenze_nachOben" werden ab 90% Batterieladung mit (1+(Ladestand%-90%)/5) multipliziert, 
  dadurch soll das hoch- und runterschalten der Batterieladung am Ende des Tages besser verhindert werden.

### ACHTUNG bitte evtl. in config.ini anpassen!!!
- Neue Variable "Grundlast_WoT" in config.ini
  Da an bestimmten Wochentagen (z.B. Wochenende) die Grundlast höher sein kann, kann sie hier für jeden Wochentag unterschiedlich gesetzt werden.
  Voraussetzung damit die Grundlast_WoT für den aktuellen Tag gesetzt wird, die Variable "Grundlast" muß "0" sein.

Änderung in SymoGen24Controller2.py und Solarprognose_WeatherData.py
- Alle Zahlenwerte beim Lesen aus der config.ini prüfen ob wirklich Zahlen definiert sind.

[0.10.0] – 2023-10-04

Änderung in SymoGen24Controller2.py
- Neuimplementierung der prognosebedingten Ladeberechnung unter Berücksichtigung der Variablen "BatSparFaktor",
  um die Ladeverteilung auf den Tag besser steuern zu können.

  Folgende Werte bewirken folgendes:  
  bei 1: Keine Verschiebung, Verteilung rein nach Prognoseüberschuss  
  von 1 bis 0.1: Die Batterieladung wird prognoseabhängig immer weiter zum Zeitunkt in "BattVollUm" verschoben.  
  größer 1: Die Batterieladung wird prognoseabhängig immer gleichmäßiger über den Tag verteilt.  

### ACHTUNG bitte in config.ini anpassen!!!
- Änderung in config.ini
  Da die Variable "BatSparFaktor" größeren Einfluss bekommt, werden die Variablen "BatWaitFaktor" und "BatWaitFaktor_Max" nicht mehr benötigt und wurden entfernt

- Änderungen in Ladewerte_Vergleichtabelle.ods eingearbeitet.

- Watt_Reservierung.json und html/EV_Reservierung.json mit ausliefern, damit die Dateien vorhanden sind, 
  falls im Verzeichnis nicht geschrieben werden darf.

- Fehlerbereinigung:
  Entladesteueung lief um 00:xx Uhr auf einen Fehler beseitigt (neue Akku_EntLadeSteuerFile.json)

[0.9.6] – 2023-09-12

Neuen Tab "html/6_tab_GEN24.php" zum lokalen Aufruf des Wechselrichters eingeführt.

### ACHTUNG bitte in config.ini anpassen!!!
Änderung in SymoGen24Controller2.py, config.ini, und config.ini.info
- Puffer_Einspeisegrenze und Puffer_WR_Kapazitaet durch WRSchreibGrenze_nachOben ersetzt bzw. entfernt, da sie ohnehin annähernd gleich sein müssen.

- Fehlerbereinigung im Messaging (evtl. doppelte Zeile)
- DEBUG erweitert

[0.9.5] – 2023-08-13

Neuprogrammierung der Entladesteuerung

### ACHTUNG bitte in config.ini anpassen!!!
Neuerungen in config.ini
- Block "[Entladung]" eingeführt und Variablen aus Block "[Reservierung]" entfernt

Neuerungen in SymoGen24Controller2.py
- Umfangreiche Änderungen im Bereich "E N T L A D E S T E U E R U N G"

Neuen Tab "html/2_tab_EntladeSteuerung.php" zur Entladesteuerung eingeführt

Hilfe an die neue Entladesteuerung angepasst.

Änderungen:
- Umwandlung von Komma in Punkt in Eingabetabellen

[0.9.4] – 2023-08-03

Änderung in 1_tab_Reservierung.php
- Manuelle Entladesteuerung in Prozent für den Hausakku eingebaut

Änderung in SymoGen24Controller2.py
- Ersetzen der Variablen BatterieVoll ab den Prozenten (z.B. 97%) die Ladung auf MaxLadung geschaltet wurde.
  Die Funktion arbeitete nicht zufriedenstellend und verhinderte nicht immer das hoch und runter schalten der Batterieladung.
  Neu:
  Der Wert "WRSchreibGrenze_nachUnten" wird ab 90% um 1+(Ladestand%-90%)/10 erhöht, 
  dadurch soll das hoch und runter schalten der Batterieladung besser verhindert werden.
- Lesen der manuellen Entladesteuerung eingebaut

### ACHTUNG bitte in config.ini anpassen!!!
Änderung in config.ini und config.ini.info
- Variable "BatterieVoll" entfernt.

Änderung in 2_tab_Hilfe.html
- Manuelle Entladesteuerung in Prozent in Hilfe beschrieben.

[0.9.3] – 2023-07-02

Änderung in SymoGen24Controller2.py
- Wenn Ladewert erstmals den Wert von "MaxLadung" erreicht immer schreiben, unabhängig der Schreibgrenzen

Änderung in html/4_tab_Crontab_log.php
- "Neu laden" Button am Ende der Ausgabe hinzugefügt
- Filter, um nur bestimmte Zeilen aus der Crontab.log auszugeben

[0.9.2] – 2023-06-07

Änderung in html/3_tab_config_ini.php
- Prüfung ob config.ini Schreibrechte hat engebaut

Änderung in SymoGen24Controller2.py
- Prüfung, ob die neuen Varaiblen Puffer_Einspeisegrenze, PV_Leistung_Watt 
  und Puffer_WR_Kapazitaet in der config.ini sind, eingebaut.

[0.9.1] – 2023-06-04

### ACHTUNG bitte in config.ini anpassen!!!
Änderung in config.ini
- Folgende neue Variablen eingeführt, um die Leistung, die der WR abregelt, besser zu steuern.  
  Zeile 76 bis 79:   
  Puffer_Einspeisegrenze  
  PV_Leistung_Watt   
  Puffer_WR_Kapazitaet  
  
Änderung in SymoGen24Controller2.py

- Puffer an den Grenzen zur Einspeisegrenze und zur WR AC Kapazität eingeführt.
  Da Der Wechselrichter schon abregelt, wenn man an die jeweiligen Grenzen kommt,
  kann die Differenz über der Grenze nicht ermittelt werden, deshal muss entweder 
  die konfigurierte Grenze unterhalb der WR Grenze konfiguriert werden.
  Damit hier nicht zuviel in die Batterie geladen wird und sie zu schnell voll ist,
  wird der Puffer angewendet, wenn die Grenze aus der config.ini erreicht wird.

[0.9.0] – 2023-05-28

Änderung in SymoGen24Controller2.py
- LadewertGrund = "aktuelleEinspeisung + aktueller Ladewert > Einspeisegrenze"
  geändert in:
  LadewertGrund = "aktuelleEinspeisung + aktuelle Batterieladung > Einspeisegrenze"
  - Da die tatsächliche aktuelle Batterieladung weniger als die Ladegrenze sein kann (wenns auch bei so viel Überschuss nicht sein dürfte),
    wurde der Ladewert wenn er über der Einspeisegrenze lag, in seltenen Fällen falsch berechnet.

Seite des Reservierungsmoduls umgebaut:
- Die verschiedenen Seiten werden nun als "TAB" dargestellt.
- Ein Tab zum Ausgeben UND Editieren der config.ini der Ladesteuerung eingefügt
  Dazu Kennwort in die html/config.php eingefügt ($passwd_configedit)
- Ein Tab zur Ausgabe der Crontab.log der Ladesteuerung von Heute eingefügt
- Mit der Namenskonvention [1-9]_tab_xxxxxxx.[php|html] können eigene Skripts als "TAB" eingebunden werden. 

[0.8.9] – 2023-05-21

Ergänzungen und präzisere Beschreibungen in der README.md

Änderung in Solarprognose_WeatherData.py
- weatherData.json nicht schreiben, wenn keine Daten kommen
  und Fehlermeldungen in Crontab.log schreiben

[0.8.8] – 2023-05-01

Änderung in SymoGen24Controller2.py
- Message an ntfy.sh optisch aufbepeppt ;-)

Änderung in SymoGen24Connector.py
- Da Programm nur mit pyModbusTCP Version 0.1.10 lauffähig abprüfen

[0.8.7] – 2023-03-23

Änderung in SymoGen24Controller2.py
- Messaging wurde nur ausgeführt, wenn Batterieentlandesteuerung aktiv ist: fixed

[0.8.6] – 2023-03-20

Änderung im Solarprognose_WeatherData.py
- KW_Faktor eingefügt, falls sich die Anlagengröße auf dem Dach zu der in Solarprognose unterscheidet.

Änderung in SymoGen24Controller2.py
- Wenn die Prognose ins Minus ging, wurde die überschreitung der Wechselrichterkapazietät falsch berechnet. -Bereinigt

Änderung im Reservierungsmodul:
- Mit "Hausakkuladung" kann nun unter 4 Otionen ausgeählt werden:
    „AUTO“ = Automatische Ladesteuerung nach Prognose
    „AUS“    = Batterieladung wird ausgeschaltet
    „HALB“ = Batterieladung erfolgt mit halber Leistung
    „VOLL“ = Batterieladung erfolgt mit voller Leistung

[0.8.5] – 2023-02-24

Änderung im Reservierungsmodul:
- Mit der Option "Hausakku mit voller Kapazität laden!!" wird die volle Batterieladung direkt nach dem Sichern eingeschaltet.

Änderung in SymoGen24Controller2.py

- Volle Batterieladung aus Reservierungsmodul eingebaut.

[0.8.4] – 2023-02-18

Änderung in SymoGen24Controller2.py

- FesterLadeleistung an erste Stelle gezogen, war bisher hinter MindBattLad,
  dadurch wurde "FesterLadeleistung" erst aktiv, wenn der Batteriestand über MindBattLad war.

NEUE FUNKTION [messaging] ermöglicht eine Nachricht über https://ntfy.sh/ auf das Smartphone,
              wenn auf den WR geschrieben wird.

- Patameter zur Steuerung in config.ini unter [messaging] eingebaut
- Funtionalität in SymoGen24Controller2.py eingebaut


[0.8.3] – 2023-02-13

Änderung in SymoGen24Controller2.py

Schaltverzögerungen eingebaut, damit nicht so oft auf den WR geschrieben wird, bei:
  - Ladesteuerung,  Mindestbatterieladung
  - Entladesteuerung, BisLadestandEIN

- Erklärungen in config.ini.info bezüglich Reservierung ergänzt

[0.8.2] – 2023-02-05

html/hilfe.html angepasst

Änderung in SymoGen24Connector.py

- die reservierte PV-Leistung wurde meisst mehrfach von der Prognose abgezogen. (Fehler bereinigt)
- Änderungen bei der Protokollierung

[0.8.1] – 2023-01-15

Änderung in SymoGen24Connector.py

- Funtion zum Auslesen der Batteriepower (Laden bzw. entladen)
  get_batterie_power()

html/hilfe.html hinzugefügt und in html/index.php eingebunden.

Änderung in config.ini

- Werte für Batterieentladesteuerung hinzugefügt.

Änderung in SymoGen24Controller2.py

- Funktion zum Holen der Config von Github entfernt

- Batterieentladesteuerung hinzugefügt.
  Die Batterieentladesteuerung schaltet das Entladen des Hausakkus ab.
  ( Nur in Verbindung mit der "Reservierung von groesseren Mengen PV Leisung" möglich )

  Zum Beispiel unter folgenden Bedingungen:

  Akkuladestatus ist unter 80 %
  UND Reservierte Leistung zur aktuellen Stunde ist über 2KW
  UND Verbrauch im Haus ist größer als 90% der reservierten Leistung


[0.8.0] – 2022-12-30

- README.md angepasst

- Modul zur Reservierung von groesseren Mengen PV Leisung für Elektroautos usw. eingebaut.
  Zum Betrieb ist ein Webserver mit PHP auf dem Steuerungsrechner noetig.
  Weiteres siehe README

[0.7.7] – 2022-09-25

Änderung in SymoGen24Controller2.py

- Ausgabe "Neuer Ladewert/Watt" bei FesterLadeleistung berichtigt
- Formel bei "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt" berichtigt


[0.7.6] – 2022-09-15

Änderung in SymoGen24Controller2.py

- Schaltverzögerungen eingebaut, wenn
  "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt"
  und
  "PrognoseAbzugswert kleiner Grundlast und Schreibgrenze"

- Fehlerbereinigung: Wenn die Ladung der Batterie in % unter "MindBattLad" war, lief das Programm auf den Fehler:
                     Fehlermeldung: name 'Tagessumme_Faktor' is not defined
  Prognoseberechnung vorangestellt, damit wird sie jetzt immer ausgeführt, auch wenn sie durch andere Bedingungen nicht verwendet wird.                   

[0.7.5] – 2022-09-06

- Erklärungen in config.ini.info präzisiert, bzw. berichtigt 
- Ausgabewerte von SymoGen24Controller2.py neu gestaltet

[0.7.4] – 2022-08-18

- Fehler in Ladewerte_Vergleichtabelle.ods bereinigt.

Änderung in SymoGen24Controller2.py 

- Kleine Anpassungen in den Variablen BattganzeLadeKapazWatt und BattganzeKapazWatt
- Ausgabe der Tagessumme für den BatWaitFaktor

[0.7.2] – 2022-08-12

Änderung in SymoGen24Controller2.py 

- Wenn der Ladestand der Batterie unter den Wert der Variablen MindBattLad fiel, wurde die Variable TagesPrognoseUeberschuss nicht definiert.
- Eventuellen Fehler in den Printbefehlen abgefangen, damit stürtzt nicht das ganze Programm ab, wenn ein Fehler in der Variablenausgabe auftritt.
- Fehler beim Berechnen der Batteriekapazität, der das Ladeverhalten von Batterien die nicht ungefähr 10KW haben stark  verfälscht, bereiningt.

[0.7.1] – 2022-08-07

- umbenannt: config.info -> config.ini.info

- Variable BattganzeKapazWatt umbenannt in BattganzeLadeKapazWatt

- StorageControlMode auf 3 stellen (bisher 1) 

- WRSchreibGrenze_nachUnten Erhöhung wenn "PrognoseAbzugswert <= Grundlast" nicht nötig

[0.7.0] – 2022-07-23


- Zusammenführen der fast wirkungsgleichen Parameter "MaxKapp" und "MaxLadung" zu "MaxLadung"

- Einführen der Variablen "BatWaitFaktor" und "BatWaitFaktor_Max". 
  Mit den Variablen kann für exakt nach Süden ausgerichtete PV-Anlagen der Zeipunkt
  des Ladebeginns in Abhängigkeit der Prognose nach hinten verschoben werden. Ist nur aktiv vor 13:00 Uhr.
  Auslieferung: 
  BatWaitFaktor = 0.0  # Funtion ist nicht aktiv, wenn der Wert 0 ist. Sinnvoller Wert um die 1-5.
  BatWaitFaktor_Max = 10  # Kann so bleiben

- "BatWaitFaktor" in Ladewerte_Vergleichtabelle.ods als Näherung eingearbeitet.

- Die meisten Eräuterungen aus der config.ini in die neue Datei config.info ausgelagert, 
  damit die config.ini übersichtlicher bleibt.


[0.6.4] – 2022-07-16

- Kappung des Ladewertes auf 100er ist nicht mehr nötig, wegen Schreibgrenzen "WRSchreibGrenze_nachOben/Unten",
  schreibe nun genau den errechneten Wert.

- LadungAus war bisher auf 10 Watt in der Prozedur festgelegt, kann nun in der config.ini als "LadungAus" festgelegt werden (z.B. 0 oder 10 Watt)

[0.6.3] – 2022-07-13

Änderung in SymoGen24Controller2.py und LoggingSymoGen24.py

- Fehlermeldungen bei fehlender weatherData.json abgefangen.
- Tippfehler in Variable  "BatterieVoll"

[0.6.2] – 2022-07-12

Änderung in SymoGen24Connector.py und SymoGen24Controller2.py

- Fehlermeldungen abgefangen, wenn:
  die Batterie offline ist und
  Modbus ausgeschaltet ist

[0.6.1] – 2022-07-11

Änderung in Solarprognose_WeatherData.py und config.ini

-  Zum Abrufen der Prognose von http://www.solarprognose.de, den Parameter "algorithm=mosmix|own-v1|clearsky" eingebaut.

[0.6.0] – 2022-07-10

Änderung in SymoGen24Controller2.py, SymoGen24Connector.py und config.ini

- Implementierung der Fallbackfunktion des Wechselrichters
 
  INFOS:
  Im Register 40359 InOutWRte_RvrtTms wird der Zeitraum bis zum Fallback in Sekunden geschrieben
  Wird innerhalb dieses Zeitraums etwas über Modbus auf den Wechselrichter geschrieben, wird der Counter neu gestartet
  Wird innerhalb des Fallbackzeitraums nicht auf den WR geschrieben erfolgt der Fallback.
  Beim Fallback wird das Register 40349 StorCtl_Mod auf 0 gesetzt, also der Ladungsspeichersteuerungsmodus deaktiviert.

- Fallback kann in der config.ini im Bereich [Fallback] ein/aus geschaltet und der Zeitabstand eingestellt werden (Auslieferung AUS)
- Register 40359 "InOutWRte_RvrtTms_Fallback" in SymoGen24Connector.py hinzugefügt
- In SymoGen24Controller2.py wird zu jeder vollen Stunde des Zeitabstandes das Register 40359 neu geschrieben 
  und dadurch der Counter zurückgesetzt, ausser es ist zu dem Zeitpunkt ein anderer Schreibzugriff passiert.



[0.5.5] – 2022-07-07

Änderung in SymoGen24Controller2.py

- Ist "FesteLadeleistung" gesetzt wird sie nun immer geschrieben, unabhängig von den Schreibgrenzen des WR,
  ausser sie ist genau gleich dem alten Wert.

[0.5.4] – 2022-07-04

Änderung in SymoGen24Controller2.py und Ladewerte_Vergleichtabelle.ods

- Ladewert bei Prognoseberechnung darf nicht größer als MaxLadung werden.

[0.5.3] – 2022-07-02

Änderung in SymoGen24Controller2.py

- Waren die Prognosen an der Grenze zur Grundlast wechselte das Programm öfters zwischen keiner und voller Lagung. 
  In dem Bereich "PrognoseAbzugswert <= Grundlast" wurde eine Schaltverzögerung angebracht.


[0.5.2] – 2022-06-23

Änderung in SymoGen24Controller2.py

- Abzugswert sollte nicht kleiner Grundlast sein, sonnst wird PV-Leistung zur Ladung der Batterie berechnet, 
  die durch die Grundlast im Haus verbraucht wird. => Batterie wird nicht voll 

[0.5.1] – 2022-06-20

Ladewerte_Vergleichtabelle.ods hinzugefügt.

[0.5.0] – 2022-06-20

Mit neuem Skript Solarprognose_WeatherData.py, damit kann alternativ eine Prognose
von http://www.solarprognose.de abgerufen werden.
Dafür ist auf http://www.solarprognose.de/ ein Account erforderlich
Evtl. kann ein Prognoseskript als Backup verwendet werden, falls ein Dienst ausfällt, entspechende dataAgeMaxInMinutes hoch stzen (z.B. 1000).


[0.4.4] – 2022-06-16

Änderung in SymoGen24Controller2.py

- Variable "MinVerschiebewert" entfernt, nicht mehr benötigt (auch aus config.ini)
- Abgefangen, wenn WR offline 


[0.4.2] – 2022-06-14

Änderung in SymoGen24Controller2.py

- Fehler bereinigt: Wenn TagesPrognoseUeberschuss und BattKapaWatt_akt = 0, ist Programm in Enlosschleife
- Steuerung über Github entfernt (auch aus config.ini)

- Variable "DiffLadedaempfung" und Auswirkungen entfernt


[0.4.1] – 2022-06-12

Änderung in SymoGen24Controller2.py

- Wenn die Prognosen so gering sind, dass die Batteriekapazietät nicht erreicht wird, obwohl der Abzugswert 0 ist
  wird der Batterieladewert auf "MaxLadung" gesetzt. Dadurch enfällt der Wert "MindestSpitzenwert".

Änderung in config.ini

- Zeile "MindestSpitzenwert = 2000" mit Erläuterung entfernt

[0.4.0] – 2022-06-12

- Beschreibung in Ladeintelligenz.pdf ergänzt

Änderung in SymoGen24Controller2.py

- Historische nicht mehr benötigte Elemente entfernt
- Schleife zur Ermittlung des Ladewertes aus den Prognosewerten läuft nun von 0 nach oben, 
  dadurch entfällt der Wert "StartKappGrenze" in der config.ini
  Der Wert "StartKappGrenze" muss nun nicht mehr an die PV-Größe angepasst werden.

Änderung in config.ini

- den Eintrag "StartKappGrenze = 11000" entfernt
- Erläuterungen ergänzt

Datei hinzugefügt: Prognosewerte_Vergleichtabelle.ods

- Durch Einträge in den roten Zellen werden die Ladewerte in den blauen Zellen berechnet
  Um die errechneten Werten von "SymoGen24Connector.py" auszugeben den Print (akt. Zeile 81) einkommentieren


[0.3.5] – 2022-06-10

Änderung in SymoGen24Controller2.py

- Kleine Änderung in Formel "Stundendaempfung"

Tippfehler bereinigt

[0.3.4] – 2022-06-09

Änderung in SymoGen24Controller2.py

- Die Formel zur Berechnung  des Batterieladewertes aus der Prognose, war falsch. Die Batterie wurde nur mit ca. 10% der nötigen Energie geladen.


[0.3.1] – 2022-06-08

Änderung von Firex2 von www.photovoltaikforum.com  eingearbeitet

    config.ini
    WeatherDataProvider2.py

- durch einen Eintrag in der config.ini kann ein zweites PV-Feld mit anderer Ausrichtung usw. in die Prognosewerte einfließen.



[0.3.0] – 2022-06-06

Danke an Firex2 von www.photovoltaikforum.com für die Tests und Hinweise


	SymoGen24Connector.py

- Lesen der config.ini zum ermitteln der der WR-IP, es reicht nun die WR-IP in der config.ini anzugeben.
- Anpassen der Register des PowerMeter (Smartmeter) zum lesen der Einspeisung
- Funktionen zur korrekten Ausgabe der Produktion (MPPT_1 + MPPT_2) bzw  der Einspeisung bei den verschieden Skalierungsfaktoren (get_mppt_power, get_meter_power)

	LoggingSymoGen24.py

- Hart gesetzte WR-IP durch Wert aus config.ini ersetzt, es reicht nun die WR-IP in der config.ini anzugeben.

	SymoGen24Controller2.py

Umfangreiche Umstellung des zu ermittelnden Ladewertes

1.) 
- der Ladewert wird aus der Datei „weatherData.json“ von forecast.solar ermittelt. Er dient hauptsächlich dazu, dass die Batterie möglichst voll wird.
- Mit der Variablen „BattVollUm“ kann gesteuert werden, wann die Batterie ungefähr voll sein soll.
- Mit der Variablen „BatSparFaktor“ kann die Batteriekapazität in Abhängigkeit von der Uhrzeit (vormittags geringerer Ladewert) für später gespart werden.
- Ab der Variablen „StartKappGrenze“ wird nach unten gerechnet, bis die darüber liegenden Prognosewerte die Batterie bis zu „BattVollUm“ voll machen.
- liegt der höchste Prognosewert am Tag unter der variablen „MindestSpitzenwert“ wird schon morgens mit „MaxLadung“ voll geladen.
- auch wenn die Batterieladung unter „MindBattLad“ liegt wird voll geladen bis der Wert „MindBattLad“ erreicht ist.

2.)
- Anhand der aktuellen Einspeisung wird ermittelt wie weit sie aktuell über der „Einspeisegrenze“ liegt, und ein entsprechender Ladewert berechnet.

3.)
- liegt die aktuelle Produktion über der AC-Ausgangsleistung des WR (Variable „WR_Kapazitaet), wird die Überschüssige Energie in die Batterie geladen, wenn der Ladewert nicht bereit höher ist.

Damit bei schwankender PV-Produktion (z.B. durchziehende Wolken, kurz eingeschaltete Verbraucher) nicht ständig auf den WR geschrieben wird, kann dies durch folgende Variablen gesteuert werden.
- WRSchreibGrenze_nachOben: Ist der berechnete Ladewert höher als diese Grenze wird sie auf den WR geschrieben.
- WRSchreibGrenze_nachUnten: Ist der berechnete Ladewert niedriger als diese Grenze wird sie auf den WR geschrieben.
Da im laufe des Tages die Produktion meistens steigt, und die Ladung, damit die Batterie voll wird, auch immer höher werden sollte, habe ich den Wert für „WRSchreibGrenze_nachUnten“ deutlich höher gesetzt.

- Wenn die Batterie bis zu folgendem Prozentsatz („BattertieVoll“) voll ist, wird voll geladen.

=================================================
Einführung einer CHANGELOG.md ab Version 0.3.0:
