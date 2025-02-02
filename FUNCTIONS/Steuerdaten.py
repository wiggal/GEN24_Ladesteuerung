# Hier die Parameter aus der WebUI Settings lesen
import json
import FUNCTIONS.SQLall
    
sqlall = FUNCTIONS.SQLall.sqlall()

class readcontroldata:

    def loadPVReservierung(self, controlfile):
        self.controlfile = controlfile
        reservierungdata = None
        with open(self.controlfile) as json_file:
            reservierungdata = json.load(json_file)
        try:
            with open(self.controlfile) as json_file:
                reservierungdata = json.load(json_file)
        except:
                print("ERROR: Reservierungsdatei fehlt, bitte erzeugen oder Option abschalten !!")
                exit()
        return reservierungdata

    def getParameter(self, argv, schluessel):
        Parameter = ""
        Meldung = ""
        if len(argv) > 1 :
            Parameter = argv[1]
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
        if Prog_Steuer_code == 0:
            if Parameter == 'schreiben':
                Options = ['logging','laden','entladen','optimierung','notstrom','dynamicprice']
            else:
                Options = Parameter.split(",")
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
    
