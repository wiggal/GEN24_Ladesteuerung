from datetime import datetime, timedelta
import pytz
import json
import requests
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

        try:
            WR_URL = 'http://'+host_ip
            response = requests.get(WR_URL)
            response.raise_for_status()  # Auslösen einer Ausnahme, wenn der Statuscode nicht 2xx ist
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

            # Nur ausführen, wenn WR erreichbar
            try:            
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
                    WRSchreibGrenze_nachOben = basics.getVarConf('Ladeberechnung','WRSchreibGrenze_nachOben','eval')
                    WRSchreibGrenze_nachUnten = basics.getVarConf('Ladeberechnung','WRSchreibGrenze_nachUnten','eval')
                    FesteLadeleistung = basics.getVarConf('Ladeberechnung','FesteLadeleistung','eval')
                    Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
                    PV_Reservierung_steuern = basics.getVarConf('Reservierung','PV_Reservierung_steuern','eval')
                    Batterieentlandung_steuern = basics.getVarConf('Entladung','Batterieentlandung_steuern','eval')
                    WREntladeSchreibGrenze_Watt = basics.getVarConf('Entladung','WREntladeSchreibGrenze_Watt','eval')
                    Notstromreserve_steuern = basics.getVarConf('Notstrom','Notstromreserve_steuern','eval')
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
                    WR_schreiben = 0
    
                    format_aktStd = "%Y-%m-%d %H:00:00"
                    aktStd = datetime.strftime(now, "%H:00")
                    Akt_Std = int(datetime.strftime(now, "%H"))
    
                    #######################################
                    ## Ab hier geht die Berechnung los
                    #######################################
    
                    TagesPrognoseGesamt = 0
                    aktuellerLadewert = 0
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


                    # Geamtprognose und Ladewert berechnen mit Funktion getLadewert
                    PrognoseUNDUeberschuss = progladewert.getLadewert(BattVollUm, Grundlast)
                    TagesPrognoseGesamt = PrognoseUNDUeberschuss[0]
                    Grundlast_Summe = PrognoseUNDUeberschuss[1]
                    aktuellerLadewert = PrognoseUNDUeberschuss[2]
                    LadewertGrund = PrognoseUNDUeberschuss[3]
                    # Ladewert auf Schreibgrenzen prüfen
                    DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                    WR_schreiben = DATA[1]

                    # Aktuelle Prognose berechnen
                    AktuellenLadewert_Array = progladewert.getAktPrognose()
                    aktuelleVorhersage = AktuellenLadewert_Array[0]
                    DEBUG_Ausgabe = AktuellenLadewert_Array[1]

                    # DEBUG_Ausgabe der Ladewertermittlung 
                    DEBUG_Ausgabe += ", aktuellerLadewert: " + str(aktuellerLadewert) + "\n"


                    # Wenn über die PV-Planung manuelle Ladung angewählt wurde
                    MaxladungDurchPV_Planung = ""
                    ManuelleSteuerung = reservierungdata.get('ManuelleSteuerung')
                    if (PV_Reservierung_steuern == 1) and (ManuelleSteuerung >= 0):
                        FesteLadeleistung = BattganzeLadeKapazWatt * ManuelleSteuerung/100
                        MaxladungDurchPV_Planung = "Manuelle Ladesteuerung in PV-Planung ausgewählt."

                    # Wenn die Variable "FesteLadeleistung" größergleich "0" ist, wird der Wert fest als Ladeleistung geschrieben
                    if FesteLadeleistung >= 0:
                        DATA = progladewert.setLadewert(FesteLadeleistung, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                        aktuellerLadewert = FesteLadeleistung
                        # wegen Rundung
                        if abs(aktuellerLadewert - alterLadewert) < 3:
                            WR_schreiben = 0
                        else:
                            WR_schreiben = 1
                        if MaxladungDurchPV_Planung == "":
                            LadewertGrund = "FesteLadeleistung"
                        else:
                            LadewertGrund = MaxladungDurchPV_Planung
    
                    # Hier Volle Ladung, wenn BattVollUm erreicht ist oder Akku = 100%!
                    elif (int(datetime.strftime(now, "%H")) >= int(BattVollUm)) or (BattStatusProz == 100):
                         aktuellerLadewert = MaxLadung
                         DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                         WR_schreiben = DATA[1]
                         LadewertGrund = "BattVollUm oder Akkustand 100% erreicht!"
        
                    else:

                        # Schaltverzögerung für MindBattLad
                        if (alterLadewert + 2 > MaxLadung):
                            MindBattLad = MindBattLad + 5

                        if ((BattStatusProz < MindBattLad)):
                            # volle Ladung ;-)
                            aktuellerLadewert = MaxLadung
                            DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                            WR_schreiben = DATA[1]
                            LadewertGrund = "BattStatusProz < MindBattLad"
    
                    # Wenn Akkuschonung > 0 ab 80% Batterieladung mit Ladewert runter fahren
                    if Akkuschonung > 0:
                        Akkuschonung_dict = progladewert.getAkkuschonWert(BattStatusProz, BattganzeLadeKapazWatt, alterLadewert, aktuellerLadewert)
                        AkkuschonungLadewert = Akkuschonung_dict[0]
                        HysteProdFakt = Akkuschonung_dict[1]
                        BattStatusProz_Grenze = Akkuschonung_dict[2]
                        AkkuSchonGrund = Akkuschonung_dict[3]
                        DEBUG_Ausgabe += Akkuschonung_dict[4]

                        if BattStatusProz >= BattStatusProz_Grenze:
                            # Um das setzen der Akkuschonung zu verhindern, wenn aktuellePVProduktion zu wenig oder der Akku wieder entladen wird.
                            if (AkkuschonungLadewert < aktuellerLadewert or AkkuschonungLadewert < alterLadewert + 10) and aktuellePVProduktion * HysteProdFakt > AkkuschonungLadewert:
                                aktuellerLadewert = AkkuschonungLadewert
                                WRSchreibGrenze_nachUnten = aktuellerLadewert / 5
                                WRSchreibGrenze_nachOben = aktuellerLadewert / 5
                                DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                                WR_schreiben = DATA[1]
                                LadewertGrund = "Akkuschonung: Ladestand >= " + AkkuSchonGrund

                    # Wenn die aktuellePVProduktion < 10 Watt ist, nicht schreiben, 
                    # um 0:00Uhr wird sonst immer Ladewert 0 geschrieben!
                    if aktuellePVProduktion < 10:
                        # Für die Nacht zwingend auf MaxLadung, 
                        # da sonst mogends evtl nicht auf 0 gestelltwerden kann, wegen WRSchreibGrenze_nachUnten
                        if alterLadewert < MaxLadung -10 and Akt_Std > 12:
                            aktuellerLadewert = MaxLadung
                            DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                            WR_schreiben = DATA[1]
                            LadewertGrund = "Auf MaxLadung stellen, da PVProduktion < 10 Watt!"
                        else:
                            WR_schreiben = 0
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
                            print("Grundlast_Summe für Tag:    ", Grundlast_Summe)
                            print("aktuellePVProduktion/Watt:  ", aktuellePVProduktion)
                            print("aktuelleEinspeisung/Watt:   ", aktuelleEinspeisung)
                            print("aktuelleBatteriePower/Watt: ", aktuelleBatteriePower)
                            print("GesamtverbrauchHaus/Watt:   ", GesamtverbrauchHaus)
                            print("Akku_Zustand in Prozent:    ", API['Akku_Zustand']*100,"%")
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
                    BatteryMaxDischarge_Zwangsladung = 0
                    EntladeEintragloeschen = "nein"
                    EntladeEintragDa = "nein"

                    if  Batterieentlandung_steuern == 1:
                        MaxEntladung = BattganzeLadeKapazWatt

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADESTEUERUNG >>>>>>>>>>>>>"
                        for element in result_get_time_of_use:
                            if element['Active'] == True and element['ScheduleType'] == 'DISCHARGE_MAX':
                                BatteryMaxDischarge = element['Power']
                                BatteryMaxDischarge_Zwangsladung = 0
                                EntladeEintragDa = "ja"
                            elif element['Active'] == True and element['ScheduleType'] == 'CHARGE_MIN':
                                BatteryMaxDischarge_Zwangsladung = element['Power']
                                EntladeEintragDa = "ja"

                        # EntladeSteuerungdaten lesen
                        entladesteurungsdata = sqlall.getSQLsteuerdaten('ENTLadeStrg')
                        # Manuellen Entladewert lesen
                        if (entladesteurungsdata.get('ManuelleEntladesteuerung')):
                            MaxEntladung_Prozent=int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1'])
                            MaxEntladung = int(MaxEntladung_Prozent*BattganzeLadeKapazWatt / 100)
                            DEBUG_Ausgabe+="\nDEBUG MaxEntladung = entladesteurungsdata:" + str(MaxEntladung)

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

                        # Ladetype = "DISCHARGE_MAX" bei Entladebegrenzung
                        Ladetype = "DISCHARGE_MAX"

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
                        # Verbrauchsgrenze == 0 (leer) && Feste Grenze == -500 #Negativer Wert = Zwangsladung
                        elif (VerbrauchsgrenzeEntladung == 0 and FesteEntladegrenze < 0):
                            BatteryMaxDischarge = BatteryMaxDischarge_Zwangsladung
                            Neu_BatteryMaxDischarge = abs(int(FesteEntladegrenze))
                            # Zwangsladung kann nur geschrieben werden, wenn aktuellerLadewert > Neu_BatteryMaxDischarge
                            if (Neu_BatteryMaxDischarge > aktuellerLadewert): aktuellerLadewert = Neu_BatteryMaxDischarge + 100
                            # Ladetype = "CHARGE_MIN" bei Zwangsladung
                            Ladetype = "CHARGE_MIN"
                        elif (MaxEntladung_Prozent < 100):
                            Neu_BatteryMaxDischarge = MaxEntladung
                        elif (EntladeEintragDa == "ja"):
                            EntladeEintragloeschen = "ja"

                        DEBUG_Ausgabe+="\nDEBUG Batterieentladegrenze NEU: " + str(Neu_BatteryMaxDischarge) + "%"

                        # Entladung_Daempfung, Unterschied muss größer WREntladeSchreibGrenze_Watt sein
                        WREntladeSchreibGrenze_Prozent = int(WREntladeSchreibGrenze_Watt / BattganzeLadeKapazWatt * 100 + 1)
                        if (abs(Neu_BatteryMaxDischarge - BatteryMaxDischarge) < WREntladeSchreibGrenze_Prozent):
                            Neu_BatteryMaxDischarge = BatteryMaxDischarge

                        ## Werte zum Überprüfen ausgeben
                        if print_level >= 1:
                            print("## ENTLADESTEUERUNG ##\n")
                            #print("Feste Entladegrenze in % : ", int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']*BattganzeLadeKapazWatt / 100), "W")
                            print("Feste Entladegrenze in % : ", int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']), "%")
                            print("VerbrauchsgrenzeEntladung: ", VerbrauchsgrenzeEntladung, "W")
                            print("Feste Entladegrenze Table: ", FesteEntladegrenze, "W")
                            if (Ladetype == "DISCHARGE_MAX") and (EntladeEintragloeschen == "nein"):
                                print("Batterieentladegrenze ALT: ", BatteryMaxDischarge, "W")
                                print("Batterieentladegrenze NEU: ", Neu_BatteryMaxDischarge, "W")
                            if (Ladetype == "CHARGE_MIN") and (EntladeEintragloeschen == "nein"):
                                print("Zwangsladung ALT:          ", BatteryMaxDischarge, "W")
                                print("Zwangsladung NEU:          ", Neu_BatteryMaxDischarge, "W")
                                print("Ladewert > Zwangsladung:   ", aktuellerLadewert, "W")
                            if (EntladeEintragloeschen == "ja"):
                                print(">> Entladeeintrag Löschen!")
                            print()

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADESTEUERUNG >>>>>>>>>>>>>"


                    ### AB HIER SCHARF wenn Argument "schreiben" übergeben
                    ######## Ladeleistung und Entladeleistung in WR Batteriemanagement schreiben 

                    bereits_geschrieben = 0
                    Schreib_Ausgabe = ""
                    Push_Schreib_Ausgabe = ""
                    # Neuen Ladewert als HTTP_Request schreiben, wenn WR_schreiben == 1 
                    if WR_schreiben == 1 or Neu_BatteryMaxDischarge != BatteryMaxDischarge or EntladeEintragloeschen == "ja":
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< LADEWERTE >>>>>>>>>>>>>"
                        DEBUG_Ausgabe+="\nDEBUG Folgender MAX_Ladewert neu zum Schreiben: " + str(aktuellerLadewert)
                        DEBUG_Ausgabe+="\nDEBUG Folgender MAX_ENT_Ladewert neu zum Schreiben: " + str(Neu_BatteryMaxDischarge)
                        payload_text = ''
                        trenner_komma = ''
                        if ('laden' in Options):
                            trenner_komma = ','
                            payload_text = '{"Active":true,"Power":' + str(aktuellerLadewert) + \
                            ',"ScheduleType":"CHARGE_MAX","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                        elif WR_schreiben == 1 :
                            Schreib_Ausgabe = Schreib_Ausgabe + "Ladesteuerung NICHT geschrieben, da Option \"laden\" NICHT gesetzt!\n"
                        if  ('entladen' in Options) and (Batterieentlandung_steuern == 1) and (EntladeEintragloeschen == "nein"):
                            payload_text += str(trenner_komma) + '{"Active":true,"Power":' + str(Neu_BatteryMaxDischarge) + \
                            ',"ScheduleType":"'+Ladetype+'","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                        elif ('entladen' not in Options):
                            Schreib_Ausgabe = Schreib_Ausgabe + "Entladesteuerung NICHT geschrieben, da Option \"entladen\" NICHT gesetzt!\n"
                        # Wenn payload_text NICHT leer dann schreiben
                        if (payload_text != ''):
                            response = request.send_request('/config/timeofuse', method='POST', payload ='{"timeofuse":[' + str(payload_text) + ']}') 
                            bereits_geschrieben = 1
                            if ('laden' in Options) and WR_schreiben == 1:
                                Schreib_Ausgabe = Schreib_Ausgabe + "CHARGE_MAX geschrieben: " + str(aktuellerLadewert) + "W\n"
                            if ('entladen' in Options) and Neu_BatteryMaxDischarge != BatteryMaxDischarge and (EntladeEintragloeschen == "nein"):
                                Schreib_Ausgabe = Schreib_Ausgabe + Ladetype + " geschrieben: " + str(Neu_BatteryMaxDischarge) + "W\n"
                            if ('entladen' in Options) and (EntladeEintragloeschen == "ja"):
                                Schreib_Ausgabe = Schreib_Ausgabe + "Entladeeintrag wurde gelöscht.\n"
                            Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei Ladegrenze schreiben: " + str(response)
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Änderungen kleiner Schreibgrenze!\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)

                    ######## WR Batteriemanagement ENDE

                    ######## Eigenverbrauchs-Optimierung  ab hier wenn eingeschaltet!
                    HYB_BACKUP_RESERVED = None
                    if  EigenverbOpt_steuern > 0:
                        EigenOptERG = progladewert.getEigenverbrauchOpt(host_ip, user, password, BattStatusProz, BattganzeKapazWatt, EigenverbOpt_steuern, MaxEinspeisung)
                        PrognoseMorgen = EigenOptERG[0]
                        Eigen_Opt_Std = EigenOptERG[1]
                        Eigen_Opt_Std_neu = EigenOptERG[2]
                        Dauer_Nacht_Std = EigenOptERG[3]
                        AkkuZielProz = EigenOptERG[4]
                        DEBUG_Ausgabe += EigenOptERG[5]
                        HYB_BACKUP_RESERVED = EigenOptERG[6]
                        aktuellePVProduktion_tmp = aktuellePVProduktion

                        # Wenn der Akku unter MindBattLad Optimierung auf 0 setzen
                        # Bereich ermoeglicht die Optimierung fuer den Tag zu setzen
                        # wegen Hysterse +5
                        if (BattStatusProz <= MindBattLad + 5) and Akt_Std < 12:
                            Dauer_Nacht_Std = 2
                            aktuellePVProduktion_tmp = 0
                        if (BattStatusProz <= MindBattLad):
                            Eigen_Opt_Std_neu = 0

                        if (Dauer_Nacht_Std > 1 or BattStatusProz < AkkuZielProz) and aktuellePVProduktion_tmp < (Grundlast + MaxEinspeisung) * 1.5:
                            if print_level >= 1:
                                print("## Eigenverbrauchs-Optimierung ##")
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

                    ######## N O T S T R O M R E S E R V E ab hier setzen, wenn eingeschaltet!
                    if  Notstromreserve_steuern >= 1 and Akt_Std > 21 and aktuellePVProduktion < 10:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< Notstromreserve >>>>>>>>>>>>>"

                        Notstrom_Werte_tmp = json.loads(basics.getVarConf('Notstrom','Notstrom_Werte','str'))
                        Notstrom_Werte = dict(sorted(Notstrom_Werte_tmp.items(), reverse=True))
                        Notstromreserve_Min = basics.getVarConf('Notstrom','Notstromreserve_Min','eval')
                        # Notstromreserve_Min kann nicht kleiner 5% sein
                        if Notstromreserve_Min < 5:
                            Notstromreserve_Min = 5
                        PrognoseMorgen = progladewert.getPrognoseMorgen()[0]/1000
                        # Aktuelle EntladeGrenze_Max und ProgGrenzeMorgen aus Notstrom_Werte ermitteln
                        EntladeGrenze_Max = Notstromreserve_Min
                        ProgGrenzeMorgen = 0
                        for Notstrom_item in Notstrom_Werte: 
                            if PrognoseMorgen < int(Notstrom_item):
                                EntladeGrenze_Max = int(Notstrom_Werte[Notstrom_item])
                                ProgGrenzeMorgen = int(Notstrom_item)

                        if HYB_BACKUP_RESERVED == None:
                            HYB_BACKUP_RESERVED = request.get_batteries(host_ip, user, password)[2]
                        # Hysterese wenn Notstrom bereits eingeschaltet
                        if HYB_BACKUP_RESERVED == EntladeGrenze_Max:
                            ProgGrenzeMorgen = ProgGrenzeMorgen * 1.2
                        Neu_HYB_BACKUP_RESERVED = Notstromreserve_Min
                        if (PrognoseMorgen < ProgGrenzeMorgen and PrognoseMorgen != 0):
                            Neu_HYB_BACKUP_RESERVED = EntladeGrenze_Max
                        # TEST Notstrom ohne Zwangsladung aus dem Netz
                        if Notstromreserve_steuern > 1 and BattStatusProz < Neu_HYB_BACKUP_RESERVED:
                            print ("TEST Notstrom ohne Zwangsladung aus dem Netz")
                            Neu_HYB_BACKUP_RESERVED = BattStatusProz
                            # aber nicht kleiner 5%
                            if Neu_HYB_BACKUP_RESERVED < 5: Neu_HYB_BACKUP_RESERVED = 5
                        if print_level >= 1:
                            print("## NOTSTROMRESERVE ##")
                            print("Prognose Morgen:     ", int(PrognoseMorgen), "KW")
                            print("ProgGrenze Morgen:   ", ProgGrenzeMorgen, "KW")
                            print("Batteriereserve:     ", HYB_BACKUP_RESERVED, "%")
                            print("Neu_Batteriereserve: ", Neu_HYB_BACKUP_RESERVED, "%")
                            print()

                        Schreib_Ausgabe = ""

                        if (Neu_HYB_BACKUP_RESERVED != HYB_BACKUP_RESERVED):
                            if ('notstrom' in Options):
                                response = request.send_request('/config/batteries', method='POST', payload ='{"HYB_BACKUP_CRITICALSOC":5,"HYB_BACKUP_RESERVED":'+ str(Neu_HYB_BACKUP_RESERVED) + '}')
                                bereits_geschrieben = 1
                                DEBUG_Ausgabe+="\nDEBUG Meldung Notstromreserve schreiben: " + str(response)
                                Schreib_Ausgabe = Schreib_Ausgabe + str(Neu_HYB_BACKUP_RESERVED) + "% Notstromreserve geschrieben.\n"
                                Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe 
                            else:
                                Schreib_Ausgabe = Schreib_Ausgabe + "Notstromreserve NICHT geschrieben, da Option \"notstrom\" NICHT gesetzt!\n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Notstromreserve, NICHTS zu schreiben!!\n"

                        if print_level >= 1:
                            print(Schreib_Ausgabe)

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADEBEGRENZUNG >>>>>>>>>>>>>"

                    ######## Notstromreserve setzen, ENDE

    
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


        except requests.exceptions.RequestException as e:
            print(datetime.now())
            print(f"Fehler bei der Verbindung: {e}")
            print(">>>>>>>>>> WR offline")

