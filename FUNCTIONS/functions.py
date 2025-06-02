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
    
    def gewichteter_median(self, paare):
        if not paare:
            return None
        paare = sorted(paare, key=lambda x: x[0])
        gesamtgewicht = sum(g for _, g in paare)
        halbgewicht = gesamtgewicht / 2
        kumuliert = 0
        for wert, gewicht in paare:
            kumuliert += gewicht
            if kumuliert >= halbgewicht:
                return wert

    def loadWeatherData(self):
        from collections import defaultdict
        from statistics import median
        conn = sqlite3.connect('weatherData.sqlite')
        cursor = conn.cursor()
    
        query = f"""
            SELECT Zeitpunkt, Prognose_W, Gewicht
            FROM weatherData
            WHERE
                Prognose_W IS NOT NULL AND
                Gewicht > 0 AND
                DATE(Zeitpunkt) BETWEEN DATE('now') AND DATE('now', '+1 day')
            ORDER BY Zeitpunkt ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        stundenwerte = defaultdict(list)
        for zeit_str, wert, gewicht in rows:
            zeit = datetime.fromisoformat(zeit_str)
            stunde = zeit.replace(minute=0, second=0, microsecond=0)
            # Vorerst ohne Gewichtung
            #stundenwerte[stunde].append((wert, gewicht))
            stundenwerte[stunde].append(wert)
    
        result = {}
        for stunde in sorted(stundenwerte):
            zeit_str = stunde.strftime("%Y-%m-%d %H:%M:%S")
            # print(stundenwerte[stunde])  #entWIGGlung
            # Vorerst ohne Gewichtung
            #result[zeit_str] = self.gewichteter_median(stundenwerte[stunde])
            result[zeit_str] = int(median(stundenwerte[stunde]))
    
        #print(result)  #entWIGGlung
        conn.close()
        return {"result": {"watts": result}}

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
