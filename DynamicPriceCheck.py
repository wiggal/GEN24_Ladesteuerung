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
import FUNCTIONS.httprequest


if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'dynprice'])
    sqlall = FUNCTIONS.SQLall.sqlall()
    dynamic = FUNCTIONS.DynamicPrice.dynamic()
    request = FUNCTIONS.httprequest.request()
    now = datetime.now()
    format = "%Y-%m-%d %H:%M:%S"

    PV_Database = basics.getVarConf('Logging','Logging_file', 'str')
    Lastgrenze = basics.getVarConf('dynprice','Lastgrenze', 'eval')
    dyn_print_level = basics.getVarConf('dynprice','dyn_print_level', 'eval')
    LastprofilNeuTage = basics.getVarConf('dynprice','LastprofilNeuTage', 'eval')
    Daysback = basics.getVarConf('dynprice','Daysback', 'eval')
    LastprofilNeuTage = basics.getVarConf('dynprice','LastprofilNeuTage', 'eval')
    Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
    Gewinnerwartung_kW = basics.getVarConf('dynprice','Gewinnerwartung_kW', 'eval')
    weatherfile = basics.getVarConf('env','filePathWeatherData','str')
    weatherdata = basics.loadWeatherData(weatherfile)
    if(dyn_print_level >= 1): print("*** BEGINN DynamicPriceCheck: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"***\n")

    # Lastprofile holen
    Lastprofil = dynamic.getLastprofil()
    TimestampNow = int(datetime.now().timestamp())

    # Lastprofil neu erzeugen, wenn es älter als LastprofilNeuTage
    if len(Lastprofil) > 0 and len(Lastprofil[0]) > 3:
        if ((TimestampNow) - int(Lastprofil[0][3]) > LastprofilNeuTage * 86400):
            if(dyn_print_level >= 1): print("Erzeuge Lastprofil, da älter als ", LastprofilNeuTage, " Tage!")
            dynamic.makeLastprofil(PV_Database, Lastgrenze, Daysback*-1)
            # Lastprofil nochmal neu holen
            Lastprofil = dynamic.getLastprofil()
    else:
        if(dyn_print_level >= 1): print("Erzeuge Lastprofil, erstmalig!!")
        dynamic.makeLastprofil(PV_Database, Lastgrenze, Daysback*-1)
        if(dyn_print_level >= 1): print("Programmende!")
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
pricelist_date = dynamic.getPrice_energycharts(LAND)


if(dyn_print_level >= 2):
    headers = ["Zeitpunkt", "Strompreis brutto(€/kWh)", "Börsenstrompreis (€/kWh)"]
    dynamic.listAStable(headers, pricelist_date)
    print()

# Zusammenführen der Listen2
pv_data = []
for key in data:
    for key2 in pricelist_date:
        if key[0] == key2[0]:
            pv_data.append([key[0], key[1], key[2], key2[1]])

# Werte als Tabelle ausgeben
if(dyn_print_level >= 1):
    headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)"]
    dynamic.listAStable(headers, pv_data)

# Akku-Kapazität und aktuelle Parameter
api = FUNCTIONS.GEN24_API.gen24api
API = api.get_API()
# Wenn Batterie offline, battery_capacity_Wh = 5%
Battery_Status = API['BAT_MODE']
if (Battery_Status == 2):
    print()
    print("******** Batterie ist offline, aktueller Ladestand wird auf 5% gesetzt!!! **********\n")
    battery_capacity_Wh = basics.getVarConf('gen24','battery_capacity_Wh', 'eval') # Kapazität in Wh aus dynprice.ini
    current_charge_Wh = battery_capacity_Wh * 0.05 # aktueller Ladestand in Wh, 500Wh geschätzt
else:
    battery_capacity_Wh = (API['BattganzeKapazWatt']) # Kapazität in Wh
    current_charge_Wh = battery_capacity_Wh - API['BattKapaWatt_akt'] # aktueller Ladestand in Wh

