**[0.13.3] – 2024-XX-XX**

Änderung in SymoGen24Controller2.py
- Bei Akkuschonung Schaltverzögerung (hysterese) eingebaut
- Bei zu geringer Prognose Akkuschonung nicht ausführen
  aktuelleVorhersage - (Grundlast /2) > AkkuschonungLadewert


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
- ein neuer Block [solcast.com2] wurde hizugefügt.

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
