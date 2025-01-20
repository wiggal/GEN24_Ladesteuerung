# Hier die Funktionen zum dynamischen Stromtarif
from datetime import datetime, timedelta
import sqlite3
import json
import requests
import FUNCTIONS.functions
    
basics = FUNCTIONS.functions.basics()

class dynamic:
    def __init__(self):
        self.now = datetime.now()

    def makeLastprofil(self, database, Lastgrenze, Daysback='-35'):
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
        # Daysback muss mindestens 8 Tage sein
        if Daysback > -8: Daysback = -8
        # Lastprofil von jetzt 35 Tage zurück für jeden Wochentag ermitteln
        sql_anweisung = """
        WITH stundenwerte AS (
            SELECT
                strftime('%Y-%m-%d %H:00:00', Zeitpunkt) AS volle_stunde,
                MAX(Netzverbrauch) AS max_netzverbrauch,
                MAX(AC_Produktion) AS max_acproduktion,
                MAX(Einspeisung) AS max_einspeisung
            FROM
                pv_daten
            WHERE
                Zeitpunkt >= datetime('now', '""" + str(Daysback) + """ days')
            GROUP BY
                strftime('%Y-%m-%d %H:00:00', Zeitpunkt)
        ),
        differenzen AS (
            SELECT
                a.volle_stunde,
                a.max_netzverbrauch - COALESCE(b.max_netzverbrauch, 0) AS Netzverbrauch,
                a.max_acproduktion - COALESCE(b.max_acproduktion, 0) AS ACProduktion,
                a.max_einspeisung- COALESCE(b.max_einspeisung, 0) AS Einspeisung
            FROM
                stundenwerte a
            LEFT JOIN
                stundenwerte b ON a.volle_stunde = datetime(b.volle_stunde, '+1 hour')
        ),
        verbrauch AS (
        SELECT
            volle_stunde,
	        CASE 
                WHEN (Netzverbrauch + ACProduktion - Einspeisung) > """ + str(Lastgrenze) + """ THEN """ + str(Lastgrenze) + """
                ELSE (Netzverbrauch + ACProduktion - Einspeisung) 
            END AS Verbrauch
        FROM
            differenzen
        )
        SELECT
            strftime('%w', volle_stunde) || '-' || strftime('%H', volle_stunde) AS ID,
            'Lastprofil' AS Schluessel,
            strftime('%H:00', volle_stunde) AS Zeit,
            strftime('%w', volle_stunde) AS Wochentag,
            /*
            # Normaler Durchschnitt
            CAST(AVG(Verbrauch) AS INTEGER) AS Verbrauch,
            # höheres Gewicht je aktueller die Werte
            */
            CASE
			    WHEN (CAST(SUM(Verbrauch * (Julianday('now') - Julianday(volle_stunde))) AS INTEGER) / CAST(SUM(Julianday('now') - Julianday(volle_stunde)) AS INTEGERA))  IS NULL THEN 600
			    ELSE CAST(SUM(Verbrauch * (Julianday('now') - Julianday(volle_stunde))) AS INTEGER) / CAST(SUM(Julianday('now') - Julianday(volle_stunde)) AS INTEGER)
            END AS Verbrauch,
            strftime('%s', 'now') AS Options
        FROM
            verbrauch
        GROUP BY
            Wochentag, Zeit
        HAVING
            Verbrauch > 0
        ORDER BY
            strftime('%w', volle_stunde), Zeit;
        """

        try:
            zeiger.execute(sql_anweisung)
            rows = zeiger.fetchall()
            dyn_print_level = basics.getVarConf('dynprice','dyn_print_level', 'eval')
            if(dyn_print_level >= 2):
                headers = ["Index", "Datenart", "Stunde", "Wochentag", "Verbrauch", "Timestamp"]
                self.listAStable(headers, rows)
        except:
            print("Die Datei PV_Daten.sqlite fehlt oder ist leer, zum Erzeugen http_SymoGen24Controller2.py aufrufen, Programmende!!")
            exit()

        if (len(rows) < 168):
            print("\n>>> Zu wenig Daten (", round((len(rows)/24), 1), "Tage) in PV_Daten.sqlite, es sind mindestens 7 ganze Tage erforderlich.\n>>> Fehlende Werte werden mit 600 Watt aufgefüllt!!\n")
            # Wenn zu wenige Tage mit 600 Watt auffüllen
            timestamp_tmp = str(int(rows[1][5]))
            for Wochentag in range(7):
                for Stunde in range(24):
                    index = f"{Wochentag}-{Stunde:02}"
                    if not any(index in subliste for subliste in rows):
                        stunde = f"{Stunde:02}:00"
                        rows.append((index,'Lastprofil',stunde,str(Wochentag),600,timestamp_tmp))
                        rows.sort()

        verbindung.commit()
        verbindung.close()
        # Daten in DB CONFIG/Prog_Steuerung.sqlite schreiben
        self.saveProg_Steuerung(rows)
        print("Lastprofil in CONFIG/Prog_Steuerung.sqlite geschrieben\n")

        return()

    def saveProg_Steuerung(self, rows):
        # Daten in DB schreiben

        verbindung = sqlite3.connect('CONFIG/Prog_Steuerung.sqlite')
        zeiger = verbindung.cursor()
        zeiger.executemany('''
                    REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES (?, ?, ?, ?, ?, ?)
                    ''', rows)
    
        verbindung.commit()
        verbindung.close()


        return ()

    def getLastprofil(self):
        try:
            # Hier die Lastprofildaten für heute und morgen auslesen
            verbindung = sqlite3.connect('CONFIG/Prog_Steuerung.sqlite')
            zeiger = verbindung.cursor()
            # Res_Feld1 = Wochentag, Zeit = Stunde, Res_Feld2 = Durchschnittsverbrauch, Options = Timestamp Erzeugung
            sql_anweisung = "SELECT Res_Feld1, Zeit, Res_Feld2, Options from steuercodes WHERE Schluessel == 'Lastprofil' AND Res_Feld1 IN (strftime('%w', 'now'), strftime('%w', 'now', '+1 day'));"
            zeiger.execute(sql_anweisung)
            rows = zeiger.fetchall()
        except:
            print("CONFIG/Prog_Steuerung.sqlite fehlt oder ist defekt,\n bitte http_SymoGen24Controller2.py ausführen!")
            print(">>> Programmabbruch >>>>")
            exit()

        return(rows)

    def getPrognosen_24H(self, weatherdata):
        i = 1
        Prognosen_24H = []
        Prognosestunden = 25
        while i < Prognosestunden:
            # ab aktueller Stunde die nächsten 24 Stunden, da ab 24 Uhr sonst keine Morgenprognose
            Std_morgen = datetime.strftime(self.now + timedelta(hours=i), "%Y-%m-%d %H:00:00")
            try:
                Prognosen_24H.append((Std_morgen, weatherdata['result']['watts'][Std_morgen]))
            except:
                Prognosen_24H.append((Std_morgen, 0))
            i  += 1
        return(Prognosen_24H)
        
    def getPrice_energycharts(self, BZN):
        # Aufschläge zum reinen Börsenpreis, return muss immer Bruttoendpreis liefern
        Nettoaufschlag = basics.getVarConf('dynprice','Nettoaufschlag', 'eval')
        MwSt = basics.getVarConf('dynprice','MwSt', 'eval')


        # Definiere den heutigen Tag (für 0:00 Uhr) und morgen (für 23:00 Uhr)
        heute = datetime.now()
        morgen = heute + timedelta(days=1)
        
        # Setze das Datum im richtigen Format für die API
        start_time = heute.strftime('%Y-%m-%d')
        end_time = morgen.strftime('%Y-%m-%d')

        # API-Endpunkt und Parameter
        url = "https://api.energy-charts.info/price"
        params = {
            "start": start_time,
            "end": end_time,
            "area": BZN,  # Beispiel: DE für Deutschland, anpassen je nach Land
            "currency": "EUR",  # Die Währung
        }
        
        try:
            apiResponse = requests.get(url, params=params, timeout=180)
            apiResponse.raise_for_status()
            if apiResponse.status_code != 204:
                json_data1 = dict(json.loads(apiResponse.text))
            else:
                print("### ERROR:  Keine forecasts-Daten von api.forecast.solar")
                exit()
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout von api.forecast.solar")
            exit()
        price = json_data1
        pricelist = list(zip(price['unix_seconds'], price['price']))
        pricelist_date = []
        for row in pricelist:
            if row[1] is not None:
                time = datetime.fromtimestamp(row[0]).strftime("%Y-%m-%d %H:%M:%S")
                price = round((row[1]/1000 + Nettoaufschlag) * MwSt, 4)
                # Zeitunkt, Bruttopreis, Börsenpreis
                pricelist_date.append((time, price, round(row[1]/1000, 3)))
        return(pricelist_date)

    def listAStable(self, headers, data, Vorspann='' ):

        # Maximale Breite für die Spalten berechnen
        col_widths = [max(len(str(item)) for item in col) for col in zip(headers, *data)]
        
        # Header ausgeben
        header_row = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
        print(Vorspann,header_row)
        print(Vorspann,"-" * len(header_row))

        # Daten ausgeben
        for row in data:
            print(Vorspann," | ".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(row))))

        return()

    def akkustand_neu(self, pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W=0):
        # Ladeverlust beim Berechnen des Akuu-SOC berücksichtigen
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        Ladeverlust = (Akku_Verlust_Prozent/200)
        if max_batt_dyn_ladung_W == 0: max_batt_dyn_ladung_W = battery_capacity_Wh
        # Ladestand für alle Zeiten neu berechnen
        for Akkustatus in pv_data_charge:
            min_net_power = Akkustatus[1] - Akkustatus[2]
            if min_net_power > charge_rate_kW: min_net_power = charge_rate_kW
            if Akkustatus[5] < 0:
                if int(Akkustatus[5] * -1) < min_net_power:
                    akku_soc += min_net_power
                else:
                    # Ladeverlust anbringen
                    akku_soc += int(Akkustatus[5] * (-1 + Ladeverlust))
            else:
                akku_soc += min_net_power
            # Akku auf Maximum begrenzen
            if akku_soc > battery_capacity_Wh: akku_soc = battery_capacity_Wh
            # Akkustatus und Ladung reduzieren, wenn SOC-Begrenzung durch Zwangsladung überschritten und der kleiste Wert größer minimum_batterylevel
            # auch hier wegen Ladeverlust anbringen, hier ladung um Ladeverlust erhöhen um auf den Akkuollstand zu kommen
            kleinster_soc = min(zeile[4] for zeile in pv_data_charge)
            if akku_soc > max_batt_dyn_ladung_W and Akkustatus[5] < -1:
                akku_soc_reduziert = int((akku_soc - max_batt_dyn_ladung_W + Akkustatus[5]) * (1 + Ladeverlust))
                if akku_soc_reduziert > -1: akku_soc_reduziert = -1
                Akkustatus[5] = akku_soc_reduziert
                akku_soc = max_batt_dyn_ladung_W
            # Akustand muss minimal unter minimum_batterylevel sein
            if akku_soc < minimum_batterylevel: akku_soc = int(minimum_batterylevel*0.99)
            Akkustatus[4] = akku_soc

        return(pv_data_charge)

    def get_charge_stop(self, pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh):
        dyn_print_level = basics.getVarConf('dynprice','dyn_print_level', 'eval')
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        Gewinnerwartung_kW = basics.getVarConf('dynprice','Gewinnerwartung_kW', 'eval')
        max_batt_dyn_ladung = basics.getVarConf('dynprice','max_batt_dyn_ladung', 'eval')
        max_batt_dyn_ladung_W = int(battery_capacity_Wh * max_batt_dyn_ladung / 100)
        # Ladewert ist -1 wenn kein Profilabler Preis
        max_ladewert = charge_rate_kW * -1
        Zeilen = 24
        while Zeilen > 0:
            if(dyn_print_level >= 3):
                headers = ["Ladezeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Batteriestand (W)", "Ladewert"]
                self.listAStable(headers, pv_data_charge, '>>')
            # größten Preis wenn Spalte 5 noch 0.1 ist, also noch nicht behandelt
            max_gefilterte_zeilen = [zeile for zeile in pv_data_charge if zeile[5] == 0.1]
            if(dyn_print_level >= 3): print(">> \n>> max: ", max_gefilterte_zeilen) 
            if max_gefilterte_zeilen:
                zeile_max_price = max(max_gefilterte_zeilen, key=lambda x: x[3])
                if(dyn_print_level >= 3): print(">> \n>> zeile_max_price: ", zeile_max_price) 
    
            # Wenn minimum_batterylevel unterschritten Ladepunkt suchen und setzen
            if zeile_max_price[4] < minimum_batterylevel:
                max_akkustand = battery_capacity_Wh - charge_rate_kW * 0.25
                kleiner_gefilterte_zeilen = [zeile for zeile in pv_data_charge if zeile[0] < zeile_max_price[0] and zeile[4] < max_akkustand and zeile[5] == 0.1]
                if kleiner_gefilterte_zeilen:
                    zeile_min_price = min(kleiner_gefilterte_zeilen, key=lambda x: x[3])
                    # Laden nur wenn profitabel
                    profit_price = round(zeile_min_price[3] * (1+(Akku_Verlust_Prozent/100)) + Gewinnerwartung_kW, 4)
                    zeilen_index = next((i for i, row in enumerate(pv_data_charge) if zeile_min_price[0] in row))
                    if(zeile_max_price[3] > profit_price):

                        # Hier noch Ladung auf max_batt_dyn_ladung des Akku begrenzen
                        if(dyn_print_level >= 3): print(">> max_batt_dyn_ladung_W: ", max_batt_dyn_ladung_W)
                        # Bei Ladung wird Verbrauch auch aus Netz gezogen + Ladeverlust anbringen
                        max_ladewert_grenze = int((pv_data_charge[zeilen_index][4] - max_batt_dyn_ladung_W) * (1 + (Akku_Verlust_Prozent/200)))
                        if(dyn_print_level >= 3): print(">> max_ladewert_grenze: ", pv_data_charge[zeilen_index][4], max_ladewert_grenze)
                        if max_ladewert_grenze > -1 or max_ladewert > charge_rate_kW * -1: max_ladewert = -1
                        if max_ladewert_grenze > max_ladewert: max_ladewert = max_ladewert_grenze

                        pv_data_charge[zeilen_index][5] = max_ladewert
                        if(dyn_print_level >= 3): print(">> \n>> Ladepunkt wenn", zeile_max_price[3], ">", profit_price, pv_data_charge[zeilen_index]) 
                    else:
                        if(dyn_print_level >= 3): print(">> \n>> Kein profitabler Preis", zeile_max_price[3], ">", profit_price, pv_data_charge[zeilen_index]) 
                        if  pv_data_charge[zeilen_index][4] > minimum_batterylevel:
                            pv_data_charge[zeilen_index][5] = -1
                else:
                    if(dyn_print_level >= 3): print(">> \n>> Keine kleiner_gefilterte_zeilen") 

            # Finde Index der Zeile mit dem gesuchten Wert
            zeilen_index = next((i for i, row in enumerate(pv_data_charge) if zeile_max_price[0] in row))
            pv_data_charge[zeilen_index][5] = 0
            # Akkustände neu berechnen
            self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W)

            Zeilen = sum(1 for row in pv_data_charge if len(row) > 5 and row[5] == 0.1)

        return(pv_data_charge)
