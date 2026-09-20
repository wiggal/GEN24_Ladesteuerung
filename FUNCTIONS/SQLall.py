# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import sqlite3
import json
    
class sqlall:
    def __init__(self):
        self.now = datetime.now()

    def create_database_PVDaten(self, path):
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()  # <-- Hier den Cursor erstellen!

            # 1. Datenbanktabelle anlegen (falls nicht vorhanden)
            cursor.execute("""
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

            # 2. Bestehende Spalten abfragen
            cursor.execute("PRAGMA table_info(pv_daten)")
            vorhandene_spalten = [
                row[1] for row in cursor.fetchall()
            ]  # <-- fetchall() klappt jetzt

            # 3. Neue Spalten definieren
            neue_spalten = {
                "AC_to_DC": "INT",
                "Wallbox": "INT",
                "Ohmpilot": "INT",
            }

            # 4. Nur fehlende Spalten hinzufügen
            for spalte, datentyp in neue_spalten.items():
                if spalte not in vorhandene_spalten:
                    cursor.execute(f"ALTER TABLE pv_daten ADD COLUMN {spalte} {datentyp}")

            # 5. Index erzeugen
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_pv_daten_zeitpunkt ON"
                " pv_daten(Zeitpunkt)"
            )

            # Das 'with sqlite3.connect()' schließt & committet automatisch!
            print("DB", path, "wurde erstellt/aktualisiert.")

    def save_SQLite(self, database, AC_Produktion, DC_Produktion, AC_to_DC, Netzverbrauch,
                Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus, Wallbox=0, Ohmpilot=0):

        # 1. Vorbereitung
        Zeitpunkt = datetime.strftime(self.now, "%Y-%m-%d %H:%M:%S")
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
        gespeichert = False

        # 2. Sicherheitsnetz: falls der Job mehrfach innerhalb derselben Minute
        # läuft (z.B. bei X:01 und erneut kurz danach), keinen Doppel-Eintrag schreiben.
        sql_query = """
            INSERT INTO pv_daten (
                Zeitpunkt, AC_Produktion, DC_Produktion, Netzverbrauch,
                Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus, AC_to_DC, Wallbox, Ohmpilot
        )
            SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM pv_daten
                WHERE strftime('%Y-%m-%d %H:%M', Zeitpunkt) = strftime('%Y-%m-%d %H:%M', ?)
            )
        """
    
        # 3. Parameter-Liste (13 Werte)
        params = (
            # INSERT Teil (1-12)
            Zeitpunkt, AC_Produktion, DC_Produktion, Netzverbrauch,
            Einspeisung, Batterie_IN, Batterie_OUT, Vorhersage, BattStatus, AC_to_DC, Wallbox, Ohmpilot,
            # Minuten-Check (13)
            Zeitpunkt
        )

        try:
            # a. Daten speichern
            zeiger.execute(sql_query, params)
            gespeichert = True
        except sqlite3.OperationalError:
            # b. Falls Tabelle fehlt: Tabelle & Index anlegen und erneut versuchen
            self.create_database_PVDaten(database)
            zeiger.execute("CREATE INDEX IF NOT EXISTS idx_pv_daten_zeitpunkt ON pv_daten(Zeitpunkt)")
            zeiger.execute(sql_query, params)
            gespeichert = True
        except Exception as e:
            print(f"Fehler beim Speichern: {e}")

        verbindung.commit()
        verbindung.close()
        return gespeichert

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

    def getSQLsteuerdaten(self, schluessel, DB='CONFIG/Prog_Steuerung.sqlite'):
        verbindung = sqlite3.connect(DB)
        zeiger = verbindung.cursor()

        # Wenn schluessel == Reservierung dann laufende Reservierungen auslesen
        if (schluessel == 'Reservierung'):
            # SQL-Abfrage
            sql_anweisung = """
                SELECT
                    s.Zeit,
                    s.Res_Feld1,
                    COALESCE(
                        NULLIF(s.Res_Feld2, 0),
                        (
                            SELECT l.Res_Feld2
                            FROM steuercodes l
                            WHERE l.Schluessel = 'Reservierung'
                            AND strftime('%H:%M', l.Zeit) = strftime('%H:%M', s.Zeit)
                            AND date(l.Zeit) < date(s.Zeit)
                            AND l.Res_Feld2 != 0
                            ORDER BY l.Zeit DESC
                            LIMIT 1
                        ),
                        0
                    ) AS Res_Feld2,
                    s.Options
                FROM steuercodes s
                WHERE s.Schluessel = 'Reservierung'
                ORDER BY s.Zeit;
            """

        elif (schluessel == 'ChargeOption'):
            # Nur Einträge laden, deren Options-UNIX-Timestamp in der Zukunft liegt
            sql_anweisung = """
                SELECT Zeit, Res_Feld1, Res_Feld2, Options
                FROM steuercodes
                WHERE Schluessel = 'ChargeOption'
                AND CAST(Options AS INTEGER) > strftime('%s', 'now');
            """

        else:
            # Alle Steuerdaten aus Prog_Steuerung.sqlite lesen
            sql_anweisung = "SELECT Zeit, Res_Feld1, Res_Feld2, Options from steuercodes WHERE Schluessel = \'" +schluessel+"\';"

        try:
            zeiger.execute(sql_anweisung)
        except:
            self.create_database_ProgSteuerung(DB)
            # Alle Steuerdaten aus Prog_Steuerung.sqlite lesen
            zeiger.execute(sql_anweisung)

        rows = zeiger.fetchall()
        data = {}
        columns = [col[0] for col in zeiger.description]
        for row in rows:
            data[row[0]] = {}
            # Hier nur Zahlen zulassen, wenn schlussel nicht wallbox
            if schluessel != 'wallbox':
                try:
                    data[row[0]][columns[1]] = float(row[1])
                except (ValueError, TypeError):
                    data[row[0]][columns[1]] = 0
            else:
                # Bei wallbox den Wert einfach direkt übernehmen
                data[row[0]][columns[1]] = row[1]

            # Feld 2 kann String enthalten, wegen viertestündlichen Strompreisen
            data[row[0]][columns[2]] = row[2]
            data[row[0]][columns[3]] = row[3]

        record_json = json.dumps(data)
        record_json = json.loads(record_json)

        verbindung.commit()
        verbindung.close()
        return(record_json)
