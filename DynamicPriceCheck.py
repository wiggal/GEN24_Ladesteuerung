################################################
# ACHTUNG: Voraussetzung mindestens zwei Wochen geloggte Daten!!!
################################################
# Über dynamische Strompreise günstige Akkunachladung bzw. -entladestop checken
# bei negativen Strompreisen bzw. ab Grenzwert Einspeisung stoppen (2. Stufe)
# Jeden Monat neues Lastprofil ermitteln und in CONFIG/Prog_Steuerung.sqlite speichern
from sys import argv
from datetime import datetime, timedelta
import requests
import configparser
import FUNCTIONS.functions
import FUNCTIONS.DynamicPrice
import FUNCTIONS.SQLall
import FUNCTIONS.Steuerdaten


if __name__ == '__main__':
    #Versionsnummer lesen
    config_v = configparser.ConfigParser()
    config_v.read('version.ini')
    prg_version = (config_v['Programm']['version'])

    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'charge', 'dynprice'])
    sqlall = FUNCTIONS.SQLall.sqlall()
    dynamic = FUNCTIONS.DynamicPrice.dynamic()
    now = datetime.now()
    format = "%Y-%m-%d %H:%M:%S"

    # Klassen dynamisch laden
    try:
        InverterApi = basics.get_inverter_class(class_type="Api")
        InverterInterface = basics.get_inverter_class(class_type="Interface")
    except ImportError as e:
        print(e)  # nur die kurze, selbst definierte Fehlermeldung
        exit(1) 

    Lastgrenze = basics.getVarConf('dynprice','Lastgrenze', 'eval')
    dyn_print_level = basics.getVarConf('dynprice','dyn_print_level', 'eval')
    LastprofilNeuTage = basics.getVarConf('dynprice','LastprofilNeuTage', 'eval')
    Daysback = basics.getVarConf('dynprice','Daysback', 'eval')
    LastprofilNeuTage = basics.getVarConf('dynprice','LastprofilNeuTage', 'eval')
    Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
    Lade_Verbrauchs_Faktor = basics.getVarConf('dynprice','Lade_Verbrauchs_Faktor', 'eval')
    Gewinnerwartung_kW = basics.getVarConf('dynprice','Gewinnerwartung_kW', 'eval')
    LAND = basics.getVarConf('dynprice','LAND', 'str')
    Preisquelle = basics.getVarConf('dynprice','Preisquelle', 'str')
    weatherdata = basics.loadWeatherData()
    if(dyn_print_level >= 1):
        print("*** BEGINN DynamicPriceCheck: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"), prg_version, "***")
        print("*** Strompreisprovider: ", Preisquelle, "***")

    # Lastprofile holen
    Lastprofil = dynamic.getLastprofil()
    TimestampNow = int(datetime.now().timestamp())

    # Lastprofil neu erzeugen, wenn es älter als LastprofilNeuTage
    PV_Database = 'PV_Daten.sqlite'
    if len(Lastprofil) > 0 and len(Lastprofil[0]) > 3:
        if ((TimestampNow) - int(float(Lastprofil[0][3])) > LastprofilNeuTage * 86400):
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
        Verbrauch.append((time, int(row[2] * Lade_Verbrauchs_Faktor)))
    else:
        time=tomorrow.strftime("%Y-%m-%d") + " " + row[1]+":00"
        Verbrauch.append((time, int(row[2] * Lade_Verbrauchs_Faktor)))

# Prognosedaten lesen
Prognose_24H = dynamic.getPrognosen_24H(weatherdata)

# Zusammenführen der Listen
data = []
for key in Prognose_24H:
    for key2 in Verbrauch:
        if key[0] == key2[0]:
            data.append((key[0], key[1], key2[1]))

# Aktuelle Strompreise holen
# Variabler Funktionsaufruf
funktion_string = 'getPrice_'+Preisquelle
funktion = getattr(dynamic, funktion_string)
pricelist_date = funktion(LAND)

if(dyn_print_level >= 2):
    headers = ["Zeitpunkt", "Strompreis brutto(€/kWh)", "Börsenstrompreis (€/kWh)"]
    dynamic.listAStable(headers, pricelist_date)
    print()

# Zusammenführen der Listen2
pv_data = []
for key in pricelist_date:
    key_neu = key[0][:14] + "00" + key[0][16:]
    for key2 in data:
        if key_neu == key2[0]:
            pv_data.append([key[0], key2[1], key2[2], key[1]])

host_ip = basics.getVarConf('inverter','hostNameOrIp', 'str')
# Werte als Tabelle ausgeben
if(dyn_print_level >= 3):
    headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch*"+str(Lade_Verbrauchs_Faktor)+"(W)", "Strompreis (€/kWh)"]
    dynamic.listAStable(headers, pv_data)

