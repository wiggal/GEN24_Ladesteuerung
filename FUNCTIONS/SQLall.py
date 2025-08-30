# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import sqlite3
import json
    
class sqlall:
    def __init__(self):
        self.now = datetime.now()

    def create_database_PVDaten(self, path):
        with sqlite3.connect(path) as zeiger:
            # Wenn Datenbanktabelle noch nicht existiert, anlegen
            zeiger.execute("""
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
            )""")
            # Spalte AC_to_DC anlegen, wenn sie nicht existiert
            zeiger.execute("""ALTER TABLE pv_daten ADD COLUMN AC_to_DC INT""")
            # Index auf Zeitpunkt erzeugen, wegen Geschwindigkeit
            zeiger.execute(""" CREATE INDEX IF NOT EXISTS idx_pv_daten_zeitpunkt ON pv_daten(Zeitpunkt)""")
        print("DB",path,"wurde erstellt.")

    def save_SQLite(self, database, AC_Produktion, DC_Produktion, AC_to_DC, Netzverbrauch, Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus):
        # Daten in SQLite_DB speichern (lifetime Zählerständer)
        Zeitpunkt = datetime.strftime(self.now, "%Y-%m-%d %H:%M:%S")
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
    
        try:
            # Index auf Zeitpunkt erzeugen, wegen Geschwindigkeit
            zeiger.execute(""" CREATE INDEX IF NOT EXISTS idx_pv_daten_zeitpunkt ON pv_daten(Zeitpunkt)""")
            # Versuch Daten in DB schreiben (geht nicht, wenn Spalte AC_to_DC noch fehlt)
            zeiger.execute("""
                    INSERT INTO pv_daten
                           VALUES (?,?,?,?,?,?,?,?,?,?)
                   """,
                  (Zeitpunkt, AC_Produktion, DC_Produktion, Netzverbrauch, Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus, AC_to_DC)
                  )
        except:
            # Wenn Datenbanktabelle noch nicht existiert, anlegen
            self.create_database_PVDaten(database)
            # Daten in DB nochmal versuchen zu schreiben
            zeiger.execute("""
                    INSERT INTO pv_daten
                           VALUES (?,?,?,?,?,?,?,?,?,?)
                   """,
                  (Zeitpunkt, AC_Produktion, DC_Produktion, Netzverbrauch, Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus, AC_to_DC)
                  )
            
    
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

    def create_database_ProgSteuerung(self, path):
        with sqlite3.connect(path) as zeiger:
            # Wenn Datenbanktabelle noch nicht existiert, anlegen
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
        print("DB",path,"wurde erstellt.")

    def getSQLsteuerdaten(self, schluessel):
        verbindung = sqlite3.connect('CONFIG/Prog_Steuerung.sqlite')
        zeiger = verbindung.cursor()

        try:
            # Wenn schluessel == Reservierung dann laufende Reservierungen auslesen
            if (schluessel == 'Reservierung'):
                # SQL-Abfrage
                query = """
                SELECT strftime('%H:00:00', Zeit) AS Stunde,
                    MIN(Res_Feld2) AS Res_Feld2
                FROM steuercodes
                WHERE Res_Feld2 != 0
                AND ID LIKE '1%'
                AND Schluessel = 'Reservierung'
                GROUP BY strftime('%Y-%m-%d %H', Zeit)
                ORDER BY Stunde;
                """
                # Abfrage ausführen
                zeiger.execute(query)
            
                # Ergebnis in ein Array laden (Liste von Tupeln)
                laufende_array = zeiger.fetchall()
                if (laufende_array): print("DEBUG: ", laufende_array)  #entWIGGlung

            # Alle Steuerdaten aus Prog_Steuerung.sqlite lesen
            sql_anweisung = "SELECT Zeit, Res_Feld1, Res_Feld2, Options from steuercodes WHERE Schluessel = \'" +schluessel+"\';"
            zeiger.execute(sql_anweisung)
        except:
            self.create_database_ProgSteuerung('CONFIG/Prog_Steuerung.sqlite')
            # Alle Steuerdaten aus Prog_Steuerung.sqlite lesen
            sql_anweisung = "SELECT Zeit, Res_Feld1, Res_Feld2, Options from steuercodes WHERE Schluessel = \'" +schluessel+"\';"
            zeiger.execute(sql_anweisung)

        rows = zeiger.fetchall()
        data = {}
        columns = [col[0] for col in zeiger.description]
        for row in rows:
            data[row[0]] = {}
            # Hier nur Zahlen zulassen
            try:
                data[row[0]][columns[1]] = float(row[1])
            except (ValueError, TypeError):
                data[row[0]][columns[1]] = 0

            # Feld 2 kann String enthalten, wegen viertestündlichen Strompreisen
            data[row[0]][columns[2]] = row[2]
            data[row[0]][columns[3]] = row[3]

            # Wenn schluessel == Reservierung dann nach laufenden Reservierungen suchen und einfügen
            if (schluessel == 'Reservierung' and row[0] != 'ManuelleSteuerung'):
                # Stunde extrahieren
                stunde = datetime.fromisoformat(row[0]).strftime("%H:00:00")
                # Wert suchen
                wert = None
                for laufende_row in laufende_array:
                    if laufende_row[0] == stunde:
                        data[row[0]][columns[2]] = laufende_row[1]
                        print("DEBUG: ",row[0],data[row[0]])  #entWIGGlung
                        break

        record_json = json.dumps(data)
        record_json = json.loads(record_json)

        verbindung.commit()
        verbindung.close()
        return(record_json)
