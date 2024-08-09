from datetime import datetime, timedelta
import pytz
import json
import requests
from ping3 import ping
from sys import argv
import FUNCTIONS.PrognoseLadewert
import FUNCTIONS.Steuerdaten
import FUNCTIONS.functions
import FUNCTIONS.GEN24_API
import FUNCTIONS.SQLall
import FUNCTIONS.httprequest


if __name__ == '__main__':
        basics = FUNCTIONS.functions.basics()
        config = basics.loadConfig(['default', 'charge'])
        request = FUNCTIONS.httprequest.request()
        sqlall = FUNCTIONS.SQLall.sqlall()
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"


        host_ip = basics.getVarConf('gen24','hostNameOrIp', 'str')
        user = basics.getVarConf('gen24','user', 'str')
        password = basics.getVarConf('gen24','password', 'str')
        # Hier Hochkommas am Anfang und am Ende enternen
        password = password[1:-1]

        alterLadewert = 0
        result_get_time_of_use = request.get_time_of_use(host_ip, user, password)
        for element in result_get_time_of_use:
            if element['Active'] == True and element['ScheduleType'] == 'CHARGE_MAX':
                alterLadewert = element['Power']

        # WebUI-Parameter aus CONFIG/Prog_Steuerung.sqlite lesen
        SettingsPara = FUNCTIONS.Steuerdaten.readcontroldata()
        print_level = basics.getVarConf('env','print_level','eval')
        Parameter = SettingsPara.getParameter(argv, 'ProgrammStrg')
        Options = Parameter[2]
        
        Ausgabe_Parameter = ''
        if(Parameter[1] != "" and print_level >= 1):
            Ausgabe_Parameter = ">>>Parameteränderung durch WebUI-Settings: "  + str(Parameter[1])
            if(Parameter[0] == "exit0"):
                # Batteriemangement zurücksetzen
                if result_get_time_of_use != []:
                    response = request.send_request('/config/timeofuse', method='POST', payload ='{"timeofuse":[]}')
                    print("Batteriemanagementeinträge gelöscht!")
                # Ende Programm
            if(Parameter[0] == "exit0") or (Parameter[0] == "exit1"):
                print(now, "ProgrammSTOPP durch WebUI-Settings: ", Parameter[1])
                exit()
                # Ende Programm

        if ping(host_ip):
            # Nur ausführen, wenn WR erreichbar
            try:            
                    newPercent = None
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< E I N >>>>>>>\n\n"
    
                    ###############################
    
                    weatherfile = basics.getVarConf('env','filePathWeatherData','str')
                    weatherdata = basics.loadWeatherData(weatherfile)

    
                    # Benoetigte Variablen definieren und auf Zahlen prüfen
                    BatSparFaktor = basics.getVarConf('Ladeberechnung','BatSparFaktor','eval')
                    MaxLadung = basics.getVarConf('Ladeberechnung','MaxLadung','eval')
                    Akkuschonung = basics.getVarConf('Ladeberechnung','Akkuschonung','eval')
                    Einspeisegrenze = basics.getVarConf('Ladeberechnung','Einspeisegrenze','eval')
                    WR_Kapazitaet = basics.getVarConf('Ladeberechnung','WR_Kapazitaet','eval')
                    PV_Leistung_Watt = basics.getVarConf('Ladeberechnung','PV_Leistung_Watt','eval')
                    Grundlast = basics.getVarConf('Ladeberechnung','Grundlast','eval')
                    MindBattLad = basics.getVarConf('Ladeberechnung','MindBattLad','eval')
                    GrenzwertGroestePrognose = basics.getVarConf('Ladeberechnung','GrenzwertGroestePrognose','eval')
                    WRSchreibGrenze_nachOben = basics.getVarConf('Ladeberechnung','WRSchreibGrenze_nachOben','eval')
                    WRSchreibGrenze_nachUnten = basics.getVarConf('Ladeberechnung','WRSchreibGrenze_nachUnten','eval')
                    FesteLadeleistung = basics.getVarConf('Ladeberechnung','FesteLadeleistung','eval')
                    Fallback_on = basics.getVarConf('Fallback','Fallback_on','eval')
                    Cronjob_Minutenabstand = basics.getVarConf('Fallback','Cronjob_Minutenabstand','eval')
                    Fallback_Zeitabstand_Std = basics.getVarConf('Fallback','Fallback_Zeitabstand_Std','eval')
                    Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
                    PV_Reservierung_steuern = basics.getVarConf('Reservierung','PV_Reservierung_steuern','eval')
                    Batterieentlandung_steuern = basics.getVarConf('Entladung','Batterieentlandung_steuern','eval')
                    WREntladeSchreibGrenze_Watt = basics.getVarConf('Entladung','WREntladeSchreibGrenze_Watt','eval')
                    EntladeGrenze_steuern = basics.getVarConf('Entladung','EntladeGrenze_steuern','eval')
                    EigenverbOpt_steuern = basics.getVarConf('EigenverbOptimum','EigenverbOpt_steuern','eval')
                    MaxEinspeisung = basics.getVarConf('EigenverbOptimum','MaxEinspeisung','eval')

                    # um Divison durch Null zu verhindern kleinsten Wert setzen
                    if BatSparFaktor < 0.1:
                        BatSparFaktor = 0.1
                                       
                    # Grundlast je Wochentag, wenn Grundlast == 0
                    if (Grundlast == 0):
                        try:
                            Grundlast_WoT = basics.getVarConf('Ladeberechnung','Grundlast_WoT','str')
                            Grundlast_WoT_Array = Grundlast_WoT.split(',')
                            Grundlast = eval(Grundlast_WoT_Array[datetime.today().weekday()])
                        except:
                            print("ERROR: Grundlast für den Wochentag konnte nicht gelesen werden, Grundlast = 0 !!")
                            Grundlast = 0

                    api = FUNCTIONS.GEN24_API.gen24api
                    API = api.get_API()
                    Battery_Status = API['BAT_MODE']
                    # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 2.0, AKKU AUS
                    # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 0.0, AKKU EIN
                    if (Battery_Status == 2):
                        print(datetime.now())
                        print("Batterie ist Offline keine Steuerung möglich!!! ")
                        print()
                        exit()
                    BattganzeLadeKapazWatt = (API['BattganzeLadeKapazWatt'])
                    BattganzeKapazWatt = (API['BattganzeKapazWatt'])
                    BattStatusProz = API['BattStatusProz']
                    BattKapaWatt_akt = API['BattKapaWatt_akt']
                    aktuelleEinspeisung = API['aktuelleEinspeisung'] * -1
                    aktuellePVProduktion = API['aktuellePVProduktion']
                    aktuelleBatteriePower = API['aktuelleBatteriePower']
                    GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower

                    oldPercent = int(alterLadewert/BattganzeLadeKapazWatt*10000)

                    # Reservierungsdatei lesen, wenn Reservierung eingeschaltet
                    reservierungdata = {}
                    if  PV_Reservierung_steuern == 1:
                        reservierungdata_tmp = sqlall.getSQLsteuerdaten('Reservierung')
                        # Spalte 1 und 2 aufaddieren
                        reservierungdata = dict()
                        for key in reservierungdata_tmp:
                            Res_Feld = 0
                            i = 0
                            for key2 in reservierungdata_tmp[key]:
                                if(i<2):
                                    Res_Feld += reservierungdata_tmp[key][key2]
                                i += 1
                            reservierungdata[key] = Res_Feld

                    # 0 = nicht auf WR schreiben, 1 = auf WR schreiben
                    newPercent_schreiben = 0
    
                    format_aktStd = "%Y-%m-%d %H:00:00"
    
    
                    #######################################
                    ## Ab hier geht die Berechnung los
                    #######################################
    
                    TagesPrognoseUeberschuss = 0
                    TagesPrognoseGesamt = 0
                    aktuellerLadewert = 0
                    PrognoseUberschuss = 0
                    Grundlast_Summe = 0
                    aktuelleVorhersage = 0
                    LadewertGrund = ""

                    # Klasse ProgLadewert initieren
                    progladewert = FUNCTIONS.PrognoseLadewert.progladewert(weatherdata, WR_Kapazitaet, reservierungdata, BattKapaWatt_akt, MaxLadung, Einspeisegrenze, aktuelleBatteriePower)

                    # WRSchreibGrenze_nachUnten ab 90% Batteriestand prozentual erhöhen (ersetzen von BatterieVoll!!)
                    if ( BattStatusProz > 90 ):
                        WRSchreibGrenze_nachUnten = int(WRSchreibGrenze_nachUnten * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachUnten: " + str(WRSchreibGrenze_nachUnten) +"\n"
                        WRSchreibGrenze_nachOben = int(WRSchreibGrenze_nachOben * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachOben: " + str(WRSchreibGrenze_nachOben) +"\n"

                    # BattVollUm setzen evtl. mit DIFF zum Sonnenuntergang
                    BattVollUm = basics.getVarConf('Ladeberechnung','BattVollUm','eval')
                    if BattVollUm <= 0:
                       BattVollUm = progladewert.getSonnenuntergang(PV_Leistung_Watt) + BattVollUm
                    # Bei Akkuschonung BattVollUm eine Stunde vor verlegen
                    if Akkuschonung > 0:
                        BattVollUm = BattVollUm - 1


                    # Geamtprognose und Ladewert berechnen mit Funktion getRestTagesPrognoseUeberschuss
                    PrognoseUNDUeberschuss = progladewert.getRestTagesPrognoseUeberschuss(BattVollUm, Grundlast)
                    TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                    TagesPrognoseGesamt = PrognoseUNDUeberschuss[1]
                    PrognoseUberschuss = PrognoseUNDUeberschuss[2]
                    Grundlast_Summe = PrognoseUNDUeberschuss[3]
                    GroestePrognose = PrognoseUNDUeberschuss[4]
                    aktuellerLadewert = PrognoseUNDUeberschuss[5]
                    LadewertGrund = PrognoseUNDUeberschuss[6]

                    # Aktuelle Prognose berechnen
                    AktuellenLadewert_Array = progladewert.getPrognoseLadewert()
                    aktuelleVorhersage = AktuellenLadewert_Array[0]
                    DEBUG_Ausgabe = AktuellenLadewert_Array[1]

                    # DEBUG_Ausgabe der Ladewertermittlung 
                    DEBUG_Ausgabe += "\nDEBUG TagesPrognoseUeberschuss: " + str(TagesPrognoseUeberschuss) + ", Grundlast: " + str(Grundlast)
                    DEBUG_Ausgabe += ", aktuellerLadewert: " + str(aktuellerLadewert) + "\n"


                    # Wenn über die PV-Planung manuelle Ladung angewählt wurde
                    MaxladungDurchPV_Planung = ""
                    ManuelleSteuerung = reservierungdata.get('ManuelleSteuerung')
                    if (PV_Reservierung_steuern == 1) and (ManuelleSteuerung >= 0):
                        FesteLadeleistung = BattganzeLadeKapazWatt * ManuelleSteuerung/100
                        MaxladungDurchPV_Planung = "Manuelle Ladesteuerung in PV-Planung ausgewählt."

                    # Wenn die Variable "FesteLadeleistung" größer "0" ist, wird der Wert fest als Ladeleistung in Watt geschrieben einstellbare Wattzahl
                    if FesteLadeleistung >= 0:
                        DATA = progladewert.setLadewert(FesteLadeleistung, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                        aktuellerLadewert = FesteLadeleistung
                        newPercent = DATA[0]
                        # wegen Rundung
                        if abs(newPercent - oldPercent) < 3:
                            newPercent_schreiben = 0
                        else:
                            newPercent_schreiben = 1
                        if MaxladungDurchPV_Planung == "":
                            LadewertGrund = "FesteLadeleistung"
                        else:
                            LadewertGrund = MaxladungDurchPV_Planung
    
                    # Hier Volle Ladung, wenn BattVollUm erreicht ist!
                    elif (int(datetime.strftime(now, "%H")) >= int(BattVollUm)):
                         aktuellerLadewert = MaxLadung
                         DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                         newPercent = DATA[0]
                         newPercent_schreiben = DATA[1]
                         LadewertGrund = "BattVollUm erreicht!!"
        
                    else:

                        # Schaltverzögerung für MindBattLad
                        if (alterLadewert + 2 > MaxLadung):
                            MindBattLad = MindBattLad + 5

                        if ((BattStatusProz < MindBattLad)):
                            # volle Ladung ;-)
                            aktuellerLadewert = MaxLadung
                            DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]
                            LadewertGrund = "BattStatusProz < MindBattLad"
    
                        else:
    
                            if (TagesPrognoseGesamt > Grundlast) and ((TagesPrognoseGesamt - Grundlast_Summe) < BattKapaWatt_akt):
                                # Auch hier die Schaltverzögerung anbringen und dann MaxLadung, also immer nach oben.
                                if BattKapaWatt_akt + Grundlast_Summe - TagesPrognoseGesamt < WRSchreibGrenze_nachOben:
                                    # Nach Prognoseberechnung darf es trotzdem nach oben gehen aber nicht von MaxLadung nach unten !
                                    WRSchreibGrenze_nachUnten = 100000
                                    DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    # Nur wenn newPercent_schreiben = 0 dann LadewertGrund mit Hinweis übreschreiben
                                    if newPercent_schreiben == 0:
                                        newPercent = oldPercent
                                        LadewertGrund = "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt (Unterschied weniger als Schreibgrenze)"
                                else:
                                    # volle Ladung ;-)
                                    aktuellerLadewert = MaxLadung
                                    DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    LadewertGrund = "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt"
    
                            # PrognoseUberschuss - 100 um Schaltverzögerung wieder nach unten zu erreichen
                            elif (TagesPrognoseUeberschuss < BattKapaWatt_akt) and (PrognoseUberschuss - 100 <= Grundlast):
                                # Auch hier die Schaltverzögerung anbringen und dann MaxLadung, also immer nach oben.
                                if BattKapaWatt_akt - TagesPrognoseUeberschuss < WRSchreibGrenze_nachOben:
                                    # Nach Prognoseberechnung darf es trotzdem nach oben gehen aber nicht von MaxLadung nach unten !
                                    WRSchreibGrenze_nachUnten = 100000
                                    DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    # Nur wenn newPercent_schreiben = 0 dann LadewertGrund mit Hinweis übreschreiben
                                    if newPercent_schreiben == 0:
                                        LadewertGrund = "PrognoseUberschuss nahe Grundlast (Unterschied weniger als Schreibgrenze)"
                                else:
                                    # volle Ladung ;-)
                                    aktuellerLadewert = MaxLadung
                                    DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    LadewertGrund = "PrognoseUberschuss kleiner Grundlast und Schreibgrenze"

                            else: 
                                DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]

                        # Wenn größter Prognosewert je Stunde ist kleiner als GrenzwertGroestePrognose volle Ladung
                        if GrenzwertGroestePrognose > GroestePrognose:
                            aktuellerLadewert = MaxLadung
                            DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]
                            LadewertGrund = "Größter Prognosewert " + str(GroestePrognose) + " ist kleiner als GrenzwertGroestePrognose " + str(GrenzwertGroestePrognose)

                    # Wenn Akkuschonung > 0 ab 80% Batterieladung mit Ladewert runter fahren
                    if Akkuschonung > 0:
                        Ladefaktor = 1
                        BattStatusProz_Grenze = 100
                        # Schaltverzoegerung neu 
                        if (BattStatusProz >= 78 and ( abs((BattganzeKapazWatt * 0.2) - alterLadewert) < 3 )) or BattStatusProz >= 80:
                            Ladefaktor = 0.2
                            AkkuSchonGrund = '80%, Ladewert = 0.2C'
                            BattStatusProz_Grenze = 80
                        if (BattStatusProz >= 88 and ( abs((BattganzeKapazWatt * 0.1) - alterLadewert) < 3 )) or BattStatusProz >= 90:
                            Ladefaktor = 0.1
                            AkkuSchonGrund = '90%, Ladewert = 0.1C'
                            BattStatusProz_Grenze = 90
                        if (BattStatusProz >= 94 and ( abs((BattganzeKapazWatt * 0.1* Akkuschonung) - alterLadewert) < 3 )) or BattStatusProz >= 95:
                            Ladefaktor = 0.1 * Akkuschonung
                            AkkuSchonGrund = '95%, Ladewert = ' + str(Ladefaktor) + 'C'
                            BattStatusProz_Grenze = 95

                        AkkuschonungLadewert = int(BattganzeKapazWatt * Ladefaktor)

                        if BattStatusProz >= BattStatusProz_Grenze:
                            DEBUG_Ausgabe += "\nDEBUG <<<<<< Meldungen von Akkuschonung >>>>>>> "
                            DEBUG_Ausgabe += "\nDEBUG AkkuschonungLadewert-alterLadewert: " + str(abs(AkkuschonungLadewert - alterLadewert))
                            DEBUG_Ausgabe += "\nDEBUG BattStatusProz_Grenze: " + str(BattStatusProz_Grenze)
                            DEBUG_Ausgabe += "\nDEBUG AkkuschonungLadewert: " + str(AkkuschonungLadewert) + "\n"
                            DEBUG_Ausgabe += "DEBUG aktuellerLadewert: " + str(aktuellerLadewert) + "\n"
                            # Um das setzen der Akkuschonung zu verhindern, wenn zu wenig PV Energie kommt oder der Akku wieder entladen wird nur bei entspechender Vorhersage anwenden
                            if (AkkuschonungLadewert < aktuellerLadewert or AkkuschonungLadewert < alterLadewert + 10) and aktuellePVProduktion > AkkuschonungLadewert:
                                aktuellerLadewert = AkkuschonungLadewert
                                WRSchreibGrenze_nachUnten = aktuellerLadewert / 5
                                WRSchreibGrenze_nachOben = aktuellerLadewert / 5
                                DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]
                                LadewertGrund = "Akkuschonung: Ladestand >= " + AkkuSchonGrund

                    # Wenn die aktuellePVProduktion < 10 Watt ist, nicht schreiben, 
                    # um 0:00Uhr wird sonst immer Ladewert 0 geschrieben!
                    if aktuellePVProduktion < 10:
                        # Für die Nacht zwingend auf MaxLadung, 
                        # da sonst mogends evtl nicht auf 0 gestelltwerden kann, wegen WRSchreibGrenze_nachUnten
                        if alterLadewert < MaxLadung -10 :
                            aktuellerLadewert = MaxLadung
                            DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, oldPercent)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]
                            LadewertGrund = "Auf MaxLadung stellen, da PVProduktion < 10 Watt!"
                        else:
                            newPercent_schreiben = 0
                            LadewertGrund = "Nicht schreiben, da PVProduktion < 10 Watt!"

                    # Auf ganze Watt runden
                    aktuellerLadewert = int(aktuellerLadewert)

                    if print_level >= 1:
                        try:
                            print("***** BEGINN: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"*****\n")
                            print("## HTTP-LADESTEUERUNG ##")
                            if(Ausgabe_Parameter != ''): print(Ausgabe_Parameter)
                            print("aktuellePrognose:           ", aktuelleVorhersage)
                            print("TagesPrognose - BattVollUm: ", TagesPrognoseGesamt,"-", BattVollUm)
                            print("PrognoseUberschuss/Stunde:  ", PrognoseUberschuss)
                            print("Grundlast_Summe für Tag:    ", Grundlast_Summe)
                            print("aktuellePVProduktion/Watt:  ", aktuellePVProduktion)
                            print("aktuelleEinspeisung/Watt:   ", aktuelleEinspeisung)
                            print("aktuelleBatteriePower/Watt: ", aktuelleBatteriePower)
                            print("GesamtverbrauchHaus/Watt:   ", GesamtverbrauchHaus)
                            print("aktuelleBattKapazität/Watt: ", BattKapaWatt_akt)
                            print("Batteriestatus in Prozent:  ", BattStatusProz,"%")
                            print("LadewertGrund: ", LadewertGrund)
                            print("Bisheriger Ladewert/Watt:   ", alterLadewert)
                            print("Neuer Ladewert/Watt:        ", aktuellerLadewert)
                            print()
                        except Exception as e:
                            print()
                            print("Fehler in den Printbefehlen, Ausgabe nicht möglich!")
                            print("Fehlermeldung:", e)
                            print()


                    DEBUG_Ausgabe+="\nDEBUG BattVollUm:                 " + str(BattVollUm) + "Uhr"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachUnten:  " + str(WRSchreibGrenze_nachUnten) + "W"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachOben:   " + str(WRSchreibGrenze_nachOben) + "W"
                    

                    ######## IN  WR Batteriemanagement schreiben, später gemeinsam
                    ######## E N T L A D E S T E U E R U N G  ab hier wenn eingeschaltet!

                    BatteryMaxDischarge = BattganzeLadeKapazWatt
                    Neu_BatteryMaxDischarge = BattganzeLadeKapazWatt

                    if  Batterieentlandung_steuern == 1:
                        MaxEntladung = BattganzeLadeKapazWatt

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADESTEUERUNG >>>>>>>>>>>>>"
                        for element in result_get_time_of_use:
                            if element['Active'] == True and element['ScheduleType'] == 'DISCHARGE_MAX':
                                BatteryMaxDischarge = element['Power']

                        # EntladeSteuerungdaten lesen
                        entladesteurungsdata = sqlall.getSQLsteuerdaten('ENTLadeStrg')
                        # Manuellen Entladewert lesen
                        if (entladesteurungsdata.get('ManuelleEntladesteuerung')):
                            MaxEntladung = int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']*BattganzeLadeKapazWatt / 100)
                            DEBUG_Ausgabe+="\nDEBUG MaxEntladung = entladesteurungsdata:" + str(MaxEntladung)

                        aktStd = datetime.strftime(now, "%H:00")

                        # Verbrauchsgrenze Entladung lesen
                        if (entladesteurungsdata.get(aktStd)):
                            VerbrauchsgrenzeEntladung = entladesteurungsdata[aktStd]['Res_Feld1']
                        else:
                            VerbrauchsgrenzeEntladung = 0

                        DEBUG_Ausgabe+="\nDEBUG VerbrauchsgrenzeEntladung aus Spalte 1: " + str(VerbrauchsgrenzeEntladung)
                        # Feste Entladegrenze lesen
                        if (entladesteurungsdata.get(aktStd)):
                            FesteEntladegrenze = entladesteurungsdata[aktStd]['Res_Feld2']
                        else:
                            FesteEntladegrenze = 0

                        DEBUG_Ausgabe+="\nDEBUG FesteEntladegrenze aus Spalte 2: " + str(FesteEntladegrenze)

                        # Wenn folgende Bedingungen wahr, Entladung neu schreiben
                        # Verbrauchsgrenze == 2000 && Feste Grenze == 0 (leer)
                        if (GesamtverbrauchHaus > VerbrauchsgrenzeEntladung and VerbrauchsgrenzeEntladung > 0 and FesteEntladegrenze == 0):
                            Neu_BatteryMaxDischarge = int(GesamtverbrauchHaus - VerbrauchsgrenzeEntladung)
                        # Verbrauchsgrenze == 2000 && Feste Grenze == 500 
                        elif (GesamtverbrauchHaus > VerbrauchsgrenzeEntladung and VerbrauchsgrenzeEntladung > 0 and FesteEntladegrenze > 0):
                            Neu_BatteryMaxDischarge = int(FesteEntladegrenze)
                        # Verbrauchsgrenze == 0 (leer) && Feste Grenze == 500
                        elif (VerbrauchsgrenzeEntladung == 0 and FesteEntladegrenze > 0):
                            Neu_BatteryMaxDischarge = int(FesteEntladegrenze)
                        else:
                            Neu_BatteryMaxDischarge = MaxEntladung

                        DEBUG_Ausgabe+="\nDEBUG Batterieentladegrenze NEU: " + str(Neu_BatteryMaxDischarge) + "%"

                        # Entladung_Daempfung, Unterschied muss größer WREntladeSchreibGrenze_Watt sein
                        WREntladeSchreibGrenze_Prozent = int(WREntladeSchreibGrenze_Watt / BattganzeLadeKapazWatt * 100 + 1)
                        if (abs(Neu_BatteryMaxDischarge - BatteryMaxDischarge) < WREntladeSchreibGrenze_Prozent):
                            Neu_BatteryMaxDischarge = BatteryMaxDischarge

                        ## Werte zum Überprüfen ausgeben
                        if print_level >= 1:
                            print("######### E N T L A D E S T E U E R U N G #########\n")
                            print("Feste Entladegrenze:       ", int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']*BattganzeLadeKapazWatt / 100), "W")
                            print("Batteriestatus in Prozent: ", BattStatusProz, "%")
                            print("GesamtverbrauchHaus:       ", GesamtverbrauchHaus, "W")
                            print("VerbrauchsgrenzeEntladung: ", VerbrauchsgrenzeEntladung, "W")
                            print("Batterieentladegrenze ALT: ", BatteryMaxDischarge, "W")
                            print("Batterieentladegrenze NEU: ", Neu_BatteryMaxDischarge, "W")
                            print()

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADESTEUERUNG >>>>>>>>>>>>>"


                    ### AB HIER SCHARF wenn Argument "schreiben" übergeben
                    ######## Ladeleistung und Entladeleistung in WR Batteriemanagement schreiben 

                    bereits_geschrieben = 0
                    Schreib_Ausgabe = ""
                    Push_Schreib_Ausgabe = ""
                    # Neuen Ladewert als HTTP_Request schreiben, wenn newPercent_schreiben == 1 
                    if newPercent_schreiben == 1 or Neu_BatteryMaxDischarge != BatteryMaxDischarge:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< LADEWERTE >>>>>>>>>>>>>"
                        DEBUG_Ausgabe+="\nDEBUG Folgender MAX_Ladewert neu zum Schreiben: " + str(aktuellerLadewert)
                        DEBUG_Ausgabe+="\nDEBUG Folgender MAX_ENT_Ladewert neu zum Schreiben: " + str(Neu_BatteryMaxDischarge)
                        payload_text = ''
                        trenner_komma = ''
                        if ('laden' in Options):
                            trenner_komma = ','
                            payload_text = '{"Active":true,"Power":' + str(aktuellerLadewert) + \
                            ',"ScheduleType":"CHARGE_MAX","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                        elif newPercent_schreiben == 1 :
                            Schreib_Ausgabe = Schreib_Ausgabe + "Ladesteuerung NICHT geschrieben, da Option \"laden\" NICHT gesetzt!\n"
                        if  ('entladen' in Options) and (Batterieentlandung_steuern == 1):
                            payload_text += str(trenner_komma) + '{"Active":true,"Power":' + str(Neu_BatteryMaxDischarge) + \
                            ',"ScheduleType":"DISCHARGE_MAX","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                        elif Neu_BatteryMaxDischarge != BatteryMaxDischarge:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Entladesteuerung NICHT geschrieben, da Option \"entladen\" NICHT gesetzt!\n"
                        # Wenn payload_text NICHT leer dann schreiben
                        if (payload_text != ''):
                            response = request.send_request('/config/timeofuse', method='POST', payload ='{"timeofuse":[' + str(payload_text) + ']}')
                            bereits_geschrieben = 1
                            if ('laden' in Options) and newPercent_schreiben == 1:
                                Schreib_Ausgabe = Schreib_Ausgabe + "CHARGE_MAX geschrieben: " + str(aktuellerLadewert) + "W\n"
                            if ('entladen' in Options) and Neu_BatteryMaxDischarge != BatteryMaxDischarge:
                                Schreib_Ausgabe = Schreib_Ausgabe + "DISCHARGE_MAX geschrieben: " + str(Neu_BatteryMaxDischarge) + "W\n"
                            Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei Ladegrenze schreiben: " + str(response)
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Änderungen kleiner Schreibgrenze!\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)

                    ######## WR Batteriemanagement ENDE

                    ######## Eigenverbrauchs-Optimierung  ab hier wenn eingeschaltet!
                    if  EigenverbOpt_steuern == 1:
                        EigenOptERG = progladewert.getEigenverbrauchOpt(host_ip, user, password, BattStatusProz, BattganzeKapazWatt, MaxEinspeisung)
                        PrognoseMorgen = EigenOptERG[0]
                        Eigen_Opt_Std = EigenOptERG[1]
                        Eigen_Opt_Std_neu = EigenOptERG[2]
                        Dauer_Nacht_Std = EigenOptERG[3]
                        AkkuZielProz = EigenOptERG[4]
                        DEBUG_Ausgabe += EigenOptERG[5]
                        aktuellePVProduktion_tmp = aktuellePVProduktion

                        # Wenn der Akku unter MindBattLad Optimierung auf 0 setzen
                        # Bereich ermoeglicht die Optimierung fuer den Tag zu setzen
                        # + 10, da wegen Hysterse bereits +5 weiter oben
                        if (BattStatusProz <= MindBattLad + 10):
                            Dauer_Nacht_Std = 2
                            aktuellePVProduktion_tmp = 0
                        if (BattStatusProz <= MindBattLad):
                            Eigen_Opt_Std_neu = 0

                        if (Dauer_Nacht_Std > 1 or BattStatusProz < AkkuZielProz) and aktuellePVProduktion_tmp < (Grundlast + MaxEinspeisung) * 1.5:
                            if print_level >= 1:
                                print("### Eigenverbrauchs-Optimierung ###")
                                print("Prognose Morgen: ", PrognoseMorgen, "KW")
                                print("Eigenverbrauchs-Opt. ALT: ", Eigen_Opt_Std, "W")
                                print("Eigenverbrauchs-Opt. NEU: ", Eigen_Opt_Std_neu, "W")
                                print()

                            Opti_Schreib_Ausgabe = ""

                            if (Eigen_Opt_Std_neu != Eigen_Opt_Std):
                                if ('optimierung' in Options):
                                    response = request.send_request('/config/batteries', method='POST', payload ='{"HYB_EM_POWER":'+ str(Eigen_Opt_Std_neu) + ',"HYB_EM_MODE":1}')
                                    bereits_geschrieben = 1
                                    DEBUG_Ausgabe+="\nDEBUG Meldung Eigenverbrauchs-Opt. schreiben: " + str(response)
                                    Opti_Schreib_Ausgabe = Opti_Schreib_Ausgabe + "Eigenverbrauchs-Opt.: " + str(Eigen_Opt_Std_neu) + "W geschrieben\n"
                                    Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Opti_Schreib_Ausgabe
                                else:
                                    Opti_Schreib_Ausgabe = Opti_Schreib_Ausgabe + "Eigenverbrauchs-Opt.: " + str(Eigen_Opt_Std_neu) +"W NICHT geschrieben,\nda Option \"optimierung\"  NICHT gesetzt!\n"
                            else:
                                Opti_Schreib_Ausgabe = Opti_Schreib_Ausgabe + "Eigenverbrauchs-Opt.: Keine Änderung!\n"

                            if print_level >= 1:
                                print(Opti_Schreib_Ausgabe)
                    ######## Eigenverbrauchs-Optimierung  ENDE!!!
    
                    # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
                    if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
                        Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
                        apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
                        print("PushMeldung an ", Push_Message_Url, " gesendet.\n")


                    ### LOGGING, Schreibt mit den übergebenen Daten eine CSV- oder SQlite-Datei
                    ## nur wenn "schreiben" oder "logging" übergeben worden ist
                    sqlall = FUNCTIONS.SQLall.sqlall()
                    Logging_ein = basics.getVarConf('Logging','Logging_ein','eval')
                    if Logging_ein == 1:
                        Logging_Schreib_Ausgabe = ""
                        if ('logging' in Options):
                            Logging_file = basics.getVarConf('Logging','Logging_file','str')
                            # In die DB werden die liftime Verbrauchszählerstände gespeichert
                            sqlall.save_SQLite(Logging_file, API['AC_Produktion'], API['DC_Produktion'], API['Netzverbrauch'], API['Einspeisung'], \
                            API['Batterie_IN'], API['Batterie_OUT'], aktuelleVorhersage, BattStatusProz)
                            Logging_Schreib_Ausgabe = 'In SQLite-Datei gespeichert!'
                        else:
                            Logging_Schreib_Ausgabe = "Logging NICHT gespeichert, da Option \"logging\" NICHT gesetzt!\n" 

                        if print_level >= 1:
                            print(Logging_Schreib_Ausgabe)
                    # LOGGING ENDE



                    #DEBUG ausgeben
                    if print_level >= 2:
                        print(DEBUG_Ausgabe)
                    if print_level >= 1:
                        print("***** ENDE: ", datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),"*****\n")


            except OSError:
                print("Es ist ein Fehler aufgetreten!!!")


        else:
            print(datetime.now())
            print("WR offline")

