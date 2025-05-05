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
        database = 'PV_Daten.sqlite'
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
        try:
            zeiger.execute(sql_anweisung)
            DB_data = zeiger.fetchall()
        except:
            print("Die Datei PV_Daten.sqlite fehlt oder ist leer, MaximalPrognosebegrenzung deaktivieren!")
            # Schließe die Verbindung
            verbindung.close()
            exit()

        # Schließe die Verbindung
        verbindung.close()

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

