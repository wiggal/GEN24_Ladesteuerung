################################################
# ACHTUNG: Voraussetzung mindestens zwei Wochen geloggte Daten!!!
################################################
# Über dynamische Strompreise günstige Akkunachladung bzw. -entladestop checken
# bei negativen Strompreisen bzw. ab Grenzwert Einspeisung stoppen (2. Stufe)
# Jeden Monat neues Lastprofil ermitteln und in CONFIG/Prog_Steuerung.sqlite speichern
from sys import argv
from datetime import datetime, timedelta
import FUNCTIONS.functions
import FUNCTIONS.DynamicPrice
import FUNCTIONS.SQLall
import FUNCTIONS.PrognoseLadewert
import FUNCTIONS.GEN24_API


if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'dynprice'])
    sqlall = FUNCTIONS.SQLall.sqlall()
    dynamic = FUNCTIONS.DynamicPrice.dynamic()
    now = datetime.now()
    format = "%Y-%m-%d %H:%M:%S"

    PV_Database = basics.getVarConf('Logging','Logging_file', 'str')
    Lastgrenze = basics.getVarConf('dynprice','Lastgrenze', 'eval')
    weatherfile = basics.getVarConf('env','filePathWeatherData','str')
    weatherdata = basics.loadWeatherData(weatherfile)

    # Lastprofile holen
    Lastprofil = dynamic.getLastprofil()
    TimestampNow = int(datetime.now().timestamp())

    # Lastprofil neu erzeugen, wenn es älter als zwei Wochen (1209600s) ist.
    if len(Lastprofil) > 0 and len(Lastprofil[0]) > 3:
        if ((TimestampNow) - int(Lastprofil[0][3]) > 1209500):
            print("Erzeuge Lastprofil, da älter als zwei Wochen!")
            dynamic.makeLastprofil(PV_Database, Lastgrenze)
    else:
        print("Erzeuge Lastprofil, erstmalig!!")
        dynamic.makeLastprofil(PV_Database, Lastgrenze)
        print("Programmende!")
        exit()


# ***** Ab hier Berechnung des AKKU-Status

# Erzeugen einer Liste mit timestamp, pv_prognose, Verbrauch, Preis

#Verbrauch aus Lastprofil
Verbrauch = []
# Aktuelles Datum Wochentag
today = datetime.now()
tomorrow = today + timedelta(days=1)
today_weekday = (today.weekday() + 1)  % 7  # Montag=0 -> Sonntag=0
for row in Lastprofil:
    if (row[0] == today_weekday):
        time=today.strftime("%Y-%m-%d") + " " + row[1]+":00"
        Verbrauch.append((time, row[2]))
    else:
        time=tomorrow.strftime("%Y-%m-%d") + " " + row[1]+":00"
        Verbrauch.append((time, row[2]))

# Prognosedaten lesen
Prognose_24H = dynamic.getPrognosen_24H(weatherdata)

# Zusammenführen der Listen
data = []
for key in Prognose_24H:
    for key2 in Verbrauch:
        if key[0] == key2[0]:
            data.append((key[0], key[1], key2[1]))

# Aktuelle Strompreise holen

LAND = basics.getVarConf('dynprice','LAND', 'str')
# List Date (2024-10-27 23:00:00), Euro/kWh
priecelist_date = dynamic.getPrice_energycharts(LAND, TimestampNow)

# Zusammenführen der Listen2
pv_data = []
for key in data:
    for key2 in priecelist_date:
        if key[0] == key2[0]:
            pv_data.append((key[0], key[1], key[2], key2[1]))

# entWIGGlung
# Werte als Tabelle ausgeben
headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)"]
dynamic.listAStable(headers, pv_data)
# ENDWIGGlung


### von GPT