#current_charge_Wh = 9000   #entWIGGlung
# Mindest-Ladestand in Prozent vom GEN24 lesen
host_ip = basics.getVarConf('gen24','hostNameOrIp', 'str')
user = basics.getVarConf('gen24','user', 'str')
password = basics.getVarConf('gen24','password', 'str')
# Hier Hochkommas am Anfang und am Ende enternen
password = password[1:-1]
BAT_M0_SOC_MIN = request.get_batteries(host_ip, user, password)[3]
HYB_BACKUP_RESERVED = request.get_batteries(host_ip, user, password)[2]
minimum_batterylevel_Prozent = BAT_M0_SOC_MIN
if HYB_BACKUP_RESERVED > BAT_M0_SOC_MIN: minimum_batterylevel_Prozent = HYB_BACKUP_RESERVED

minimum_batterylevel_kWh =  int(battery_capacity_Wh / 100 * minimum_batterylevel_Prozent)     # Mindest-Ladestand in Wh
Prozent5_batterylevel_kWh =  battery_capacity_Wh / 100 * 5     # 5_Prozent-Ladestand in Wh
charge_rate_kW =  basics.getVarConf('dynprice','charge_rate_kW', 'eval')        # Ladegeschwindigkeit in kW

# Akkuwerte als Tabelle ausgeben
if(dyn_print_level >= 1):
    headers = ["Batteriekapazität (Wh)", "Aktueller Ladestand (Wh)", "minimaler Ladestand (Wh)"]
    table_liste = [(str(battery_capacity_Wh), str(current_charge_Wh), str(minimum_batterylevel_kWh))]
    print()
    dynamic.listAStable(headers, table_liste)
    print()

if(dyn_print_level >= 2): print("\n*****************  DEBUGGING *****************")

# Spalte Akkustand und Ladewatt 0.1 anhängen
pv_data_charge = [zeile + [0, 0.1] for zeile in pv_data]

# Akkustände neu berechnen
dynamic.akkustand_neu(pv_data_charge, minimum_batterylevel_kWh, current_charge_Wh, charge_rate_kW, battery_capacity_Wh)
# Mit Funktion get_charge_stop Ladepunkte usw. berechnen
pv_data_charge = dynamic.get_charge_stop(pv_data_charge, minimum_batterylevel_kWh, current_charge_Wh, charge_rate_kW, battery_capacity_Wh)

if(dyn_print_level >= 1):
    print("\n>>>>>>>> Batteriestand und Ladezeitpunkte")
    headers = ["Ladezeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)", "Ladewert"]
    dynamic.listAStable(headers, pv_data_charge)

# Aktuelles Datum und Uhrzeit
jetzt = datetime.now()
# Startzeit jetzt
heute_start = datetime(jetzt.year, jetzt.month, jetzt.day, jetzt.hour)

# SteuerCode erzeugen
# Für jede Stunde Steuercode  EntLadesteuerung ermitteln
# Alte Einträge in ENTLadeStrg lesen
entladesteurungsdata = sqlall.getSQLsteuerdaten('ENTLadeStrg')

