# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import json
import configparser
    
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
    
