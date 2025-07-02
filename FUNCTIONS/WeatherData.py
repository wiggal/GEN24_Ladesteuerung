# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime, timedelta
import os
import json
import configparser
import sqlite3
from collections import defaultdict
from statistics import median, mean
import FUNCTIONS.functions

basics = FUNCTIONS.functions.basics()
    
class WeatherData:
    def __init__(self):
        self.now = datetime.now()

    def check_or_create_db(self, path):
        # Prüfen, ob Datei existiert und ob sie leer ist
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            print("DB existiert nicht oder ist leer. Wird neu erstellt.")
            return self.create_database(path)

        # Prüfen, ob Datei eine gültige SQLite-DB ist
        try:
            with sqlite3.connect(path) as conn:
                conn.execute("SELECT name FROM sqlite_master LIMIT 1;")
        except sqlite3.DatabaseError:
            print("DB beschädigt oder ungültig. Neu erstellen.")
            os.remove(path)
            create_database(path)

    def create_database(self, path):
        with sqlite3.connect(path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weatherData (
                    Zeitpunkt TEXT,
                    Quelle TEXT,
                    Prognose_W INTEGER,
                    Gewicht INTEGER,
                    Options TEXT,
                    UNIQUE(Zeitpunkt, Quelle)
                );
            """)
        print("DB wurde erstellt.")


    def storeWeatherData_SQL(self, data, quelle, gewicht_neu=-1, loesche_quelle=''):
        self.check_or_create_db('weatherData.sqlite')
        verbindung = sqlite3.connect('weatherData.sqlite')
        zeiger = verbindung.cursor()
        print_level = basics.getVarConf('env','print_level','eval')
        # Alte Einträge löschen die älter 35 Tage sind
        loesche_bis = (datetime.today() - timedelta(days=35)).date().isoformat()

        #Prognosen kleiner 10 löschen
        data = [entry for entry in data if entry[2] >= 10]

        try:
            # Index auf Zeitpunkt anlegen, falls nicht vorhanden
            zeiger.execute("""
                CREATE INDEX IF NOT EXISTS idx_weatherData_Zeitpunkt ON weatherData(Zeitpunkt);
            """)
        
            # Alte Daten löschen
            zeiger.execute("""
                DELETE FROM weatherData
                WHERE datetime(Zeitpunkt) < datetime(?);
            """, (loesche_bis,))
        
            # Basis-Quellenliste
            loesche_quellen = ['Ergebnis', 'Median']
            if (loesche_quelle != ''):
                loesche_quellen.append(loesche_quelle)
            # SQL-Statement generieren
            platzhalter = ', '.join(['?'] * len(loesche_quellen))

            # Datensätze mit Quelle = 'Ergebnis, 'Median' usw' löschen, Historisch
            zeiger.execute(f"""
                DELETE FROM weatherData
                WHERE Quelle IN ({platzhalter});
            """, loesche_quellen)

            # Neue Prognosen speichern
            zeiger.executemany("""
            INSERT OR REPLACE INTO weatherData (Zeitpunkt, Quelle, Prognose_W, Gewicht, Options)
            VALUES (?, ?, ?, ?, ?);
            """, data)

        except Exception as e:
            print("Fehler:", e)
            import traceback
            traceback.print_exc()
            print("ERROR :", self.now, "Die Prognosedaten von ", quelle, "konnten NICHT gespeichert werden!")
            exit(0)

        # Hier noch prüfen ob sich das gewicht_neu geändert hat und evtl. in DB ändern
        # Aber nur wenn gewicht_neu nicht -1, da es sonst nicht von einem Wetterdienst kommt
        if (gewicht_neu != -1):
            if print_level >= 3:
                print("DEBUG Gewichte überprüft für ", quelle)
            zeiger.execute("""
                UPDATE weatherData
                SET Gewicht = ?
                WHERE Quelle = ? AND Gewicht != ?
            """, (gewicht_neu, quelle, gewicht_neu))
        else:
            if print_level >= 3:
                print("DEBUG Gewichte !!NICHT!! überprüft für ", quelle)

        verbindung.commit()
        verbindung.close()

        return()
    
    def get_produktion_result(self, von_tag):
        conn = sqlite3.connect('PV_Daten.sqlite')
        verbindung = conn.cursor()
        heute = datetime.now().strftime('%Y-%m-%d 23:59:59')
        aktuelle_Std = datetime.now().strftime('%Y-%m-%d %H:00:00')
        config = basics.loadConfig(['charge'])
        Max_Leistung = basics.getVarConf('Ladeberechnung','PV_Leistung_Watt','eval')
        # Der offset soll die Stunde in die Mitte der Produktion verschieben
        offset = '+30 minutes'
        sql_anweisung = f"""
        WITH VerschobenePVDaten AS (
            SELECT
                datetime(Zeitpunkt, '{offset}') AS verschobenerZeitpunkt,
                DC_Produktion
            FROM pv_daten
            WHERE Zeitpunkt BETWEEN '{von_tag}' AND '{heute}'
        ),
        Alle_PVDaten AS (
            SELECT verschobenerZeitpunkt AS Zeitpunkt,
                DC_Produktion
            FROM VerschobenePVDaten
            GROUP BY STRFTIME('%Y%m%d%H', Zeitpunkt)
        ),
        ProduktionDiff AS (
            SELECT
                STRFTIME('%Y-%m-%d %H:00:00', Zeitpunkt) AS Zeitpunkt,
                (LEAD(DC_Produktion) OVER (ORDER BY Zeitpunkt) - DC_Produktion) AS Produktion
            FROM Alle_PVDaten
        )
        SELECT *
        FROM ProduktionDiff
        WHERE Produktion > 10;
        """
        try:
            verbindung.execute(sql_anweisung)
            DB_data = verbindung.fetchall()
        except Exception as e:
            print("Fehler:", e)
            import traceback
            traceback.print_exc()
            print("Die Datei PV_Daten.sqlite fehlt oder ist leer!")
            DB_data = []
            DB_data.append((aktuelle_Std, 0),)
            # Schließe die Verbindung
            verbindung.close()

        Produktion = [] 
        Watt_zuvor = None
        for Stunde, Watt in DB_data:
            # Wenn Aufzeichnung länger ausgefallen ist, entstehen sonst grosse Produktionen
            if (Watt > Max_Leistung * 1.15 and Watt_zuvor != None):
                Watt = Watt_zuvor
            else:
                Watt_zuvor = Watt
            Produktion.extend([(Stunde, 'Produktion', Watt, '0', '')])

        return(Produktion)

    def get_opt_prognose(self, Produktion, Basis):
        # 1. Dictionaries vorbereiten
        prognose_dict = {zeit: watt for zeit, _, watt, *_ in Basis}
        produktion_dict = {zeit: watt for zeit, _, watt, *_ in Produktion}
        # 2. Faktoren nach Uhrzeit (HH:MM:SS) sammeln
        faktoren_nach_stunde = defaultdict(list)
        for zeit in prognose_dict:
            # Damit nur relevate Prognosen verwendet werden Faktor nur bei > 100Watt
            if zeit in produktion_dict: 
                uhrzeit = zeit[11:]  # z.B. '05:00:00'
                if produktion_dict[zeit] > 100 and prognose_dict[zeit] > 100:
                    faktor = produktion_dict[zeit] / prognose_dict[zeit]
                else:
                    faktor = 1.0
                faktoren_nach_stunde[uhrzeit].append(faktor)
        
        #entWIGGlung CSV AUSGABE DER FAKTOREN
        # print(zeit, produktion_dict[zeit], prognose_dict[zeit], faktor)  #entWIGGlung
        #import csv
        #import sys
        #for uhrzeit, faktoren in faktoren_nach_stunde.items():
            #faktoren_als_text = [str(round(f, 4)).replace('.', ',') for f in faktoren]
            #zeile = [uhrzeit] + faktoren_als_text
            #print(";".join(zeile))
        #entWIGGlung

        # 3. Median-Faktor je Uhrzeit berechnen
        median_faktoren = {
            uhrzeit: median(faktoren)
            for uhrzeit, faktoren in faktoren_nach_stunde.items()
        }
        # 4. Justierte Prognose-Liste erzeugen
        Opt_Prognose = []
        for zeit in prognose_dict:
            uhrzeit = zeit[11:]  # z. B. '06:00:00'
            faktor = median_faktoren.get(uhrzeit)
            if faktor:
                neue_prognose = round(prognose_dict[zeit] * faktor)
                Opt_Prognose.append((zeit, "Prognose", neue_prognose, '0', ''))

        return(Opt_Prognose)

    def store_forecast_result(self):
        print_level = basics.getVarConf('env','print_level','eval')
        ForecastCalcMethod = basics.getVarConf('env','ForecastCalcMethod','str')
        conn = sqlite3.connect('weatherData.sqlite')
        cursor = conn.cursor()
    
        # 'Prognose', 'Median', 'Produktion' ausschließen, da sie nicht zur Mittelbildung verwendet werden
        query = f"""
            SELECT Zeitpunkt, Prognose_W, Gewicht
            FROM weatherData
            WHERE
                Prognose_W IS NOT NULL AND
                Gewicht > 0 AND
                Quelle NOT IN ('Prognose', 'Median', 'Produktion')
            ORDER BY Zeitpunkt ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        stundenwerte = defaultdict(list)
        akt_Std = self.now.strftime("%H:00:00")
        akt_tag_Std = self.now.strftime("%Y-%m-%d %H:00:00")
        von_tag = '2222-01-01'

        # DB-Prognosewerte aufbereiten
        for zeit_str, wert, gewicht in rows:
            zeit = datetime.fromisoformat(zeit_str)
            akt_tag = zeit.strftime("%Y-%m-%d")
            if akt_tag < von_tag: von_tag = akt_tag
            stunde = zeit.replace(minute=0, second=0, microsecond=0)
            # extend([wert] * gewicht) fügt den wert genau gewicht-mal der Liste hinzu
            # Damit hat man einen gewichteten Median
            if (wert > 10):
                try:
                    gewicht = int(gewicht)
                except (ValueError, TypeError):
                    gewicht = 0
                stundenwerte[stunde].extend([wert] * gewicht)

        result = {}
        result_basis = {}
        for stunde in sorted(stundenwerte):
            if stundenwerte.get(stunde):
                zeit_str = stunde.strftime("%Y-%m-%d %H:%M:%S")

                # Statistische Auswertungen nach ForecastCalcMethod
                if ( 'median' in ForecastCalcMethod):
                    result[zeit_str] = int(median(stundenwerte[stunde]))
                elif ( 'mittel' in ForecastCalcMethod):
                    result[zeit_str] = int(mean(stundenwerte[stunde]))
                elif ( 'min' in ForecastCalcMethod):
                    result[zeit_str] = int(min(stundenwerte[stunde]))
                elif ( 'max' in ForecastCalcMethod):
                    result[zeit_str] = int(max(stundenwerte[stunde]))
                else:
                    print("ERROR: Es wurde keine zulässige ForecastCalcMethod gefunden!!!")
                    exit()

        DB_data = []
        Prognose = []
        # Produktion aus PV_Daten.sqlite holen
        Produktion = self.get_produktion_result(von_tag)
        DB_data.extend(Produktion)

        loesche_quelle=''
        if ( '+' in ForecastCalcMethod):
            # Ermittelte Prognosedaten als Basis und Optimierung als Prognose speichern.
            Basis = []
            Basis.extend([(ts, 'Basis', val, '0', '') for ts, val in result.items()])
            DB_data.extend(Basis)
            # Hier Funktion zur Prognoseoptimierung aufrufen
            Prognose = self.get_opt_prognose(Produktion, Basis)
        else:
            # Ermittelte Prognosedaten direkt als Prognose speichern.
            Prognose.extend([(ts, 'Prognose', val, '0', '') for ts, val in result.items()])
            loesche_quelle='Basis'

        # Prognose immer in DB
        DB_data.extend(Prognose)
            
        # Speichern der Resultate  in DB
        self.storeWeatherData_SQL(DB_data, 'Basis, Prognose, Produktion', '-1', loesche_quelle)
        conn.close()

        return()

    def getSQLcurrentDayProduction(self, database):
        try:
            verbindung = sqlite3.connect(database)
            zeiger = verbindung.cursor()
            sql_anweisung = "SELECT MAX(DC_Produktion)- MIN(DC_Produktion) AS DC_Produktion from pv_daten where Zeitpunkt LIKE '" + self.now.strftime("%Y-%m-%d")+"%';"
            zeiger.execute(sql_anweisung)
            row = zeiger.fetchall()
            currentDayProduction = round(row[0][0]/1000,1)
        except:
            currentDayProduction = 0

        return (currentDayProduction)

    def sum_pv_data(self, pvdaten_dict):
        # Prognosedaten für mehrere Strings addieren
        # 1. Daten aus allen Blöcken zusammenfassen und Werte addieren
        daten_dict = {}

        for block in pvdaten_dict:
            for zeit, quelle, wert, flag, kommentar in pvdaten_dict.get(block, []):
                key = (zeit, quelle)
                if key in daten_dict:
                    daten_dict[key]['wert'] += wert
                else:
                    daten_dict[key] = {'wert': wert, 'flag': flag, 'kommentar': kommentar}

        # 2. Ergebnisliste ohne Blöcke erzeugen
        dict_watts = []
        for (zeit, quelle), info in daten_dict.items():
            dict_watts.append((zeit, quelle, info['wert'], info['flag'], info['kommentar']))

        # Ergebnis nach Zeit sortieren
        dict_watts.sort(key=lambda x: x[0])

        return(dict_watts)