SteuerCode = []
DBCode = []
for stunde in range(1, 25):  # die nächsten 24 Stunden beginnend mit nächster Stunde
    zeitpunkt = heute_start + timedelta(hours=stunde)
    Stunde = zeitpunkt.strftime("%H:%M")  # Stunde im Speicherformat
    Res_Feld1 = 0
    Res_Feld2 = 0
    Options = ''
    SuchStunde = zeitpunkt.strftime("%Y-%m-%d %H:%M:%S")
    # wenn Stundeneintrag in CONFIG/Prog_Steuerung.sqlite noch fehlt
    try:
        if entladesteurungsdata[Stunde]['Res_Feld1'] + entladesteurungsdata[Stunde]['Res_Feld2'] > 0:
            Res_Feld1 = entladesteurungsdata[Stunde]['Res_Feld1']
            Res_Feld2 = entladesteurungsdata[Stunde]['Res_Feld2']
        if entladesteurungsdata[Stunde]['Options'] != '':
            Options = entladesteurungsdata[Stunde]['Options']
    except:
        Res_Feld1 = 0
        Res_Feld2 = 0
        Options = ''

    for Stundenliste in pv_data_charge:
        if SuchStunde in Stundenliste:
            if Res_Feld1 + Res_Feld2 > 0:
                Options = str(Res_Feld1)+","+str(Res_Feld2)
            Res_Feld1 = 0
            Res_Feld2 = Stundenliste[5]
            break
    # Wenn keine DynamicPriceCheck-Eintrag evtl gemerkte Einträge wiederherstellen
    if Options != '' and Res_Feld2 >= 0:
        Res_Feld = Options.split(',')
        Res_Feld1 = Res_Feld[0]
        Res_Feld2 = Res_Feld[1]
        Options = ''

    SteuerCode.append((Stunde, 'ENTLadeStrg', Stunde, Res_Feld1, Res_Feld2, Options))
    # wenn Stundeneintrag in CONFIG/Prog_Steuerung.sqlite noch fehlt
    try:
        DBCode.append((Stunde, 'ENTLadeStrg', Stunde, entladesteurungsdata[Stunde]['Res_Feld1'], entladesteurungsdata[Stunde]['Res_Feld2'], entladesteurungsdata[Stunde]['Options']))
    except:
        DBCode.append((Stunde, 'ENTLadeStrg', Stunde, 0, 0, ''))

    # DEBUG CSV-Ausgabe
    if(dyn_print_level >= 1 and 'Stundenliste' in locals()):
        import csv
        if stunde == 1 :
            try:
                with open("DEBUG.csv", "r") as file:
                    file = open('DEBUG.csv',"a")
                    csvzeile = [str(SuchStunde), "ENTLadeStrg", str(Res_Feld1), str(Res_Feld2), str(Stundenliste[3]), str(Stundenliste[4])]
                    writer = csv.writer(file, delimiter=',')
                    writer.writerow(csvzeile)
                    file.close()
            except FileNotFoundError:
                # Behandle den Fall, dass die Datei nicht existiert
                file = open('DEBUG.csv',"a")
                csvheader = ["Stunde", "Schluessel", "Entladung", "Entladegrenze", "Preis €/kWh", "Akkustand/W"]
                csvzeile = [str(SuchStunde), "ENTLadeStrg", str(Res_Feld1), str(Res_Feld2), str(Stundenliste[3]), str(Stundenliste[4])]
                writer = csv.writer(file, delimiter=',')
                writer.writerow(csvheader)
                writer.writerow(csvzeile)
                file.close()
    # DEBUG CSV-Ausgabe

if(dyn_print_level >= 1):
    # Zu schreibenen SteuerCode ausgeben
    print("\nFolgende Steuercodes wurden ermittelt:")
    headers = ["Index", "Schlüssel", "Stunde", "Verbrauchsgrenze", "Feste Entladegrenze", "Options"]
    dynamic.listAStable(headers, SteuerCode)

Parameter = ''
if len(argv) > 1 :
    Parameter = argv[1]

if( Parameter == 'schreiben'):
    SteuerCode.sort()
    DBCode.sort()
    if SteuerCode == DBCode:
        if(dyn_print_level >= 1): print("\nSteuercodes wurden NICHT geschrieben, da keine Veränderung!")
    else:
        dynamic.saveProg_Steuerung(SteuerCode)
        if(dyn_print_level >= 1): print("\nSteuercodes wurden geschrieben! (siehe Tabelle ENTLadeStrg)")
else:
    if(dyn_print_level >= 1): print("\nSteuercodes wurden NICHT geschrieben, Parameter schreiben fehlt")

if(dyn_print_level >= 1): print("***** ENDE: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"*****\n")