try:
    # Ping Ersatz, prüft ob WR online
    response = requests.get('http://'+host_ip)
    response.raise_for_status()  # Auslösen einer Ausnahme, wenn der Statuscode nicht 2xx ist
except requests.exceptions.RequestException as e:
    print(datetime.now())
    print(f"Fehler bei der Verbindung: {e}")
    print(">>>>>>>>>> WR offline")
    exit()

# Akku-Kapazität und aktuelle Parameter
inverter_api = InverterApi()
API = inverter_api.get_API()
# Wenn Batterie offline, battery_capacity_Wh = 5% => in GEN24_API.gen24api()
battery_capacity_Wh = (API['BattganzeKapazWatt']) # Kapazität in Wh
current_charge_Wh = battery_capacity_Wh - API['BattKapaWatt_akt'] # aktueller Ladestand in Wh

# Mindest-Ladestand in Prozent vom GEN24 und aus der dynprice.ini lesen
user = basics.getVarConf('inverter','user', 'str')
password = basics.getVarConf('inverter','password', 'str')
Akku_MindestSOC = basics.getVarConf('dynprice','Akku_MindestSOC', 'eval')
# Hier Hochkommas am Anfang und am Ende enternen
password = password[1:-1]
#  Klasse FroniusGEN24 initiieren
inverter_interface = InverterInterface(host_ip, user, password, API['Version'])
batteries_array = inverter_interface.get_http_data()
BAT_M0_SOC_MIN = batteries_array[1]['BAT_M0_SOC_MIN']
HYB_BACKUP_RESERVED = batteries_array[1]['HYB_BACKUP_RESERVED']
minimum_batterylevel_Prozent = BAT_M0_SOC_MIN
if HYB_BACKUP_RESERVED > BAT_M0_SOC_MIN: minimum_batterylevel_Prozent = HYB_BACKUP_RESERVED
# größeren Wert als minimum_batterylevel_Prozent definieren
minimum_batterylevel_Prozent = max(minimum_batterylevel_Prozent, Akku_MindestSOC)

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

if(dyn_print_level >= 3): print("\n*****************  DEBUGGING *****************")

# Spalte Akkustand und Ladewatt -0.01 anhängen
pv_data_charge = [zeile + [0, -0.01] for zeile in pv_data]
# Prüfen, ob vietelstündliche Strompreise
Stundenteile = 1
if(len(pv_data_charge) > 24): Stundenteile = 4
# Mit Funktion get_charge_stop Ladepunkte usw. berechnen
pv_data_charge = dynamic.get_charge_stop(pv_data_charge, minimum_batterylevel_kWh, current_charge_Wh, charge_rate_kW, battery_capacity_Wh, current_charge_Wh, Stundenteile)

if(dyn_print_level >= 3): print("\n***************** ENDE DEBUGGING *****************")

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
# Schleife für die nächsten 24 Stunden in gegebenem Intervall
for stunde in range(1, 25):  # die nächsten 24 Stunden beginnend mit nächster Stunde
    zeitpunkt = heute_start + timedelta(hours=stunde)
    Stunde = zeitpunkt.strftime("%H:%M")  # Stunde im Speicherformat
    Res_Feld1 = 0
    Res_Feld2 = 0 
    Res_Feld2_array = {}
    Options = ''
    # Wenn viertelstündliche Preise vorhanden, berücksichtigen
    for minuten in [0, 15, 30, 45]:
        zeitpunkt = zeitpunkt.replace(minute=minuten, second=0, microsecond=0)
        SuchStunde = zeitpunkt.strftime("%Y-%m-%d %H:%M:00")

        for Stundenliste in pv_data_charge:
            if SuchStunde in Stundenliste:
                Res_Feld1 = 0
                Res_Feld2_array[minuten] = Stundenliste[5]
                if Stundenliste[5] != 0:
                    Options = 'DynPrice'
                break
    Res_Feld2_werte = list(Res_Feld2_array.values())
    # Wenn alle viertestündlichen Werte gleich, nur einmal ausgeben
    if(len(set(Res_Feld2_werte)) == 1):
        Res_Feld2 = Res_Feld2_array[0]
    # Wenn viertestündliche Werte unterschiedlich, alle ausgeben
    if(len(set(Res_Feld2_werte)) > 1):
        Res_Feld2 = ";".join(str(wert) for wert in Res_Feld2_werte)

    # Wenn manueller Eintrag, Eintrag nicht überschreiben
    # Damit kein Fehler kommt, wenn Datensatz in SQLsteuerdatei nicht existiert
    try:
        if entladesteurungsdata[Stunde]['Options'] != 'DynPrice' and entladesteurungsdata[Stunde]['Res_Feld2'] < 0:
            Res_Feld2 = entladesteurungsdata[Stunde]['Res_Feld2']
            Options = entladesteurungsdata[Stunde]['Options']
            for zeile in pv_data_charge:
                if zeile[0] == SuchStunde:
                    zeile[5] = Res_Feld2  
                    break 
    except:
        pass

    SteuerCode.append((Stunde, 'ENTLadeStrg', Stunde, Res_Feld1, Res_Feld2, Options))
    # wenn Stundeneintrag in CONFIG/Prog_Steuerung.sqlite noch fehlt
    try:
        DBCode.append((Stunde, 'ENTLadeStrg', Stunde, entladesteurungsdata[Stunde]['Res_Feld1'], entladesteurungsdata[Stunde]['Res_Feld2'], entladesteurungsdata[Stunde]['Options']))
    except:
        DBCode.append((Stunde, 'ENTLadeStrg', Stunde, 0, 0, ''))

