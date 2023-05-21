# GEN24_Ladesteuerung 
(getestet unter Python 3.8 und 3.9)

Ladesteuerung für  Fronius Symo GEN24 Plus um die 70% Kappung zu umgehen,
und Produktion über der AC-Ausgangsleistung des WR als DC in die Batterie zu laden.

Das Programm wurde auf Grundlage von https://github.com/godfuture/SymoGen24Weather erstellt.
Herzlichen Dank an "godfuture"

Voraussetzung ist, dass "Slave als Modbus TCP" am GEN24 aktiv ist und 
und auf "int + SF" gestellt ist, sonst passen die Register nicht.

Folgende Installationen sind nötig, damit die Pythonskripte funktionieren
(getestet auf einem Ubuntu/Mint und auf einem Raspberry Pi mit Debian GNU/Linux 11)

sudo apt install python3

sudo apt install python3-pip

sudo pip install pyModbusTCP==v0.1.10   # mit Version 0.2.x nicht lauffähig

sudo pip install pickledb

sudo pip install pytz

sudo pip install xmltodict

sudo pip install NumPy

sudo pip install ping3



Die Startskripte können per Cronjobs gestartet werden. <br>
Als Erstes muss ein start_WeatherData.. aufgerufen werden, damit Prognosedaten in weatherData.json vorhanden sind!!!

Beispiele Crontabeintraege ("DIR" durch dein Insttallationverzeichnis ersetzen) <br>
Ausführrechte für die start_...sh skripte setzen nicht vergessen (chmod +x start_*)

*/5 05-20 * * * /DIR/start_LoggingSymoGen24.sh <br>
*/5 04-20 * * * /DIR/start_SymoGen24Controller2.sh <br>
33 6,8,10,12,14,16 * * * /DIR/start_WeatherDataProvider2.sh <br>
8 5,10,15,19 * * * /DIR/start_Solarprognose_WeatherData.py.sh #Minuten und Sekunden (config.ini) anpassen <br>

# Crontab.log jeden Montag abräumen <br>
0 5 * * 1 mv /DIR/Crontab.log /DIR/Crontab.log_weg <br>


WeatherDataProvider2.py

holt die Sonnenstundenprognosen von forecast.solar und schreibt sie in weatherData.json <br>
Damit die Wetterdaten aktuell bleiben ist es besser sie öfter abzufragen (bei mir alle 2 Std)

Solarprognose_WeatherData.py 

Kann alternativ zu WeatherDataProvider2.py benutzt werden, ist etwas genauer, es ist aber ein Account erforderlich, <br>
hier wird eine genauer Zeitpunkt für die Anforderung vorgegeben. <br>
Holt die Sonnenstundenprognosen von solarprognose.de und schreibt sie in weatherData.json <br>
Damit die Wetterdaten aktuell bleiben ist es besser sie öfter abzufragen (bei mir alle 3 Std) <br>

SymoGen24Connector.py

Wird von SymoGen24Controller2.py aufgerufen und stellt die Verbindung Zum Wechselrichter (GENR24 Plus) her.


SymoGen24Controller2.py

berechnet die aktuell besten Ladewerte aufgrund der Werte in weatherData.json und der tatsächlichen Einspeisung bzw Produktion und gibt sie aus.
Mit dem Parameter "schreiben" aufgerufen (was in der start_SymoGen24Controller2.sh geschieht) schreibt er die Ladewerte auf den Wechselrichter <br>
falls Aenderungen ausserhalb der gesetzten Grenzen sind.


LoggingSymoGen24.py (optional)

schreibt folgende Werte in die Log.csv zur Auswertung der Ergebnisse mit z.B. libreoffice Calci, in folgendem Format:
Zeit,Ladung Akku,Verbrauch Haus,Leistung ins Netz,Produktion,Prognose forecast.solar,Aktuelle Ladegrenze,Batteriestand in Prozent


#####################################################################

Modul zur Reservierung von groesseren Mengen PV-Leistung <br>
======================================================= <br>
(z.B. E-Autos)

Das Modul ist in PHP programmiert und setzt einen entprechend konfigurierten Webserver (z.B. Apache) voraus. <br>
Konfiguration muss in der "config.php" angepasst werden.

Bei Apache ist dies z.B.:

Installation: <br>
sudo apt install apache2 php <br>
In /etc/apache2/apache2.conf  <br>
<Directory /srv/> durch <Directory /DIR/html/> ersetzen!<br>

In /etc/apache2/sites-available/000-default.conf <br>
DocumentRoot /var/www/html durch DocumentRoot /DIR/html/ ersetzen<br>

Apache neu starten <br>
sudo systemctl restart apache2 <br>

und Reservierung im Browser aufrufen (= IP oder localen Namen des RasberryPi).

Alle eingetragenen Reservierungen werden in die Datei /DIR/Watt_Reservierung.json geschrieben. <br>
In der html/config.php müssen die Dateipfade und Variablen angepasst werden.  <br>

Ist das Modul eingeschaltet (in /DIR/config.ini -->> PV_Reservierung_steuern = 1) wird die Reservierung <br>
beim nächsten Aufruf von SymoGen24Controller2.py mit eingerechnet.

 der gewählten Ladestufe (AUS, HALB, VOLL) unter Hausakkuladung beim nächsten Aufruf von SymoGen24Controller2.py berücksichtigt.
Mit der gewählten Ladestufe (AUS, HALB, VOLL) unter Hausakkuladung wird die volle Batterieladung nach dem Sichern eingeschaltet,
und eim nächsten Aufruf von SymoGen24Controller2.py auf den Wechselrichter geschrieben. <br>
Die prognosebasierte Ladesteuerung ist dadurch deaktivieren, und kann mit der Option "AUTO" wieder aktiviert werden.<br>

BatterieENTladesteuerung <br>
  Die Batterieentladesteuerung schaltet das Entladen des Hausakkus ab, wenn sehr hohe reservierte Verbräuche anliegen.<br>
  ( Nur in Verbindung mit der "Reservierung von groesseren Mengen PV Leisung" möglich )<br>

  Zum Beispiel unter folgenden Bedingungen (Einstellungen in config.ini):<br>

  Akkuladestatus ist unter 80 %<br>
UND Reservierte Leistung zur aktuellen Stunde ist über 2KW<br>
UND Verbrauch im Haus ist größer als 90% der reservierten Leistung<br>


