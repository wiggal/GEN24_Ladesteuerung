# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import json
import configparser

def loadConfig(conf_file):
        # Damit die Variable config auch in der Funktion "getVarConf" vorhanden ist (global config)
        global config
        config = configparser.ConfigParser()
        try:
                config.read_file(open(conf_file))
                config.read(conf_file)
        except:
                print('ERROR: config file not found.')
                exit(0)
        return config

def loadWeatherData(weatherfile):
        data = None
        try:
            with open(weatherfile) as json_file:
                data = json.load(json_file)
        except:
                print("ERROR: Wetterdatei fehlt oder ist fehlerhaft, bitte erst Wetterdaten neu laden!!")
                exit()
        return data

def storeWeatherData(wetterfile, data, now):
    try:
        out_file = open(wetterfile, "w")
        format = "%Y-%m-%d %H:%M:%S"
        data.update({'messageCreated': datetime.strftime(now, format)})
        json.dump(data, out_file, indent = 6)
        out_file.close()
    except:
        print("ERROR: Die Weterdatei " + wetterfile + " konnte NICHT geschrieben werden!")
        exit(0)
    return()

def loadPVReservierung(file):
        reservierungdata = None
        try:
            with open(file) as json_file:
                reservierungdata = json.load(json_file)
        except:
                print("ERROR: Reservierungsdatei fehlt, bitte erzeugen oder Option abschalten !!")
                exit()
        return reservierungdata

def getVarConf(var_block, var, Type):
        aktueller_Monat = str(datetime.strftime(datetime.now(), "%m"))
        # Für alle Varaiblen aus dem Block [Ladeberechnung] lesen welche Zusatz_Ladebloecke vorhanden sind
        # ausgenommen die Variable Zusatz_Ladebloecke, wegen Endlosschleife
        if (var_block == 'Ladeberechnung') and not (var_block == 'Ladeberechnung' and var == 'Zusatz_Ladebloecke'):
            Bloecke = getVarConf('Ladeberechnung','Zusatz_Ladebloecke','str')
            if ( Bloecke != 'aus' ):
                Bloecke = Bloecke.replace(" ", "")
                Bloecke = Bloecke.split(",")
                for Block in Bloecke:
                    # Hier pruefen ob Monat in Ersatzblock vorkommt und dann Ersatzblockvariable lesen!!
                    # Zusatz_configs lesen
                    Ersatzmonate = getVarConf( Block ,'Monate','str')
                    Ersatzmonate = Ersatzmonate.replace(" ", "")
                    Ersatzmonate = Ersatzmonate.split(",")
                    if ( aktueller_Monat in Ersatzmonate ):
                        if ( var in config[ Block ] ):
                            var_block = Block

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

import sqlite3
# Daten in SQLite_DB speichern (lifetime Zählerständer)
def save_SQLite(database, AC_Produktion, DC_Produktion, Netzverbrauch, Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus):
    verbindung = sqlite3.connect(database)
    zeiger = verbindung.cursor()

    Zeitpunkt = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

    # Datenbanktabelle anlegen, wenn sie nicht existiert
    sql_anweisung = """
    CREATE TABLE IF NOT EXISTS pv_daten (
    Zeitpunkt DATETIME,
    AC_Produktion INT,
    DC_Produktion INT,
    Netzverbrauch INT,
    Einspeisung INT,
    Batterie_IN INT,
    Batterie_OUT INT,
    Vorhersage SMALLINT,
    BattStatus FLOAT
    );"""
    zeiger.execute(sql_anweisung)

    # Daten in DB schreiben
    zeiger.execute("""
                INSERT INTO pv_daten
                       VALUES (?,?,?,?,?,?,?,?,?)
               """,
              (Zeitpunkt, AC_Produktion, DC_Produktion, Netzverbrauch, Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus)
              )

    zeiger.execute(sql_anweisung)

    verbindung.commit()
    verbindung.close()

    return ()


