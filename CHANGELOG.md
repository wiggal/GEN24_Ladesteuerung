[0.3.5] – 2022-06-10

Aenderung in SymoGen24Connector.py

- Kleine Änderung in Formel "Stundendaempfung"

Tippfehler bereinigt

[0.3.4] – 2022-06-09

Aenderung in SymoGen24Connector.py

- Die Formel zur Berechnung  des Batterieladewertes aus der Prognose, war falsch. Die Batterie wurde nur mit ca. 10% der nötigen Energie geladen.


[0.3.1] – 2022-06-08

Aenderung von Firex2 von www.photovoltaikforum.com  eingearbeitet

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
