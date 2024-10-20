from datetime import datetime, timedelta
import pytz
import requests
import FUNCTIONS.SymoGen24Connector
from ping3 import ping
from sys import argv
import FUNCTIONS.PrognoseLadewert
import FUNCTIONS.Steuerdaten
import FUNCTIONS.functions
import FUNCTIONS.GEN24_API
import FUNCTIONS.SQLall


if __name__ == '__main__':
        basics = FUNCTIONS.functions.basics()
        config = basics.loadConfig(['default', 'charge'])
        sqlall = FUNCTIONS.SQLall.sqlall()
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"

        # WebUI-Parameter aus CONFIG/Prog_Steuerung.sqlite lesen
        SettingsPara = FUNCTIONS.Steuerdaten.readcontroldata()
        print_level = basics.getVarConf('env','print_level','eval')
        Parameter = SettingsPara.getParameter(argv, 'ProgrammStrg')
        Options = Parameter[2]
        
        Ausgabe_Parameter = ''
        if(Parameter[1] != "" and print_level >= 1):
            Ausgabe_Parameter = ">>>Parameteränderung durch WebUI-Settings: "  + str(Parameter[1])
            if(Parameter[0] == "exit0"):
                # Ladungsspeichersteuerungsmodus deaktivieren 
                host_ip = basics.getVarConf('gen24','hostNameOrIp', 'str')
                host_port = basics.getVarConf('gen24','port', 'str')
                gen24 = FUNCTIONS.SymoGen24Connector.SymoGen24(host_ip, host_port, False)
                if gen24.read_data('StorageControlMode') != 0:
                    valueNew = gen24.write_data('StorageControlMode', 0 )
                    print("StorageControlMode 0 neu geschrieben.")
            if(Parameter[0] == "exit0") or (Parameter[0] == "exit1"):
                print(now, "ProgrammSTOPP durch WebUI-Settings: ", Parameter[1])
                exit()
                # Ende Programm

        host_ip = basics.getVarConf('gen24','hostNameOrIp', 'str')
        host_port = basics.getVarConf('gen24','port', 'str')
        if ping(host_ip):
            # Nur ausführen, wenn WR erreichbar
            gen24 = None
            auto = False
            try:            
                    newPercent = None
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< E I N >>>>>>>\n\n"
    
                    ###############################
    
                    weatherfile = basics.getVarConf('env','filePathWeatherData','str')
                    weatherdata = basics.loadWeatherData(weatherfile)

                    gen24 = FUNCTIONS.SymoGen24Connector.SymoGen24(host_ip, host_port, auto)
                    
                    if gen24.read_data('Battery_Status') == 1:
                        print(datetime.now())
                        print("Batterie ist Offline keine Steuerung möglich!!! ")
                        print()
                        exit()
    
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
                    Fallback_on = basics.getVarConf('Fallback','Fallback_on','eval')
                    Cronjob_Minutenabstand = basics.getVarConf('Fallback','Cronjob_Minutenabstand','eval')
                    Fallback_Zeitabstand_Std = basics.getVarConf('Fallback','Fallback_Zeitabstand_Std','eval')
                    Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
                    PV_Reservierung_steuern = basics.getVarConf('Reservierung','PV_Reservierung_steuern','eval')
                    Batterieentlandung_steuern = basics.getVarConf('Entladung','Batterieentlandung_steuern','eval')
                    WREntladeSchreibGrenze_Watt = basics.getVarConf('Entladung','WREntladeSchreibGrenze_Watt','eval')
                    EntladeGrenze_steuern = basics.getVarConf('Entladung','EntladeGrenze_steuern','eval')

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


                    # Benoetigte Variablen vom GEN24 lesen und definieren
                    # Hier nun über API
                    api = FUNCTIONS.GEN24_API.gen24api
                    API = api.get_API()
                    BattganzeLadeKapazWatt = (API['BattganzeLadeKapazWatt'])
                    BattganzeKapazWatt = (API['BattganzeKapazWatt'])
                    BattStatusProz = API['BattStatusProz']
                    BattKapaWatt_akt = API['BattKapaWatt_akt']
                    aktuelleEinspeisung = API['aktuelleEinspeisung'] * -1
                    aktuellePVProduktion = API['aktuellePVProduktion']
                    aktuelleBatteriePower = API['aktuelleBatteriePower']
                    GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower

                    # Aktuelle Entladewert von Modbus holen
                    BatteryMaxDischargePercent = int(gen24.read_data('BatteryMaxDischargePercent')/100) 

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
                    oldPercent = gen24.read_data('BatteryMaxChargePercent')
                    alterLadewert = int(oldPercent*BattganzeLadeKapazWatt/10000)
    
                    format_aktStd = "%Y-%m-%d %H:00:00"
                    aktStd = datetime.strftime(now, "%H:00")

    
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

                    # Einspeisebegrenzung prüfen
                    Einspeisegrenze = progladewert.getEinspeiseGrenzeLadewert(WRSchreibGrenze_nachOben, aktuellerLadewert, aktuelleEinspeisung, aktuellePVProduktion, LadewertGrund, alterLadewert, PV_Leistung_Watt)
                    aktuellerLadewert = Einspeisegrenze[0]
                    LadewertGrund = Einspeisegrenze[1]
                    DEBUG_Ausgabe += Einspeisegrenze[2]
                    # AC-Kapazität prüfen
                    ACKapazitaet = progladewert.getAC_KapaLadewert(WRSchreibGrenze_nachOben, aktuellerLadewert, aktuellePVProduktion, LadewertGrund, alterLadewert, PV_Leistung_Watt)
                    aktuellerLadewert = ACKapazitaet[0]
                    LadewertGrund = ACKapazitaet[1]

                    # ladewert in Prozent
                    DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                    newPercent = DATA[0]
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
                        newPercent = DATA[0]
                        # wegen Rundung
                        if abs(newPercent - oldPercent) < 3:
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
                         newPercent = DATA[0]
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
                            newPercent = DATA[0]
                            WR_schreiben = DATA[1]
                            LadewertGrund = "BattStatusProz < MindBattLad"
    
                    # Wenn Akkuschonung > 0 ab 80% Batterieladung mit Ladewert runter fahren
                    HysteProdFakt = 2
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
                                newPercent = DATA[0]
                                WR_schreiben = DATA[1]
                                LadewertGrund = "Akkuschonung: Ladestand >= " + AkkuSchonGrund

                    # Wenn die aktuellePVProduktion < 10 Watt ist, nicht schreiben, 
                    # um 0:00Uhr wird sonst immer Ladewert 0 geschrieben!
                    if aktuellePVProduktion < 10:
                        # Für die Nacht zwingend auf MaxLadung, 
                        # da sonst mogends evtl nicht auf 0 gestelltwerden kann, wegen WRSchreibGrenze_nachUnten
                        Akt_Std = int(datetime.strftime(now, "%H"))
                        if alterLadewert < MaxLadung -10 and Akt_Std > 12:
                            aktuellerLadewert = MaxLadung
                            DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                            newPercent = DATA[0]
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
                            print("## MODBUS LADESTEUERUNG ###")
                            print("\n++ WIRD AB VERSION 0.25 nicht mehr gepflegt!!! ++\n")
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
                            print("Bisheriger Ladewert/Prozent:", oldPercent/100,"%")
                            print("Neuer Ladewert/Watt:        ", aktuellerLadewert)
                            print("Neuer Ladewert/Prozent:     ", newPercent/100,"%")
                            print()
                        except Exception as e:
                            print()
                            print("Fehler in den Printbefehlen, Ausgabe nicht möglich!")
                            print("Fehlermeldung:", e)
                            print()


                    DEBUG_Ausgabe+="\nDEBUG BattVollUm:                 " + str(BattVollUm) + "Uhr"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachUnten:  " + str(WRSchreibGrenze_nachUnten) + "W"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachOben:   " + str(WRSchreibGrenze_nachOben) + "W"

                    ### AB HIER SCHARF wenn Argument "schreiben" übergeben
                    bereits_geschrieben = 0
                    Schreib_Ausgabe = ""
                    Push_Schreib_Ausgabe = ""
                    # Neuen Ladewert in Prozent schreiben, wenn WR_schreiben == 1
                    if WR_schreiben == 1:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< LADEWERTE >>>>>>>>>>>>>"
                        DEBUG_Ausgabe+="\nDEBUG Folgender Ladewert neu zum Schreiben: " + str(newPercent)
                        if ('laden' in Options):
                            valueNew = gen24.write_data('BatteryMaxChargePercent', newPercent)
                            bereits_geschrieben = 1
                            Schreib_Ausgabe = Schreib_Ausgabe + "Am WR geschrieben: " + str(newPercent / 100) + "% = " + str(aktuellerLadewert) + "W\n"
                            Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei Ladegrenze schreiben: " + str(valueNew)
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Ladesteuerung NICHT geschrieben, da Option \"laden\" NICHT gesetzt!\n"
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Änderung kleiner Schreibgrenze!\n"

                    # Ladungsspeichersteuerungsmodus aktivieren wenn nicht aktiv
                    # kann durch Fallback (z.B. nachts) erfordelich sein, ohne dass Änderung an der Ladeleistung nötig ist
                    if gen24.read_data('StorageControlMode') != 3:
                        if (Options != []):
                            DEBUG_Ausgabe += "\nDEBUG StorageControlMode 3 schreiben! "
                            valueNew = gen24.write_data('StorageControlMode', 3 )
                            bereits_geschrieben = 1
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode 3 neu geschrieben.\n"
                            Push_Schreib_Ausgabe += "StorageControlMode 3 neu geschrieben.\n"
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei StorageControlMode schreiben: " + str(valueNew)
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode NICHT geschrieben, da KEINE Option zum Schreiben gesetzt.\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)
    
                    ######## E N T L A D E S T E U E R U N G  ab hier wenn eingeschaltet!

                    if  Batterieentlandung_steuern == 1:
                        MaxEntladung = 100  #hier 100%

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADESTEUERUNG >>>>>>>>>>>>>"

                        # EntladeSteuerungdaten lesen
                        entladesteurungsdata = sqlall.getSQLsteuerdaten('ENTLadeStrg')
                        # Manuellen Entladewert lesen
                        if (entladesteurungsdata.get('ManuelleEntladesteuerung')):
                            MaxEntladung = int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1'])
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

                        # Wenn folgende Bedingungen wahr, Entladung neu schreiben
                        # Verbrauchsgrenze == 2000 && Feste Grenze == 0 (leer)
                        if (GesamtverbrauchHaus > VerbrauchsgrenzeEntladung and VerbrauchsgrenzeEntladung > 0 and FesteEntladegrenze == 0):
                            Neu_BatteryMaxDischargePercent = int((GesamtverbrauchHaus - VerbrauchsgrenzeEntladung)/BattganzeLadeKapazWatt*100)
                        # Verbrauchsgrenze == 2000 && Feste Grenze == 500 
                        elif (GesamtverbrauchHaus > VerbrauchsgrenzeEntladung and VerbrauchsgrenzeEntladung > 0 and FesteEntladegrenze > 0):
                            Neu_BatteryMaxDischargePercent = int(FesteEntladegrenze/BattganzeLadeKapazWatt*100)
                        # Verbrauchsgrenze == 0 (leer) && Feste Grenze == 500
                        elif (VerbrauchsgrenzeEntladung == 0 and FesteEntladegrenze > 0):
                            Neu_BatteryMaxDischargePercent = int(FesteEntladegrenze/BattganzeLadeKapazWatt*100)
                        else:
                            Neu_BatteryMaxDischargePercent = MaxEntladung

                        DEBUG_Ausgabe+="\nDEBUG Batterieentladegrenze NEU: " + str(Neu_BatteryMaxDischargePercent) + "%"

                        # Entladung_Daempfung, Unterschied muss größer WREntladeSchreibGrenze_Watt sein
                        WREntladeSchreibGrenze_Prozent = int(WREntladeSchreibGrenze_Watt / BattganzeLadeKapazWatt * 100 + 1)
                        if (abs(Neu_BatteryMaxDischargePercent - BatteryMaxDischargePercent) < WREntladeSchreibGrenze_Prozent):
                            Neu_BatteryMaxDischargePercent = BatteryMaxDischargePercent

                        ## Werte zum Überprüfen ausgeben
                        if print_level >= 1:
                            print("######### E N T L A D E S T E U E R U N G #########\n")
                            print("Feste Entladegrenze:       ", entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1'], "%")
                            print("Batteriestatus in Prozent: ", BattStatusProz, "%")
                            print("GesamtverbrauchHaus:       ", GesamtverbrauchHaus, "W")
                            print("VerbrauchsgrenzeEntladung: ", VerbrauchsgrenzeEntladung, "W")
                            print("Batterieentladegrenze ALT: ", BatteryMaxDischargePercent, "%")
                            print("Batterieentladegrenze NEU: ", Neu_BatteryMaxDischargePercent, "%")
                            print()

                        Schreib_Ausgabe = ""

                        if (Neu_BatteryMaxDischargePercent != BatteryMaxDischargePercent):
                            if ('entladen' in Options):
                                valueNew = gen24.write_data('BatteryMaxDischargePercent', Neu_BatteryMaxDischargePercent * 100)
                                bereits_geschrieben = 1
                                DEBUG_Ausgabe+="\nDEBUG Meldung Entladewert schreiben: " + str(valueNew)
                                Schreib_Ausgabe = Schreib_Ausgabe + "Folgender Wert wurde geschrieben für Batterieentladung: " + str(Neu_BatteryMaxDischargePercent) + "%\n"
                                Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe 
                            else:
                                Schreib_Ausgabe = Schreib_Ausgabe + "Entladesteuerung NICHT geschrieben, da Option \"entladen\" NICHT gesetzt!\n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Unterschied Alte und Neue Werte der Batterieentladung kleiner ("+ str(WREntladeSchreibGrenze_Watt) + "W), NICHTS zu schreiben!!\n"

                        if print_level >= 1:
                            print(Schreib_Ausgabe)

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADESTEUERUNG >>>>>>>>>>>>>"

                    ######## E N T L A D E B E G R E N Z U N G ab hier wenn eingeschaltet!
                    if  EntladeGrenze_steuern == 1 and aktuellePVProduktion < 10:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADEBEGRENZUNG >>>>>>>>>>>>>"

                        MaxEntladung = 100
                        ProgGrenzeMorgen = basics.getVarConf('Entladung','ProgGrenzeMorgen','eval')
                        EntladeGrenze_Min = basics.getVarConf('Entladung','EntladeGrenze_Min','eval')
                        EntladeGrenze_Max = basics.getVarConf('Entladung','EntladeGrenze_Max','eval')
                        PrognoseMorgen = progladewert.getPrognoseMorgen()[0]/1000
                        Battery_MinRsvPct = int(gen24.read_data('Battery_MinRsvPct')/100)
                        Neu_Battery_MinRsvPct = EntladeGrenze_Min
                        if (PrognoseMorgen < ProgGrenzeMorgen and PrognoseMorgen != 0):
                            Neu_Battery_MinRsvPct = EntladeGrenze_Max
                        if print_level >= 1:
                            print("######### E N T L A D E B E G R E N Z U N G #########\n")
                            print("Prognose Morgen: ", PrognoseMorgen, "KW")
                            print("Batteriereserve: ", Battery_MinRsvPct, "%")
                            print("Neu_Batteriereserve: ", Neu_Battery_MinRsvPct, "%")
                            print()

                        Schreib_Ausgabe = ""

                        if (Neu_Battery_MinRsvPct != Battery_MinRsvPct):
                            if ('entladen' in Options):
                                valueNew = gen24.write_data('Battery_MinRsvPct', Neu_Battery_MinRsvPct * 100)
                                bereits_geschrieben = 1
                                DEBUG_Ausgabe+="\nDEBUG Meldung Entladegrenze schreiben: " + str(valueNew)
                                Schreib_Ausgabe = Schreib_Ausgabe + "Folgender Wert wurde geschrieben für Batterieentladebegrenzung: " + str(Neu_Battery_MinRsvPct) + "%\n"
                                Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe 
                            else:
                                Schreib_Ausgabe = Schreib_Ausgabe + "Batterieentladebegrenzung NICHT geschrieben, da Option \"entladen\" NICHT gesetzt!\n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Batterieentladebegrenzung hat sich nicht verändert, NICHTS zu schreiben!!\n"

                        if print_level >= 1:
                            print(Schreib_Ausgabe)

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADEBEGRENZUNG >>>>>>>>>>>>>"

                    # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
                    if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
                        Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
                        apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
                        print("PushMeldung an ", Push_Message_Url, " gesendet.\n")


                    ######## PV Reservierung ENDE


                    # FALLBACK des Wechselrichters bei Ausfall der Steuerung
                    if Fallback_on != 0:
                        Fallback_Schreib_Ausgabe = ""
                        akt_Fallback_time = gen24.read_data('InOutWRte_RvrtTms_Fallback')
                        if Fallback_on == 2:
                            Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback ist eingeschaltet.\n"
                            DEBUG_Ausgabe+="\nDEBUG <<<<<<<< FALLBACK >>>>>>>>>>>>>"
                            Akt_Zeit_Rest = int(datetime.strftime(now, "%H%M")) % (Fallback_Zeitabstand_Std*100)
                            Fallback_Sekunden = int((Fallback_Zeitabstand_Std * 3600) + (Cronjob_Minutenabstand * 60 * 0.9))
                            # Zur vollen Fallbackstunde wenn noch kein Schreibzugriff war Fallback schreiben
                            if Akt_Zeit_Rest == 0 or akt_Fallback_time != Fallback_Sekunden:
                                if bereits_geschrieben == 0 or akt_Fallback_time != Fallback_Sekunden:
                                    if (Options != []):
                                        fallback_msg = gen24.write_data('InOutWRte_RvrtTms_Fallback', Fallback_Sekunden)
                                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback " + str(Fallback_Sekunden) + " geschrieben.\n"
                                        DEBUG_Ausgabe+="\nDEBUG Meldung FALLBACK schreiben: " + str(fallback_msg)
                                    else:
                                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback wurde NICHT geschrieben, da KEINE Option zum Schreiben gesetzt.\n"
                                else:
                                    Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback wurde NICHT geschrieben, da bereits auf den WR geschrieben wurde.\n"

                        else:
                            Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback ist NICHT eingeschaltet.\n"
                            if akt_Fallback_time != 1:
                                if (Options != []):
                                    fallback_msg = gen24.write_data('InOutWRte_RvrtTms_Fallback', 0)
                                    Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback Deaktivierung geschrieben.\n"
                                    DEBUG_Ausgabe+="\nDEBUG Meldung FALLBACK Deaktivierung schreiben: " + str(fallback_msg)
                                else:
                                    Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback Deaktivierung NICHT geschrieben, da KEINE Option zum Schreiben gesetzt.\n"

                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "InOutWRte_RvrtTms_Fallback: " + str(gen24.read_data('InOutWRte_RvrtTms_Fallback')) + "\n"
                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "StorageControlMode:    " + str(gen24.read_data('StorageControlMode')) + "\n"
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE FALLBACK >>>>>>>>>>>>>"

                        if print_level >= 1:
                            print(Fallback_Schreib_Ausgabe)
                    # FALLBACK ENDE

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


            finally:
                    if (gen24 and not auto):
                            gen24.modbus.close()


        else:
            print(datetime.now())
            print("WR offline")

