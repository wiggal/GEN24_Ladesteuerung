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

    def getSQLlastProduktion(self, database):
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
        sql_anweisung = "SELECT MIN(CASt(AC_Produktion as INTEGER)), DC_Produktion from pv_daten WHERE DC_Produktion = (SELECT MAX(CASt(DC_Produktion as INTEGER))FROM pv_daten);"
        zeiger.execute(sql_anweisung)
        row = zeiger.fetchall()
        AC_Produktion = row[0][0]
        DC_Produktion = row[0][1]

        return (AC_Produktion, DC_Produktion)

    def getSQLsteuerdaten(self, schluessel):
        verbindung = sqlite3.connect('CONFIG/Prog_Steuerung.sqlite')
        zeiger = verbindung.cursor()

        try:
            # Alle Steuerdaten aus Prog_Steuerung.sqlite lesen
            sql_anweisung = "SELECT Zeit, Res_Feld1, Res_Feld2, Options from steuercodes WHERE Schluessel = \'" +schluessel+"\';"
            zeiger.execute(sql_anweisung)
        except:
            # Datenbanktabelle anlegen, wenn sie nicht existiert
            sql_anweisung = " CREATE TABLE IF NOT EXISTS steuercodes ( ID TEXT, Schluessel TEXT, Zeit TEXT, Res_Feld1 INT, Res_Feld2 INT, Options text);"
            zeiger.execute(sql_anweisung)
            sql_anweisung = 'CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_title ON steuercodes (ID, Schluessel)'
            zeiger.execute(sql_anweisung)
            sql_anweisung = " INSERT OR IGNORE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES  ('23:09','ProgrammStrg','23:09','0','0','');"
            zeiger.execute(sql_anweisung)
            sql_anweisung = " INSERT OR IGNORE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES  ('23:59','Reservierung','ManuelleSteuerung','-1','0','');"
            zeiger.execute(sql_anweisung)
            sql_anweisung = " INSERT OR IGNORE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES  ('23:58','ENTLadeStrg','ManuelleEntladesteuerung','100','0','');"
            zeiger.execute(sql_anweisung)
            # Alle Steuerdaten aus Prog_Steuerung.sqlite lesen
            sql_anweisung = "SELECT Zeit, Res_Feld1, Res_Feld2, Options from steuercodes WHERE Schluessel = \'" +schluessel+"\';"
            zeiger.execute(sql_anweisung)

        rows = zeiger.fetchall()
        data = dict()
        columns = [col[0] for col in zeiger.description]
        for row in rows:
            data[row[0]] = dict()
            data[row[0]][columns[1]] = row[1]
            data[row[0]][columns[2]] = row[2]
            data[row[0]][columns[3]] = row[3]
        record_json = json.dumps(data, indent=2)
        record_json = json.loads(record_json)

        verbindung.commit()
        verbindung.close()
        return(record_json)



    
    
