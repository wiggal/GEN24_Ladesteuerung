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
