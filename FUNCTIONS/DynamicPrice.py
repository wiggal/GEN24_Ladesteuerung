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
        # Verbrauch je Stunde = Zähler-Differenz auf die erfasste Zeit hochgerechnet (mittlere Leistung in W), Stunden mit < 30 Minuten Daten zählen nicht
        sql_anweisung = """
        WITH differenzen AS (
			select Zeitpunkt AS volle_stunde,
                (max(DC_Produktion) - min(DC_Produktion)) as Produktion,
                (max(Netzverbrauch) - min(Netzverbrauch)) as Netzverbrauch,
                (max(Batterie_IN) - min(Batterie_IN)) as InBatterie,
                (max(Batterie_OUT) - min(Batterie_OUT)) as VonBatterie,
                (max(Einspeisung) - min(Einspeisung)) as Einspeisung,
                (julianday(max(Zeitpunkt)) - julianday(min(Zeitpunkt))) * 1440.0 as minuten
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
                WHEN minuten < 30 THEN NULL   -- zu wenig Messwerte in dieser Stunde
                WHEN ((Netzverbrauch + Produktion - Einspeisung + VonBatterie - InBatterie) * 60.0 / minuten) > """ + str(Lastgrenze) + """ THEN """ + str(Lastgrenze) + """
                ELSE ((Netzverbrauch + Produktion - Einspeisung + VonBatterie - InBatterie) * 60.0 / minuten)
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
            AVG(Verbrauch) > 0
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
            print("Die Datei PV_Daten.sqlite fehlt oder ist leer, zum Erzeugen EnergyController.py aufrufen, Programmende!!")
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
            sql_anweisung = "SELECT Res_Feld1, Zeit, Res_Feld2, Options from steuercodes WHERE Schluessel == 'Lastprofil' AND Res_Feld1 IN (strftime('%w', 'now', 'localtime'), strftime('%w', 'now', 'localtime', '+1 day'));"
            zeiger.execute(sql_anweisung)
            rows = zeiger.fetchall()
        except:
            print("CONFIG/Prog_Steuerung.sqlite fehlt oder ist defekt,\n bitte EnergyController.py ausführen!")
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
        

    def get_pricelist_date_viertel(self, json_data1, provider):
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

        if(self.dyn_print_level >= 3): print("++ Tageszeit_Preisanteil: ", Tageszeit_Preisanteil, "\n") #DEBUG

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
                    pricelist_date.append((time_str, brutto_preis, round(row[1] / 1000, 5)))

        except Exception as e:
            print(f"### WARNUNG: Keine verwertbaren Daten von {provider}: {e}")
            pricelist_date = []

        return(pricelist_date)

    def getPrice_db(self, BZN=None):
        # Kein API-Aufruf, sondern Rückgriff auf die zuletzt in PV_Daten.sqlite
        # gespeicherten Strompreise. Als expliziter, letzter Eintrag in der
        # Preisquelle-Fallback-Kette gedacht, z.B. Preisquelle = energyforecast;energycharts;db
        try:
            verbindung = sqlite3.connect('PV_Daten.sqlite')
            zeiger = verbindung.cursor()
            sql_anweisung = "SELECT * from strompreise WHERE DATE(Zeitpunkt) BETWEEN DATE('now') AND DATE('now', '+1 day');"
            zeiger.execute(sql_anweisung)
            pricelist_date = zeiger.fetchall()
            verbindung.close()
        except Exception as e:
            print(f"### WARNUNG: Zugriff auf PV_Daten.sqlite/strompreise fehlgeschlagen: {e}")
            pricelist_date = []

        if pricelist_date == []:
            print("### WARNUNG: In der DB sind auch keine aktuellen Strompreise vorhanden!")

        return(pricelist_date)

    def getPrice_smard_api(self, BZN):
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

        #DEBUG
        if(self.dyn_print_level >= 2): 
            print("++ ", url)
            print("++  BZN = ", BZN, "; Gebietsfilter = ", Gebietsfilter, "; resolution = ", resolution, "\n")

        timeout_sec = 30
        Push_Schreib_Ausgabe = ''
        
        json_data1 = {}
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
        heute_start = datetime.now().date()
        pricelist_date_tmp = self.get_pricelist_date_viertel(json_data1, 'smard.api')
        # neue Liste mit allen Einträgen ab heute
        pricelist_date = [
                    entry for entry in pricelist_date_tmp
                    if datetime.strptime(entry[0], "%Y-%m-%d %H:%M:%S").date() >= heute_start ]

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

        #DEBUG
        if(self.dyn_print_level >= 2): 
            print("\n++ ", url)
            print("++  BZN = ", BZN, "; resolution = ", resolution, "\n")

        timeout_sec = 30
        Push_Schreib_Ausgabe = ''
        
        json_data1 = {}
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
        pricelist_date = self.get_pricelist_date_viertel(json_data1, 'api.energy-charts.info')
        # wenn resolution == hour Mittelwerte bilden
        if(resolution == 'hour'):
            pricelist_date = self.get_stuendliches_mittel(pricelist_date)

        return(pricelist_date)

    def getPrice_energyforecast(self, BZN='DE-LU'):
        # Kostenlose Free-Stufe von energyforecast.de: EPEX SPOT Day-Ahead + Prognose,
        # bis zu 2 Tage im Voraus, 50 Requests/Tag. API-Key unter energyforecast.de -> API Keys anlegen
        # und in der Config unter [dynprice] als 'energyforecast_token' hinterlegen.
        # BZN entspricht dem 'domain'-Parameter von energyforecast.de: DE-LU, AT, FR, NL, BE, PL, DK1, DK2
        api_token = basics.getVarConf('dynprice','energyforecast_token', 'str')
        # Token nie im Klartext ausgeben (Debug-Ausgabe, Fehlermeldungen, Push-Nachricht)
        def maskiere(text):
            text = str(text)
            return text.replace(api_token, '***') if api_token else text

        # lokale resolution-Einstellung ('hour' / 'quarter_hour') auf das API-Enum abbilden
        resolution_cfg = basics.getVarConf('dynprice','resolution', 'str')
        resolution = 'HOURLY' if resolution_cfg == 'hour' else 'QUARTER_HOURLY'

        # fixed_cost_cent und vat bewusst auf 0 gesetzt: die API liefert dann den reinen
        # EPEX-Preis (ct/kWh), Netzentgelte/Tagesanteil/MwSt werden wie bei den anderen
        # Providern zentral in get_pricelist_date_viertel() berechnet
        url = "https://www.energyforecast.de/api/v1/predictions/next_48_hours?token={}&fixed_cost_cent=0&vat=0&resolution={}&domain={}".format(api_token, resolution, BZN)

        #DEBUG
        if(self.dyn_print_level >= 2):
            print("\n++ ", maskiere(url))
            print("++  BZN = ", BZN, "; resolution = ", resolution, "\n")

        timeout_sec = 30
        Push_Schreib_Ausgabe = ''

        json_data1 = {}
        try:
            apiResponse = requests.get(url, timeout=timeout_sec)
            apiResponse.raise_for_status()
            if apiResponse.status_code != 204:
                raw = json.loads(apiResponse.text)
                # erwartetes Format: [{"start": "2025-01-20T13:00:00.000000+01:00", "end": "...", "price": 0.0823}, ...]
                # (price in EUR/kWh bei fixed_cost_cent=0&vat=0) -> in unix_seconds/EUR-MWh für
                # get_pricelist_date_viertel() umwandeln (Faktor 1000: EUR/kWh -> EUR/MWh)
                unix_seconds = []
                prices = []
                for eintrag in raw:
                    dt = datetime.strptime(eintrag['start'], "%Y-%m-%dT%H:%M:%S.%f%z")
                    unix_seconds.append(int(dt.timestamp()))
                    prices.append(eintrag['price'] * 1000)
                json_data1 = {
                    "license_info": "energyforecast.de (EPEX SPOT Day-Ahead + Prognose)",
                    "unix_seconds": unix_seconds,
                    "price": prices
                }
            else:
                Ausgabe = "### ERROR:  Keine Strompreise von energyforecast.de"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.Timeout:
                Ausgabe = "### ERROR: Timeout, keine Strompreise von energyforecast.de"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.HTTPError as http_err:
                Ausgabe = maskiere(f"### ERROR: HTTP-Fehler: {http_err} (Status Code: {apiResponse.status_code})")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.RequestException as req_err:
                Ausgabe = maskiere(f"### ERROR: Verbindungsfehler oder andere Probleme: {req_err}")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except (KeyError, ValueError) as parse_err:
                Ausgabe = maskiere(f"### ERROR: Unerwartetes Antwortformat von energyforecast.de: {parse_err}")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe

        # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
        Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
        if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
            Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
            apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
            print("PushMeldung an ", Push_Message_Url, " gesendet.\n")

        # viertelstündliche Netzentgelte addieren
        pricelist_date = self.get_pricelist_date_viertel(json_data1, 'energyforecast.de')

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

    def entladung_werte(self, pv_data_charge, minimum_batterylevel, akku_soc, Stundenteile=1):
        """Entladeleistung der Batterie (W, an Haus und Netz) je Zeile, abgeleitet aus dem geplanten Akkustand (Spalte 4).
        Unterhalb des Mindeststands wird keine Entladung gezählt (die Rundung auf 99 % des Mindeststands ist keine echte Entladung)."""
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        EFF = 1 + Akku_Verlust_Prozent / 200
        if akku_soc < minimum_batterylevel: minimum_batterylevel = akku_soc
        werte = []; vorher = akku_soc
        for zeile in pv_data_charge:
            if vorher > minimum_batterylevel and zeile[4] < vorher:
                werte.append(int((vorher - zeile[4]) * Stundenteile / EFF))
            else:
                werte.append(0)
            vorher = zeile[4]
        return werte

    @staticmethod
    def teile_zahlen(wert):
        """Zerlegt einen ENTLadeStrg-Wert (eine Zahl oder viertelstündlich 'a;b;c;d') in eine Liste von Zahlen; Leeres/Ungültiges wird 0."""
        if wert is None: return [0.0]
        zahlen = []
        for teil in str(wert).split(';'):
            try:
                zahlen.append(float(teil))
            except ValueError:
                zahlen.append(0.0)
        return zahlen

    @staticmethod
    def teil_fuer_slot(teile, zeitpunkt, Stundenteile, stunde='min'):
        """Wert aus der Liste teile (siehe teile_zahlen) für den Planungsslot 'JJJJ-MM-TT HH:MM:SS'.
        Eine Zahl gilt für die ganze Stunde, mehrere Zahlen teilen die Stunde gleichmäßig auf (wie get_FesteEntladegrenze im Controller).
        Bei Stundenauflösung (Stundenteile = 1) werden die Werte zusammengefasst: stunde='min' = kleinster Wert (Zwangsladung/Stopp),
        stunde='mittel' = Durchschnitt (Leistung)."""
        if len(teile) == 1: return teile[0]
        if Stundenteile == 1:
            return min(teile) if stunde == 'min' else sum(teile) / len(teile)
        index = min(len(teile) - 1, int(int(zeitpunkt[14:16]) // (60 / len(teile))))
        return teile[index]

    @staticmethod
    def steuercode_aktion(res_feld1, res_feld2, options=None):
        """Kurztext für das Protokoll: was bedeutet der Eintrag in ENTLadeStrg (Einspeisung, Zwangsladung, Entladestopp ...).
        Ist options angegeben und nicht 'DynPrice', wurde der Eintrag von Hand gesetzt und bekommt den Zusatz '(manuell)'."""
        r1 = dynamic.teile_zahlen(res_feld1)          # Verbrauchsgrenze bzw. Einspeisung (negativ), evtl. viertelstündlich
        werte = dynamic.teile_zahlen(res_feld2)       # Feste Entladegrenze bzw. Zwangsladung (negativ), evtl. viertelstündlich
        laden = [w <= -2 for w in werte]; stopp = [w == -1 for w in werte]
        manuell = options is not None and options != 'DynPrice'
        einspeisung = [w < 0 for w in r1]
        teilweise = False
        # Bei manuellen Einträgen steht die Leistung schon in der Spalte Verbrauchsgrenze, daher ohne Wattangabe
        if any(einspeisung):
            text = "Einspeisung" if manuell else "Einspeisung %d W" % int(-min(r1))
            teilweise = not all(einspeisung)
        elif all(laden): text = "Zwangsladung"
        elif any(laden): text = "Zwangsladung"; teilweise = True
        elif all(stopp): text = "Entladestopp"
        elif any(stopp): text = "Entladestopp"; teilweise = True
        elif any(w > 0 for w in werte): text = "feste Entladegrenze"
        elif any(w > 0 for w in r1): text = "Verbrauchsgrenze"
        else: text = ""
        zusaetze = (["teilweise"] if teilweise else []) + (["manuell"] if text and manuell else [])
        if text and zusaetze: text += " (" + ", ".join(zusaetze) + ")"
        return text

    def akkustand_neu(self, pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, max_batt_dyn_ladung_W=0, mitPV=1, Stundenteile=1, einspeisung=None):
        # Ladeverlust beim Berechnen des Akuu-SOC berücksichtigen
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        netzlade_preisschwelle = basics.getVarConf('dynprice','netzlade_preisschwelle', 'eval')
        # Falls der Akku-SOC kleiner als minimum_batterylevel => akku_soc
        if akku_soc < minimum_batterylevel: minimum_batterylevel = akku_soc
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
            akku_soc_vorher = akku_soc
            # Einspeisung aus dem Akku ins Netz (Leistung in W, versorgt zuerst das Haus)
            feedP = einspeisung.get(Akkustatus[0], 0) if einspeisung else 0
            if feedP > 0:
                akku_soc -= int(feedP * (1 + (Akku_Verlust_Prozent/200)) / Stundenteile)
            elif Ladewert_tmp < 0:
                # Wenn PV-Produktion größer Zwangsladung, PV-Produktion zum SOC.
                if int(Akkustatus[5] * -1) < min_net_power:
                    akku_soc += int(min_net_power / Stundenteile)
                else:
                    akku_soc += int(((Akkustatus[5] * -1) / (1 + (Akku_Verlust_Prozent/200))) / Stundenteile)
                    # Zwangsladung aus dem Netz nur bis max_batt_dyn_ladung (Wh) rechnen.
                    # -1 = Entladestopp, -0.1/-0.01 = Marker => keine Netzladung
                    if Akkustatus[5] < -1 and akku_soc > max_batt_dyn_ladung_W:
                        akku_soc = max(akku_soc_vorher, max_batt_dyn_ladung_W)
            else:
                if min_net_power > 0:
                    akku_soc += int(min_net_power / Stundenteile)
                else:
                    akku_soc += int((min_net_power * (1 + (Akku_Verlust_Prozent/200))) / Stundenteile)
                    

            # Akustand muss minimal unter minimum_batterylevel sein
            if akku_soc < minimum_batterylevel: 
                akku_soc = int(minimum_batterylevel*0.99)
            # Akku nochmal auf Maximum begrenzen
            if akku_soc > battery_capacity_Wh: akku_soc = battery_capacity_Wh
            Akkustatus[4] = akku_soc

        return(pv_data_charge)

    def getPrice_awattar(self, BZN):
        import yaml
        resolution = basics.getVarConf('dynprice','resolution', 'str') 
        # --- Gebietsfilter bestimmen ---
        if BZN.upper() == 'DE-LU':
            Gebietsfilter = 'de'
        elif BZN.upper() == 'AT':
            Gebietsfilter = 'at'
        else:
            raise ValueError(f"Fehlerhaftes BZN '{BZN}'. Erlaubt sind 'AT' oder 'DE-LU'.")

        url = f"https://api.awattar.{Gebietsfilter}/v1/marketdata/current.yaml?tomorrow=include"

        if(self.dyn_print_level >= 2): 
            print("++ ", url)
            print("++  BZN = ", BZN, "; Gebietsfilter = ", Gebietsfilter, "; resolution = ", resolution, "\n")

        data = {}
        result = {}
        Push_Schreib_Ausgabe = ""
        try:
            # --- API-Abruf ---
            r = requests.get(url)
            r.raise_for_status()
            if r.status_code != 204:
                # --- YAML statt JSON laden ---
                data = yaml.safe_load(r.text)
                # --- Aktuelle Stunde bestimmen ---
                date_now = data.get("date_now")
                if not isinstance(date_now, datetime):
                    date_now = datetime.strptime(str(date_now), "%Y-%m-%d %H:%M:%S")
                current_hour = date_now.replace(minute=0, second=0, microsecond=0)

                # --- Viertelstundenpreise aus relativen Werten ---
                unix_seconds = []
                prices = []

                # Verwende range, um großzügig heutige + morgige Stunden zu erfassen
                for offset in range(-24, 48):
                    key = f"data_price_hour_rel_{offset:+03d}_amount"
                    if key in data:
                        price_eur_per_kwh = data[key] / 100.0  # Cent/kWh → €/kWh
                        hour_time = current_hour + timedelta(hours=offset)
                        # 4 Viertelstunden pro Stunde
                        for q in range(4):
                            ts = hour_time + timedelta(minutes=15*q)
                            unix_seconds.append(int(ts.timestamp()))
                            prices.append(round(price_eur_per_kwh * 1000, 2))  # €/MWh

                result = {
                    'license_info': 'CC BY 4.0 (creativecommons.org/licenses/by/4.0) from Bundesnetzagentur | SMARD.de',
                    'unix_seconds': unix_seconds,
                    'price': prices,
                    'unit': 'EUR / MWh',
                    'deprecated': False
                }
            else:
                Ausgabe = "### ERROR:  Keine Strompreise von api.awattar"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.Timeout:
                Ausgabe = "### ERROR: Timeout, keine Strompreise von api.awattar"
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except requests.exceptions.HTTPError as http_err:
                Ausgabe = (f"### ERROR: HTTP-Fehler: {http_err} (Status Code: {r.status_code})")
                print(Ausgabe)
                Push_Schreib_Ausgabe += Ausgabe
        except Exception as e:
            Ausgabe = f"### ERROR: Verbindungsfehler oder andere Probleme: {e}"
            print(Ausgabe)
            Push_Schreib_Ausgabe += Ausgabe


        # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
        Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
        if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
            Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
            apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
            print("PushMeldung an ", Push_Message_Url, " gesendet.\n")
            #DEBUG


        # viertelstündliche Netzentgelte addieren
        pricelist_date = self.get_pricelist_date_viertel(result, 'awattar')

        # wenn resolution == hour Mittelwerte bilden
        if(resolution == 'hour'):
            pricelist_date = self.get_stuendliches_mittel(pricelist_date)

        return (pricelist_date)


    def conf_opt(self, key, default, typ='eval'):
        # Optionalen Wert aus [dynprice] lesen; fehlt er in der ini, gilt der Standardwert
        try:
            wert = basics.getVarConf('dynprice', key, typ)
        except (Exception, SystemExit):
            return default
        return default if wert is None or wert == '' else wert

    def get_morgen_ziel(self, pv_data_charge, weatherdata, Lastprofil, minimum_batterylevel, akku_soc, charge_rate_kW,
                        battery_capacity_Wh, ziel_prozent, min_gewinn_Wh=0, einspeisegrenze_W=None):
        """Bestimmt den Sonnenaufgang der nächsten Nacht im Planungshorizont, bis zu dem der Akku auf ziel_prozent geleert
        sein soll, damit PV-Überschuss oberhalb der Einspeisegrenze aufgenommen werden kann. Mit min_gewinn_Wh = 0 gilt das
        Ziel immer, mit min_gewinn_Wh > 0 nur, wenn dadurch mindestens so viel PV-Überschuss mehr aufgenommen wird.
        Rückgabe (info, text); info = None wenn nicht anwendbar.
        info = {'idx', 'zeit', 'ziel_wh', 'verlust_voll_Wh', 'verlust_ziel_Wh', 'gewinn_Wh'}"""
        if not pv_data_charge: return None, "keine Planungsdaten"
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        EFF = 1 + Akku_Verlust_Prozent / 200
        CAP = battery_capacity_Wh
        lo = min(minimum_batterylevel, akku_soc)
        ziel_wh = max(CAP * ziel_prozent / 100.0, lo)
        # 1) Nacht suchen (mind. 2 Stunden PV <= 50 W), dann erster Slot mit PV > Verbrauch = Beginn des Überschusses
        quarter = any(z[0][14:16] != "00" for z in pv_data_charge)
        min_rows = 2 * (4 if quarter else 1)
        low_run = 0; night_seen = False; idx = None; erstes_licht = None
        for i, z in enumerate(pv_data_charge):
            if z[1] <= 50:
                low_run += 1
                # Beginnt der Horizont in der Dunkelheit (z.B. Lauf um 5 Uhr), zählt das schon als Nacht
                if low_run >= min_rows or i == 0: night_seen = True
            else:
                if night_seen and erstes_licht is None: erstes_licht = i
                if night_seen and z[1] > z[2]:
                    idx = i; break
                low_run = 0
        if idx is None and night_seen:
            # Kein PV-Überschuss im Horizont: erstes Licht, sonst Ende des Horizonts (= Morgen)
            idx = erstes_licht if erstes_licht is not None else len(pv_data_charge) - 1
        if idx is None: return None, "keine Nacht im Planungshorizont gefunden"
        zeit = pv_data_charge[idx][0]
        if min_gewinn_Wh <= 0:
            # Ziel gilt immer: keine Wirtschaftlichkeitsprüfung, daher auch keine Einspeisegrenze/Wetterdaten/Lastprofil nötig
            info = {'idx': idx, 'zeit': zeit, 'ziel_wh': ziel_wh, 'verlust_voll_Wh': None, 'verlust_ziel_Wh': None, 'gewinn_Wh': None}
            return info, f"Sonnenaufgang {zeit[11:16]}, Ziel {int(ziel_wh)} Wh ({int(round(ziel_wh / CAP * 100))} %): Morgen-Ziel aktiv (feste Vorgabe)"
        if einspeisegrenze_W is None: return None, "Einspeisegrenze unbekannt (Einspeisegrenze_W oder [Ladeberechnung] Einspeisegrenze setzen)"
        try:
            watts = weatherdata['result']['watts']
        except (KeyError, TypeError):
            return None, "keine PV-Prognose für den nächsten Tag"
        datum = pv_data_charge[idx][0][:10]
        h0 = int(pv_data_charge[idx][0][11:13])
        # 2) Verbrauch des Tages aus dem Lastprofil (Wochentag wie im Check: Sonntag = 0)
        try:
            wd = (datetime.strptime(datum, "%Y-%m-%d").weekday() + 1) % 7
        except ValueError:
            return None, "ungültiges Datum"
        verbr = {}
        for row in Lastprofil or []:
            try:
                if int(row[0]) == wd: verbr[int(row[1][:2])] = float(row[2])
            except (TypeError, ValueError, IndexError):
                continue
        if not verbr and Lastprofil:
            try:
                mittel = sum(float(r[2]) for r in Lastprofil) / len(Lastprofil)
                verbr = {h: mittel for h in range(24)}
            except (TypeError, ValueError, IndexError):
                verbr = {}
        if not verbr: return None, "kein Lastprofil für den nächsten Tag"
        # 3) Tag simulieren: Akku füllt sich mit Überschuss, alles über Akku + Einspeisegrenze geht verloren
        def verlust(s0):
            soc = float(s0); lost = 0.0
            for h in range(h0, 24):
                pv = float(watts.get(f"{datum} {h:02d}:00:00", 0) or 0)
                v = verbr.get(h, 0.0)
                net = pv - v                                   # W über 1 Stunde = Wh
                if net > 0:
                    lade = max(0.0, min(net, charge_rate_kW, CAP - soc))
                    soc += lade
                    lost += max(0.0, (net - lade) - einspeisegrenze_W)
                else:
                    soc -= min(-net * EFF, max(0.0, soc - lo))
            return lost
        v_voll = verlust(CAP); v_ziel = verlust(ziel_wh)
        gewinn = v_voll - v_ziel
        text = (f"Sonnenaufgang {zeit[11:16]}, Ziel {int(ziel_wh)} Wh ({int(round(ziel_wh / CAP * 100))} %), "
                f"PV-Verlust über Einspeisegrenze {int(v_voll)} Wh (Akku voll) / {int(v_ziel)} Wh (Akku auf Ziel) => "
                f"Gewinn {int(gewinn)} Wh")
        if gewinn < min_gewinn_Wh:
            return None, text + f" < {min_gewinn_Wh} Wh: kein Morgen-Ziel nötig"
        return {'idx': idx, 'zeit': zeit, 'ziel_wh': ziel_wh, 'verlust_voll_Wh': v_voll,
                'verlust_ziel_Wh': v_ziel, 'gewinn_Wh': gewinn}, text + ": Morgen-Ziel aktiv"

    def plan_dp(self, pv_data_charge, boerse, minimum_batterylevel, akku_soc, charge_rate_kW,
                battery_capacity_Wh, Stundenteile=1, einspeisen=0, einspeise_max_W=0, restwert='auto',
                ziel_idx=None, ziel_wh=0, ziel_strafe='hart'):
        """Optimale Planung per dynamischer Programmierung (wird von DynamicPriceCheck.py verwendet; get_charge_stop ist das frühere Greedy-Verfahren).
        Wählt je Zeitslot: Entladung frei (0), Entladestopp (-1) oder Zwangsladung (-W) und
        optional Einspeisung Akku->Netz zum Börsenpreis (nur ganze Stunden).
        Kosten = Netzbezug * Bruttopreis - Einspeiseerlös * Börsenpreis (+ Gewinnerwartung_kW je kWh Netzladung);
        der Akkustand am Ende wird mit 'restwert' (EUR/kWh, auto = niedrigster Preis * Verlustfaktor) bewertet.
        Schreibt Ladewert in Spalte 5 und Akkustand in Spalte 4, gibt (pv_data_charge, einspeisung) zurück,
        einspeisung = {Zeitpunkt: Leistung_W}.
        Optional: ziel_idx/ziel_wh = Zeilenindex (Sonnenaufgang) und Ziel-Akkustand in Wh; jede kWh darüber kostet
        ziel_strafe EUR ('hart' = 100, das Ziel gilt unabhängig vom Preis; auto = Mittel der teuersten 25 % der Bruttopreise)."""
        import time as _time
        t_start = _time.time()
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        Gewinnerwartung_kW = basics.getVarConf('dynprice','Gewinnerwartung_kW', 'eval')
        max_batt_dyn_ladung = basics.getVarConf('dynprice','max_batt_dyn_ladung', 'eval')
        EFF = 1 + Akku_Verlust_Prozent / 200
        DT = 1.0 / Stundenteile
        CAP = battery_capacity_Wh
        limit = int(CAP * max_batt_dyn_ladung / 100)
        if limit <= 0 or limit > CAP: limit = CAP
        akku_soc = min(akku_soc, CAP)
        lo = min(minimum_batterylevel, akku_soc)
        n = len(pv_data_charge)
        einspeisung = {}
        for z in pv_data_charge: z[5] = 0
        if n == 0 or CAP - lo < 50:
            self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, limit, 1, Stundenteile)
            return pv_data_charge, einspeisung

        pv = [z[1] for z in pv_data_charge]; cons = [z[2] for z in pv_data_charge]; price = [z[3] for z in pv_data_charge]
        bors = [boerse.get(z[0]) for z in pv_data_charge]
        try:
            restwert_zahl = float(restwert)
        except (TypeError, ValueError):
            restwert_zahl = None                      # 'auto' oder ungültiger Wert => automatisch
        if restwert_zahl is None:
            # Konservativer Restwert: Ersatzkosten, wenn die Energie später zum niedrigsten Preis nachgeladen würde.
            # (Mittelpreis wäre zu optimistisch: der Akku würde nur wegen der Gutschrift am Ende vollgeladen.)
            pterm = min(price) * EFF
        else:
            pterm = restwert_zahl

        def exp_rev(overflow_wh, t):
            # Erlös für PV-Überschuss, der nicht gespeichert werden kann (Börsenpreis, nie negativ gerechnet)
            b = bors[t]
            return overflow_wh / 1000 * max(b, 0.0) if b is not None else 0.0

        def step(soc, t, mode, Pw=0.0):
            d = (cons[t] - pv[t]) * DT                      # Wh Defizit (>0) bzw. Überschuss (<0)
            if mode == 'feed':
                B = min(Pw * DT, max(0.0, soc - lo) / EFF)    # Wh, die der Akku abgibt (nach Verlust)
                used = min(B, max(0.0, d)); export = B - used + max(0.0, -d)
                grid = max(0.0, d) - used
                return soc - B * EFF, grid / 1000 * price[t] - export / 1000 * bors[t]
            if mode == 'charge':
                room = max(0.0, (max(limit, soc) - soc) * EFF)
                inflow = min(Pw * DT, room)
                surplus = max(0.0, -d)
                gridch = max(0.0, inflow - surplus)
                grid = gridch + max(0.0, d)
                extra = max(0.0, surplus - inflow)
                soc_new = min(CAP, soc + inflow / EFF + extra / EFF)
                stored_pv = max(0.0, (soc_new - soc) * EFF - gridch)
                overflow = max(0.0, surplus - stored_pv)          # PV-Überschuss, der nicht in den Akku passt
                return soc_new, grid / 1000 * price[t] + Gewinnerwartung_kW * gridch / 1000 - exp_rev(overflow, t)
            if mode == 'stop':
                if d > 0: return soc, d / 1000 * price[t]
                soc_new = min(CAP, soc + (-d) / EFF)
                return soc_new, -exp_rev(max(0.0, -d - (soc_new - soc) * EFF), t)
            # free
            if d > 0:
                b = min(d, max(0.0, soc - lo) / EFF)
                return soc - b * EFF, (d - b) / 1000 * price[t]
            soc_new = min(CAP, soc + (-d) / EFF)
            return soc_new, -exp_rev(max(0.0, -d - (soc_new - soc) * EFF), t)

        stepwh = max(25.0, (CAP - lo) / 300.0)
        L = int((CAP - lo) / stepwh) + 1
        levels = [lo + i * stepwh for i in range(L)]
        def interp(V, s):
            x = (s - lo) / stepwh
            i = max(0, min(L - 2, int(x))); f = min(1.0, max(0.0, x - i))
            return V[i] * (1 - f) + V[i + 1] * f

        charge_levels = [charge_rate_kW * f for f in (0.25, 0.5, 0.75, 1.0)] if charge_rate_kW > 100 else []
        feed_levels = [einspeise_max_W * f for f in (0.25, 0.5, 0.75, 1.0)] if (einspeisen and einspeise_max_W > 100) else []
        # Einspeisung nur für volle Stunden (der Controller liest Spalte 1 nur je Stunde)
        def block_len(t):
            if Stundenteile == 1: return 1 if bors[t] is not None else 0
            if t + Stundenteile > n: return 0
            h = pv_data_charge[t][0]
            if h[14:16] != "00": return 0
            for k in range(Stundenteile):
                zk = pv_data_charge[t + k][0]
                if zk[:13] != h[:13] or bors[t + k] is None: return 0
            return Stundenteile
        blen = [block_len(t) if feed_levels else 0 for t in range(n)]

        strafe = 0.0
        if ziel_idx is not None and 0 <= ziel_idx < n:
            try:
                strafe = float(ziel_strafe)
            except (TypeError, ValueError):
                if str(ziel_strafe).strip().lower() == 'auto':
                    top = sorted(price)[-max(1, n // 4):]          # wirtschaftlich gewichtet: Mittel der teuersten 25 %
                    strafe = sum(top) / len(top)
                else:
                    strafe = 100.0                                 # 'hart': Ziel gilt unabhängig vom Preis
            ziel_wh = max(float(ziel_wh), float(lo))
        V = [None] * (n + 1)
        V[n] = [-(s - lo) / EFF / 1000 * pterm for s in levels]   # Restwert = Gutschrift (negative Kosten)
        pol = [None] * n
        for t in range(n - 1, -1, -1):
            Vt = []; pt = []
            for s in levels:
                best, ba = 1e18, None
                for mode, Pw in [('free', 0.0), ('stop', 0.0)] + [('charge', p) for p in charge_levels]:
                    sn, c = step(s, t, mode, Pw)
                    if mode == 'charge' and sn - s < 1: continue
                    v = c + interp(V[t + 1], sn)
                    if v < best: best, ba = v, (mode, Pw)
                if blen[t]:
                    for p in feed_levels:
                        sn, c = s, 0.0
                        for k in range(blen[t]):
                            sn, ck = step(sn, t + k, 'feed', p); c += ck
                        if s - sn < max(100.0, 0.5 * p * DT * blen[t] * EFF): continue   # keine 'Phantom-Einspeisung'
                        v = c + interp(V[t + blen[t]], sn)
                        if v < best: best, ba = v, ('feed', p)
                Vt.append(best); pt.append(ba)
            if strafe > 0 and t == ziel_idx:
                # Akkustand zu Beginn des Sonnenaufgangs-Slots: alles über dem Ziel nimmt später keinen PV-Überschuss auf
                Vt = [v + strafe * max(0.0, s - ziel_wh) / EFF / 1000 for v, s in zip(Vt, levels)]
            V[t] = Vt; pol[t] = pt

        # Plan vorwärts abgreifen
        soc = float(akku_soc); t = 0
        while t < n:
            idx = max(0, min(L - 1, int(round((soc - lo) / stepwh))))
            mode, Pw = pol[t][idx]
            if mode == 'feed':
                s_blk = soc
                for k in range(blen[t]):
                    s_blk, _c = step(s_blk, t + k, 'feed', Pw)
                if soc - s_blk >= max(100.0, 0.5 * Pw * DT * blen[t] * EFF):
                    for k in range(blen[t]):
                        einspeisung[pv_data_charge[t + k][0]] = int(Pw)
                    soc = s_blk; t += blen[t]; continue
                mode = 'free'     # Akku kann (wegen Interpolation) die Einspeisung nicht liefern
            if mode == 'charge':
                room = max(0.0, (max(limit, soc) - soc) * EFF)
                P_out = int(min(Pw * DT, room) / DT)          # nie mehr als bis zum Limit laden
                if P_out >= 100:
                    pv_data_charge[t][5] = -P_out
                    soc, _c = step(soc, t, 'charge', P_out)
                else:
                    soc, _c = step(soc, t, 'free')
            elif mode == 'stop':
                pv_data_charge[t][5] = -1
                soc, _c = step(soc, t, 'stop')
            else:
                soc, _c = step(soc, t, 'free')
            t += 1

        self.akkustand_neu(pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, limit, 1, Stundenteile, einspeisung)
        if(self.dyn_print_level >= 1):
            print("DP-Planung: Restwert %.3f EUR/kWh, Einspeisung %s, Rechenzeit %.1f s" % (pterm, "ja" if feed_levels else "nein", _time.time() - t_start))
        return pv_data_charge, einspeisung

    def get_charge_stop(self, pv_data_charge, minimum_batterylevel, akku_soc, charge_rate_kW, battery_capacity_Wh, current_charge_Wh, Stundenteile=1):
        Akku_Verlust_Prozent = basics.getVarConf('dynprice','Akku_Verlust_Prozent', 'eval')
        Gewinnerwartung_kW = basics.getVarConf('dynprice','Gewinnerwartung_kW', 'eval')
        max_batt_dyn_ladung = basics.getVarConf('dynprice','max_batt_dyn_ladung', 'eval')
        netzlade_preisschwelle = basics.getVarConf('dynprice','netzlade_preisschwelle', 'eval')
        max_batt_dyn_ladung_W = int(battery_capacity_Wh * max_batt_dyn_ladung / 100)
        if max_batt_dyn_ladung_W <= 0 or max_batt_dyn_ladung_W > battery_capacity_Wh:
            max_batt_dyn_ladung_W = battery_capacity_Wh
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
            if (max_batt_dyn_ladung_W - zeile_max_soc[4] < charge_rate_kW): charge_rate_kW_tmp = int((max_batt_dyn_ladung_W - zeile_max_soc[4]) + 1.1)
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
            # Keine Zeile mit -0.01 mehr übrig => fertig (sonst würde die letzte Zeile überschrieben)
            if max_index == -1:
                break
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
                # Platzbedarf für eine weitere Ladung: ein Viertel der Laderate, bei engem
                # Limit aber höchstens 10 % des nutzbaren Bereichs (sonst wird nie bis zum Limit geladen)
                platz_bedarf = min(charge_rate_kW * 0.25, max(0, max_batt_dyn_ladung_W - minimum_batterylevel) * 0.1)
                max_akkustand = max_batt_dyn_ladung_W - platz_bedarf
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

        # Wenn die Batterie leer ist, Ladestopp -1 auf 0 ändern, da ja nichts entladen werden kann 
        for row in pv_data_charge:
            if row[5] == -1 and row[4] < minimum_batterylevel * 1.05:
                row[5] = 0

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

        # Daten einfügen oder aktualisieren
        for entry in strompreise:
            zeiger.execute('''
                INSERT OR REPLACE INTO strompreise (Zeitpunkt, Bruttopreis, Boersenpreis)
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

        # in priceforecast alle Werte loeschen, wenn es länger nicht gelaufen ist...
        zeiger.execute(
            "DELETE FROM priceforecast"
        )

        zeiger.executemany("""
        INSERT OR REPLACE INTO priceforecast (Zeitpunkt, PV_Prognose, PrognNetzverbrauch, PrognNetzladen, PrognBattStatus)
        VALUES (?, ?, ?, ?, ?);
        """, priceforecast)

        verbindung.commit()
        verbindung.close()
    
        return ()
