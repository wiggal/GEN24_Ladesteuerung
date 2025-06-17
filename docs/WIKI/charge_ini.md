## Einstellungen zur Lade-, Entladesteuerung usw. in charge_priv.ini:

**`[Ladeberechnung]`  
Hier folgen alle Einstellungen, um die PV-Energie gesteuert mit der PV-Prognose in den Akku zu laden.**  

`FesteLadeleistung = -1`  
Wenn die Variable "FesteLadeleistung" größer/gleich "0" Watt ist, wird der Wert geschrieben, und der Akku wird immer mit der eingestellten Leistung geladen.  
FesteLadeleistung = -1, die Ladesteuerung erfolgt mit den aus der Prognose und den Einstellungen hier, errechneten Werten, dynamisch.

`BattVollUm = -4`  
Bis wann soll die Batterie voll sein:  
Ganze Zahl > 0 ist eine feste Stunde.  
Ganze Zahl <= 0 ist die Differenz zum Sonnenuntergang (= Prognosewert < 2% PV_Leistung_Watt).  

`BatSparFaktor = 0.5`  
Faktor, um mehr Batteriekapazität für später aufzusparen.  
Wenn BatSparFaktor > 0: (Batteriekapazität) / (Zeit bis BatVollUm) * BatSparFaktor.  
Wenn BatSparFaktor == 0: Ladung an den Prognosespitzen (Netzdienlich).  

`MaxLadung = 3000`  
Größter Batterieladewert, der im WR gesetzt werden soll.  

`Einspeisegrenze = 8000`  
Die Einspeisegrenze die vom Netzbetreiber vorgegebn wurde.  
Da der GEN24 die Begrenzung selbständig macht, wird der Wert nur für die Berechnung verwendet.  

`WR_Kapazitaet = 10000`  
AC Kapazität des Wechselrichters.  
Da der GEN24 die Begrenzung selbständig macht, wird der Wert nur für die Berechnung verwendet.  

`PV_Leistung_Watt = 11400`  
PV-Leistung reellen Spitzenwert, wird für die Berechnung benötigt.

`Grundlast = 0`  
Grundlast wird verwendet um den Wert "aktuellerUeberschuss" zu berechnen.  
Grundlast je nach Wochentag wird gesetzt, wenn Grundlast == 0  
`Grundlast_WoT = 600, 600, 600, 600, 800, 900, 900`  
Wochentage  = Mo,  Die, Mi,  Do,  Fr,  Sa,   So

`WRSchreibGrenze_nachOben = 700`  
`WRSchreibGrenze_nachUnten = 1500`  
Schaltverzögerung um Schreibzugriffe auf WR zu minimieren

`MindBattLad = 25`  
Liegt der Batteriestatus unter MindBattLad in % wird voll mit MaxLadung geladen. 

`LadungAus = 0`  
Wenn die Ladung vom Programm ausgeschaltet wird, wird der Ladewert auf diesen Wert gesetzt, wenn man immer eine gewisse Mindestladung haben will.

`GrenzwertGroestePrognose = 2000`  
Wenn der größte Prognosewert je Stunde am Tag kleiner als GrenzwertGroestePrognose ist, wird mit vollem Wert (= MaxLadung) geladen

`Akkuschonung = 1`  
Akkuschonung (0=aus, 1=ein)  
Wenn Akkuschonung ein, wird BattVollUm um eine Stunde vor verlegt, da am Schluss nicht mehr so stark geladen wird.  
ACHTUNG: Bei einer Überschreitung der Einspeisegrenze bzw. der AC-Leistung des WR wird der Wert der Akkuschonung evtl. überschritten!  

`Akkuschonung_Werte = {"80": "0.2", "90": "0.1", "95": "0.05"}`  
Akkuschonung_Werte = {"Ladestand%" : "LadewertC", ...}





**will be continued ...............**