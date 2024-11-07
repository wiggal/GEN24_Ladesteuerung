# Über dynamische Strompreise günstige Akkunachladung bzw. -entladestop checken
# bei negativen Strompreisen bzw. ab Grenzwert Einspeisung stoppen (2. Stufe)
# Jeden Monat neues Lastprofil ermitteln und in CONFIG/Prog_Steuerung.sqlite speichern
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
    try:
        if ((TimestampNow) - int(Lastprofil[0][3]) > 1209500):
            print("Erzeuge Lastprofil, da älter als zwei Wochen!")
            dynamic.makeLastprofil(PV_Database, Lastgrenze)
    except OSError:
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
#current_charge_Wh = 3000 # entWIGGlung
minimum_charge_Prozent = 20      # Mindest-Ladestand in Prozent 
minimum_charge_Wh =  battery_capacity_Wh / 100 * minimum_charge_Prozent     # Mindest-Ladestand in Wh
charge_rate_kW = 3000         # Ladegeschwindigkeit in kW
discharge_rate_kW = 4500      # Entladegeschwindigkeit in kW

# entWIGGlung
# Werte als Tabelle ausgeben
headers = ["Batteriekapazität (Wh)", "Aktueller Ladestand (Wh)", "minimaler Ladestand (Wh)"]
print()
table_liste = [(str(battery_capacity_Wh), str(current_charge_Wh), str(minimum_charge_Wh))]
dynamic.listAStable(headers, table_liste)
print()
# entWIGGlung


# Initialer Zustand des Akkus
battery_status_init = current_charge_Wh

# Listen für Lade- und Entladeentscheidungen
charging_times = []
stopping_times = []
charging_cost = 0
stopping_cost = 0

for ladeArray, ladeWatt in zip(['charging', 'stopping'], [charge_rate_kW, 0]):
    pv_data_tmp = [("2000-01-01 00:00:00", 0, 0, 9999.999)]
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

        # PV-Strom in Akku laden wenn unter minimum_charge_Wh und Prognose kleiner Verbrauch
        best_price = price
        if battery_status + net_power < minimum_charge_Wh and net_power < 0:
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
                charging_cost += cost_tmp
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

# entWIGGlung
# Werte als Tabelle ausgeben
charging_times.sort(key=lambda x: x[0])
headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)"]
print()
dynamic.listAStable(headers, charging_times)
print("\nBatteriekapazität: ", battery_status_charging)
print("Kosten Batterieladung: ", round(charging_cost, 2), "€")
print("Preis Akkustandplus  : ", round(Akkuplus, 2), "€")
print("Vergleichskosten Akku: ", round(charging_cost + Akkuplus, 2), "€")
print()

headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)"]
print()
stopping_times.sort(key=lambda x: x[0])
dynamic.listAStable(headers, stopping_times)
print("\nBatteriekapazität: ", battery_status_stopping)
print("Kosten Stopp Ladung: ", round(stopping_cost, 2), "€")
# entWIGGlung
