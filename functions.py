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

def getVarConf(block, var, Type):
        # Variablen aus config lesen und auf Zahlen prüfen
        try:
            if(Type == 'eval'):
                error_type = "als Zahl "
                return_var = eval(config[block][var])
            else:
                error_type = ""
                return_var = str(config[block][var])
        except:
            print("ERROR: die Variable [" + block + "][" + var + "] wurde NICHT " + error_type + "definiert!")
            exit(0)
        return return_var

## CSV-Logfile schreiben
from pathlib import Path
from csv import writer
def write_csv(csv_file, aktuelleBatteriePower, GesamtverbrauchHaus, aktuelleEinspeisung, aktuellePVProduktion, aktuelleVorhersage, BattStatusProz):
    # Kopf schreiben, wenn Datei nicht extistiert
    csv_file = Path(csv_file)
    if not csv_file.is_file():
        with open(csv_file, 'w', newline='') as student_file:
            writer_head = writer(student_file)
            writer_head.writerow(["Zeit","Ladung Akku","Verbrauch","Einspeisung","Produktion","Prognose","Batteriestand %"])
            student_file.close()

    Zeit = datetime.strftime(datetime.now(), "%m-%d %H:%M")
    list_data=[Zeit, aktuelleBatteriePower, GesamtverbrauchHaus, aktuelleEinspeisung, aktuellePVProduktion, aktuelleVorhersage, BattStatusProz]
    with open(csv_file, 'a', newline='') as student_file:
        writer_data = writer(student_file)
        writer_data.writerow(list_data)
        student_file.close()

    return()

import sqlite3

# Daten in SQLite_DB speichern
def save_SQLite(database, BatteriePower, Gesamtverbrauch, Einspeisung, PVProduktion, Vorhersage, BattStatus):
    verbindung = sqlite3.connect(database)
    zeiger = verbindung.cursor()

    Zeitpunkt = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

    # Datenbanktabelle anlegen, wenn sie nicht existiert
    sql_anweisung = """
    CREATE TABLE IF NOT EXISTS pv_daten (
    Zeitpunkt DATETIME,
    BatteriePower SMALLINT,
    Gesamtverbrauch SMALLINT,
    Einspeisung SMALLINT,
    PVProduktion SMALLINT,
    Vorhersage SMALLINT,
    BattStatus FLOAT
    );"""
    zeiger.execute(sql_anweisung)

    # Daten in DB schreiben
    zeiger.execute("""
                INSERT INTO pv_daten
                       VALUES (?,?,?,?,?,?,?)
               """,
              (Zeitpunkt, BatteriePower, Gesamtverbrauch, Einspeisung, PVProduktion, Vorhersage, BattStatus)
              )

    zeiger.execute(sql_anweisung)

    verbindung.commit()
    verbindung.close()

    return ()


