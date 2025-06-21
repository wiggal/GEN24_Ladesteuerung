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

    def getVarConf(self, var_block, var, Type):
        try:
            value = config[var_block][var].replace(',', '.').strip()
            if Type == 'eval':
                error_type = "als Zahl "
                # Nur Float- oder Integer-Parsing, kein eval!
                if '.' in value:
                    return_var = float(value)
                else:
                    return_var = int(value)
            else:
                error_type = ""
                return_var = value
        except (KeyError, ValueError):
            print(f"ERROR: die Variable [{var_block}][{var}] wurde NICHT {error_type}definiert!")
            exit(0)
        return return_var

    def loadWeatherData(self):
        conn = sqlite3.connect('weatherData.sqlite')
        cursor = conn.cursor()
    
        query = f"""
            SELECT Zeitpunkt, Prognose_W
            FROM weatherData
            WHERE
                Prognose_W > 30 AND
                Quelle IS 'Prognose' AND
                DATE(Zeitpunkt) BETWEEN DATE('now') AND DATE('now', '+1 day')
            ORDER BY Zeitpunkt ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        result = dict(rows)

        conn.close()
        return {"result": {"watts": result}}