# Akku-Kapazität und aktuelle Parameter
api = FUNCTIONS.GEN24_API.gen24api
API = api.get_API()
battery_capacity_Wh = (API['BattganzeKapazWatt']) # Kapazität in Wh
current_charge_Wh = battery_capacity_Wh - API['BattKapaWatt_akt'] # aktueller Ladestand in Wh
minimum_batterylevel_Prozent = basics.getVarConf('dynprice','minimum_batterylevel_Prozent', 'eval')      # Mindest-Ladestand in Prozent 
minimum_batterylevel_kWh =  battery_capacity_Wh / 100 * minimum_batterylevel_Prozent     # Mindest-Ladestand in Wh
charge_rate_kW =  basics.getVarConf('dynprice','charge_rate_kW', 'eval')        # Ladegeschwindigkeit in kW
minimum_price_difference = basics.getVarConf('dynprice','minimum_price_difference', 'eval')
price_difference = max(zeile[3] for zeile in pv_data) - min(zeile[3] for zeile in pv_data)


# entWIGGlung
# Werte als Tabelle ausgeben
headers = ["Batteriekapazität (Wh)", "Aktueller Ladestand (Wh)", "minimaler Ladestand (Wh)"]
print()
table_liste = [(str(battery_capacity_Wh), str(current_charge_Wh), str(minimum_batterylevel_kWh))]
dynamic.listAStable(headers, table_liste)
print()
# entWIGGlung


# Initialer Zustand des Akkus
battery_status_init = current_charge_Wh

# Listen für Lade- und Entladeentscheidungen
charging_times = []
stopping_times = []
charging_cost_tmp = 0
stopping_cost = 0

for ladeArray, ladeWatt in zip(['charging', 'stopping'], [charge_rate_kW, 0]):
    pv_data_tmp = [("2000-01-01 00:00:00", 0, 0, 9999.999, 0)]
    battery_status = battery_status_init
    # Iteration durch die Stunden
    #print("#############  ", ladeArray, "############\n")
    for row in pv_data:
        pv = int(row[1])   # Prognose für PV-Leistung in kW
        consumption = int(row[2])  # Verbrauch in Wh
        price = row[3]  # Preis in Euro/Wh
        row = row + (battery_status, )
    
        # Berechnen der Nettostromproduktion
        net_power = pv - consumption

        # PV-Strom in Akku laden wenn unter minimum_batterylevel_kWh und Prognose kleiner Verbrauch
        best_price = price
        if battery_status + net_power < minimum_batterylevel_kWh and net_power < 0:
            # bisherigen kleisten Wert bisher suchen
            #print("\nJetzt ",ladeArray,":   ", row)
            kleinster_price = min(zeile[3] for zeile in pv_data_tmp)
            # Wenn kleister Wert bisher kleiner aktueller price, Ladung vorverlegen
            if ( kleinster_price < price ):
                best_price = kleinster_price
                gefundene_zeile = None  # Variable für die gefundene Zeile
                for zeile in pv_data_tmp:
                    if zeile[3] == kleinster_price:
                        consumption = zeile[2]
                        gefundene_zeile = zeile
                        break  # Beende die Schleife, wenn der Wert gefunden wurde
                #print("Bessere ",ladeArray,":", gefundene_zeile)
                # Wenn frühere Zeile gefunden => entfernen, aktuelle Zeile hinzufügen
                pv_data_tmp.remove(gefundene_zeile)
                pv_data_tmp.append(row)
            else:
                gefundene_zeile = row

            # charge_rate_kW zu Speicher geben
            battery_status += ladeWatt
            cost_tmp = round(((best_price * (ladeWatt + consumption)) / 1000),3)
            if ( ladeArray == 'charging' ):
                charging_times.append(gefundene_zeile)
                charging_cost_tmp += cost_tmp
            if ( ladeArray == 'stopping' ):
                stopping_times.append(gefundene_zeile)
                stopping_cost += cost_tmp

        else:
            # ansonsten speicher weiter mit net_power ent- bzw. laden
            battery_status += net_power
            # und pv_data_tmp für Suche kleinster Wert füllen
            pv_data_tmp.append(row)

        
        if battery_status > battery_capacity_Wh: battery_status = battery_capacity_Wh
        if ( ladeArray == 'charging' ):
            battery_status_charging = battery_status
        if ( ladeArray == 'stopping' ):
            battery_status_stopping = battery_status

