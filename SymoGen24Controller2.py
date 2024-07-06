from datetime import datetime, timedelta
import pytz
import requests
import FUNCTIONS.SymoGen24Connector
from ping3 import ping
from sys import argv
from FUNCTIONS.functions import loadConfig, loadWeatherData, loadPVReservierung, getVarConf, save_SQLite
from FUNCTIONS.fun_Ladewert import getLadewertinGrenzen, getRestTagesPrognoseUeberschuss, getPrognoseLadewert, setLadewert, \
        getPrognoseMorgen, globalfrommain, getEinspeiseGrenzeLadewert, getAC_KapaLadewert, getParameter
from FUNCTIONS.fun_API import get_API


if __name__ == '__main__':
        config = loadConfig('config.ini')
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"

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
                # Ladungsspeichersteuerungsmodus deaktivieren 
                host_ip = getVarConf('gen24','hostNameOrIp', 'str')
                host_port = getVarConf('gen24','port', 'str')
                gen24 = FUNCTIONS.SymoGen24Connector.SymoGen24(host_ip, host_port, False)
                if gen24.read_data('StorageControlMode') != 0:
                    valueNew = gen24.write_data('StorageControlMode', 0 )
                    print("StorageControlMode 0 neu geschrieben.")
                print(now, "ProgrammSTOPP durch WebUI-Settings: ", Parameter[1])
                exit()
                

        host_ip = getVarConf('gen24','hostNameOrIp', 'str')
        host_port = getVarConf('gen24','port', 'str')
        if ping(host_ip):
            # Nur ausführen, wenn WR erreichbar
            gen24 = None
            auto = False
            try:            
                    newPercent = None
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< E I N >>>>>>>\n\n"
    
                    ###############################
    
                    weatherfile = getVarConf('env','filePathWeatherData','str')
                    data = loadWeatherData(weatherfile)

                    gen24 = FUNCTIONS.SymoGen24Connector.SymoGen24(host_ip, host_port, auto)
                    
                    if gen24.read_data('Battery_Status') == 1:
                        print(datetime.now())
                        print("Batterie ist Offline keine Steuerung möglich!!! ")
                        print()
                        exit()
    
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


                    # Benoetigte Variablen vom GEN24 lesen und definieren
                    # Hier nun über API
                    API = get_API()
                    BattganzeLadeKapazWatt = (API['BattganzeLadeKapazWatt'])
                    BattganzeKapazWatt = (API['BattganzeKapazWatt'])
                    BattStatusProz = API['BattStatusProz']
                    BattKapaWatt_akt = API['BattKapaWatt_akt']
                    aktuelleEinspeisung = API['aktuelleEinspeisung']
                    aktuellePVProduktion = API['aktuellePVProduktion']
                    aktuelleBatteriePower = API['aktuelleBatteriePower']
                    GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower

                    # Aktuelle Entladewert von Modbus holen
                    BatteryMaxDischargePercent = int(gen24.read_data('BatteryMaxDischargePercent')/100) 

                    reservierungdata = {}
                    # Reservierungsdatei lesen, wenn Reservierung eingeschaltet
                    if  PV_Reservierung_steuern == 1:
                        Reservierungsdatei = getVarConf('Reservierung','PV_ReservieungsDatei','str')
                        reservierungdata = loadPVReservierung(Reservierungsdatei)

                    # 0 = nicht auf WR schreiben, 1 = schon auf WR schreiben
                    newPercent_schreiben = 0
                    oldPercent = gen24.read_data('BatteryMaxChargePercent')
                    alterLadewert = int(oldPercent*BattganzeLadeKapazWatt/10000)
    
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
                        WRSchreibGrenze_nachUnten = int(WRSchreibGrenze_nachUnten * (1 + ( BattStatusProz - 90 ) / 5))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachUnten: " + str(WRSchreibGrenze_nachUnten) +"\n"
                        WRSchreibGrenze_nachOben = int(WRSchreibGrenze_nachOben * (1 + ( BattStatusProz - 90 ) / 5))
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
                    AktuellenLadewert_Array = getEinspeiseGrenzeLadewert(WRSchreibGrenze_nachOben, aktuellerLadewert, aktuelleEinspeisung, aktuellePVProduktion, \
                                            LadewertGrund, alterLadewert, PV_Leistung_Watt)
                    aktuellerLadewert = AktuellenLadewert_Array[0]
                    LadewertGrund = AktuellenLadewert_Array[1]
                    DEBUG_Ausgabe = AktuellenLadewert_Array[2]
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
                            # Um des setzen der Akkuschonung zu verhindern, wenn zu wenig PV Energie kommt oder der Akku wieder entladen wird nur bei entspechender Vorhersage anwenden
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
                        # Für die Nacht zwingend auf MaxLadung, 
                        # da sonst mogends evtl nicht auf 0 gestelltwerden kann, wegen WRSchreibGrenze_nachUnten
                        if alterLadewert < MaxLadung -10 :
                            aktuellerLadewert = MaxLadung
                            DATA = setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten)
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
                            print("******* BEGINN: ", datetime.now(),"******* ")
                            print("\n## MODBUS LADESTEUERUNG ###")
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
                    ### AB HIER SCHARF wenn Argument "schreiben" übergeben

                    bereits_geschrieben = 0
                    Schreib_Ausgabe = ""
                    Push_Schreib_Ausgabe = ""
                    # Neuen Ladewert in Prozent schreiben, wenn newPercent_schreiben == 1
                    if newPercent_schreiben == 1:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< LADEWERTE >>>>>>>>>>>>>"
                        DEBUG_Ausgabe+="\nDEBUG Folgender Ladewert neu zum Schreiben: " + str(newPercent)
                        if len(argv) > 1 and (argv[1] == "schreiben"):
                            valueNew = gen24.write_data('BatteryMaxChargePercent', newPercent)
                            bereits_geschrieben = 1
                            Schreib_Ausgabe = Schreib_Ausgabe + "Am WR geschrieben: " + str(newPercent / 100) + "% = " + str(aktuellerLadewert) + "W\n"
                            Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei Ladegrenze schreiben: " + str(valueNew)
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Es wurde nix geschrieben, da NICHT \"schreiben\" übergeben wurde: \n"
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Alte und Neue Werte unterscheiden sich weniger als die Schreibgrenzen des WR, NICHTS zu schreiben!!\n"

                    # Ladungsspeichersteuerungsmodus aktivieren wenn nicht aktiv
                    # kann durch Fallback (z.B. nachts) erfordelich sein, ohne dass Änderung an der Ladeleistung nötig ist
                    if gen24.read_data('StorageControlMode') != 3:
                        if len(argv) > 1 and (argv[1] == "schreiben"):
                            DEBUG_Ausgabe += "\nDEBUG StorageControlMode 3 schreiben! "
                            valueNew = gen24.write_data('StorageControlMode', 3 )
                            bereits_geschrieben = 1
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode 3 neu geschrieben.\n"
                            Push_Schreib_Ausgabe += "StorageControlMode 3 neu geschrieben.\n"
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei StorageControlMode schreiben: " + str(valueNew)
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode neu wurde NICHT geschrieben, da NICHT \"schreiben\" übergeben wurde:\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)
    
                    ######## E N T L A D E S T E U E R U N G  ab hier wenn eingeschaltet!

                    if  Batterieentlandung_steuern == 1:
                        MaxEntladung = 100

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADESTEUERUNG >>>>>>>>>>>>>"

                        # EntladeSteuerungFile lesen
                        EntladeSteuerungFile = getVarConf('Entladung','Akku_EntladeSteuerungsFile','str')
                        entladesteurungsdata = loadPVReservierung(EntladeSteuerungFile)
                        # Manuellen Entladewert lesen
                        if (entladesteurungsdata.get('ManuelleEntladesteuerung')):
                            MaxEntladung = entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']
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
                            if len(argv) > 1 and (argv[1] == "schreiben"):
                                valueNew = gen24.write_data('BatteryMaxDischargePercent', Neu_BatteryMaxDischargePercent * 100)
                                bereits_geschrieben = 1
                                DEBUG_Ausgabe+="\nDEBUG Meldung Entladewert schreiben: " + str(valueNew)
                                Schreib_Ausgabe = Schreib_Ausgabe + "Folgender Wert wurde geschrieben für Batterieentladung: " + str(Neu_BatteryMaxDischargePercent) + "%\n"
                                Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe 
                            else:
                                Schreib_Ausgabe = Schreib_Ausgabe + "Für Batterieentladung wurde NICHT " + str(Neu_BatteryMaxDischargePercent) +"% geschrieben, da NICHT \"schreiben\" übergeben wurde: \n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Unterschied Alte und Neue Werte der Batterieentladung kleiner ("+ str(WREntladeSchreibGrenze_Watt) + "W), NICHTS zu schreiben!!\n"

                        if print_level >= 1:
                            print(Schreib_Ausgabe)

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADESTEUERUNG >>>>>>>>>>>>>"

                    ######## E N T L A D E B E G R E N Z U N G ab hier wenn eingeschaltet!
                    if  EntladeGrenze_steuern == 1 and aktuellePVProduktion < 10:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADEBEGRENZUNG >>>>>>>>>>>>>"

                        MaxEntladung = 100
                        ProgGrenzeMorgen = getVarConf('Entladung','ProgGrenzeMorgen','eval')
                        EntladeGrenze_Min = getVarConf('Entladung','EntladeGrenze_Min','eval')
                        EntladeGrenze_Max = getVarConf('Entladung','EntladeGrenze_Max','eval')
                        PrognoseMorgen = getPrognoseMorgen()[0]/1000
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
                            if len(argv) > 1 and (argv[1] == "schreiben"):
                                valueNew = gen24.write_data('Battery_MinRsvPct', Neu_Battery_MinRsvPct * 100)
                                bereits_geschrieben = 1
                                DEBUG_Ausgabe+="\nDEBUG Meldung Entladegrenze schreiben: " + str(valueNew)
                                Schreib_Ausgabe = Schreib_Ausgabe + "Folgender Wert wurde geschrieben für Batterieentladebegrenzung: " + str(Neu_Battery_MinRsvPct) + "%\n"
                                Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe 
                            else:
                                Schreib_Ausgabe = Schreib_Ausgabe + "Für Batterieentladebegrenzung wurde NICHT " + str(Neu_Battery_MinRsvPct) +"% geschrieben, da NICHT \"schreiben\" übergeben wurde: \n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Batterieentladebegrenzung hat sich nicht verändert, NICHTS zu schreiben!!\n"

                        if print_level >= 1:
                            print(Schreib_Ausgabe)

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADEBEGRENZUNG >>>>>>>>>>>>>"

                    # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
                    if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
                        Push_Message_Url = getVarConf('messaging','Push_Message_Url','str')
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
                                    if len(argv) > 1 and (argv[1] == "schreiben"):
                                        fallback_msg = gen24.write_data('InOutWRte_RvrtTms_Fallback', Fallback_Sekunden)
                                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback " + str(Fallback_Sekunden) + " geschrieben.\n"
                                        DEBUG_Ausgabe+="\nDEBUG Meldung FALLBACK schreiben: " + str(fallback_msg)
                                    else:
                                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback wurde NICHT geschrieben, da NICHT \"schreiben\" übergeben wurde:\n"
                                else:
                                    Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback wurde NICHT geschrieben, da bereits auf den WR geschrieben wurde.\n"

                        else:
                            Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback ist NICHT eingeschaltet.\n"
                            if akt_Fallback_time != 0:
                                if len(argv) > 1 and (argv[1] == "schreiben"):
                                    fallback_msg = gen24.write_data('InOutWRte_RvrtTms_Fallback', 0)
                                    Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback Deaktivierung geschrieben.\n"
                                    DEBUG_Ausgabe+="\nDEBUG Meldung FALLBACK Deaktivierung schreiben: " + str(fallback_msg)
                                else:
                                    Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback Deaktivierung NICHT geschrieben, da NICHT \"schreiben\" übergeben wurde:\n"

                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "InOutWRte_RvrtTms_Fallback: " + str(gen24.read_data('InOutWRte_RvrtTms_Fallback')) + "\n"
                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "StorageControlMode:    " + str(gen24.read_data('StorageControlMode')) + "\n"
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE FALLBACK >>>>>>>>>>>>>"

                        if print_level >= 1:
                            print(Fallback_Schreib_Ausgabe)
                    # FALLBACK ENDE

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


            finally:
                    if (gen24 and not auto):
                            gen24.modbus.close()


        else:
            print(datetime.now())
            print("WR offline")

