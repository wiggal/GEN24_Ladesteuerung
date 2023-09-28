# GEN24_Ladesteuerung 
(getestet unter Python 3.8 und 3.9)

![Screenshot](pics/Steuerungstabellen.png)

Ladesteuerung für  Fronius Symo GEN24 Plus um die 70% Kappung zu umgehen,
und Produktion über der AC-Ausgangsleistung des WR als DC in die Batterie zu laden.

Das Programm wurde auf Grundlage von https://github.com/godfuture/SymoGen24Weather erstellt. <br>
Herzlichen Dank an "godfuture"

Voraussetzung ist, dass "Slave als Modbus TCP" am GEN24 aktiv <br>
und auf "int + SF" gestellt ist, sonst passen die Register nicht.

Folgende Installationen sind nötig, damit die Pythonskripte funktionieren <br>
(getestet auf einem Ubuntu/Mint und auf einem Raspberry Pi mit Debian GNU/Linux 11)

sudo apt install python3 <br>
sudo apt install python3-pip <br>
sudo pip install pyModbusTCP==v0.1.10   # mit Version 0.2.x nicht lauffähig <br>
sudo pip install pickledb <br>
sudo pip install pytz <br>
sudo pip install xmltodict <br>
sudo pip install NumPy==v1.23.1 <br>
sudo pip install requests <br>
sudo pip install ping3 <br>


Die Startskripte können per Cronjobs gestartet werden. <br>
Als Erstes muss ein start_WeatherData.. aufgerufen werden, damit Prognosedaten in weatherData.json vorhanden sind!!!

Beispiele Crontabeintraege ("DIR" durch dein Insttallationverzeichnis ersetzen) <br>
Ausführrechte für die start_...sh skripte setzen nicht vergessen (chmod +x start_*)

*/5 05-20 * * * /DIR/start_LoggingSymoGen24.sh <br>
*/5 04-20 * * * /DIR/start_SymoGen24Controller2.sh <br>
33 6,8,10,12,14,16 * * * /DIR/start_WeatherDataProvider2.sh <br>
8 5,10,15,19 * * * /DIR/start_Solarprognose_WeatherData.py.sh #Minuten und Sekunden (config.ini) anpassen <br>

#Crontab.log jeden Montag abräumen <br>
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
falls Änderungen außerhalb der gesetzten Grenzen sind.


LoggingSymoGen24.py (optional)

schreibt folgende Werte in die Log.csv zur Auswertung der Ergebnisse mit z.B. libreoffice Calc, in folgendem Format:
Zeit,Ladung Akku,Verbrauch Haus,Leistung ins Netz,Produktion,Prognose forecast.solar,Aktuelle Ladegrenze,Batteriestand in Prozent


#####################################################################

Modul zur Reservierung von größeren Mengen PV-Leistung <br>
======================================================= <br>
(z.B. E-Autos)

Das Modul ist in PHP programmiert und setzt einen entsprechend konfigurierten Webserver (z.B. Apache, ) voraus. <br>
Konfiguration muss in der "config.php" angepasst werden.<br>

Nur zum testen kann der PHPeigene Webserver benutzt werden. Einfach unter /DIR/html/ folgendes aufrufen:<br>
php -S 0.0.0.0:7777 <br>
Und im Browser localhost:7777 aufrufen.<br>

Webserver Apache z.B.:

Installation: <br>
sudo apt install apache2 php <br>
In /etc/apache2/apache2.conf  <br>
<Directory /srv/> durch <Directory /DIR/html/> ersetzen!<br>

In /etc/apache2/sites-available/000-default.conf <br>
DocumentRoot /var/www/html durch DocumentRoot /DIR/html/ ersetzen<br>

ACHTUNG!! /DIR/ und /DIR/html/ muss Schreibrechte für Apache haben!!<br>
Mit der Namenskonvention [1-9]_tab_xxxxxxx.[php|html] können eigene Skripts als "Tab" eingebunden werden.<br>
Vorhandene Module:<br>
1_tab_LadeSteuerung.php    ==>> Reservierung von großen PV-Mengen und feste manuelle Ladesteuerung<br>
2_tab_EntladeSteuerung.php ==>>  EntladeSteuerung durch Eintrag in Tabelle und feste manuelle Entladesteuerung<br>
3_tab_Hilfe.html       ==>> Hile zu Reservierung von großen PV-Mengen<br>
4_tab_config_ini.php   ==>> Anzeigen und Editieren der config.ini<br>
5_tab_Crontab_log.php  ==>> Anzeigen der Logdatei Crontab.log<br>
6_tab_GEN24.php        ==>> lokaler Aufruf des GEN24<br>

Apache neu starten <br>
sudo systemctl restart apache2 <br>

Reservierung im Browser aufrufen (= IP oder localen Namen des RasberryPi).

Batterieladesteuerung ( TAB--> LadeSteuerung )<br>

Alle eingetragenen Reservierungen werden in die Datei /DIR/Watt_Reservierung.json geschrieben. <br>
In der html/config.php müssen die Dateipfade und Variablen angepasst werden.  <br>

Ist das Modul eingeschaltet (in /DIR/config.ini -->> PV_Reservierung_steuern = 1) wird die Reservierung <br>
beim nächsten Aufruf von SymoGen24Controller2.py mit eingerechnet.

Mit einer gewählten Ladestufe (AUS, HALB, VOLL) unter Hausakkuladung wird die entsprechende Batterieladeleistung,
beim nächsten Aufruf von SymoGen24Controller2.py auf den Wechselrichter geschrieben. <br>
Die prognosebasierte Ladesteuerung ist dadurch deaktivieren, und kann mit der Option "AUTO" wieder aktiviert werden.<br>

BatterieENTladesteuerung ( TAB--> EntladeSteuerung )<br>

Unter "Feste Entladegrenze " kann die maximale Entladeleistung
in den Schritten 0, 20, 40, 60, 80 oder 100 Prozent fest eingestellt werden.

In der Entladetabelle können Leistungen in KW zur Steuerung der Akkuentladung eingetragen werden.

Weitere Erklärungen stehen in der Hilfe (3_tab_Hilfe.html)




