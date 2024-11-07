# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import json
import configparser
import sqlite3

    
class basics:
    def __init__(self):
        self.now = datetime.now()

    def loadConfig(self, conf_files):
            # Damit die Variable config auch in der Funktion "getVarConf" vorhanden ist (global config)
            global config
            # Damit kann man auch meherer configs nacheinander lesen
            try:
                config
            except NameError:
                config = configparser.ConfigParser()
            # Standard.ini lesen
            for conf_file in conf_files:
                c_file = 'CONFIG/'+conf_file+'.ini'
                try:
                        config.read_file(open(c_file))
                        config.read(c_file)
                except:
                        print("\nERROR: ", e, "\n")
            # _priv_ini lesen
            for conf_file in conf_files:
                c_file = 'CONFIG/'+conf_file+'_priv.ini'
                try:
                        config.read_file(open(c_file))
                        config.read(c_file)
                except Exception as e:
                        print("\nERROR: ", e, "\n")
            # Monatsabhängige ini lesen
            if ( 'charge' in conf_files ):
                aktueller_Monat = str(datetime.strftime(datetime.now(), "%m"))
                for (c_file, monate) in config.items('monats_priv.ini'):
                    if aktueller_Monat in monate:
                        c_file = 'CONFIG/'+c_file
                        try:
                            config.read_file(open(c_file))
                            config.read(c_file)
                        except Exception as e:
                            print("\nERROR: ", e, "\n")
                return config
    
    def loadWeatherData(self, weatherfile):
            data = None
            try:
                with open(weatherfile) as json_file:
                    data = json.load(json_file)
            except:
                    data = {'messageCreated': '2000-01-01 01:01:01'}

            return data
    
    def storeWeatherData(self, wetterfile, data, now, wetterdienst):
        try:
            out_file = open(wetterfile, "w")
            format = "%Y-%m-%d %H:%M:%S"
            data.update({'messageCreated': datetime.strftime(now, format)})
            data.update({'createdfrom': wetterdienst})
            json.dump(data, out_file, indent = 6)
            out_file.close()
        except:
            print("ERROR: Die Wetterdatei " + wetterfile + " konnte NICHT geschrieben werden!")
            exit(0)
        return()
    
    def getVarConf(self, var_block, var, Type):
            # Variablen aus config lesen und auf Zahlen prüfen
            try:
                if(Type == 'eval'):
                    error_type = "als Zahl "
                    return_var = eval(config[var_block][var].replace(',', '.'))
                else:
                    error_type = ""
                    return_var = str(config[var_block][var])
            except:
                print("ERROR: die Variable [" + var_block + "][" + var + "] wurde NICHT " + error_type + "definiert!")
                exit(0)
            return return_var
    
    def checkMaxPrognose(self, data):
        database = self.getVarConf('Logging','Logging_file','str')
        print_level = self.getVarConf('env','print_level','eval')
        MaxProGrenz_Faktor = self.getVarConf('env','MaxProGrenz_Faktor','eval')
        MaxProGrenz_Dayback = self.getVarConf('env','MaxProGrenz_Dayback','eval') * -1
        DEBUG_txt = "Folgende Prognosen wurden auf einen Maximalwert reduziert:\n"
        Anzahl_Begrenzung = 0

        # Datum Sommer und Winterzeit ermitteln
        # Aktuelles Jahr ermitteln
        current_year = datetime.now().year
        # Datum für den 31. März des aktuellen Jahres
        date_03 = datetime(current_year, 3, 31)
        # Datum für den 31. Oktober des aktuellen Jahres
        date_10 = datetime(current_year, 10, 31)
        # Wochentag ermitteln (0=Sonntag, 6=Samstag)
        weekday_03 = (date_03.weekday() + 1) % 7
        weekday_10 = (date_10.weekday() + 1) % 7
        letzter_So_03 = 31 - weekday_03
        letzter_So_10 = 31 - weekday_10
        Sommerzeit_anfang= str(current_year)+"-03-"+str(letzter_So_03)+" 02"
        Winterzeit_anfang= str(current_year)+"-10-"+str(letzter_So_10)+" 02"

        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
        sql_anweisung = """
            WITH stundenwerte AS (
                        SELECT
                            strftime('%Y-%m-%d %H:00:00', Zeitpunkt) AS volle_stunde,
                            MAX(DC_Produktion) AS max_dcproduktion
                        FROM
                            pv_daten
                        WHERE
                            Zeitpunkt >= datetime('now', '""" + str(MaxProGrenz_Dayback) + """ days')
                        GROUP BY
                            strftime('%Y-%m-%d %H:00:00', Zeitpunkt)
                    ),
                    sommerzeit AS (
                        SELECT 
                            CASE
                                WHEN volle_stunde BETWEEN '""" + str(Sommerzeit_anfang) + """' AND '""" + str(Winterzeit_anfang) + """' THEN DATETIME(volle_stunde, '-1 hour')
                            ELSE volle_stunde
                            END AS volle_stunde,
                            max_dcproduktion
                        FROM stundenwerte
                    ),
                    differenzen AS (
                        SELECT
                            strftime('%H:00:00',a.volle_stunde) AS Stunde,
                            a.max_dcproduktion - COALESCE(b.max_dcproduktion, 0) AS DCProduktion
                        FROM
                            sommerzeit a
                        LEFT JOIN
                            sommerzeit b ON a.volle_stunde = datetime(b.volle_stunde, '+1 hour')
			            WHERE
				            DCProduktion < 20000
                    )
            SELECT
            Stunde, MAX(DCProduktion) AS maximalwert
            FROM differenzen
            GROUP BY Stunde
            ORDER BY Stunde;
            """
        zeiger.execute(sql_anweisung)
        DB_data = zeiger.fetchall()
        for hour in DB_data:
            DB_MaxWatt = int(hour[1] * MaxProGrenz_Faktor)
            search_substring = str(hour[0])
            for key, value in data['result']['watts'].items():
                if isinstance(key, str) and search_substring in key:
                    if (data['result']['watts'][key] > DB_MaxWatt):
                        DEBUG_txt += str(key) + " " + str(data['result']['watts'][key]) + " ==>> " + str(DB_MaxWatt) + "\n"
                        Anzahl_Begrenzung += 1
                        data['result']['watts'][key] = DB_MaxWatt

        if print_level == 2:
            print("checkMaxPrognose mit letze ", MaxProGrenz_Dayback, " Tage!")
            print(DEBUG_txt)

        return (data)

    def Prognoseoptimierung(self, data):
        import pandas as pd
        import pytz
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_squared_error
        database = self.getVarConf('Logging','Logging_file','str')
        print_level = self.getVarConf('env','print_level','eval')
        MaxProGrenz_Dayback = self.getVarConf('env','MaxProGrenz_Dayback','eval')

        # Verbindung zur SQLite-Datenbank herstellen
        conn = sqlite3.connect(database)
        
        # Abfrage der historischen Daten
        query = """
        WITH stundenwerte AS (
                    SELECT
                        strftime('%Y-%m-%d %H:00:00', Zeitpunkt) AS volle_stunde,
                        MIN(DC_Produktion) AS max_dcproduktion,
				        AVG(Vorhersage) AS Vorhersage
                    FROM
                        pv_daten
                    WHERE
                        (Zeitpunkt BETWEEN date('now', '-"""+str(MaxProGrenz_Dayback)+""" day') AND date('now', '+"""+str(MaxProGrenz_Dayback)+""" day'))
                        OR (Zeitpunkt BETWEEN date('now', '-1 year', '-"""+str(MaxProGrenz_Dayback)+""" day') AND date('now', '-1 year', '+"""+str(MaxProGrenz_Dayback)+""" day'))
                        OR (Zeitpunkt BETWEEN date('now', '-2 year', '-"""+str(MaxProGrenz_Dayback)+""" day') AND date('now', '-2 year', '+"""+str(MaxProGrenz_Dayback)+""" day'))
                    GROUP BY
                        strftime('%Y-%m-%d %H:00:00', Zeitpunkt)
                ),
                differenzen AS (
                    SELECT
                        a.volle_stunde AS Stunde,
                        a.max_dcproduktion - COALESCE(b.max_dcproduktion, 0) AS DCProduktion,
				        ROUND(a.Vorhersage) AS Vorhersage
                    FROM
                        stundenwerte a
                    LEFT JOIN
                        stundenwerte b ON a.volle_stunde = datetime(b.volle_stunde, '+1 hour')
                )
		        SELECT Stunde, DCProduktion, Vorhersage
		        From differenzen
                WHERE DCProduktion < 15000 AND Stunde IS NOT NULL
                """
		
        df = pd.read_sql(query, conn)

        # Schließe die Verbindung
        conn.close()

        ### UTC ZEIT einfügen (wegen Sommer und Winterzeit)
        # Zeitzone definieren (z.B. für Berlin)
        local_tz = pytz.timezone("Europe/Berlin")

        # Funktion zur Umwandlung in UTC
        def convert_to_utc(local_time):
            # String in datetime umwandeln und lokalisieren
            localized_time = local_tz.localize(pd.to_datetime(local_time))
            # Umwandlung in UTC
            return localized_time.astimezone(pytz.utc)

        # Neue Spalte mit UTC-Zeiten hinzufügen
        df['utc_time'] = df['Stunde'].apply(convert_to_utc)


        # Fehlende Werte behandeln
        df.ffill(inplace=True)

        # Konvertiere das Datum in das richtige Format
        df['utc_time'] = pd.to_datetime(df['utc_time'])
        df['hour'] = df['utc_time'].dt.hour

        # Merkmale und Zielvariable definieren
        X = df[['hour']]
        y = df['DCProduktion']

        # Train-Test-Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Modell trainieren (Ist nach Tests das beste Modell)
        model = RandomForestRegressor(n_estimators=200)
        model.fit(X_train, y_train)

        # Vorhersagen auf dem Test-Set machen
        y_pred = model.predict(X_test)

        # Modell bewerten
        #mse = mean_squared_error(y_test, y_pred)
        #print(f'Mean Squared Error: {mse}')

        # weatherData.json = data
        future_data = data

        # Konvertiere das JSON-Format in ein DataFrame
        future_df = pd.DataFrame(list(future_data['result']['watts'].items()), columns=['datetime', 'predicted_power'])
        # Neue Spalte mit UTC-Zeiten hinzufügen
        future_df['utc_time'] = future_df['datetime'].apply(convert_to_utc)

        # Konvertiere das Datum in das richtige Format
        future_df['utc_time'] = pd.to_datetime(future_df['utc_time'])
        future_df['hour'] = future_df['utc_time'].dt.hour

        # Vorhersagen für die nächsten 48 Stunden machen (basierend auf historischen Daten)
        future_df['predicted_actual_power'] = model.predict(future_df[['hour']])
        # Immer auf volle 100 abrunden
        future_df['predicted_actual_power'] = (future_df['predicted_actual_power']-49).round(-2).astype(int)

        # evtl als DEBUG verwenden
        if print_level == 2:
            df_print = future_df[['datetime', 'predicted_power', 'predicted_actual_power']]
            print("Prognoseoptimierung mit scikit-learn")
            print(df_print)

        # Kleinsten Vorhersagewert ermitteln
        future_df["KleinererWert"] = future_df[["predicted_power", "predicted_actual_power"]].min(axis=1)

        # data im json-Format wieder erzeugen
        df_data = future_df[['datetime', 'KleinererWert']]
        data_values = dict(df_data.values.tolist())
        # Werte durch neue Werte ersetzen
        data['result']['watts'] = data_values

        return(data)
        
