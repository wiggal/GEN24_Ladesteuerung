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
    dyn_print_level = basics.getVarConf('dynprice','dyn_print_level', 'eval')
    LastprofilNeuTage = basics.getVarConf('dynprice','LastprofilNeuTage', 'eval')
    Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
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
            dynamic.makeLastprofil(PV_Database, Lastgrenze)
    else:
        if(dyn_print_level >= 1): print("Erzeuge Lastprofil, erstmalig!!")
        dynamic.makeLastprofil(PV_Database, Lastgrenze)
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
# List Date (2024-10-27 23:00:00), Euro/kWh
priecelist_date = dynamic.getPrice_energycharts(LAND, TimestampNow)

# Zusammenführen der Listen2
pv_data = []
for key in data:
    for key2 in priecelist_date:
        if key[0] == key2[0]:
            pv_data.append((key[0], key[1], key[2], key2[1]))

# Werte als Tabelle ausgeben
if(dyn_print_level >= 1):
    headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)"]
    dynamic.listAStable(headers, pv_data)


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


# Werte als Tabelle ausgeben
if(dyn_print_level >= 1):
    headers = ["Batteriekapazität (Wh)", "Aktueller Ladestand (Wh)", "minimaler Ladestand (Wh)"]
    table_liste = [(str(battery_capacity_Wh), str(current_charge_Wh), str(minimum_batterylevel_kWh))]
    print()
    dynamic.listAStable(headers, table_liste)
    print()


# Initialer Zustand des Akkus
battery_status_init = current_charge_Wh

# Listen für Lade- und Entladeentscheidungen
charging_times = []
stopping_times = []
charging_cost_tmp = 0
stopping_cost = 0
Hinweiszeichen = '>>>>>>>>>>'

if(dyn_print_level >= 2): print("\n*****************  DEBUGGING *****************")
for ladeArray, ladeWatt in zip(['charging', 'stopping'], [charge_rate_kW, 0]):
    pv_data_tmp = [("2000-01-01 00:00:00", 0, 0, 9999.999, 0)]
    battery_status = battery_status_init
    # Iteration durch die Stunden
    if(dyn_print_level >= 2): print("\n", Hinweiszeichen, ladeArray, Hinweiszeichen)
    i = 0
    while i < len(pv_data):
        row = pv_data[i]
        price = row[3]  # Preis in Euro/Wh
        battery_status_diff = 0
    
        # Berechnen der Nettostromproduktion
        # Prognose für PV-Leistung in Wh - Verbrauch in Wh
        net_power = int(row[1]) - int(row[2])

        # PV-Strom in Akku laden wenn unter minimum_batterylevel_kWh und Prognose kleiner Verbrauch
        best_price = price
        if battery_status + net_power < minimum_batterylevel_kWh and net_power < 0:
            # bisherigen kleisten Wert bisher suchen
            if(dyn_print_level >= 2): print("Jetzt  ",ladeArray,":   ", row + (battery_status,))
            kleinster_price = min(zeile[3] for zeile in pv_data_tmp)
            # Wenn kleister Wert bisher kleiner aktueller price, Ladung vorverlegen
            if ( kleinster_price < price):
                best_price = kleinster_price
                gefundene_zeile = None
                for zeile in pv_data_tmp:
                    if zeile[3] == kleinster_price:
                        net_power = int(zeile[1]) - int(zeile[2])
                        gefundene_zeile = zeile
                        break  # Beende die Schleife, wenn der Wert gefunden wurde
                if(dyn_print_level >= 2): print("Besser ",ladeArray,":", gefundene_zeile)
                # Bereits abgezogener Produktion - Verbrauch wieder addieren, und aktuelle net_power addieren
                battery_status_diff = gefundene_zeile[4] - battery_status
                battery_status += (int(gefundene_zeile[2])-int(gefundene_zeile[1]))
                # Wenn frühere Zeile gefunden => entfernen,
                pv_data_tmp.remove(gefundene_zeile)
            else:
                row = row + (battery_status,)
                gefundene_zeile = row
                i += 1

            #prüfen ob charging = charge_rate_kW, noch in Akku passt
            if battery_status + ladeWatt > battery_capacity_Wh:
                ladeWatt = battery_capacity_Wh - battery_status

            # charge_rate_kW zu Speicher geben
            battery_status += ladeWatt
            cost_tmp = round(((best_price * (ladeWatt + net_power)) / 1000),3)
            # aktuellen Ladewert in gefundene_zeile ersetzen
            gefundene_zeile = list(gefundene_zeile)
            gefundene_zeile[4] = battery_status + battery_status_diff
            gefundene_zeile = tuple(gefundene_zeile)
            if ( ladeArray == 'charging' ):
                charging_times.append(gefundene_zeile + (ladeWatt * -1,))
                charging_cost_tmp += cost_tmp
            if ( ladeArray == 'stopping' ):
                stopping_times.append(gefundene_zeile + (-1,))
                stopping_cost += cost_tmp

        else:
            # ansonsten speicher weiter mit net_power ent- bzw. laden
            battery_status += net_power
            # und pv_data_tmp für Suche kleinster Wert füllen
            row = row + (battery_status,)
            pv_data_tmp.append(row)
            i += 1

    if battery_status > battery_capacity_Wh: battery_status = battery_capacity_Wh
    if ( ladeArray == 'charging' ):
        battery_status_charging = battery_status
    if ( ladeArray == 'stopping' ):
        battery_status_stopping = battery_status
    Hinweiszeichen = '!!!!!!!!!!'

