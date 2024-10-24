# Hier die Funktionen zum dynamischen Stromtarif
from datetime import datetime
import sqlite3
import json
import configparser
    
class dynamic:
    def __init__(self):
        self.now = datetime.now()

    def makeLastprofil(self, database, Lastgrenze):
        verbindung = sqlite3.connect(database)
        zeiger = verbindung.cursor()
        # Lastprofil von jetzt 35 Tage zurück für jeden Wochentag ermitteln
        sql_anweisung = """
        WITH stundenwerte AS (
            SELECT
                strftime('%Y-%m-%d %H:00:00', Zeitpunkt) AS volle_stunde,
                MAX(Netzverbrauch) AS max_netzverbrauch,
                MAX(AC_Produktion) AS max_acproduktion,
                MAX(Einspeisung) AS max_einspeisung
            FROM
                pv_daten
            WHERE
                Zeitpunkt >= datetime('now', '-35 days')
                /*
                # Für einen bestimmten Monat die Zeile:
                Zeitpunkt >= datetime('now', '-35 days')
                # durch folgende für z.B. Januar 2024 ersetzen
                Zeitpunkt >= DATE('2024-01-31', '-35 days') AND Zeitpunkt < '2024-01-31'
                */
            GROUP BY
                strftime('%Y-%m-%d %H:00:00', Zeitpunkt)
        ),
        differenzen AS (
            SELECT
                a.volle_stunde,
                a.max_netzverbrauch - COALESCE(b.max_netzverbrauch, 0) AS Netzverbrauch,
                a.max_acproduktion - COALESCE(b.max_acproduktion, 0) AS ACProduktion,
                a.max_einspeisung- COALESCE(b.max_einspeisung, 0) AS Einspeisung
            FROM
                stundenwerte a
            LEFT JOIN
                stundenwerte b ON a.volle_stunde = datetime(b.volle_stunde, '+1 hour')
        ),
        verbrauch AS (
        SELECT
            volle_stunde,
	        CASE 
                WHEN (Netzverbrauch + ACProduktion - Einspeisung) > """ + str(Lastgrenze) + """ THEN """ + str(Lastgrenze) + """
                ELSE (Netzverbrauch + ACProduktion - Einspeisung) 
            END AS Verbrauch
        FROM
            differenzen
        )
        SELECT
            strftime('%w', volle_stunde) || '-' || strftime('%H', volle_stunde) AS ID,
            'Lastprofil' AS Schluessel,
            strftime('%H:00', volle_stunde) AS Zeit,
            strftime('%w', volle_stunde) AS Wochentag,
            CAST(AVG(Verbrauch) AS INTEGER) AS Verbrauch,
            strftime('%s', 'now') AS Options
        FROM
            verbrauch
        GROUP BY
            Wochentag, Zeit
        HAVING
            Verbrauch > 0
        ORDER BY
            strftime('%w', volle_stunde), Zeit;
        """

        zeiger.execute(sql_anweisung)
        rows = zeiger.fetchall()
        #print(rows)

        verbindung.commit()
        verbindung.close()

        # Daten in DB schreiben

        verbindung = sqlite3.connect('CONFIG/Prog_Steuerung.sqlite')
        zeiger = verbindung.cursor()
        zeiger.executemany('''
                    REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES (?, ?, ?, ?, ?, ?)
                    ''', rows)
    
        verbindung.commit()
        verbindung.close()

        print("Lastprofil in CONFIG/Prog_Steuerung.sqlite geschrieben")

        return ()

    def getLastprofil(self):
        # Hier die Lastprofildaten für heute und morgen auslesen
        verbindung = sqlite3.connect('CONFIG/Prog_Steuerung.sqlite')
        zeiger = verbindung.cursor()
        # Res_Feld1 = Wochentag, Zeit = Stunde, Res_Feld2 = Durchschnittsverbrauch, Options = Timestamp Erzeugung
        sql_anweisung = "SELECT Res_Feld1, Zeit, Res_Feld2, Options from steuercodes WHERE Res_Feld1 IN (strftime('%w', 'now'), strftime('%w', 'now', '+1 day'));"
        zeiger.execute(sql_anweisung)
        rows = zeiger.fetchall()

        #print(rows)
        return(rows)
