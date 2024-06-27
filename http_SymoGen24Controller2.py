from datetime import datetime, timedelta
import pytz
import requests
from ping3 import ping
from sys import argv
import json
from FUNCTIONS.functions import loadConfig, loadWeatherData, loadPVReservierung, getVarConf, save_SQLite
from FUNCTIONS.fun_Ladewert import getLadewertinGrenzen, getRestTagesPrognoseUeberschuss, getPrognoseLadewert, setLadewert, \
        getPrognoseMorgen, globalfrommain, getAC_KapaLadewert, getParameter
from FUNCTIONS.fun_API import get_API
from FUNCTIONS.fun_http import get_time_of_use, send_request


if __name__ == '__main__':
        config = loadConfig('config.ini')
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"


        host_ip = getVarConf('gen24','hostNameOrIp', 'str')
        user = getVarConf('gen24','user', 'str')
        password = getVarConf('gen24','password', 'str')
        # Hier Hochkommas am Anfang und am Ende enternen
        password = password[1:-1]

        alterLadewert = 0
        result_get_time_of_use = get_time_of_use(host_ip, user, password)
        for element in result_get_time_of_use:
            if element['Active'] == True and element['ScheduleType'] == 'CHARGE_MAX':
                alterLadewert = element['Power']

        # WebUI-Parameter lesen und aus Prog_Steuerung.json bestimmen
        print_level = getVarConf('Ladeberechnung','print_level','eval')
        Parameter = getParameter(argv)
        Ausgabe_Parameter = ''
        if len(argv) > 1:
            argv[1] = Parameter[0]
        else:
            argv.append(Parameter[0])
        if(Parameter[1] != "" and print_level >= 1):
            Ausgabe_Parameter = ">>>Parameteränderung durch WebUI-Settings: "  + str(Parameter[1])
            if(Parameter[1] == "AUS"):
                # Batteriemangement zurücksetzen
                if result_get_time_of_use != []:
                    response = send_request('/config/timeofuse', method='POST', payload ='{"timeofuse":[]}')
                    print("Batteriemanagementeinträge gelöscht!")
                print(now, "ProgrammSTOPP durch WebUI-Settings: ", Parameter[1])
                exit()

        if ping(host_ip):
            # Nur ausführen, wenn WR erreichbar
            try:            
                    newPercent = None
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< E I N >>>>>>>\n\n"
    
                    ###############################
    
                    weatherfile = getVarConf('env','filePathWeatherData','str')
                    data = loadWeatherData(weatherfile)

    
                    # Benoetigte Variablen aus config.ini definieren und auf Zahlen prüfen
                    BattVollUm = getVarConf('Ladeberechnung','BattVollUm','eval')
                    BatSparFaktor = getVarConf('Ladeberechnung','BatSparFaktor','eval')
                    MaxLadung = getVarConf('Ladeberechnung','MaxLadung','eval')
                    LadungAus = getVarConf('Ladeberechnung','LadungAus','eval')
                    Akkuschonung = getVarConf('Ladeberechnung','Akkuschonung','eval')
                    Einspeisegrenze = getVarConf('Ladeberechnung','Einspeisegrenze','eval')
                    WR_Kapazitaet = getVarConf('Ladeberechnung','WR_Kapazitaet','eval')
                    PV_Leistung_Watt = getVarConf('Ladeberechnung','PV_Leistung_Watt','eval')
                    Grundlast = getVarConf('Ladeberechnung','Grundlast','eval')
                    MindBattLad = getVarConf('Ladeberechnung','MindBattLad','eval')
                    GrenzwertGroestePrognose = getVarConf('Ladeberechnung','GrenzwertGroestePrognose','eval')
                    WRSchreibGrenze_nachOben = getVarConf('Ladeberechnung','WRSchreibGrenze_nachOben','eval')
                    WRSchreibGrenze_nachUnten = getVarConf('Ladeberechnung','WRSchreibGrenze_nachUnten','eval')
                    FesteLadeleistung = getVarConf('Ladeberechnung','FesteLadeleistung','eval')
                    Fallback_on = getVarConf('Fallback','Fallback_on','eval')
                    Cronjob_Minutenabstand = getVarConf('Fallback','Cronjob_Minutenabstand','eval')
                    Fallback_Zeitabstand_Std = getVarConf('Fallback','Fallback_Zeitabstand_Std','eval')
                    Push_Message_EIN = getVarConf('messaging','Push_Message_EIN','eval')
                    PV_Reservierung_steuern = getVarConf('Reservierung','PV_Reservierung_steuern','eval')
                    Batterieentlandung_steuern = getVarConf('Entladung','Batterieentlandung_steuern','eval')
                    WREntladeSchreibGrenze_Watt = getVarConf('Entladung','WREntladeSchreibGrenze_Watt','eval')
                    EntladeGrenze_steuern = getVarConf('Entladung','EntladeGrenze_steuern','eval')

                    # um Divison durch Null zu verhindern kleinsten Wert setzen
                    if BatSparFaktor < 0.1:
                        BatSparFaktor = 0.1
                                       
                    # Bei Akkuschonung BattVollUm eine Stunde vor verlegen
                    if Akkuschonung == 1:
                        BattVollUm = BattVollUm - 1

                    # Grundlast je Wochentag, wenn Grundlast == 0
                    if (Grundlast == 0):
                        try:
                            Grundlast_WoT = getVarConf('Ladeberechnung','Grundlast_WoT','str')
                            Grundlast_WoT_Array = Grundlast_WoT.split(',')
                            Grundlast = eval(Grundlast_WoT_Array[datetime.today().weekday()])
                        except:
                            print("ERROR: Grundlast für den Wochentag konnte nicht gelesen werden, Grundlast = 0 !!")
                            Grundlast = 0

                    API = get_API()
                    Battery_Status = API['BAT_MODE']
                    # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 2.0, AKKU AUS
                    # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 0.0, AKKU EIN
                    if (Battery_Status == 2):
                        print(datetime.now())
                        print("Batterie ist Offline keine Steuerung möglich!!! ")
                        print()
                        exit()
                    BattganzeLadeKapazWatt = (API['BattganzeLadeKapazWatt']) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattganzeKapazWatt = (API['BattganzeKapazWatt']) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattStatusProz = API['BattStatusProz']
                    BattKapaWatt_akt = API['BattKapaWatt_akt']
                    aktuelleEinspeisung = API['aktuelleEinspeisung']
                    aktuellePVProduktion = API['aktuellePVProduktion']
                    aktuelleBatteriePower = API['aktuelleBatteriePower']
                    GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower

                    oldPercent = int(alterLadewert/BattganzeLadeKapazWatt*10000)

                    # Reservierungsdatei lesen, wenn Reservierung eingeschaltet
                    reservierungdata = {}
                    if  PV_Reservierung_steuern == 1:
                        Reservierungsdatei = getVarConf('Reservierung','PV_ReservieungsDatei','str')
                        reservierungdata = loadPVReservierung(Reservierungsdatei)

                    # 0 = nicht auf WR schreiben, 1 = auf WR schreiben
                    newPercent_schreiben = 0
    
                    format_aktStd = "%Y-%m-%d %H:00:00"
    
    
                    #######################################
                    ## Ab hier geht die Berechnung los
                    #######################################
    
                    TagesPrognoseUeberschuss = 0
                    TagesPrognoseGesamt = 0
                    aktuellerLadewert = 0
                    PrognoseAbzugswert = 0
                    Grundlast_Summe = 0
                    aktuelleVorhersage = 0
                    LadewertGrund = ""

                    # WRSchreibGrenze_nachUnten ab 90% Batteriestand prozentual erhöhen (ersetzen von BatterieVoll!!)
                    if ( BattStatusProz > 90 ):
                        WRSchreibGrenze_nachUnten = int(WRSchreibGrenze_nachUnten * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachUnten: " + str(WRSchreibGrenze_nachUnten) +"\n"
                        WRSchreibGrenze_nachOben = int(WRSchreibGrenze_nachOben * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachOben: " + str(WRSchreibGrenze_nachOben) +"\n"

                    # Hier Variablen an die Module  FUNCTIONS.fun_Ladewert übergeben
                    globalfrommain(now, DEBUG_Ausgabe, BattVollUm, data, PV_Reservierung_steuern, \
                    reservierungdata, Grundlast, Einspeisegrenze, WR_Kapazitaet, BattKapaWatt_akt, \
                    MaxLadung, BatSparFaktor, PrognoseAbzugswert, aktuelleBatteriePower, BattganzeLadeKapazWatt, \
                    LadungAus, oldPercent)

                    # Prognoseberechnung mit Funktion getRestTagesPrognoseUeberschuss
                    PrognoseUNDUeberschuss = getRestTagesPrognoseUeberschuss()
                    TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                    TagesPrognoseGesamt = PrognoseUNDUeberschuss[1]
                    PrognoseAbzugswert = PrognoseUNDUeberschuss[2]
                    Grundlast_Summe = PrognoseUNDUeberschuss[3]
                    GroestePrognose = PrognoseUNDUeberschuss[4]

                    # Nun der aktuellen Ladewert mit dem ermittelten PrognoseAbzugswert bestimmen
                    AktuellenLadewert_Array = getPrognoseLadewert( PrognoseAbzugswert )
                    aktuellerLadewert = AktuellenLadewert_Array[0]
                    aktuelleVorhersage = AktuellenLadewert_Array[1]
                    LadewertGrund = AktuellenLadewert_Array[2]
                    DEBUG_Ausgabe = AktuellenLadewert_Array[3]
                    AktuellenLadewert_Array = getAC_KapaLadewert(WRSchreibGrenze_nachOben, aktuellerLadewert, aktuellePVProduktion, LadewertGrund, alterLadewert, PV_Leistung_Watt)
                    aktuellerLadewert = AktuellenLadewert_Array[0]
                    LadewertGrund = AktuellenLadewert_Array[1]

                    # DEBUG_Ausgabe der Ladewertermittlung 
                    DEBUG_Ausgabe += "\nDEBUG TagesPrognoseUeberschuss: " + str(TagesPrognoseUeberschuss) + ", Grundlast: " + str(Grundlast)
                    DEBUG_Ausgabe += ", aktuellerLadewert: " + str(aktuellerLadewert) + "\n"


                    # Wenn über die PV-Planung manuelle Ladung angewählt wurde
                    MaxladungDurchPV_Planung = ""
                    if (PV_Reservierung_steuern == 1) and (reservierungdata.get('ManuelleSteuerung')):
                        FesteLadeleistung = MaxLadung * reservierungdata.get('ManuelleSteuerung')
                        if (reservierungdata.get('ManuelleSteuerung') != 0):
                            MaxladungDurchPV_Planung = "Manuelle Ladesteuerung in PV-Planung ausgewählt."

                    # Wenn die Variable "FesteLadeleistung" größer "0" ist, wird der Wert fest als Ladeleistung in Watt geschrieben einstellbare Wattzahl
                    if FesteLadeleistung > 0:
                        DATA = setLadewert(FesteLadeleistung, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                        aktuellerLadewert = FesteLadeleistung
                        newPercent = DATA[0]
                        if newPercent == oldPercent:
                            newPercent_schreiben = 0
                        else:
                            newPercent_schreiben = 1
                        if MaxladungDurchPV_Planung == "":
                            LadewertGrund = "FesteLadeleistung"
                        else:
                            LadewertGrund = MaxladungDurchPV_Planung
    
                    # Hier Volle Ladung, wenn Stunde aus BattVollUm erreicht ist!
                    elif (int(datetime.strftime(now, "%H")) >= int(BattVollUm)):
                         aktuellerLadewert = MaxLadung
                         DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                         newPercent = DATA[0]
                         newPercent_schreiben = DATA[1]
                         LadewertGrund = "Stunde aus BattVollUm erreicht!!"
        
                    else:

                        # Schaltverzögerung für MindBattLad
                        if (alterLadewert+2 > MaxLadung):
                            MindBattLad = MindBattLad +5

                        if ((BattStatusProz < MindBattLad)):
                            # volle Ladung ;-)
                            aktuellerLadewert = MaxLadung
                            DATA = setLadewert(MaxLadung, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]
                            LadewertGrund = "BattStatusProz < MindBattLad"
    
                        else:
    
                            if (TagesPrognoseGesamt > Grundlast) and ((TagesPrognoseGesamt - Grundlast_Summe) < BattKapaWatt_akt):
                                # Auch hier die Schaltverzögerung anbringen und dann MaxLadung, also immer nach oben.
                                if BattKapaWatt_akt + Grundlast_Summe - TagesPrognoseGesamt < WRSchreibGrenze_nachOben:
                                    # Nach Prognoseberechnung darf es trotzdem nach oben gehen aber nicht von MaxLadung nach unten !
                                    WRSchreibGrenze_nachUnten = 100000
                                    DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    # Nur wenn newPercent_schreiben = 0 dann LadewertGrund mit Hinweis übreschreiben
                                    if newPercent_schreiben == 0:
                                        newPercent = oldPercent
                                        LadewertGrund = "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt (Unterschied weniger als Schreibgrenze)"
                                else:
                                    # volle Ladung ;-)
                                    aktuellerLadewert = MaxLadung
                                    DATA = setLadewert(MaxLadung, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    LadewertGrund = "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt"
    
                            # PrognoseAbzugswert - 100 um Schaltverzögerung wieder nach unten zu erreichen
                            elif (TagesPrognoseUeberschuss < BattKapaWatt_akt) and (PrognoseAbzugswert - 100 <= Grundlast):
                                # Auch hier die Schaltverzögerung anbringen und dann MaxLadung, also immer nach oben.
                                if BattKapaWatt_akt - TagesPrognoseUeberschuss < WRSchreibGrenze_nachOben:
                                    # Nach Prognoseberechnung darf es trotzdem nach oben gehen aber nicht von MaxLadung nach unten !
                                    WRSchreibGrenze_nachUnten = 100000
                                    DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    # Nur wenn newPercent_schreiben = 0 dann LadewertGrund mit Hinweis übreschreiben
                                    if newPercent_schreiben == 0:
                                        LadewertGrund = "PrognoseAbzugswert nahe Grundlast (Unterschied weniger als Schreibgrenze)"
                                else:
                                    # volle Ladung ;-)
                                    aktuellerLadewert = MaxLadung
                                    DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    LadewertGrund = "PrognoseAbzugswert kleiner Grundlast und Schreibgrenze"

                            else: 
                                DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]

                        # Wenn größter Prognosewert je Stunde ist kleiner als GrenzwertGroestePrognose volle Ladung
                        if GrenzwertGroestePrognose > GroestePrognose:
                            aktuellerLadewert = MaxLadung
                            DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]
                            LadewertGrund = "Größter Prognosewert " + str(GroestePrognose) + " ist kleiner als GrenzwertGroestePrognose " + str(GrenzwertGroestePrognose)

                    # Wenn Akkuschonung = 1 ab 80% Batterieladung mit Ladewert runter fahren
                    if Akkuschonung == 1:
                        Ladefaktor = 1
                        BattStatusProz_Grenze = 100
                        if BattStatusProz > 80:
                            Ladefaktor = 0.2
                            AkkuSchonGrund = '80%, Ladewert = 0.2C'
                            BattStatusProz_Grenze = 80
                        if BattStatusProz > 90:
                            Ladefaktor = 0.1
                            AkkuSchonGrund = '90%, Ladewert = 0.1C'
                            BattStatusProz_Grenze = 90
                        # Bei Akkuschonung Schaltverzögerung (hysterese) einbauen, wenn Ladewert ist bereits der Akkuschonwert (+/- 3%) BattStatusProz_Grenze 5% runter
                        AkkuschonungLadewert = (BattganzeKapazWatt * Ladefaktor)
                        if ( abs(AkkuschonungLadewert - alterLadewert) < 3 ):
                            BattStatusProz_Grenze = BattStatusProz_Grenze * 0.95

                        if BattStatusProz > BattStatusProz_Grenze:
                            DEBUG_Ausgabe += "\nDEBUG <<<<<< Meldungen von Akkuschonung >>>>>>> "
                            DEBUG_Ausgabe += "\nDEBUG AkkuschonungLadewert-alterLadewert: " + str(abs(AkkuschonungLadewert - alterLadewert))
                            DEBUG_Ausgabe += "\nDEBUG BattStatusProz_Grenze: " + str(BattStatusProz_Grenze)
                            DEBUG_Ausgabe += "\nDEBUG aktuelleVorhersage - (Grundlast /2) > AkkuschonungLadewert? " + str(aktuelleVorhersage - (Grundlast /2))
                            DEBUG_Ausgabe += "\nDEBUG AkkuschonungLadewert: " + str(AkkuschonungLadewert) + "\n"
                            DEBUG_Ausgabe += "DEBUG aktuellerLadewert: " + str(aktuellerLadewert) + "\n"
                            # Um das setzen der Akkuschonung zu verhindern, wenn zu wenig PV Energie kommt oder der Akku wieder entladen wird nur bei entspechender Vorhersage anwenden
                            if (AkkuschonungLadewert < aktuellerLadewert or AkkuschonungLadewert < alterLadewert + 10) and aktuelleVorhersage - (Grundlast /2) > AkkuschonungLadewert:
                                aktuellerLadewert = AkkuschonungLadewert
                                WRSchreibGrenze_nachUnten = aktuellerLadewert / 5
                                WRSchreibGrenze_nachOben = aktuellerLadewert / 5
                                DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]
                                LadewertGrund = "Akkuschonung: Ladestand > " + AkkuSchonGrund

                    # Wenn die aktuellePVProduktion < 10 Watt ist, nicht schreiben, 
                    # um 0:00Uhr wird sonst immer Ladewert 0 geschrieben!
                    if aktuellePVProduktion < 10:
                        newPercent_schreiben = 0
                        LadewertGrund = "Nicht schreiben, da PVProduktion < 10 Watt!"

                    # Auf ganze Watt runden
                    aktuellerLadewert = int(aktuellerLadewert)

                    if print_level >= 1:
                        try:
                            print("******* BEGINN: ", datetime.now(),"******* ")
                            print("\n## HTTP-LADESTEUERUNG ##")
                            if(Ausgabe_Parameter != ''): print(Ausgabe_Parameter)
                            print("aktuellePrognose:           ", aktuelleVorhersage)
                            print("RestTagesPrognose:          ", TagesPrognoseGesamt)
                            print("PrognoseAbzugswert/Stunde:  ", PrognoseAbzugswert)
                            print("Grundlast_Summe für Tag:    ", Grundlast_Summe)
                            print("aktuellePVProduktion/Watt:  ", aktuellePVProduktion)
                            print("aktuelleEinspeisung/Watt:   ", aktuelleEinspeisung)
                            print("aktuelleBatteriePower/Watt: ", aktuelleBatteriePower)
                            print("GesamtverbrauchHaus/Watt:   ", GesamtverbrauchHaus)
                            print("aktuelleBattKapazität/Watt: ", BattKapaWatt_akt)
                            print("Batteriestatus in Prozent:  ", BattStatusProz,"%")
                            print("LadewertGrund: ", LadewertGrund)
                            print("Bisheriger Ladewert/Watt:   ", alterLadewert)
                            print("Bisheriger Ladewert/Prozent:", oldPercent/100,"%")
                            print("Neuer Ladewert/Watt:        ", aktuellerLadewert)
                            print("Neuer Ladewert/Prozent:     ", newPercent/100,"%")
                            print("newPercent_schreiben:       ", newPercent_schreiben)
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

                    BatteryMaxDischarge = 0
                    Neu_BatteryMaxDischarge = 0

                    if  Batterieentlandung_steuern == 1:
                        MaxEntladung = BattganzeLadeKapazWatt

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADESTEUERUNG >>>>>>>>>>>>>"
                        for element in result_get_time_of_use:
                            if element['Active'] == True and element['ScheduleType'] == 'DISCHARGE_MAX':
                                BatteryMaxDischarge = element['Power']

                        # EntladeSteuerungFile lesen
                        EntladeSteuerungFile = getVarConf('Entladung','Akku_EntladeSteuerungsFile','str')
                        entladesteurungsdata = loadPVReservierung(EntladeSteuerungFile)
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
                        if len(argv) > 1 and (argv[1] == "schreiben"):
                            payload_text = '{"Active":true,"Power":' + str(aktuellerLadewert) + \
                            ',"ScheduleType":"CHARGE_MAX","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                            if  Batterieentlandung_steuern == 1:
                                payload_text += ',{"Active":true,"Power":' + str(Neu_BatteryMaxDischarge) + \
                                ',"ScheduleType":"DISCHARGE_MAX","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                            response = send_request('/config/timeofuse', method='POST', payload ='{"timeofuse":[' + str(payload_text) + ']}')
                            bereits_geschrieben = 1
                            if newPercent_schreiben == 1:
                                Schreib_Ausgabe = Schreib_Ausgabe + "CHARGE_MAX per HTTP geschrieben: " + str(aktuellerLadewert) + "W\n"
                            if Neu_BatteryMaxDischarge != BatteryMaxDischarge:
                                Schreib_Ausgabe = Schreib_Ausgabe + "DISCHARGE_MAX per HTTP geschrieben: " + str(Neu_BatteryMaxDischarge) + "W\n"
                            Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei Ladegrenze schreiben: " + str(response)
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Es wurde nix geschrieben, da NICHT \"schreiben\" übergeben wurde: \n"
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Alte und Neue Werte unterscheiden sich weniger als die Schreibgrenzen des WR, NICHTS zu schreiben!!\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)

                    ######## WR Batteriemanagement ENDE
    
                    # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
                    if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
                        Push_Message_Url = getVarConf('messaging','Push_Message_Url','str')
                        apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
                        print("PushMeldung an ", Push_Message_Url, " gesendet.\n")


                    ### LOGGING, Schreibt mit den übergebenen Daten eine CSV- oder SQlite-Datei
                    ## nur wenn "schreiben" oder "logging" übergeben worden ist
                    Logging_ein = getVarConf('Logging','Logging_ein','eval')
                    if Logging_ein == 1:
                        Logging_Schreib_Ausgabe = ""
                        if len(argv) > 1 and (argv[1] == "schreiben" or argv[1] == "logging"):
                            Logging_file = getVarConf('Logging','Logging_file','str')
                            # In die DB werden die liftime Verbrauchszählerstände gespeichert
                            save_SQLite(Logging_file, API['AC_Produktion'], API['DC_Produktion'], API['Netzverbrauch'], API['Einspeisung'], \
                            API['Batterie_IN'], API['Batterie_OUT'], aktuelleVorhersage, BattStatusProz)
                            Logging_Schreib_Ausgabe = 'Daten wurden in die SQLite-Datei gespeichert!'
                        else:
                            Logging_Schreib_Ausgabe = "Logging wurde NICHT gespeichert, da NICHT \"logging\" oder \"schreiben\" übergeben wurde:\n" 

                        if print_level >= 1:
                            print(Logging_Schreib_Ausgabe)
                    # LOGGING ENDE



                    #DEBUG ausgeben
                    if print_level >= 2:
                        print(DEBUG_Ausgabe)
                    if print_level >= 1:
                        print("************* ENDE: ", datetime.now(),"************* \n")


            except OSError:
                print("Es ist ein Fehler aufgetreten!!!")


        else:
            print(datetime.now())
            print("WR offline")

