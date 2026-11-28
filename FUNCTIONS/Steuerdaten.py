# Hier die Parameter aus der WebUI Settings lesen
import FUNCTIONS.SQLall
    
sqlall = FUNCTIONS.SQLall.sqlall()

class readcontroldata:

    def getParameter(self, argv, schluessel):
        Parameter = ""
        Meldung = ""
        if len(argv) > 1 :
            Parameter = argv[1]
        # Prog_Steuerung.json lesen
        Prog_Steuer_code_tmp = sqlall.getSQLsteuerdaten(schluessel)
        if not Prog_Steuer_code_tmp:
            # Zeile fehlt (z.B. gelöscht): Standardzeilen wieder anlegen (INSERT OR IGNORE) und neu lesen
            sqlall.create_database_ProgSteuerung('CONFIG/Prog_Steuerung.sqlite')
            Prog_Steuer_code_tmp = sqlall.getSQLsteuerdaten(schluessel)
        if Prog_Steuer_code_tmp:
            Prog_Steuer_code = list(Prog_Steuer_code_tmp.values())[0]['Res_Feld1']
            Optionen_sql = list(Prog_Steuer_code_tmp.values())[0]['Options']
        else:
            # Auch danach nichts vorhanden: wie WebUI "aus" => Aufrufparameter gelten
            Prog_Steuer_code = 0
            Optionen_sql = ''
        Optionen_sql = Optionen_sql or ''
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