# Durchschnittsstrompreis um den unterschiedlichen Ladezustand auszugleichen
kleinster_price = min(zeile[3] for zeile in charging_times)
Akkuplus = ((battery_status_stopping-battery_status_charging)*kleinster_price/1000)
charging_cost = round(charging_cost_tmp + Akkuplus, 2)

# entWIGGlung
# Werte als Tabelle ausgeben
charging_times.sort(key=lambda x: x[0])
headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)"]
print()
dynamic.listAStable(headers, charging_times)
print("\nBatteriekapazität: ", battery_status_charging)
print("Kosten Batterieladung: ", round(charging_cost_tmp, 2), "€")
print("Preis Akkustandplus  : ", round(Akkuplus, 2), "€")
print("Vergleichskosten Akku: ", round(charging_cost, 2), "€")
print()

headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)"]
print()
stopping_times.sort(key=lambda x: x[0])
dynamic.listAStable(headers, stopping_times)
print("\nBatteriekapazität: ", battery_status_stopping)
print("Kosten Stopp Ladung: ", round(stopping_cost, 2), "€")
# entWIGGlung

# Aktuelles Datum und Uhrzeit
jetzt = datetime.now()

### Daten zum schreiben in CONFIG/Prog_Steuerung.sqlite vorbereiten

# Ladewert ermitteln charging OR stopping
if (charging_cost > stopping_cost):
    Ladewert = 1 # Mit 1Watt entladen = Lade und Entladenstopp
    LadeProfil = stopping_times
    Ausgabe = "Ladung stoppen"
else:
    Ladewert = charge_rate_kW * -1 # Minuswert um aus dem Netz zu laden
    LadeProfil = charging_times
    Ausgabe = "Speicher Laden"

# Startzeit jetzt
heute_start = datetime(jetzt.year, jetzt.month, jetzt.day, jetzt.hour)

# Für jede Stunde Steuercode  EntLadesteuerung ermitteln

SteuerCode = []
for stunde in range(24):  # die nächsten 24 Stunden
    zeitpunkt = heute_start + timedelta(hours=stunde)
    Stunde = zeitpunkt.strftime("%H:%M")  # Stunde im Speicherformat
    Ladewert_Std = 0
    SuchStunde = zeitpunkt.strftime("%Y-%m-%d %H:%M:%S")

    for Stundenliste in LadeProfil:
        if SuchStunde in Stundenliste:
            Ladewert_Std = Ladewert
            break
    SteuerCode.append((Stunde, 'ENTLadeStrg', Stunde, '0', Ladewert_Std, ''))

# Zu schreibenen SteuerCode ausgeben
print("\nFolgende Steuercodes würden geschrieben:")
headers = ["Index", "Schlüssel", "Stunde", "Verbrauchsgrenze", "Feste Entladegrenze", "Anmerkung"]
dynamic.listAStable(headers, SteuerCode)
print("\nMindestpreisdifferenz >>> Preisdifferenz = ", minimum_price_difference, ">>>", round(price_difference, 3))

if(minimum_price_difference > price_difference): 
    print("\nSteuercodes werden nicht geschrieben, da Preisdiffernz zu klein:")
    exit()

Parameter = ''
if len(argv) > 1 :
    Parameter = argv[1]

if( Parameter == 'schreiben'):
    dynamic.saveProg_Steuerung(SteuerCode)
    print("\nSteuercodes für", Ausgabe, "wurden geschrieben! (siehe Tabelle ENTLadeStrg)")
else:
    print("\nSteuercodes für", Ausgabe, "wurden NICHT geschrieben, Parameter schreiben fehlt")



