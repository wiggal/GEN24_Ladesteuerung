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