if(dyn_print_level >= 2): print("\n*************** ENDE DEBUGGING ***************\n")

# Durchschnittsstrompreis um den unterschiedlichen Ladezustand auszugleichen
# Nur wenn Liste charging_times nicht leer ist
Ausgabe = '"Wiederherstellung ENTLadeStrg"'
if charging_times:
    kleinster_price = min(zeile[3] for zeile in charging_times)
    Akkuplus = ((battery_status_stopping-battery_status_charging)*kleinster_price/1000)
    charging_cost = round((charging_cost_tmp + Akkuplus)*(1+(Akku_Verlust_Prozent/100)), 2)

    if(dyn_print_level >= 1):
        # Werte als Tabelle ausgeben
        print(">>>>>>>>>> Batterie laden >>>>>>>>>>")
        charging_times.sort(key=lambda x: x[0])
        headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)", "Ladewert"]
        dynamic.listAStable(headers, charging_times)
        print("\nBatteriekapazität: ", battery_status_charging)
        print("Kosten Batterieladung: ", round(charging_cost_tmp, 2), "€")
        print("Kosten Ladung: ", round(charging_cost_tmp, 2), "€")
        print("Preis Akkustandplus  : ", round(Akkuplus, 2), "€")
        print("Vergleichskosten Akkuladung: ", round(charging_cost, 2), "€ (Ausgleich Akkustand, plus Ladeverluste)")
        print()
    
        print("!!!!!!!!!! Entladung stoppen !!!!!!!!!!")
        headers = ["Zeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)", "Ladewert"]
        stopping_times.sort(key=lambda x: x[0])
        dynamic.listAStable(headers, stopping_times)
        print("\nBatteriekapazität: ", battery_status_stopping)
        print("Vergleichskosten Ladungstop: ", round(stopping_cost, 2), "€")

    ### Daten zum schreiben in CONFIG/Prog_Steuerung.sqlite vorbereiten

    # Ladewert ermitteln charging OR stopping
    if (charging_cost > stopping_cost):
        Ladewert = -1 # Mit 1Watt zwangsladen = Lade und Entladenstopp
        LadeProfil = stopping_times
        Ausgabe = '"Ladung stoppen"'
    else:
        Ladewert = charge_rate_kW * -1 # Minuswert um aus dem Netz zu laden
        LadeProfil = charging_times
        Ausgabe = '"Speicher Laden"'

else:
    print("Es sind keine Ladezeiten bzw. Entladepausen nötig!!\n")

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
for stunde in range(24):  # die nächsten 24 Stunden
    zeitpunkt = heute_start + timedelta(hours=stunde)
    Stunde = zeitpunkt.strftime("%H:%M")  # Stunde im Speicherformat
    Res_Feld1 = 0
    Res_Feld2 = 0
    Options = ''
    SuchStunde = zeitpunkt.strftime("%Y-%m-%d %H:%M:%S")
    if entladesteurungsdata[Stunde]['Res_Feld1'] + entladesteurungsdata[Stunde]['Res_Feld2'] > 0:
        Res_Feld1 = entladesteurungsdata[Stunde]['Res_Feld1']
        Res_Feld2 = entladesteurungsdata[Stunde]['Res_Feld2']
    if entladesteurungsdata[Stunde]['Options'] != '':
        Options = entladesteurungsdata[Stunde]['Options']

    if 'LadeProfil' in locals():
        for Stundenliste in LadeProfil:
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
    DBCode.append((Stunde, 'ENTLadeStrg', Stunde, entladesteurungsdata[Stunde]['Res_Feld1'], entladesteurungsdata[Stunde]['Res_Feld2'], entladesteurungsdata[Stunde]['Options']))

    # DEBUG CSV-Ausgabe
    if(dyn_print_level >= 1):
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

if(dyn_print_level >= 1):
    # Zu schreibenen SteuerCode ausgeben
    print("\nFolgende Steuercodes wurden ermittelt:")
    headers = ["Index", "Schlüssel", "Stunde", "Verbrauchsgrenze", "Feste Entladegrenze", "Options"]
    dynamic.listAStable(headers, SteuerCode)
    print("\nMindestpreisdifferenz >>> Preisdifferenz = ", minimum_price_difference, ">>>", round(price_difference, 3))

else:
    if(dyn_print_level >= 1):
        print("\nMindestpreisdifferenz >>> Preisdifferenz = ", minimum_price_difference, ">>>", round(price_difference, 3))
        print("Steuercodes werden nicht geschrieben, da Preisdiffernz zu klein:")
        print("***** ENDE: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"*****\n")
        exit()

Parameter = ''
if len(argv) > 1 :
    Parameter = argv[1]

if( Parameter == 'schreiben'):
    SteuerCode.sort()
    DBCode.sort()
    if SteuerCode == DBCode:
        if(dyn_print_level >= 1): print("\nSteuercodes", Ausgabe, "wurden NICHT geschrieben, da keine Veränderung!")
    else:
        dynamic.saveProg_Steuerung(SteuerCode)
        if(dyn_print_level >= 1): print("\nSteuercodes", Ausgabe, "wurden geschrieben! (siehe Tabelle ENTLadeStrg)")
else:
    if(dyn_print_level >= 1): print("\nSteuercodes", Ausgabe, "wurden NICHT geschrieben, Parameter schreiben fehlt")

if(dyn_print_level >= 1): print("***** ENDE: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"*****\n")


