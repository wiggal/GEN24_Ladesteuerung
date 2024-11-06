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
charge_rate_kW = 3500         # Ladegeschwindigkeit in kW
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
battery_status = current_charge_Wh

# Listen für Lade- und Entladeentscheidungen
charging_times = []
stopping_times = []
pv_data_tmp = [("2000-01-01 00:00:00", 0, 0, 9999.999)]

# Iteration durch die Stunden
for row in pv_data:
    pv = int(row[1])   # Prognose für PV-Leistung in kW
    consumption = int(row[2])  # Verbrauch in Wh
    price = row[3]  # Preis in Euro/Wh

    # Berechnen der Nettostromproduktion
    net_power = pv - consumption

    # PV-Strom in Akku laden wenn unter minimum_charge_Wh und Prognose kleiner Verbrauch
    if battery_status + net_power < minimum_charge_Wh and net_power < 0:
        # bisherigen kleisten Wert bisher suchen
        print("\nJetzt laden:   ", row)
        spalte_index = 3  # Index der gewünschten Spalte
        kleinster_wert = min(zeile[spalte_index] for zeile in pv_data_tmp)
        # Wenn kleister Wert bisher kleiner aktueller price, Ladung vorverlegen
        if ( kleinster_wert < price ):
            gefundene_zeile = None  # Variable für die gefundene Zeile
            for zeile in pv_data_tmp:
                if zeile[spalte_index] == kleinster_wert:
                    gefundene_zeile = zeile
                    break  # Beende die Schleife, wenn der Wert gefunden wurde
            print("Besere Ladezeit:", gefundene_zeile, "\n")
        else:
            gefundene_zeile = row

        # charge_rate_kW zu Speicher geben
        battery_status += charge_rate_kW

    else:
        # ansonsten speicher weiter mit net_power ent- bzw. laden
        battery_status += net_power
        # und pv_data_tmp für Suche kleinster Wert füllen
        pv_data_tmp.append(row)

        
    if battery_status > battery_capacity_Wh: battery_status = battery_capacity_Wh

    print("Batteriekapazität: ", battery_status)



# ALTER CODE
"""
charging_times.append((row[0], charge_amount, price))

if net_power > 0 and battery_status < battery_capacity_Wh:  # Überschuss an Energie
charge_amount = min(net_power, charge_rate_kW, battery_capacity_Wh - battery_status)

# Entladung des Akkus, wenn mehr verbraucht wird als produziert
if net_power < 0 and battery_status > minimum_charge_Wh:  # Verbrauch übersteigt die PV-Leistung
if net_power < 0:  # Verbrauch übersteigt die PV-Leistung
    discharge_amount = min(net_power, discharge_rate_kW, battery_status - minimum_charge_Wh)
    battery_status += discharge_amount
    if battery_status <= minimum_charge_Wh:
        battery_status = minimum_charge_Wh  # Der Speicher darf nicht unter minimum_charge_Wh sinken
        stopping_times.append((row[0], discharge_amount, price))

# Ausgabe der Lade- und Entladeentscheidungen
print("Günstige Ladezeiten:")
for time, amount, price in charging_times:
    print(f"  Ladezeit: {time}, Menge: {amount:.2f} Wh, Preis: {price:.2f} Euro/kWh")

print("\nStoppzeiten für die Entladung:")
for time, amount, price in stopping_times:
    print(f"  Stoppzeit: {time}, Menge: {amount:.2f} Wh, Preis: {price:.2f} Euro/Wh")

print(f"\nEndstand des Akkus: {battery_status:.2f} Wh")
"""
