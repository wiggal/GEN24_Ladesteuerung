GEN24_Ladesteuerung

Ladesteuerung für  Fronius Symo GEN24 Plus um die 70% Kappung zu umgehen

Das Programm wurde auf Grundlage von https://github.com/godfuture/SymoGen24Weather erstellt.
Herzlichen Dank an "godfuture"

Voraussetzung ist, dass "Slave als Modbus TCP" am GEN24 aktiv ist und 
und auf "int + SF" gestellt ist, sonst passen die Register nicht.


Folgende Installationen erfolgen auf einem Ubuntu/Mint 

Folgende Installationen sind nötig, damit die Pythonskripte funktionieren

apt install python3

apt install python3-pip

pip install pyModbusTCP

pip install pickledb

pip install pytz

sudo pip install xmltodict



Die Startskripte können per Cronjobs gestartet werden.

Beispiele Crontabeintraege

*/5 05-20 * * * DIR/start_LoggingSymoGen24.sh

*/5 04-20 * * * DIR/start_SymoGen24Controller2.sh

05 */3 * * * DIR/start_WeatherDataProvider2.sh

WeatherDataProvider2.py

holt die Sonnenstundenprognosen von forecast.solar und schreibt sie in weatherData.json

Damit die Wetterdaten aktuell bleiben ist es besser sie öfter abzufragen (hier alle 3 Std)


SymoGen24Connector.py

Wird von SymoGen24Controller2.py aufgerufen und
stellt die Verbindung Zum Wechselrichter (GENR24 Plus) her.


SymoGen24Controller2.py

berechnet die aktuell besten Ladewerte aufgrund der Werte in weatherData.json und gibt sie aus.
Mit dem Parameter "schreiben" aufgerufen schreibt er die Ladewerte auf den Wechselrichter.


LoggingSymoGen24.py (optional)

schreibt folgende Werte in die Log.csv zur Auswertung der Ergebnisse mit z.B. libreoffice Calc
Zeit,Ladung Akku,Verbrauch Haus,Leistung ins Netz,Produktion,Prognose forecast.solar,Aktuelle Ladegrenze,Batteriestand in Prozent


