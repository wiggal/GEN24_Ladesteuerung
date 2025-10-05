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
        self.dyn_print_level = basics.getVarConf('dynprice','dyn_print_level', 'eval')

    def makeLastprofil(self, database, Lastgrenze, Daysback='-35'):
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
        # Daysback muss mindestens 8 Tage sein
        if Daysback > -8: Daysback = -8
        # Lastprofil von jetzt 35 Tage zurück für jeden Wochentag ermitteln (0=Sonntag)
        sql_anweisung = """
        WITH differenzen AS (
			select Zeitpunkt AS volle_stunde,
                (max(DC_Produktion) - min(DC_Produktion)) as Produktion,
                (max(Netzverbrauch) - min(Netzverbrauch)) as Netzverbrauch,
                (max(Batterie_IN) - min(Batterie_IN)) as InBatterie,
                (max(Batterie_OUT) - min(Batterie_OUT)) as VonBatterie,
                (max(Einspeisung) - min(Einspeisung)) as Einspeisung
            FROM
                pv_daten
			WHERE
                Zeitpunkt >= datetime('now', '""" + str(Daysback) + """ days')
            GROUP BY
                strftime('%Y-%m-%d %H:00:00', volle_stunde)
        ),
        verbrauch AS (
        SELECT
            volle_stunde,
	        CASE 
                WHEN (Netzverbrauch + Produktion - Einspeisung + VonBatterie - InBatterie) > """ + str(Lastgrenze) + """ THEN """ + str(Lastgrenze) + """
                ELSE (Netzverbrauch + Produktion - Einspeisung + VonBatterie - InBatterie) 
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
            */
            CAST(AVG(Verbrauch) AS INTEGER) AS Verbrauch,
            /*
            # höheres Gewicht je aktueller die Werte
            CASE
			    WHEN (CAST(SUM(Verbrauch * (Julianday('now') - Julianday(volle_stunde))) AS INTEGER) / CAST(SUM(Julianday('now') - Julianday(volle_stunde)) AS INTEGERA))  IS NULL THEN 600
			    ELSE CAST(SUM(Verbrauch * (Julianday('now') - Julianday(volle_stunde))) AS INTEGER) / CAST(SUM(Julianday('now') - Julianday(volle_stunde)) AS INTEGER)
            END AS Verbrauch,
            */
            CAST(strftime('%s', 'now') AS INTEGER) AS Options
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
            # Lastprofil ausgeben, wenn dyn_print_level >= 3
            if(self.dyn_print_level >= 3):
                headers = ["Index", "Datenart", "Stunde", "Wochentag", "Verbrauch", "Timestamp"]
                self.listAStable(headers, rows)
        except:
            print("Die Datei PV_Daten.sqlite fehlt oder ist leer, zum Erzeugen http_SymoGen24Controller2.py aufrufen, Programmende!!")
            exit()

        if (len(rows) < 168):
            print("\n>>> Zu wenig Daten (", round((len(rows)/24), 1), "Tage) in PV_Daten.sqlite, es sind mindestens 7 ganze Tage erforderlich.\n>>> Fehlende Werte werden mit 600 Watt aufgefüllt!!\n")
            # Wenn zu wenige Tage mit 600 Watt auffüllen
            try:
                timestamp_tmp = str(int(rows[1][5]))
            except:
                timestamp_tmp = int(datetime.now().timestamp())
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
        
    def get_pricelist_date_viertel(self, json_data1):
        Nettoaufschlag = basics.getVarConf('dynprice','Nettoaufschlag', 'eval')
        MwSt = basics.getVarConf('dynprice','MwSt', 'eval')

        # Tageszeitabhängiger Preisanteil viertelstündlich (z.B. $14a Netzentgelte)
        Tageszeit_Preisanteil_tmp = json.loads(basics.getVarConf('dynprice','Tageszeit_Preisanteil', 'str')) 
        # Zeitpunkte auf Minutenwerte prüfen, evtl. ergänzen und Werte sortieren
        time_points = sorted(
            (datetime.strptime(k if ":" in k else f"{k.zfill(2)}:00", "%H:%M"), float(v))
            for k, v in Tageszeit_Preisanteil_tmp.items()
        )

        Tageszeit_Preisanteil = {}

        # 15-Minuten Raster über den ganzen Tag
        current = datetime.strptime("00:00", "%H:%M")
        end_of_day = current + timedelta(days=1)

        while current < end_of_day:
            # letzten gültigen Eintrag finden
            value = None
            for t, v in time_points:
                if t <= current:
                    value = v
                else:
                    break

            # falls noch kein gültiger Startwert (z.B. Raster < erstem Eintrag) → nimm letzten Wert vom Vortag
            if value is None:
                value = time_points[-1][1]

            Tageszeit_Preisanteil[current.strftime("%H:%M")] = value
            current += timedelta(minutes=15)

        # DEBUG
        if(self.dyn_print_level >= 4): print("++ Tageszeit_Preisanteil: ", Tageszeit_Preisanteil, "\n")

        try:
            # viertelstündliche Netzentgelte addieren
            price = json_data1
            pricelist = list(zip(price['unix_seconds'], price['price']))
            pricelist_date = []
            for row in zip(price['unix_seconds'], price['price']):
                if row[1] is not None:
                    dt = datetime.fromtimestamp(row[0])
                    # Uhrzeit gerundet auf 15 Minuten
                    minutes = (dt.minute // 15) * 15
                    quarter_time = dt.replace(minute=minutes, second=0, microsecond=0).strftime("%H:%M")

                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    brutto_preis = round((row[1] / 1000 + Nettoaufschlag + Tageszeit_Preisanteil[quarter_time]) * MwSt, 4)

                    # Zeitpunkt, Bruttopreis, Börsenpreis
                    pricelist_date.append((time_str, brutto_preis, round(row[1] / 1000, 3)))

        except Exception as e:
            print("### ERROR: Keine Daten von api.energy-charts.info, deshalb die Preise aus DB verwenden!\n")
            verbindung = sqlite3.connect('PV_Daten.sqlite')
            zeiger = verbindung.cursor()
            sql_anweisung = "SELECT * from strompreise WHERE DATE(Zeitpunkt) BETWEEN DATE('now') AND DATE('now', '+1 day');"
            zeiger.execute(sql_anweisung)
            pricelist_date = zeiger.fetchall()
            if pricelist_date == []:
                print("### ERROR: In der DB sind auch keine aktuellen Strompreise vorhanden, Programmabbruch:")
                exit()

        return(pricelist_date)

    def getPrice_smart_api(self, BZN):
        # Aktuelles Datum und Uhrzeit
        jetzt = datetime.now()
        # Wochentag berechnen (Montag = 0, Sonntag = 6)
        wochentag = jetzt.weekday()
        # Start der Woche (Montag 00:00)
        montag = datetime(jetzt.year, jetzt.month, jetzt.day) - timedelta(days=wochentag)
        montag = montag.replace(hour=0, minute=0, second=0, microsecond=0)
        heute = jetzt.replace(hour=0, minute=0, second=0, microsecond=0)
        # Unix-Timestamp berechnen
        montag_timestamp = int(montag.timestamp())

        # API-URL mit Parameter
        Gebietsfilter = 4169 # für DE-LU 
        if(BZN == 'AT'): Gebietsfilter = 4170

        #  stündliche oder viertestündliche Strompreise
        resolution = basics.getVarConf('dynprice','resolution', 'str') 
        url = "https://smard.api.proxy.bund.dev/app/chart_data/{}/{}/{}_{}_{}_{}000.json".format(Gebietsfilter, BZN, Gebietsfilter, BZN, resolution, montag_timestamp)
        timeout_sec = 30
        Push_Schreib_Ausgabe = ''
        
        try:
            apiResponse = requests.get(url, timeout=timeout_sec)
            apiResponse.raise_for_status()
            if apiResponse.status_code != 204:
                raw = dict(json.loads(apiResponse.text))
                # Format für Funktion get_pricelist_date_viertel erzeugen
                unix_seconds = [ts // 1000 for ts, val in raw["series"]]
                prices = [val for ts, val in raw["series"]]
                json_data1 = {
                    "license_info": "CC BY 4.0 (creativecommons.org/licenses/by/4.0) from Bundesnetzagentur | SMARD.de",
                    "unix_seconds": unix_seconds,
                    "price": prices
                }
            else:
                Ausgabe = "### ERROR:  Keine Strompreise von api.energy-charts.info"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.Timeout:
                Ausgabe = "### ERROR: Timeout, keine Strompreise von api.energy-charts.info"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.HTTPError as http_err:
                Ausgabe = (f"### ERROR: HTTP-Fehler: {http_err} (Status Code: {apiResponse.status_code})")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.RequestException as req_err:
                Ausgabe = (f"### ERROR: Verbindungsfehler oder andere Probleme: {req_err}")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe

        # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
        Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
        if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
            Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
            apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
            print("PushMeldung an ", Push_Message_Url, " gesendet.\n")

        # viertelstündliche Netzentgelte addieren
        pricelist_date = self.get_pricelist_date_viertel(json_data1)

        return(pricelist_date)

    def get_stuendliches_mittel(self, data):
        from collections import defaultdict
        import statistics

        # Daten nach Stunden gruppieren
        groups = defaultdict(lambda: {"val1": [], "val2": []})

        for t_str, v1, v2 in data:
            dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
            hour_key = dt.replace(minute=0, second=0, microsecond=0)  # nur volle Stunde
            groups[hour_key]["val1"].append(v1)
            groups[hour_key]["val2"].append(v2)

        # Mittelwerte berechnen
        hourly_means = []
        for hour, vals in sorted(groups.items()):
            mean_v1 = round(statistics.mean(vals["val1"]), 4)
            mean_v2 = round(statistics.mean(vals["val2"]), 4)
            hour_str = hour.strftime("%Y-%m-%d %H:%M:%S")  # zurück in String
            hourly_means.append((hour_str, mean_v1, mean_v2))

        return(hourly_means)

    def getPrice_energycharts(self, BZN):
        # Definiere den heutigen Tag (für 0:00 Uhr) und morgen (für 23:00 Uhr)
        heute = datetime.now()
        morgen = heute + timedelta(days=1)
        
        # Setze das Datum im richtigen Format für die API
        start_time = heute.strftime('%Y-%m-%d')
        end_time = morgen.strftime('%Y-%m-%d')

        # API-URL mit Parameter
        resolution = basics.getVarConf('dynprice','resolution', 'str') 
        url = "https://api.energy-charts.info/price?bzn={}&start={}&end={}".format(BZN, start_time, end_time)
        timeout_sec = 30
        Push_Schreib_Ausgabe = ''
        
        try:
            apiResponse = requests.get(url, timeout=timeout_sec)
            apiResponse.raise_for_status()
            if apiResponse.status_code != 204:
                json_data1 = dict(json.loads(apiResponse.text))
            else:
                Ausgabe = "### ERROR:  Keine Strompreise von api.energy-charts.info"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.Timeout:
                Ausgabe = "### ERROR: Timeout, keine Strompreise von api.energy-charts.info"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.HTTPError as http_err:
                Ausgabe = (f"### ERROR: HTTP-Fehler: {http_err} (Status Code: {apiResponse.status_code})")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.RequestException as req_err:
                Ausgabe = (f"### ERROR: Verbindungsfehler oder andere Probleme: {req_err}")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe

        # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
        Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
        if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
            Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
            apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
            print("PushMeldung an ", Push_Message_Url, " gesendet.\n")

        # viertelstündliche Netzentgelte addieren
        pricelist_date = self.get_pricelist_date_viertel(json_data1)
        # wenn resolution == hour Mittelwerte bilden
        if(resolution == 'hour'):
            pricelist_date = self.get_stuendliches_mittel(pricelist_date)

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

    def akkustand_neu(self, pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W=0, mitPV=1, Stundenteile=1):
        # Ladeverlust beim Berechnen des Akuu-SOC berücksichtigen
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        netzlade_preisschwelle = basics.getVarConf('dynprice','netzlade_preisschwelle', 'eval')
        # Wenn keine Maximaler Zwangsladung-SOC (0) Akkukapazität setzen.
        if max_batt_dyn_ladung_W == 0: max_batt_dyn_ladung_W = battery_capacity_Wh

        # Ladestand für alle Zeiten neu berechnen
        for Akkustatus in pv_data_charge:
            min_net_power = Akkustatus[1] - Akkustatus[2]
            # Wenn mitPV == 0 dann PV-ertrag nicht in Speicher laden, um auf negative Strompreise zu warten
            Ladewert_tmp = Akkustatus[5]
            if mitPV == 0: 
                if min_net_power > 0: min_net_power = 0
                if Akkustatus[5] == -0.01: Ladewert_tmp = 0
            if min_net_power > charge_rate_kW: min_net_power = charge_rate_kW
            #if Akkustatus[5] < 0:
            if Ladewert_tmp < 0:
                # Wenn PV-Produktion größer Zwangsladung, PV-Produktion zum SOC.
                if int(Akkustatus[5] * -1) < min_net_power:
                    akku_soc += int(min_net_power / Stundenteile)
                else:
                    akku_soc += int(((Akkustatus[5] * -1) / (1 + (Akku_Verlust_Prozent/200))) / Stundenteile)
            else:
                if min_net_power > 0:
                    akku_soc += int(min_net_power / Stundenteile)
                else:
                    akku_soc += int((min_net_power * (1 + (Akku_Verlust_Prozent/200))) / Stundenteile)
                    

            # Akustand muss minimal unter minimum_batterylevel sein
            if akku_soc < minimum_batterylevel: akku_soc = int(minimum_batterylevel*0.99)
            # Akku nochmal auf Maximum begrenzen
            if akku_soc > battery_capacity_Wh: akku_soc = battery_capacity_Wh
            Akkustatus[4] = akku_soc

        return(pv_data_charge)

    def get_charge_stop(self, pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, current_charge_Wh, Stundenteile=1):
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        Gewinnerwartung_kW = basics.getVarConf('dynprice','Gewinnerwartung_kW', 'eval')
        max_batt_dyn_ladung = basics.getVarConf('dynprice','max_batt_dyn_ladung', 'eval')
        netzlade_preisschwelle = basics.getVarConf('dynprice','netzlade_preisschwelle', 'eval')
        max_batt_dyn_ladung_W = int(battery_capacity_Wh * max_batt_dyn_ladung / 100)
        # Ladewert ist -1 wenn kein Profilabler Preis
        max_ladewert = charge_rate_kW * -1

        # 1.) negative bzw. sehr niedrige Strompreise suchen und da Akku vollladen
        # Akkustand ohne PV-Leistung ermitteln
        self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W, 0, Stundenteile)
        min_Preis_zeilen = [zeile for zeile in pv_data_charge if zeile[3] < netzlade_preisschwelle]
        # noch nach Preis sortieren
        min_Preis_zeilen = sorted(min_Preis_zeilen, key=lambda x: x[3])
        if(self.dyn_print_level >= 3 and min_Preis_zeilen):
            print("\n>> ******** Wenn Strompreis unter netzlade_preisschwelle ********")

        for min_Preis_Std in min_Preis_zeilen:
            charge_rate_kW_tmp = charge_rate_kW
            spaeter_zeile_max_soc = [zeile for zeile in pv_data_charge if zeile[0] >= min_Preis_Std[0]]
            zeile_max_soc = max(spaeter_zeile_max_soc, key=lambda x: x[4])
            if (battery_capacity_Wh - zeile_max_soc[4] < charge_rate_kW): charge_rate_kW_tmp = int((battery_capacity_Wh - zeile_max_soc[4]) + 1.1)
            if charge_rate_kW_tmp > 100:
                min_Preis_Std[5]= charge_rate_kW_tmp * -1
            # NOCHMAL: Akkustand ohne PV-Leistung ermitteln
            self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W, 0, Stundenteile)
            if(self.dyn_print_level >= 3):
                headers = ["Ladezeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Akku ("+str(current_charge_Wh)+"W)", "Ladewert"]
                self.listAStable(headers, pv_data_charge, '>>')

        if(self.dyn_print_level >= 3 and min_Preis_zeilen):
            print(">> ******** ENDE: Wenn Strompreis unter netzlade_preisschwelle ********\n")

        # 2.) alle Stunden in denen der Akku reicht auf 0 setzen, größte zuerst
        self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W, 1, Stundenteile)
        Zeilen = len(pv_data_charge)
        while Zeilen > 0:
            max_index = -1
            max_preis = -1
            Akkustand = -1
            zeile_min_soc = min(pv_data_charge, key=lambda x: x[4])
            # Suche nach dem größten Preis mit Spalte 5 = -0.01
            for index, item in enumerate(pv_data_charge):
                if item[5] == -0.01 and item[3] > max_preis:
                    Verbrauch = item[2] - item[1]
                    max_preis = item[3]
                    max_index = index
            # Bewertung auf 0 setzen, wenn Akkustand reicht oder PV > Verbrauch, sonst -0.1
            kleinster_SOC_nach_max_price = min(([zeile for zeile in pv_data_charge if zeile[0] >= pv_data_charge[max_index][0]]), key=lambda x: x[4])
            if(self.dyn_print_level >= 4): print("++ kleinster_SOC_nach_max_price", kleinster_SOC_nach_max_price)
            if kleinster_SOC_nach_max_price[4] - Verbrauch > minimum_batterylevel:
                pv_data_charge[max_index][5] = 0
            else:
                pv_data_charge[max_index][5] = -0.1 

            self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W, 1, Stundenteile)

            if(self.dyn_print_level >= 4):
                headers = ["Ladezeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Akku ("+str(current_charge_Wh)+"W)", "Ladewert"]
                self.listAStable(headers, pv_data_charge, '++')

            Zeilen -= 1

        # 3.) nächster Schritt Alle Zeiten mit -0.1 auf Zwangsladung oder Ladestopp prüfen
        self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W, 1, Stundenteile)
        Zeilen = sum(1 for row in pv_data_charge if len(row) > 5 and row[5] == -0.1)
        SOC_ueber_Min = 0
        while Zeilen > 0:
            # Wenn kleinster SOC nicht erreicht Überschuss merken
            zeile_min_soc = min(pv_data_charge, key=lambda x: x[4])
            SOC_ueber_Min_tmp = zeile_min_soc[4]-minimum_batterylevel
            SOC_ueber_Min = SOC_ueber_Min_tmp
            if(self.dyn_print_level >= 3): print(">> Differenz zu minimalem SOC => SOC_ueber_Min: ", SOC_ueber_Min)
            max_ladewert = charge_rate_kW * -1
            zeile_max_price_Ladewert = 0
            if(self.dyn_print_level >= 3):
                headers = ["Ladezeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Akku ("+str(current_charge_Wh)+"W)", "Ladewert"]
                self.listAStable(headers, pv_data_charge, '>>')
            # größten Preis wenn Spalte 5 noch -0.1 ist, also noch nicht behandelt
            max_gefilterte_zeilen = [zeile for zeile in pv_data_charge if zeile[5] == -0.1]
            if max_gefilterte_zeilen:
                zeile_max_price = max(max_gefilterte_zeilen, key=lambda x: x[3])
                if(self.dyn_print_level >= 3): print(">> \n>> zeile_max_price: ", zeile_max_price) 
    
            # Wenn zeile_max_price vorhanden, Batterieladung dafür suchen
            if zeile_max_price:
                zeile_max_price_Ladewert = -1
                max_akkustand = battery_capacity_Wh - charge_rate_kW * 0.25
                kleiner_gefilterte_zeilen = [zeile for zeile in pv_data_charge if zeile[0] < zeile_max_price[0] and zeile[4] < max_akkustand and zeile[5] != -1 and zeile[5] > charge_rate_kW * -1 and zeile_max_price[3] > zeile[3]]
                kleinster_SOC_nach_max_price = min(([zeile for zeile in pv_data_charge if zeile[0] >= zeile_max_price[0]]), key=lambda x: x[4])
                laden = 0
                if kleinster_SOC_nach_max_price[4] - zeile_max_price[2] + zeile_max_price[1] < minimum_batterylevel: laden = 1
                if(self.dyn_print_level >= 3): print(">> kleinster_SOC_nach_max_price, laden:", kleinster_SOC_nach_max_price, laden)

                if kleiner_gefilterte_zeilen and laden == 1:
                    if(self.dyn_print_level >= 3): print(">> ======== LADEN =======\n>> kleiner_gefilterte_zeilen für profit_price: ", kleiner_gefilterte_zeilen) 
                    zeile_min_price = min(kleiner_gefilterte_zeilen, key=lambda x: x[3])
                    # Laden nur wenn profitabel
                    profit_price = round(zeile_min_price[3] * (1+(Akku_Verlust_Prozent/100)) + Gewinnerwartung_kW, 4)
                    zeilen_index = next((i for i, row in enumerate(pv_data_charge) if zeile_min_price[0] in row))
                    if(zeile_max_price[3] > profit_price):
                        # Bei Ladung wird Verbrauch auch aus Netz gezogen + Ladeverlust anbringen
                        min_net_power = pv_data_charge[zeilen_index][1] - pv_data_charge[zeilen_index][2]
                        # Hier noch PV-Ladung auf max_batt_dyn_ladung des Akku begrenzen
                        if min_net_power > charge_rate_kW: min_net_power = charge_rate_kW

                        # Ladewert sollte nur so groß wie der Verbrauch sein
                        if pv_data_charge[zeilen_index][5] < 0:
                            max_ladewert_grenze_tmp = zeile_max_price[1] - zeile_max_price[2]
                        else:
                            max_ladewert_grenze_tmp = zeile_max_price[1] - zeile_max_price[2] - pv_data_charge[zeilen_index][1] + pv_data_charge[zeilen_index][2]

                        # Abweichung vom SOC-Minimum berücksichtigen
                        max_ladewert_grenze_tmp += SOC_ueber_Min
                        # Hier noch Ladeverlust addieren
                        max_ladewert_ohne_Ladeverlust = max_ladewert_grenze_tmp
                        max_ladewert_grenze_tmp = int(max_ladewert_grenze_tmp * (1 + (Akku_Verlust_Prozent/200)))

                        # wenn die eingesparte Energie schon höher ist als die benötigte
                        if max_ladewert_grenze_tmp > 0: 
                            if pv_data_charge[zeilen_index][5] > -2:
                                max_ladewert_grenze_tmp = -2
                            else:
                                max_ladewert_grenze_tmp = 0

                        max_ladewert_grenze = int(max_ladewert_grenze_tmp )

                        if(self.dyn_print_level >= 3): print(">> Ladepunkt gefunden", zeile_max_price[3], ">", profit_price, pv_data_charge[zeilen_index],\
                                                            "\n>> Ladung ohne und mit Laderverlust", max_ladewert_ohne_Ladeverlust, max_ladewert_grenze, "\n>> ")
                        if max_ladewert_grenze > -1 or max_ladewert > charge_rate_kW * -1: max_ladewert = -1
                        if max_ladewert_grenze > max_ladewert: max_ladewert = max_ladewert_grenze
                        if pv_data_charge[zeilen_index][5] + max_ladewert > charge_rate_kW * -1:
                            pv_data_charge[zeilen_index][5] = round(pv_data_charge[zeilen_index][5] + max_ladewert)
                            zeile_max_price_Ladewert = 0
                        else:
                            # Wenn die Summe der Zwangsladungen größer als charge_rate_kW 
                            if(self.dyn_print_level >= 3): print(">> charge_rate_kW + pv_data_charge[zeilen_index][5] + max_ladewert_grenze",charge_rate_kW , pv_data_charge[zeilen_index][5] , max_ladewert_grenze)
                            if(self.dyn_print_level >= 3): print(">> SOC_ueber_Min:", SOC_ueber_Min)
                            pv_data_charge[zeilen_index][5] = charge_rate_kW * -1
                            zeile_max_price_Ladewert = -0.1

                    else:
                        if(self.dyn_print_level >= 3): print(">> Kein profitabler Preis gefunden:", zeile_max_price[3], ">", profit_price, pv_data_charge[zeilen_index]) 
                        if(self.dyn_print_level >= 3): print(">> \n>>  ======== STOPPEN =======") 
                        # Hier kleisten Preis der eine Entladung, und keinen PV-Überschuss hat suchen, sonnst kann man nichts einsparen
                        # Nur Preise die kleiner zeile_max_price[3]
                        kleiner_gefilterte_zeilen = [zeile for zeile in pv_data_charge if zeile[0] < zeile_max_price[0] and zeile[5] != -1 and zeile[5] >= -0.1 and zeile[1] - zeile[2] < 0 and zeile_max_price[3] > zeile[3]]
                        if kleiner_gefilterte_zeilen:
                            if(self.dyn_print_level >= 3): print(">> kleiner_gefilterte_zeilen für Ladestopp: ", kleiner_gefilterte_zeilen) 
                            zeile_min_price = min(kleiner_gefilterte_zeilen, key=lambda x: x[3])
                            zeilen_index_min_price = next((i for i, row in enumerate(pv_data_charge) if zeile_min_price[0] in row))
    
                            # Prüfen, welche Verbrauch am größten ist
                            max_price_verbrauch = zeile_max_price[2] - zeile_max_price[1]
                            if pv_data_charge[zeilen_index_min_price][5] == 0:
                                kleiner_price_verbrauch = pv_data_charge[zeilen_index_min_price][2] - pv_data_charge[zeilen_index_min_price][1]
                            else:
                                kleiner_price_verbrauch = 0
        
                            if(self.dyn_print_level >= 3): print(">> \n>> max_price_verbrauch, kleiner_price_verbrauch, SOC_ueber_Min:",max_price_verbrauch, kleiner_price_verbrauch, SOC_ueber_Min) 
                            # Wenn noch genügend Platz zum SOC-Minimum, Zeile auf entladen.
                            if SOC_ueber_Min > max_price_verbrauch:
                                SOC_ueber_Min -= max_price_verbrauch
                                zeile_max_price_Ladewert = 0
                            elif SOC_ueber_Min + kleiner_price_verbrauch > max_price_verbrauch:
                                zeile_max_price_Ladewert = 0
                                pv_data_charge[zeilen_index_min_price][5] = -1
                                if(self.dyn_print_level >= 3): print(">> hier Entladung stoppen: ",pv_data_charge[zeilen_index_min_price])
                            else:
                                zeile_max_price_Ladewert = -0.1
                                pv_data_charge[zeilen_index_min_price][5] = -1
                                if(self.dyn_print_level >= 3): print(">> hier Entladung stoppen: ",pv_data_charge[zeilen_index_min_price])
                        else:
                            if(self.dyn_print_level >= 3): print(">> \n>> Kein kleinerer Preis für Ladestopp gefunden!\n>> ") 

                else:
                    if(self.dyn_print_level >= 3): print(">> \n>> Kein kleinerer Preis gefunden, oder Laden nicht nötig!\n>> ") 
                    # Wenn gemerkte Energie größer als Verbrauch, dann 0 setzen
                    if SOC_ueber_Min >  zeile_max_price[2]: zeile_max_price_Ladewert = 0
                    if laden == 0: zeile_max_price_Ladewert = 0
                        
                        
            # Finde Index der Zeile mit dem gesuchten Wert
            zeilen_index_max_price = next((i for i, row in enumerate(pv_data_charge) if zeile_max_price[0] in row))
            pv_data_charge[zeilen_index_max_price][5] = zeile_max_price_Ladewert
            # Akkustände neu berechnen
            self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W, 1, Stundenteile)

            Zeilen = sum(1 for row in pv_data_charge if len(row) > 5 and row[5] == -0.1)

        return(pv_data_charge)


    # Strompreise in SQLite_DB speichern
    def save_Strompreise(self, database, strompreise, priceforecast):
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
    
        # Wenn Datenbanktabelle strompreise noch nicht existiert, anlegen
        zeiger.execute("""
        CREATE TABLE IF NOT EXISTS strompreise (
        Zeitpunkt DATETIME PRIMARY KEY,
        Bruttopreis REAL,
        Boersenpreis REAL
        )""")
        # Index auf Zeitpunkt erzeugen, wegen Geschwindigkeit
        zeiger.execute(""" CREATE INDEX IF NOT EXISTS idx_strompreise_zeitpunkt ON strompreise(Zeitpunkt)""")

        # Löschen aller Einträge für heute und morgen
        # damit Umstellung von viert- auf stündlich funktioniert
        heute = datetime.today()
        morgen = heute + timedelta(days=1)
        zeiger.execute(
            "DELETE FROM strompreise WHERE Zeitpunkt BETWEEN ? AND ?",
            (heute.strftime('%Y-%m-%d 00:00:00'),
             morgen.strftime('%Y-%m-%d 23:59:59'))
        )

        # auch in priceforecast Werte von heute und morgen loeschen
        zeiger.execute(
            "DELETE FROM priceforecast WHERE Zeitpunkt BETWEEN ? AND ?",
            (heute.strftime('%Y-%m-%d 00:00:00'),
             morgen.strftime('%Y-%m-%d 23:59:59'))
        )

        # Daten einfügen oder aktualisieren
        for entry in strompreise:
            zeiger.execute('''
                INSERT INTO strompreise (Zeitpunkt, Bruttopreis, Boersenpreis)
                VALUES (?, ?, ?)
                ON CONFLICT(Zeitpunkt) DO UPDATE SET
                Bruttopreis = excluded.Bruttopreis,
                Boersenpreis = excluded.Boersenpreis
            ''', entry)

        # Wenn Datenbanktabelle priceforecast noch nicht existiert, anlegen
        zeiger.execute("""
        CREATE TABLE IF NOT EXISTS priceforecast (
        Zeitpunkt DATETIME PRIMARY KEY,
        PV_Prognose INT,
        PrognNetzverbrauch INT,
        PrognNetzladen INT,
        PrognBattStatus FLOAT
        )""")

        zeiger.executemany("""
        INSERT INTO priceforecast (Zeitpunkt, PV_Prognose, PrognNetzverbrauch, PrognNetzladen, PrognBattStatus)
        VALUES (?, ?, ?, ?, ?);
        """, priceforecast)

        verbindung.commit()
        verbindung.close()
    
        return ()
