from datetime import datetime
import json
from sys import argv
import requests
import configparser
import FUNCTIONS.PrognoseLadewert
import FUNCTIONS.Steuerdaten
import FUNCTIONS.functions
import FUNCTIONS.SQLall
import FUNCTIONS.GEN24_API as inverter_api_class
import FUNCTIONS.GEN24_interface as inverter_interface_class


if __name__ == '__main__':
        #Versionsnummer lesen
        config_v = configparser.ConfigParser()
        config_v.read('version.ini')
        prg_version = (config_v['Programm']['version'])

        basics = FUNCTIONS.functions.basics()
        config = basics.loadConfig(['default', 'charge'])
        sqlall = FUNCTIONS.SQLall.sqlall()
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"

        print_level = basics.getVarConf('env','print_level','eval')
        if print_level >= 1:
            print("***** BEGINN: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"*****")
        host_ip = basics.getVarConf('gen24','hostNameOrIp', 'str')
        user = basics.getVarConf('gen24','user', 'str')
        password = basics.getVarConf('gen24','password', 'str')
        # Hier Hochkommas am Anfang und am Ende enternen
        password = password[1:-1]

        try:
            # Ping Ersatz, prüft ob WR online
            response = requests.get('http://'+host_ip)
            response.raise_for_status()  # Auslösen einer Ausnahme, wenn der Statuscode nicht 2xx ist
            # API lesen, wegen Versionsnummer
            inverter_api = inverter_api_class.inverter_api()
            API = inverter_api.get_API()
            DEBUG_interface = False
            if(print_level == 5): DEBUG_interface = True
            #  Klasse FroniusGEN24 initiieren
            inverter_interface = inverter_interface_class.InverterInterface(host_ip, user, password, API['Version'], DEBUG_interface)
            # Reservierungsdatei lesen, hier am Anfang, damit die DB evtl. angelegt wird 
            reservierungdata_tmp = sqlall.getSQLsteuerdaten('Reservierung')
            alterLadewert = 0
            # alten Ladewert lesen
            request_data = inverter_interface.get_http_data()
            Eigen_Opt_Std_arry = request_data[1]
            result_get_time_of_use = request_data[0]
            for eintrag in result_get_time_of_use:
                if eintrag.get('Active') and eintrag.get('ScheduleType') == 'CHARGE_MAX':
                    alterLadewert = int(eintrag.get('Power'))
                    break

            # WebUI-Parameter aus CONFIG/Prog_Steuerung.sqlite lesen
            SettingsPara = FUNCTIONS.Steuerdaten.readcontroldata()
            Parameter = SettingsPara.getParameter(argv, 'ProgrammStrg')
            Options = Parameter[2]
        
            Ausgabe_Parameter = ''
            if(Parameter[1] != "" and print_level >= 1):
                Ausgabe_Parameter = "DEBUG Parameteränderung durch WebUI-Settings: "  + str(Parameter[1])
                if(Parameter[0] == "exit0"):
                    # Batteriemangement zurücksetzen
                    if result_get_time_of_use != []:
                        #response = inverter_interface.send_request('config/timeofuse', method='POST', payload ='{"timeofuse":[]}', add_praefix=True)  #entWIGGlung
                        response = inverter_interface.update_inverter_config("remove_timeofuse")
                        print("Batteriemanagementeinträge gelöscht!")
                    # Ende Programm
                if(Parameter[0] == "exit0") or (Parameter[0] == "exit1"):
                    print(now, "ProgrammSTOPP durch WebUI-Settings: ", Parameter[1])
                    exit()
                    # Ende Programm
            else:
                # Aufrufparameter ausgeben
                Ausgabe_Parameter = "DEBUG Aufrufparameter: "  + str(Parameter[2])

            # Nur ausführen, wenn WR erreichbar
            try:            
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< E I N >>>>>>>\nDEBUG"
    
                    ###############################
    
                    # weatherdata ist hier der Median aus weatherData.sqlite
                    weatherdata = basics.loadWeatherData()
    
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
                    Batterieentlandung_steuern = basics.getVarConf('Entladung','Batterieentlandung_steuern','eval')
                    WREntladeSchreibGrenze_Watt = basics.getVarConf('Entladung','WREntladeSchreibGrenze_Watt','eval')
                    Notstromreserve_steuern = basics.getVarConf('Notstrom','Notstromreserve_steuern','eval')
                    EigenverbOpt_steuern = basics.getVarConf('EigenverbOptimum','EigenverbOpt_steuern','eval')
                    MaxEinspeisung = basics.getVarConf('EigenverbOptimum','MaxEinspeisung','eval')

                    # Grundlast je Wochentag, wenn Grundlast == 0
                    if (Grundlast == 0):
                        try:
                            Grundlast_WoT = basics.getVarConf('Ladeberechnung','Grundlast_WoT','str')
                            Grundlast_WoT_Array = Grundlast_WoT.split(',')
                            Grundlast = eval(Grundlast_WoT_Array[datetime.today().weekday()])
                        except:
                            print("ERROR: Grundlast für den Wochentag konnte nicht gelesen werden, Grundlast = 0 !!")
                            Grundlast = 0

                    BattganzeKapazWatt = (API['BattganzeKapazWatt'])
                    BattganzeLadeKapazWatt_Akku = (API['BattganzeLadeKapazWatt'])
                    LadeAmpere = 50
                    # LadeAmpere bei HVM = 50A bei HVS = 25A
                    if (BattganzeLadeKapazWatt_Akku / API['udc_mittel']) < 37: LadeAmpere = 25
                    # LadeAmpere Gen24 = 22A
                    BattganzeLadeKapazWatt = BattganzeLadeKapazWatt_Akku / LadeAmpere * 22
                    BattStatusProz = API['BattStatusProz']
                    BattKapaWatt_akt = API['BattKapaWatt_akt']
                    aktuelleBatteriePower = API['aktuelleBatteriePower']
                    aktuelleEinspeisung = API['aktuelleEinspeisung'] * -1
                    aktuellePVProduktion = API['aktuellePVProduktion']
                    GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower

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
                    progladewert_inst = FUNCTIONS.PrognoseLadewert.progladewert(weatherdata, WR_Kapazitaet, reservierungdata_tmp, MaxLadung, Einspeisegrenze, aktuelleBatteriePower, Eigen_Opt_Std_arry)
                    # evtl. Ladung des Akku auf SOC_Proz_Grenze begrenzen, und damit BattKapaWatt_akt reduzieren
                    Sdt_24H = datetime.now().hour
                    PrognoseMorgen = progladewert_inst.getPrognoseMorgen(0,24-Sdt_24H)[0]/1000
                    PrognoseLimit_SOC = basics.getVarConf('Ladeberechnung','PrognoseLimit_SOC','eval')
                    Akkuschonung_Werte = basics.getVarConf('Ladeberechnung','Akkuschonung_Werte','str')
                    # Akkuschonung_Werte in ein Dictionary umwandeln, ersten Wert extrahieren und in float umwandeln
                    SOC_data = json.loads(Akkuschonung_Werte)
                    SOC_Proz_Grenze = float(next(iter(SOC_data.keys())))
                    Ladelimit_80 = ' (100%)'
                    BattKapaWatt_akt_SOC = BattKapaWatt_akt
                    if PrognoseLimit_SOC >= 0 and PrognoseMorgen > PrognoseLimit_SOC:
                        BattKapaWatt_akt_SOC = int(BattKapaWatt_akt - BattganzeKapazWatt*((100-SOC_Proz_Grenze)/100))
                        Ladelimit_80 = '('+str(SOC_Proz_Grenze)+'%)'

                    # WRSchreibGrenze_nachUnten ab 90% Batteriestand prozentual erhöhen (ersetzen von BatterieVoll!!)
                    if ( BattStatusProz > 90 ):
                        WRSchreibGrenze_nachUnten = int(WRSchreibGrenze_nachUnten * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachUnten: " + str(WRSchreibGrenze_nachUnten) +"\n"
                        WRSchreibGrenze_nachOben = int(WRSchreibGrenze_nachOben * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachOben: " + str(WRSchreibGrenze_nachOben) +"\n"

                    # BattVollUm setzen evtl. mit DIFF zum Sonnenuntergang
                    BattVollUm = basics.getVarConf('Ladeberechnung','BattVollUm','eval')
                    Sonnenuntergang = progladewert_inst.getSonnenuntergang(PV_Leistung_Watt)
                    if BattVollUm <= 0:
                       BattVollUm = Sonnenuntergang + BattVollUm

                    # Akkuschonung aus PV-Planung ermitteln
                    ManuelleStrg_Akkuschon = int(reservierungdata_tmp['ManuelleSteuerung']['Res_Feld2'])
                    # Bei Akkuschonung BattVollUm eine Stunde vor verlegen
                    if Akkuschonung > 0 or ManuelleStrg_Akkuschon == 1:
                        BattVollUm = BattVollUm - 1


                    # Geamtprognose und Ladewert berechnen mit Funktion getLadewert
                    PrognoseUNDUeberschuss = progladewert_inst.getLadewert(BattVollUm, Grundlast, alterLadewert, BattKapaWatt_akt)
                    TagesPrognoseGesamt = PrognoseUNDUeberschuss[0]
                    Grundlast_Summe = PrognoseUNDUeberschuss[1]
                    aktuellerLadewert = PrognoseUNDUeberschuss[2]
                    LadewertGrund = PrognoseUNDUeberschuss[3] + Ladelimit_80
                    # Ladewert auf Schreibgrenzen prüfen
                    WR_schreiben = progladewert_inst.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, alterLadewert)

                    # Aktuelle Prognose berechnen
                    (aktuelleVorhersage, DEBUG_Ausgabe) = progladewert_inst.getLoggingPrognose(BattKapaWatt_akt)

                    # Wenn über die PV-Planung manuelle Ladung angewählt wurde
                    MaxladungDurchPV_Planung = ""
                    ManuelleSteuerung = int(reservierungdata_tmp['ManuelleSteuerung']['Res_Feld1'])
                    # Prüfen, ob Einträge schon abgelaufen
                    try: 
                        Ablaufdatum = int(reservierungdata_tmp['ManuelleSteuerung']['Options'])
                    except: 
                        Ablaufdatum = 0
                    if (Ablaufdatum > int(datetime.now().timestamp())):
                        if (ManuelleSteuerung >= 0):
                            FesteLadeleistung = BattganzeLadeKapazWatt * ManuelleSteuerung/100
                            MaxladungDurchPV_Planung = "Sliderwert in PV-Planung gewählt."
                        # Wenn über die PV-Planung MaxLadung gewählt wurde (-2), MaxLadung setzen
                        if (ManuelleSteuerung == -2):
                            FesteLadeleistung = MaxLadung
                            MaxladungDurchPV_Planung = "MaxLadung in PV-Planung gewählt."
                    else:
                        # Wenn Einträge abgelaufen, wieder die Akkuschoneinstellung aus charge_priv.ini
                        ManuelleStrg_Akkuschon = Akkuschonung

                    # Wenn die Variable "FesteLadeleistung" größergleich "0" ist, wird der Wert fest als Ladeleistung geschrieben
                    if FesteLadeleistung >= 0:
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
                         WR_schreiben = progladewert_inst.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, alterLadewert)
                         LadewertGrund = "BattVollUm oder Akkustand 100% erreicht!"
        
                    else:

                        # Schaltverzögerung für MindBattLad
                        if (alterLadewert + 2 > MaxLadung):
                            MindBattLad = MindBattLad + 5

                        if ((BattStatusProz < MindBattLad)):
                            # volle Ladung ;-)
                            aktuellerLadewert = MaxLadung
                            WR_schreiben = progladewert_inst.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, alterLadewert)
                            LadewertGrund = "BattStatusProz < MindBattLad"
    
                    # Wenn Akkuschonung > 0 ab 80% Batterieladung mit Ladewert runter fahren, Werte auch für Zwangsladung bestimmen
                    (aktuellerLadewert, WR_schreiben, LadewertGrund, DEBUG_Ausgabe, 
                    WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, SOC_Proz_Grenze, AkkuschonungLadewert) = \
                        progladewert_inst.ladeanpassung_akkuschonung(
                            Akkuschonung, 
                            Batterieentlandung_steuern, 
                            BattStatusProz, 
                            BattganzeLadeKapazWatt_Akku, 
                            alterLadewert, 
                            aktuellerLadewert, 
                            ManuelleStrg_Akkuschon, 
                            aktuellePVProduktion, 
                            SOC_Proz_Grenze, 
                            PrognoseLimit_SOC, 
                            PrognoseMorgen, 
                            BattKapaWatt_akt_SOC, 
                            BattKapaWatt_akt, 
                            WRSchreibGrenze_nachOben, # Übergabe der aktuellen Werte
                            WRSchreibGrenze_nachUnten, # Übergabe der aktuellen Werte
                            DEBUG_Ausgabe, 
                            LadewertGrund,
                            WR_schreiben
                    )

                    # Wenn die aktuellePVProduktion < 50 Watt ist, nicht schreiben, 
                    # um 0:00Uhr wird sonst immer Ladewert 0 geschrieben!
                    if aktuellePVProduktion < 50:
                        # Für die Nacht zwingend auf MaxLadung, 
                        # da sonst mogends evtl nicht auf 0 gestelltwerden kann, wegen WRSchreibGrenze_nachUnten
                        if alterLadewert < MaxLadung -10 and Akt_Std > 12:
                            aktuellerLadewert = MaxLadung
                            WR_schreiben = progladewert_inst.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, alterLadewert)
                            LadewertGrund = "Auf MaxLadung stellen, da PVProduktion < 50 Watt!"
                        else:
                            WR_schreiben = 0
                            LadewertGrund = "Nicht schreiben, da PVProduktion < 50 Watt!"

                    # Auf ganze Watt runden
                    aktuellerLadewert = int(aktuellerLadewert)

                    if print_level >= 1:
                        try:
                            if(Ausgabe_Parameter != ''): print(Ausgabe_Parameter)
                            print("Programmversion:            ", prg_version)
                            print("aktuellePrognose:           ", aktuelleVorhersage)
                            print("TagesPrognose - BattVollUm: ", TagesPrognoseGesamt,"-", BattVollUm)
                            print("Grundlast_Summe für Tag:    ", Grundlast_Summe)
                            print("aktuellePVProduktion/Watt:  ", aktuellePVProduktion)
                            print("aktuelleEinspeisung/Watt:   ", aktuelleEinspeisung)
                            print("aktuelleBatteriePower/Watt: ", aktuelleBatteriePower)
                            print("GesamtverbrauchHaus/Watt:   ", GesamtverbrauchHaus)
                            print("aktuelleBattKapazität/Watt: ", BattKapaWatt_akt)
                            print("Batteriestatus in Prozent:  ", BattStatusProz,"%")
                            print("LadewertGrund: ", LadewertGrund)
                            print("Bisheriger Ladewert/Watt:   ", alterLadewert)
                            print(f"Neuer Ladewert/Watt({BatSparFaktor: .1f}):   {aktuellerLadewert}")
                            print()
                        except Exception as e:
                            print()
                            print("Fehler in den Printbefehlen, Ausgabe nicht möglich!")
                            print("Fehlermeldung:", e)
                            print()


                    DEBUG_Ausgabe+="DEBUG\nDEBUG BattVollUm:                 " + str(BattVollUm) + "Uhr"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachUnten:  " + str(WRSchreibGrenze_nachUnten) + "W"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachOben:   " + str(WRSchreibGrenze_nachOben) + "W"
                    

                    ######## IN  WR Batteriemanagement schreiben, später gemeinsam
                    ######## E N T L A D E S T E U E R U N G  ab hier wenn eingeschaltet!

                    BatteryMaxDischarge = BattganzeLadeKapazWatt
                    Neu_BatteryMaxDischarge = BattganzeLadeKapazWatt
                    BatteryMaxDischarge_Zwangsladung = 0
                    EntladeEintragloeschen = "nein"
                    EntladeEintragDa = "nein"
                    Ladetype = ""

                    if  Batterieentlandung_steuern > 0:
                        MaxEntladung = BattganzeLadeKapazWatt

                        DEBUG_Ausgabe+="DEBUG\nDEBUG <<<<<<<< ENTLADESTEUERUNG >>>>>>>>>>>>>"
                        for eintrag in result_get_time_of_use:
                            if eintrag.get('Active') and eintrag.get('ScheduleType') == 'DISCHARGE_MAX':
                                BatteryMaxDischarge = int(eintrag.get('Power'))
                                BatteryMaxDischarge_Zwangsladung = 0
                                EntladeEintragDa = "ja"
                            elif eintrag.get('Active') and eintrag.get('ScheduleType') == 'CHARGE_MIN':
                                BatteryMaxDischarge_Zwangsladung = int(eintrag.get('Power'))
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
                        # Feste Entladegrenze aus Tabelle  ENTLadeStrg lesen
                        if (entladesteurungsdata.get(aktStd)):
                            # Funktion aufrufen, die eine evtl. viertelstündliche zuteilung macht
                            FesteEntladegrenze_tmp = progladewert_inst.get_FesteEntladegrenze(str(entladesteurungsdata[aktStd]['Res_Feld2']))
                            FesteEntladegrenze = FesteEntladegrenze_tmp[0]
                            DEBUG_Ausgabe += FesteEntladegrenze_tmp[1]
                        else:
                            FesteEntladegrenze = 0

                        DEBUG_Ausgabe+="\nDEBUG FesteEntladegrenze aus Spalte 2: " + str(FesteEntladegrenze)

                        # Ladetype = "DISCHARGE_MAX" bei Entladebegrenzung
                        Ladetype = "DISCHARGE_MAX"

                        # Feste Entladebegrenzung ab einem bestimmten Verbrauch
                        Verbrauch_Feste_Entladegrenze = basics.getVarConf('Entladung','Verbrauch_Feste_Entladegrenze','eval')
                        Feste_Entladegrenze = basics.getVarConf('Entladung','Feste_Entladegrenze','eval')

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
                            # Akkuschonung auch bei Zwangsladung
                            if (AkkuschonungLadewert < Neu_BatteryMaxDischarge and Batterieentlandung_steuern > 1): Neu_BatteryMaxDischarge = AkkuschonungLadewert
                            DEBUG_Ausgabe+="\nDEBUG Akkuschonung auch bei Zwangsladung: " + str(AkkuschonungLadewert)
                            # Zwangsladung kann nur geschrieben werden, wenn aktuellerLadewert > Neu_BatteryMaxDischarge
                            if (Neu_BatteryMaxDischarge > aktuellerLadewert): aktuellerLadewert = Neu_BatteryMaxDischarge + 100
                            # Ladetype = "CHARGE_MIN" bei Zwangsladung
                            Ladetype = "CHARGE_MIN"
                        elif (MaxEntladung_Prozent < 100):
                            Neu_BatteryMaxDischarge = MaxEntladung
                        # Hausverbrauch größer z.B. 10kW und Entladung batterie größer Feste_Entladegrenze => wenn AKKU leer dann nicht
                        # aktuelleBatteriePower > Feste_Entladegrenze/2 = Damit sie nicht einschaltet, wenn Akku bereits leer ist.
                        # Feste_Entladegrenze/2 = sonst schaltet sie beim nächsten Durchlauf wieder aus, da die aktuelleBatteriePower dann kleiner ist.
                        elif (Verbrauch_Feste_Entladegrenze > 0 and GesamtverbrauchHaus > Verbrauch_Feste_Entladegrenze and aktuelleBatteriePower > Feste_Entladegrenze/2 and Ladetype == "DISCHARGE_MAX"):
                            Neu_BatteryMaxDischarge = Feste_Entladegrenze
                        elif (EntladeEintragDa == "ja"):
                            EntladeEintragloeschen = "ja"

                        DEBUG_Ausgabe+="\nDEBUG Batterieentladegrenze NEU: " + str(Neu_BatteryMaxDischarge) + "%"

                        # Entladung_Daempfung, Unterschied muss größer WREntladeSchreibGrenze_Watt sein
                        if (abs(Neu_BatteryMaxDischarge - BatteryMaxDischarge) < WREntladeSchreibGrenze_Watt) and Ladetype != "CHARGE_MIN":
                            Neu_BatteryMaxDischarge = BatteryMaxDischarge

                        ## Werte zum Überprüfen ausgeben
                        if print_level >= 1:
                            print("## ENTLADESTEUERUNG ##\n")
                            print("Feste Entladegrenze in % : ", int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']), "%")
                            print("VerbrauchsgrenzeEntladung: ", VerbrauchsgrenzeEntladung, "W")
                            print("Feste Entladegrenze Table: ", FesteEntladegrenze, "W")
                            if (Ladetype == "DISCHARGE_MAX") and (EntladeEintragloeschen == "nein"):
                                print("Batterieentladegrenze ALT: ", int(BatteryMaxDischarge), "W")
                                print("Batterieentladegrenze NEU: ", int(Neu_BatteryMaxDischarge), "W")
                            if (Ladetype == "CHARGE_MIN") and (EntladeEintragloeschen == "nein"):
                                print("Zwangsladung ALT:          ", int(BatteryMaxDischarge), "W")
                                print("Zwangsladung NEU:          ", int(Neu_BatteryMaxDischarge), "W")
                                print("Ladewert >= Zwangsladung:   ", aktuellerLadewert, "W")
                            if (EntladeEintragloeschen == "ja"):
                                print(">> Entladeeintrag löschen!")
                            print()

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADESTEUERUNG >>>>>>>>>>>>>"


                    ### AB HIER SCHARF wenn Argument "schreiben" übergeben
                    ######## Ladeleistung und Entladeleistung in WR Batteriemanagement schreiben 
                    Schreib_Ausgabe = ""
                    Push_Schreib_Ausgabe = ""

                    if WR_schreiben == 11 or Neu_BatteryMaxDischarge != BatteryMaxDischarge or EntladeEintragloeschen == "ja":  #entWIGGlung
                        (bereits_geschrieben, Schreib_Ausgabe, Push_Schreib_Ausgabe, DEBUG_Ausgabe) = \
                            inverter_interface.write_battery_limits(
                                WR_schreiben,
                                aktuellerLadewert,
                                Neu_BatteryMaxDischarge,
                                BatteryMaxDischarge,
                                EntladeEintragloeschen,
                                Options,
                                Batterieentlandung_steuern,
                                EntladeEintragDa,
                                Ladetype,
                                print_level,
                                DEBUG_Ausgabe
                            )
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Keine Änderung der Lade-/Entladewerte notwendig.\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)

                    ######## WR Batteriemanagement ENDE

                    ######## Eigenverbrauchs-Optimierung  ab hier wenn eingeschaltet!
                    HYB_BACKUP_RESERVED = None
                    if  EigenverbOpt_steuern > 0:
                        EigenOptERG = progladewert_inst.getEigenverbrauchOpt(host_ip, user, password, BattStatusProz, BattganzeKapazWatt, EigenverbOpt_steuern, MaxEinspeisung)
                        Prognose_24H = EigenOptERG[0]
                        Eigen_Opt_Std = EigenOptERG[1]
                        Eigen_Opt_Std_neu = EigenOptERG[2]
                        Dauer_Nacht_Std = EigenOptERG[3]
                        AkkuZielProz = EigenOptERG[4]
                        DEBUG_Ausgabe += EigenOptERG[5]
                        HYB_BACKUP_RESERVED = EigenOptERG[6]
                        aktuellePVProduktion_tmp = aktuellePVProduktion

                        # Bei Eigen_Opt_Std_neu == 0 auf HYB_EM_MODE = 0, Eigenverbrauchs-Optimierung = Automatisch schalten
                        HYB_EM_MODE = 1
                        if (Eigen_Opt_Std_neu == 0):
                            HYB_EM_MODE = 0

                        if (Dauer_Nacht_Std > 0.5 or BattStatusProz < MindBattLad):
                            if print_level >= 1:
                                print("## Eigenverbrauchs-Optimierung ##")
                                print("Prognose nächste 24Std: ", Prognose_24H, "KW")
                                print("Eigenverbrauchs-Opt. ALT: ", Eigen_Opt_Std, "W")
                                print("Eigenverbrauchs-Opt. NEU: ", Eigen_Opt_Std_neu, "W")
                                print()

                            Opti_Schreib_Ausgabe = ""

                            if (Eigen_Opt_Std_neu != Eigen_Opt_Std):
                                if ('optimierung' in Options):
                                    #response = inverter_interface.send_request('config/batteries', method='POST', payload ='{"HYB_EM_POWER":'+ str(Eigen_Opt_Std_neu) + ',"HYB_EM_MODE":'+str(HYB_EM_MODE)+'}', add_praefix=True)  #entWIGGlung
                                    response = inverter_interface.update_inverter_config( "eigenverbrauchsoptimierung", Eigen_Opt_Std_neu=str(Eigen_Opt_Std_neu), HYB_EM_MODE=str(HYB_EM_MODE))

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
                    if  Notstromreserve_steuern >= 1 and Akt_Std > Sonnenuntergang and Akt_Std < Sonnenuntergang+2:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< Notstromreserve >>>>>>>>>>>>>"

                        Notstrom_Werte_tmp = json.loads(basics.getVarConf('Notstrom','Notstrom_Werte','str'))
                        Notstrom_Werte = dict(sorted(Notstrom_Werte_tmp.items(), key=lambda item: int(item[0]), reverse=True))
                        Notstromreserve_Min = basics.getVarConf('Notstrom','Notstromreserve_Min','eval')
                        # Notstromreserve_Min kann nicht kleiner 5% sein
                        if Notstromreserve_Min < 5:
                            Notstromreserve_Min = 5
                        Prognose_24H = progladewert_inst.getPrognoseMorgen()[0]/1000
                        # Aktuelle EntladeGrenze_Max und ProgGrenzeMorgen aus Notstrom_Werte ermitteln
                        EntladeGrenze_Max = Notstromreserve_Min
                        ProgGrenzeMorgen = 0
                        for Notstrom_item in Notstrom_Werte: 
                            if Prognose_24H < int(Notstrom_item):
                                EntladeGrenze_Max = int(Notstrom_Werte[Notstrom_item])
                                ProgGrenzeMorgen = int(Notstrom_item)

                        if HYB_BACKUP_RESERVED == None:
                            HYB_BACKUP_RESERVED = Eigen_Opt_Std_arry['HYB_BACKUP_RESERVED']
                        # Hysterese wenn Notstrom bereits eingeschaltet
                        if HYB_BACKUP_RESERVED == EntladeGrenze_Max:
                            ProgGrenzeMorgen = int(ProgGrenzeMorgen * 1.2)
                        Neu_HYB_BACKUP_RESERVED = Notstromreserve_Min
                        if (Prognose_24H < ProgGrenzeMorgen and Prognose_24H != 0):
                            Neu_HYB_BACKUP_RESERVED = EntladeGrenze_Max
                        # TEST Notstrom ohne Zwangsladung aus dem Netz
                        if Notstromreserve_steuern > 1 and BattStatusProz < Neu_HYB_BACKUP_RESERVED:
                            print ("TEST Notstrom ohne Zwangsladung aus dem Netz")
                            Neu_HYB_BACKUP_RESERVED = int(BattStatusProz)
                            # aber nicht kleiner 5%
                            if Neu_HYB_BACKUP_RESERVED < 5: Neu_HYB_BACKUP_RESERVED = 5
                        if print_level >= 1:
                            print("## NOTSTROMRESERVE ##")
                            print("Prognose nächste 24Std:     ", int(Prognose_24H), "KW")
                            print("ProgGrenze Morgen:   ", ProgGrenzeMorgen, "KW")
                            print("Batteriereserve:     ", HYB_BACKUP_RESERVED, "%")
                            print("Neu_Batteriereserve: ", Neu_HYB_BACKUP_RESERVED, "%")
                            print()

                        Schreib_Ausgabe = ""

                        if (Neu_HYB_BACKUP_RESERVED != HYB_BACKUP_RESERVED):
                            if ('notstrom' in Options):
                                #response = inverter_interface.send_request('config/batteries', method='POST', payload ='{"HYB_BACKUP_CRITICALSOC":5,"HYB_BACKUP_RESERVED":'+ str(Neu_HYB_BACKUP_RESERVED) + '}', add_praefix=True)  #entWIGGlung
                                response = inverter_interface.update_inverter_config("BACKUP_RESERVE", Neu_HYB_BACKUP_RESERVED=str(Neu_HYB_BACKUP_RESERVED))

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
                    Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
                    if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
                        Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
                        apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
                        print("PushMeldung an ", Push_Message_Url, " gesendet.\n")


                    ### LOGGING, Schreibt mit den übergebenen Daten SQlite-Datei
                    ## nur wenn "schreiben" oder "logging" übergeben worden ist
                    sqlall = FUNCTIONS.SQLall.sqlall()
                    Logging_Schreib_Ausgabe = ""
                    if ('logging' in Options):
                        # In die DB werden die liftime Verbrauchszählerstände gespeichert
                        sqlall.save_SQLite('PV_Daten.sqlite', API['AC_Produktion'], API['DC_Produktion'], API['AC_to_DC'], API['Netzverbrauch'], API['Einspeisung'], \
                        API['Batterie_IN'], API['Batterie_OUT'], aktuelleVorhersage, BattStatusProz)
                        Logging_Schreib_Ausgabe = 'In SQLite-Datei gespeichert!'
                    else:
                        Logging_Schreib_Ausgabe = "Logging NICHT gespeichert, da Option \"logging\" NICHT gesetzt!\n" 

                    if print_level >= 1:
                        print(Logging_Schreib_Ausgabe)
                    # LOGGING ENDE



                    #DEBUG ausgeben
                    if print_level >= 2:
                        DEBUG_Ausgabe+= "\nDEBUG\nDEBUG <<<<<< A U S >>>>>>>\n"
                        print(DEBUG_Ausgabe)
                    if print_level >= 1:
                        print("***** ENDE: ", datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),"*****\n")


            except OSError:
                print("Es ist ein Fehler aufgetreten!!!")


        except requests.exceptions.RequestException as e:
            print(datetime.now())
            print(f"Fehler bei der Verbindung: {e}")
            print(">>>>>>>>>> WR offline")

