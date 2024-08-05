# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import sqlite3
import json
    
class sqlall:
    def __init__(self):
        self.now = datetime.now()

    # Daten in SQLite_DB speichern (lifetime Zählerständer)
    def save_SQLite(self, database, AC_Produktion, DC_Produktion, Netzverbrauch, Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus):
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
    
        Zeitpunkt = datetime.strftime(self.now, "%Y-%m-%d %H:%M:%S")
    
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

    def getSQLsteuerdaten(self, schluessel):
        # Alle Steuerdaten aus Prog_Steuerung.sqlite lesen
        verbindung = sqlite3.connect('CONFIG/Prog_Steuerung.sqlite')
        zeiger = verbindung.cursor()
        sql_anweisung = "SELECT Zeit, Res_Feld1, Res_Feld2 from steuercodes WHERE Schluessel = \'" +schluessel+"\';"

        zeiger.execute(sql_anweisung)
        rows = zeiger.fetchall()
        data = dict()
        columns = [col[0] for col in zeiger.description]
        for row in rows:
            data[row[0]] = dict()
            data[row[0]][columns[1]] = row[1]
            data[row[0]][columns[2]] = row[2]
        record_json = json.dumps(data, indent=2)
        record_json = json.loads(record_json)

        verbindung.commit()
        verbindung.close()
        return(record_json)



    
    
