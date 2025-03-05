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
            if(self.dyn_print_level >= 2):
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

        # API-URL mit Parameter
        url = "https://api.energy-charts.info/price?bzn={}&start={}&end={}".format(BZN, start_time, end_time)
        timeout_sec = 10
        # Nur für die Entwicklung
        # if(self.dyn_print_level >= 5): timeout_sec = 1
        
        try:
            apiResponse = requests.get(url, timeout=timeout_sec)
            apiResponse.raise_for_status()
            if apiResponse.status_code != 204:
                json_data1 = dict(json.loads(apiResponse.text))
            else:
                print("### ERROR:  Keine Strompreise von api.energy-charts.info")
                exit()
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout, keine Strompreise von api.energy-charts.info")
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
        # Wenn keine Maximaler Zwangsladung-SOC (0) Akkukapazität setzen.
        if max_batt_dyn_ladung_W == 0: max_batt_dyn_ladung_W = battery_capacity_Wh
        # Ladestand für alle Zeiten neu berechnen
        for Akkustatus in pv_data_charge:
            min_net_power = Akkustatus[1] - Akkustatus[2]
            if min_net_power > charge_rate_kW: min_net_power = charge_rate_kW
            if Akkustatus[5] < 0:
                # Wenn PV-Produktion größer Zwangsladung, PV-Produktion zum SOC.
                if int(Akkustatus[5] * -1) < min_net_power:
                    akku_soc += min_net_power
                else:
                    akku_soc += int((Akkustatus[5] * -1) / (1 + (Akku_Verlust_Prozent/200)))
            else:
                if min_net_power > 0:
                    akku_soc += min_net_power
                else:
                    akku_soc += int(min_net_power * (1 + (Akku_Verlust_Prozent/200)))
                    

            # Akustand muss minimal unter minimum_batterylevel sein
            if akku_soc < minimum_batterylevel: akku_soc = int(minimum_batterylevel*0.99)
            # Akku nochmal auf Maximum begrenzen
            if akku_soc > battery_capacity_Wh: akku_soc = battery_capacity_Wh
            Akkustatus[4] = akku_soc

        return(pv_data_charge)

    def get_charge_stop(self, pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, current_charge_Wh):
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        Gewinnerwartung_kW = basics.getVarConf('dynprice','Gewinnerwartung_kW', 'eval')
        max_batt_dyn_ladung = basics.getVarConf('dynprice','max_batt_dyn_ladung', 'eval')
        max_batt_dyn_ladung_W = int(battery_capacity_Wh * max_batt_dyn_ladung / 100)
        self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W)
        # Ladewert ist -1 wenn kein Profilabler Preis
        max_ladewert = charge_rate_kW * -1

        # 1.) alle Stunden in denen der Akku reicht auf 0 setzen, größte zuerst
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

            self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W)

            if(self.dyn_print_level >= 4):
                headers = ["Ladezeitpunkt", "PV_Prognose (W)", "Verbrauch (W)", "Strompreis (€/kWh)", "Akku ("+str(current_charge_Wh)+"W)", "Ladewert"]
                self.listAStable(headers, pv_data_charge, '++')

            Zeilen -= 1

        # 2.) nächster Schritt Alle Zeten mit -0.1 auf Zwangsladung oder Ladestopp prüfen
        self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W)
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
                        # Hier noch Ladeverlust addieren  #entWIGGlung
                        max_ladewert_ohne_Ladeverlust = max_ladewert_grenze_tmp
                        max_ladewert_grenze_tmp = int(max_ladewert_grenze_tmp * (1 + (Akku_Verlust_Prozent/200)))  #entWIGGlung 

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
            self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W)

            Zeilen = sum(1 for row in pv_data_charge if len(row) > 5 and row[5] == -0.1)

        return(pv_data_charge)


    # Strompreise in SQLite_DB speichern
    def save_Strompreise(self, database, strompreise):
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
    
        # Wenn Datenbanktabelle noch nicht existiert, anlegen
        zeiger.execute("""
        CREATE TABLE IF NOT EXISTS strompreise (
        Zeitpunkt DATETIME PRIMARY KEY,
        Bruttopreis REAL,
        Boersenpreis REAL
        )""")

        # Daten einfügen oder aktualisieren
        for entry in strompreise:
            zeiger.execute('''
                INSERT INTO strompreise (Zeitpunkt, Bruttopreis, Boersenpreis)
                VALUES (?, ?, ?)
                ON CONFLICT(Zeitpunkt) DO UPDATE SET
                Bruttopreis = excluded.Bruttopreis,
                Boersenpreis = excluded.Boersenpreis
            ''', entry)

    
        verbindung.commit()
        verbindung.close()
    
        return ()
