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
        # print("Prog_Steuer_code: ", Prog_Steuer_code)
        if Prog_Steuer_code == 1:
            Meldung = "AUS"
            Parameter = 'exit'
        if Prog_Steuer_code == 2:
            Meldung = "Analyse in Crontab.log"
            Parameter = 'analyse'
        if Prog_Steuer_code == 3:
            Meldung = "NUR Logging"
            Parameter = 'logging'
        if Prog_Steuer_code == 4:
            Meldung = "WR-Steuerung und Logging"
            Parameter = 'schreiben'
        return(Parameter, Meldung)
    
