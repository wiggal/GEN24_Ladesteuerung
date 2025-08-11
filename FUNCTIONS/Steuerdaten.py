# Hier die Parameter aus der WebUI Settings lesen
import json
from datetime import date
import FUNCTIONS.SQLall
    
sqlall = FUNCTIONS.SQLall.sqlall()

class readcontroldata:

    def getParameter(self, argv, schluessel):
        Parameter = ""
        Meldung = ""
        if len(argv) > 1 :
            Parameter = argv[1]
        # uuid erstellen
        self.get_uuid('', 'uuid')
        # Prog_Steuerung.json lesen
        Prog_Steuer_code_tmp = sqlall.getSQLsteuerdaten(schluessel)
        Prog_Steuer_code = list(Prog_Steuer_code_tmp.values())[0]['Res_Feld1']
        Optionen_sql = list(Prog_Steuer_code_tmp.values())[0]['Options']
        Optionen = []
        # Aus Optionen array erzeugen
        for i in Optionen_sql.split(":"):
            Optionen.append(i)
        # Options nur bei Ladesteuerung Code 4 füllen
        Options = []

        # wenn WebUI-Settings ausgeschaltet Aufrufparameter (schreiben, logging) umsetzen
        if Prog_Steuer_code == 0 or 'nowebui' in Parameter:
            if Parameter == 'schreiben':
                Options = ['logging','laden','entladen','optimierung','notstrom','dynamicprice']
            else:
                Options = Parameter.split(",")
        else:
            # Ab hier WebUI-Settings
            if Prog_Steuer_code == 1:
                Meldung = "AUS (WR löschen)"
                Parameter = 'exit0'
            if Prog_Steuer_code == 2:
                Meldung = "AUS (WR belassen)"
                Parameter = 'exit1'
            if Prog_Steuer_code == 3:
                Meldung = "Analyse in Crontab.log"
                Parameter = 'logging'
            if Prog_Steuer_code == 4:
                Meldung = "Ladesteuerung:" + str(Optionen)
                Parameter = 'schreiben'
                Options = Optionen

        return(Parameter, Meldung, Options)
    
    def get_uuid(self, argv, schluessel):

        # uuid für die Instanz erzeugen
        uuid_tmp = sqlall.getSQLsteuerdaten(schluessel)
        heute = date.today().strftime("%Y-%m-%d")
        lastday = ''
        if not uuid_tmp:
            import uuid
            uuid = str(uuid.uuid4())
        else:
            uuid_ar = [next(iter(uuid_tmp)), *uuid_tmp[next(iter(uuid_tmp))].values()]
            uuid = uuid_ar[3]
            lastday = uuid_ar[0]

        if (lastday != heute):
            import sqlite3
            with sqlite3.connect('CONFIG/Prog_Steuerung.sqlite') as zeiger:
                # Wenn uuid zu alt in DB schreiben
                sql_anweisung = """
                    INSERT INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ID, Schluessel) DO UPDATE SET
                        Zeit = excluded.Zeit,
                        Res_Feld1 = excluded.Res_Feld1,
                        Res_Feld2 = excluded.Res_Feld2,
                        Options = excluded.Options
                    """
                zeiger.execute(sql_anweisung, ('uuid', 'uuid', heute, '0', '0', uuid))
            import threading
            import requests
            url = "https://tuxis.de/GEN24_LOG/save_uuid.php?UUID="+uuid+"&DATE="+heute
            def fire_and_forget():
                try:
                    requests.get(url, timeout=0.1)
                except Exception:
                    pass
            threading.Thread(target=fire_and_forget, daemon=True).start()


        return()
