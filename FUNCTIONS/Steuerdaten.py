# Hier die Parameter aus der WebUI Settings lesen
import json
    
class readcontroldata:
    #def __init__(self, test='2'):

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

    def getParameter(self, argv, controlfile):
        self.argv = argv
        self.controlfile = controlfile
        Parameter = ""
        Meldung = ""
        if len(self.argv) > 1 :
            Parameter = self.argv[1]
        # Prog_Steuerung.json lesen
        Prog_Steuer_code_tmp = self.loadPVReservierung(self.controlfile)
        Prog_Steuer_code = int(Prog_Steuer_code_tmp['Steuerung'])
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
    