# Akkuzustand nochmal neu berechnen mit manuellen Einträgen aus ENTLadeStrg
max_batt_dyn_ladung = basics.getVarConf('dynprice','max_batt_dyn_ladung', 'eval')
max_batt_dyn_ladung_W = int(battery_capacity_Wh * max_batt_dyn_ladung / 100)
dynamic.akkustand_neu(pv_data_charge, minimum_batterylevel_kWh, current_charge_Wh, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W, 1, Stundenteile)

if(dyn_print_level >= 1):
    print(">>>>>>>> Batteriestand und Ladezeitpunkte")
    headers = ["Ladezeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Akku ("+str(current_charge_Wh)+"W)", "Ladewert"]
    dynamic.listAStable(headers, pv_data_charge)

if(dyn_print_level >= 1):
    # Zu schreibenen SteuerCode ausgeben
    print("\nFolgende Steuercodes wurden ermittelt:")
    headers = ["Index", "Schlüssel", "Stunde", "Verbrauchsgrenze", "Feste Entladegrenze", "Options"]
    dynamic.listAStable(headers, SteuerCode)

# WebUI-Parameter aus CONFIG/Prog_Steuerung.sqlite lesen
SettingsPara = FUNCTIONS.Steuerdaten.readcontroldata()
Parameter = SettingsPara.getParameter(argv, 'ProgrammStrg')
Options = Parameter[2]

if ('dynamicprice' in Options):
    SteuerCode.sort()
    DBCode.sort()
    if SteuerCode == DBCode:
        if(dyn_print_level >= 1): print("\nSteuercodes wurden NICHT geschrieben, da keine Veränderung!")
    else:
        dynamic.saveProg_Steuerung(SteuerCode)
        if(dyn_print_level >= 1): print("\nSteuercodes wurden geschrieben! (siehe Tabelle ENTLadeStrg)")
else:
    if(dyn_print_level >= 1): print("\nSteuercodes wurden NICHT geschrieben, da Option \"dynamicprice\" NICHT gesetzt!")

if(dyn_print_level >= 1): print("***** ENDE: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"*****\n")

# Strompreise in PV_Daten.sqlite/Strompreise speichern
# Neue Liste mit den Ergebnissen
priceforecast = []
for row in pv_data_charge:
    Ladezeitpunkt = row[0]
    PV_Prognose = row[1]
    Verbrauch = row[2]
    Akkustand_W = row[4]
    Ladewert = row[5]

    if Ladewert == -1:
        Netzverbrauch = Verbrauch - PV_Prognose
        Netzladen = 0
        if Netzverbrauch < 0: Netzverbrauch = 0
    elif Ladewert < -1:
        Netzverbrauch = Verbrauch - PV_Prognose
        Netzladen = Ladewert * -1
        if Netzverbrauch < 0:
            Netzladen = Netzladen + Netzverbrauch
            Netzverbrauch = 0
    else:
        if Akkustand_W < minimum_batterylevel_kWh:
            Netzverbrauch = Verbrauch - PV_Prognose
        else:
            Netzverbrauch = 0
        Netzladen = 0

    PrognBattStatus = round(Akkustand_W/battery_capacity_Wh*100, 1)
    priceforecast.append([Ladezeitpunkt,PV_Prognose,Netzverbrauch,Netzladen,PrognBattStatus])

if(dyn_print_level >= 3):
    # priceforecast Daten für DB
    print(">>  Folgende Strompreisvorhersage in PV_Daten.sqlite/priceforecast speichern.")
    headers = ["Ladezeitpunkt", "PV_Prognose", "PrognNetzverbrauch", "PrognNetzladen", "PrognBattStatus"]
    dynamic.listAStable(headers, priceforecast, '>> ')

if ('logging' in Options):
    # pv_data_charge aufbereiten:
    dynamic.save_Strompreise('PV_Daten.sqlite', pricelist_date, priceforecast)
    Logging_Schreib_Ausgabe = 'Strompreise in SQLite-Datei gespeichert!'
else:
    Logging_Schreib_Ausgabe = "Strompreise NICHT gespeichert, da Option \"logging\" NICHT gesetzt!\n" 
if dyn_print_level >= 1:
    print(Logging_Schreib_Ausgabe)
