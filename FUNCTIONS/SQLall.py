# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import sqlite3
    
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
    
    
