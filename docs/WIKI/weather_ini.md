## Einstellungen zu den PV-Vorhersagediensten in `weather_priv.ini`:
**`[env]`  
Hier folgen einige grundlegende Einstellungen.**  
`MaximalPrognosebegrenzung = 0`  
Hier kann die Vorhersage auf lokale Gegebenheiten begrenzt werden, etwa eine Abschattung im Westen nach 15:00 Uhr.
Entweder mit dem höchsten Wert aus dem letzten MaxProGrenz_Dayback, evtl. multipliziert mit dem Faktor MaxProGrenz_Faktor, oder mit einem durch scikit-learn, einem Machine Learning Programm in Python.  
; 0 = aus  
; 1 = ein: damit wird die Prognose auf den höchsten Wert je Stunde der Produktion der letzten MaxProGrenz_Dayback Tage begrenzt  
`MaxProGrenz_Faktor = 1`  
Hier wird der Faktor festgelegt, mit dem der ermittelte maximale Prognosewert multipliziert wird.  
`MaxProGrenz_Dayback = 35`  
Hier wird die Anzahl der letzten Tage festgelegt, die zur Ermittlung des maximalen Prognosewertes verwendet wird.  

**`[pv.strings]`  
Hier kann die Anzahl der Strings für bestimmte Wetterdienste auf zwei erhöht werden.**  
`anzahl = 1`  
Wenn ein zweites Feld mit anderer Ausrichtung vorhanden ist, hier Anzahl=2 eintragen und die Werte unter [forecast.solar2] und/oder [solcast.com2] eintragen.  

**`[forecast.solar] bzw. [forecast.solar2]`  
Hier die Werte eintragen, wenn die Prognose mit Solarprognose_WeatherData.py von www.solarprognose.de geholt werden soll.**  
Daten werden für api.forecast.solar und zukünftig auch für api.akkudoktor.net verwendet!!

`weatherfile = weatherData.json`  
Hier kann die Datei, in die die Prognosewerte gespeichert werden, verändert werden, z.B. um sie mit anderen Prognosen zu vergleichen. Das Programm arbeitet immer mit weatherData.json.  

`api_key = kein`  
Wenn api_key **nicht** 'kein' ist, wird er für die Prognoseabfrage verwendet

; wenn ein API key vorhanden ist, koennen die Forecasts mit aktuellen Ertragswerten des Tages (aus der DB) verbessert werden.  
; 'ja' nutzt diese Funktion der API, 'nein' nicht.  
; Siehe https://doc.forecast.solar/actual  
`forecastactual = nein `

; wenn "damping" eingesetzt werden soll, hier die entsprechenden Werte einstellen. '0,0' ist Standardwert (kein Damping)  
; 0,0 bedeutet kein Damping, 0.25,0.75 bedeutet etwas damping am Morgen, hohes Damping am nachmittag.  
; beide Werte müssen zwischen 0 und 1 sein  
; Siehe https://doc.forecast.solar/damping  
`forecastdamping = 0,0`

`api_pers_plus = nein`  
Wenn ein api_pers_plus vorhanden ist (api_pers_plus = ja) können zwei Ausrichtungen in einer Abfrage behandelt werden.

; lat und lon sind die Positionsdaten der Anlage bzw. des Strings. Nutze https://www.suncalc.org/ oder andere Tools zur Identifikation  
`lat = 44.444` Breitengrad  
`lon = 11.111` Längengrad  

; horizon gibt mögliche Verschattungen pro String an:  
; die 12 Zahlen werden in Grad angegeben und repräsentieren im Uhrzeigersinn in 30 Grad Schritten, beginnen bei Nord, den Horizont  
; siehe https://doc.forecast.solar/horizon  
; wenn zum Beipiel im Südwesten ein großer Baum Schatten wirft:  
; 0,0,0,0,0,0,0,20,45,20,0,0  
`horizon = 0,0,0,0,0,0,0,0,0,0,0,0'`  

`dec = 30` Winkel der Module (0=waagerecht, 90=senkrecht)  
`az = 0` Himmelsrichtung (-180=Nord, -90=Osten, 0=Süd, 90=West, 180=Nord)  
`kwp = 11.4` kWp der PV-Anlage  

; Wert in Minuten, bis bisherige Daten ihre Gültigkeit verlieren und neue von der API abgerufen werden sollen  
; aktuell gueltige Werte fuer die Anzahl an API Aufrufen pro 60 Minuten findet man unter https://doc.forecast.solar/account_models  
`dataAgeMaxInMinutes = 100` Mindestabstand in Minuten, innerhalb dem keine neuen Werte angefordert werden.  

**`[solarprognose]`  
Hier die Werte eintragen, wenn die Prognose mit Solarprognose_WeatherData.py von http://www.solarprognose.de geholt werden soll**  
Bei solarprognose.de ist ein Account erforderlich.  

`weatherfile = weatherData.json` wie forecast.solar.  
`accesstoken = xxxxxx` accesstoken des Accounts

`item = inverter` Daten aus Account.  
`id = 1111`  Daten aus Account.  
`type = hourly`  Daten aus Account.  

`Zeitversatz = 0`  
Der Zeitversatz verschiebt die Prognose um X Stunden nach vor (-) oder nach hinten, eventuelle Zeitverschiebung.  

`dataAgeMaxInMinutes = 1000` wie forecast.solar  
`WaitSec = 21` Sekunden des sleep = Daten aus Account. 

`algorithm = own-v1`  
Mögliche Werte mosmix|own-v1|clearsky, für mosmix muss dem Standort eine Mosmix Station zugeordnet sein.  
Karte mit Stationen: https://wettwarn.de/mosmix/mosmix.html  

`KW_Faktor = 1.00` 
Falls die Anlagengröße in kWp nicht mit der Größe in Solarprognose übereinstimmt (z.B. Erweiterung)

**`[solcast.com] bzw. [solcast.com2]`  
Hier die Werte eintragen, wenn die Prognose mit Solcast_WeatherData.py von https://api.solcast.com.au geholt werden soll.**  

`weatherfile = weatherData.json` wie forecast.solar.  
`api_key = xxxx`  Daten aus Account.  
`resource_id = xxxx-xxxx-xxxx-xxxx`  Daten aus Account.  
`dataAgeMaxInMinutes = 1000` wie forecast.solar.  

`Zeitzone = +1`  
Zeitversatz zu UTC, hier für Zeitzone Europe/Berlin UTC +1, Sommerzeit = +1 erfolgt nun automatisch.  
`KW_Faktor = 1.00`  
Falls die Anlagengröße in kWp nicht mit der Größe in solcast.com übereinstimmt (z.B. Erweiterung)  

`no_history = 0`  
Wenn no_history = 1 dann werden von solcast.com keine historischen Daten geholt, sondern aus der Datei weatherData.json, dadurch hat man bei einer Ausrichtung 10 und bei zwei Ausrichtungen 5 Abfragen.







