GEN24_Ladesteuerung

Ladesteuerung für  Fronius Symo GEN24 Plus um die 70% Kappung zu umgehen

Das Programm wurde auf Grundlage von https://github.com/godfuture/SymoGen24Weather erstellt.
Herzlichen Dank an "godfuture"

Voraussetzung ist, dass "Slave als Modbus TCP" am GEN24 aktiv ist und 
und auf "int + SF" gestellt ist, sonst passen die Register nicht.


Folgende Installationen erfolgten auf einem Ubuntu/Mint 

Folgende Installationen sind nötig, damit die Pythonskripte funktionieren

sudo apt install python3

sudo apt install python3-pip

sudo pip install pyModbusTCP==v0.1.10   # Version 0.2.0 verursachte Fehler auf meinem Raspberry Pi

sudo pip install pickledb

sudo pip install pytz

sudo pip install xmltodict

sudo pip install NumPy

sudo pip install ping3



Die Startskripte können per Cronjobs gestartet werden.

Beispiele Crontabeintraege

*/5 05-20 * * * /DIR/start_LoggingSymoGen24.sh

*/5 04-20 * * * /DIR/start_SymoGen24Controller2.sh

33 6,8,10,12,14,16 * * * /DIR/start_WeatherDataProvider2.sh

8 6,9,13,16 * * * /DIR/start_Solarprognose_WeatherData.py.sh


WeatherDataProvider2.py

holt die Sonnenstundenprognosen von forecast.solar und schreibt sie in weatherData.json
Damit die Wetterdaten aktuell bleiben ist es besser sie öfter abzufragen (hier alle 2 Std)

Solarprognose_WeatherData.py 

Kann alternativ zu WeatherDataProvider2.py benutzt werden, ist etwas genauer, es ist aber ein Account erforderlich,
hier wird eine genauer Zeitpunkt für die Anforderung vorgegeben.
Holt die Sonnenstundenprognosen von solarprognose.de und schreibt sie in weatherData.json
Damit die Wetterdaten aktuell bleiben ist es besser sie öfter abzufragen (hier alle 2 Std)

SymoGen24Connector.py

Wird von SymoGen24Controller2.py aufgerufen und
stellt die Verbindung Zum Wechselrichter (GENR24 Plus) her.


SymoGen24Controller2.py

berechnet die aktuell besten Ladewerte aufgrund der Werte in weatherData.json und der tatsächlichen Einspeisung bzw Produktion und gibt sie aus.
Mit dem Parameter "schreiben" aufgerufen schreibt er die Ladewerte auf den Wechselrichter falls Aenderungen in den gesetzten Grenzen sind.


LoggingSymoGen24.py (optional)

schreibt folgende Werte in die Log.csv zur Auswertung der Ergebnisse mit z.B. libreoffice Calc
Zeit,Ladung Akku,Verbrauch Haus,Leistung ins Netz,Produktion,Prognose forecast.solar,Aktuelle Ladegrenze,Batteriestand in Prozent


