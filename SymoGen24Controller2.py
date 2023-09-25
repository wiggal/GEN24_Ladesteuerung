import json
import configparser
from datetime import datetime, timedelta
import pytz
import requests
import SymoGen24Connector
from ping3 import ping
from sys import argv

def loadConfig(conf_file):
        config = configparser.ConfigParser()
        try:
                config.read_file(open('config.ini'))
                config.read(conf_file)
        except:
                exit()
        return config

def loadWeatherData(config):
        data = None
        try:
            with open(config['env']['filePathWeatherData']) as json_file:
                data = json.load(json_file)
        except:
                print("Wetterdatei fehlt oder ist fehlerhaft, bitte erst Wetterdaten neu laden!!")
                exit()
        return data

def loadPVReservierung(file):
        reservierungdata = None
        try:
            with open(file) as json_file:
                reservierungdata = json.load(json_file)
        except:
                print(file , " fehlt, bitte erzeugen oder Option abschalten !!")
                exit()
        return reservierungdata

def getPrognose(Stunde):
        if data['result']['watts'].get(Stunde):
            data_tmp = data['result']['watts'][Stunde]
            # Wenn Reservierung eingeschaltet und Reservierungswert vorhanden von Prognose abziehen.
            if ( PV_Reservierung_steuern == 1 and reservierungdata.get(Stunde)):
                data_tmp = data['result']['watts'][Stunde] - reservierungdata[Stunde]
                # Minuswerte verhindern
                if ( data_tmp< 0): data_tmp = 0
            getPrognose = data_tmp
        else:
            getPrognose = 0
        return getPrognose


def getRestTagesPrognoseUeberschuss( AbzugWatt, aktuelleEinspeisung, aktuellePVProduktion ):

        # alle Prognodewerte zwischen aktueller Stunde und 22:00 lesen
        format_Tag = "%Y-%m-%d"
        # aktuelle Stunde und aktuelle Minute
        Akt_Std = int(datetime.strftime(now, "%H"))
        Akt_Minute = int(datetime.strftime(now, "%M"))
        i = Akt_Std
        Pro_Uebersch_Tag = 0
        Pro_Uebersch_Tag_voll = 0
        Pro_Ertrag_Tag = 0
        Pro_LadeKapa_Rest = 0
        Grundlast_Sum = 0
        # um Divison durch Null zu verhindern kleinsten Wert setzen
        global BatSparFaktor
        if BatSparFaktor < 0.1:
            BatSparFaktor = 0.1

        # in Schleife Prognosewerte bis BattVollUm durchlaufen
        while i < BattVollUm:
            Std = datetime.strftime(now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
            Prognose = getPrognose(Std)

            # Prognoseüberschuss mit und ohne Dämpfung rechnen
            Pro_Uebersch = (Prognose - AbzugWatt) / BatSparFaktor
            Pro_Uebersch_voll = (Prognose - AbzugWatt)

            # wenn nicht zur vollen Stunde, Wert anteilsmaessig
            Grundlast_tmp = Grundlast
            if i == Akt_Std:
                Prognose = (Prognose / 60 * (60 - Akt_Minute))
                Pro_Uebersch = (Pro_Uebersch / 60 * (60 - Akt_Minute))
                Pro_Uebersch_voll = (Pro_Uebersch_voll / 60 * (60 - Akt_Minute))
                Grundlast_tmp = int((Grundlast / 60 * (60 - Akt_Minute)))

            Pro_Ertrag_Tag += Prognose

            if Prognose > 0:
                Grundlast_Sum += Grundlast_tmp

            if Pro_Uebersch > MaxLadung:
                Pro_Uebersch = MaxLadung

            if Pro_Uebersch_voll > MaxLadung:
                Pro_Uebersch_voll = MaxLadung

            if Pro_Uebersch > 0:
                Pro_Uebersch_Tag += Pro_Uebersch

            if Pro_Uebersch_voll > 0:
                Pro_Uebersch_Tag_voll += Pro_Uebersch_voll

            i  += 1


        # Hier noch den aktuellen Ladewert der Schleife ermitteln und im return mitgeben
        # Prognose nur bis BattVollUm berechnen
        Pro_Akt1 = 0
        Pro_Akt2 = 0
        if (Akt_Std < BattVollUm):
            LadewertStd = datetime.strftime(now, format_aktStd)
            Pro_Akt1 = (getPrognose(LadewertStd))
        if (Akt_Std + 1 < BattVollUm):
            LadewertStd_naechste = datetime.strftime(now + timedelta(minutes = (60)), format_aktStd)
            Pro_Akt2 = (getPrognose(LadewertStd_naechste))

        # zu jeder Minute den genauen Zwischenwert mit den beiden Stundenprognosen rechnen
        # wenn Letzte Stunde vor BatterieVollUm dann nicht Prognose von nächster Stund addieren!!
        Pro_Akt = int((Pro_Akt1 * (60 - Akt_Minute) + Pro_Akt2 * Akt_Minute) / 60)
        if ( Pro_Akt< 0): Pro_Akt = 0

        # Nun den Aktuellen Ladewert rechnen 
        # Batterieladewert mit allen Einfluessen aus der Prognose rechnen
        aktuellerLadewert = int((Pro_Akt - AbzugWatt)/BatSparFaktor)
        LadewertGrund = "Prognoseberechnung / BatSparFaktor"

        if aktuellerLadewert < 0: aktuellerLadewert = 0

        # Erklärung: aktuelleBatteriePower ist beim Laden der Batterie minus
        # Wenn Einspeisung über Einspeisegrenze, dann könnte WR schon abregeln, desshalb WRSchreibGrenze_nachOben addieren
        if aktuelleEinspeisung - aktuelleBatteriePower > Einspeisegrenze:
            EinspeisegrenzUeberschuss = int(aktuelleEinspeisung - aktuelleBatteriePower - Einspeisegrenze + (WRSchreibGrenze_nachOben * 1.05))
        else:
            EinspeisegrenzUeberschuss = int(aktuelleEinspeisung - aktuelleBatteriePower - Einspeisegrenze)
        # Damit durch die Pufferaddition nicht die maximale PV_Leistung überschritten wird
        if EinspeisegrenzUeberschuss > PV_Leistung_Watt - Einspeisegrenze:
            EinspeisegrenzUeberschuss = PV_Leistung_Watt - Einspeisegrenze

        if EinspeisegrenzUeberschuss > aktuellerLadewert and (BattganzeLadeKapazWatt * oldPercent/10000) <= (MaxLadung + 100):
            aktuellerLadewert = int(EinspeisegrenzUeberschuss)
            LadewertGrund = "PV_Leistungsüberschuss > Einspeisegrenze"

        # Ladeleistung auf MaxLadung begrenzen
        if (aktuellerLadewert > MaxLadung):
            aktuellerLadewert = MaxLadung

        # Wenn  PV-Produktion > WR_Kapazitaet (AC)
        if aktuellePVProduktion > WR_Kapazitaet:
            kapazitaetsueberschuss = int(aktuellePVProduktion - WR_Kapazitaet + WRSchreibGrenze_nachOben)
            if kapazitaetsueberschuss > PV_Leistung_Watt - WR_Kapazitaet:
                kapazitaetsueberschuss = PV_Leistung_Watt - WR_Kapazitaet
            if (kapazitaetsueberschuss > aktuellerLadewert ):
                aktuellerLadewert = kapazitaetsueberschuss
                LadewertGrund = "PV-Produktion > AC_Kapazitaet WR"

        # Bei Minuswerten "LadungAus" setzen
        if aktuellerLadewert < LadungAus:
            aktuellerLadewert = LadungAus


        return int(Pro_Uebersch_Tag), int(Pro_Ertrag_Tag), aktuellerLadewert, Grundlast_Sum, Pro_Akt, LadewertGrund, int(Pro_Uebersch_Tag_voll)

def setLadewert(fun_Ladewert):
        if fun_Ladewert > MaxLadung:
            fun_Ladewert = MaxLadung

        newPercent = (int(fun_Ladewert/BattganzeLadeKapazWatt*10000))
        if newPercent < LadungAus:
            newPercent = LadungAus

        # Schaltvezögerung
        # mit altem Ladewert vergleichen
        diffLadewert_nachOben = int(fun_Ladewert - oldPercent*BattganzeLadeKapazWatt/10000)
        diffLadewert_nachUnten = int((oldPercent*BattganzeLadeKapazWatt/10000) - fun_Ladewert)

        # Wenn die Differenz in hundertstel Prozent kleiner als die Schreibgrenze nix schreiben
        newPercent_schreiben = 0
        if ( diffLadewert_nachOben > WRSchreibGrenze_nachOben ):
            newPercent_schreiben = 1
        if ( diffLadewert_nachUnten > WRSchreibGrenze_nachUnten ):
            newPercent_schreiben = 1

        # Wenn MaxLadung erstmals erreicht ist immer schreiben
        if (fun_Ladewert == MaxLadung) and (abs(diffLadewert_nachOben) > 3):
            newPercent_schreiben = 1

        return(newPercent, newPercent_schreiben)

if __name__ == '__main__':
        config = loadConfig('config.ini')
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"

        if ping(config['gen24']['hostNameOrIp']):
            # Nur ausführen, wenn WR erreichbar
            gen24 = None
            auto = False
            try:            
                    newPercent = None
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< WR schreiben EIN >>>>>>>"
    
                    ###############################
    
                    data = loadWeatherData(config)

                    # Reservierungsdatei lesen, wenn Reservierung eingeschaltet
                    PV_Reservierung_steuern = eval(config['Reservierung']['PV_Reservierung_steuern'])
                    if  PV_Reservierung_steuern == 1:
                        reservierungdata = loadPVReservierung(config['Reservierung']['PV_ReservieungsDatei'])

                    gen24 = SymoGen24Connector.SymoGen24(config['gen24']['hostNameOrIp'], config['gen24']['port'], auto)

                    if gen24.read_data('Battery_Status') == 1:
                        print(datetime.now())
                        print("Batterie ist Offline keine Steuerung möglich!!! ")
                        print()
                        exit()
    
                    # Benoetigte Variablen definieren
                    # eval = Rechenwerte aus Config in Zahlen umwandeln
                    print_level = eval(config['Ladeberechnung']['print_level'])
                    BattVollUm = eval(config['Ladeberechnung']['BattVollUm'])
                    BatSparFaktor = eval(config['Ladeberechnung']['BatSparFaktor'])
                    MaxLadung = eval(config['Ladeberechnung']['MaxLadung'])
                    LadungAus = eval(config['Ladeberechnung']['LadungAus'])
                    Einspeisegrenze = eval(config['Ladeberechnung']['Einspeisegrenze'])
                    WR_Kapazitaet = eval(config['Ladeberechnung']['WR_Kapazitaet'])
                    PV_Leistung_Watt = eval(config['Ladeberechnung']['PV_Leistung_Watt'])
                    Grundlast = eval(config['Ladeberechnung']['Grundlast'])
                    MindBattLad = eval(config['Ladeberechnung']['MindBattLad'])
                    WRSchreibGrenze_nachOben = eval(config['Ladeberechnung']['WRSchreibGrenze_nachOben'])
                    WRSchreibGrenze_nachUnten = eval(config['Ladeberechnung']['WRSchreibGrenze_nachUnten'])
                    FesteLadeleistung = eval(config['Ladeberechnung']['FesteLadeleistung'])
                    Fallback_on = eval(config['Fallback']['Fallback_on'])
                    Cronjob_Minutenabstand = eval(config['Fallback']['Cronjob_Minutenabstand'])
                    Fallback_Zeitabstand_Std = eval(config['Fallback']['Fallback_Zeitabstand_Std'])
                    BattganzeLadeKapazWatt = (gen24.read_data('BatteryChargeRate')) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattganzeKapazWatt = (gen24.read_data('Battery_capa')) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattStatusProz = gen24.read_data('Battery_SoC')/100
                    BattKapaWatt_akt = int((1 - BattStatusProz/100) * BattganzeKapazWatt)
                    aktuelleEinspeisung = int(gen24.get_meter_power() * -1)
                    aktuellePVProduktion = int(gen24.get_mppt_power())
                    aktuelleBatteriePower = int(gen24.get_batterie_power())
                    BatteryMaxDischargePercent = int(gen24.read_data('BatteryMaxDischargePercent')/100) 
                    Push_Message_EIN = eval(config['messaging']['Push_Message_EIN'])
                    Push_Message_Url = config['messaging']['Push_Message_Url']

                    # 0 = nicht auf WR schreiben, 1 = schon auf WR schreiben
                    newPercent_schreiben = 0
                    oldPercent = gen24.read_data('BatteryMaxChargePercent')
                    alterLadewert = int(oldPercent*BattganzeLadeKapazWatt/10000)
    
                    format_aktStd = "%Y-%m-%d %H:00:00"
    
    
                    #######################################
                    ## Ab hier gehts los wie Ablaufdiagramm
                    #######################################
    
                    Schleifenwert_TagesPrognoseUeberschuss = 1000000
                    TagesPrognoseUeberschuss = 0
                    TagesPrognoseGesamt = 0
                    aktuellerLadewert = 0
                    PrognoseAbzugswert = 0
                    Grundlast_Summe = 0
                    aktuelleVorhersage = 0
                    LadewertGrund = ""

                    # WRSchreibGrenze_nachUnten ab 90% prozentual erhöhen (ersetzen von BatterieVoll!!)
                    if ( BattStatusProz - 90 > 0 ):
                        WRSchreibGrenze_nachUnten = int(WRSchreibGrenze_nachUnten * (1 + ( BattStatusProz - 90 ) / 10))

                    # Abzugswert sollte nicht kleiner Grundlast sein, sonnst wird PV-Leistung zur Ladung der Batterie berechnet,
                    # die durch die Grundlast im Haus verbraucht wird. => Batterie wird nicht voll
                    i = Grundlast
                    # Gesamte Tagesprognose, Tagesüberschuß aus Prognose und aktuellen Ladewert ermitteln
                    # Schleife laeft von 0 nach oben, bis der Prognoseueberschuss die aktuelle Batteriekapazietaet erreicht
                    while (Schleifenwert_TagesPrognoseUeberschuss > BattKapaWatt_akt):
                        PrognoseUNDUeberschuss = getRestTagesPrognoseUeberschuss( i, aktuelleEinspeisung, aktuellePVProduktion )
                        Schleifenwert_TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                        PrognoseAbzugswert = i
                        TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                        TagesPrognoseGesamt = PrognoseUNDUeberschuss[1]
                        aktuellerLadewert = PrognoseUNDUeberschuss[2]
                        Grundlast_Summe = PrognoseUNDUeberschuss[3]
                        aktuelleVorhersage = PrognoseUNDUeberschuss[4]
                        LadewertGrund = PrognoseUNDUeberschuss[5]
                        TagesPrognoseUeberschuss_voll = PrognoseUNDUeberschuss[6]
                        i += 100
                    # Nun habe ich die Werte und muss hier Verzweigen
                    print("TagesPrognoseUeberschuss, TagesPrognoseUeberschuss_voll, aktuellerLadewert: ", TagesPrognoseUeberschuss, TagesPrognoseUeberschuss_voll, aktuellerLadewert)

                    #  BatterieLuecke prozentual verteilen
                    BatterieLuecke = BattKapaWatt_akt - TagesPrognoseUeberschuss
                    aktuellerLadewert = int(aktuellerLadewert + (BatterieLuecke /(BattVollUm-(int(datetime.strftime(now, "%H"))+int(datetime.strftime(now, "%M"))/60)+0.001)))
                    # Ladeleistung auf MaxLadung begrenzen
                    if (aktuellerLadewert > MaxLadung):
                        aktuellerLadewert = MaxLadung
                    print(datetime.strftime(now, "%D %H:%M"),"(",BatSparFaktor, ") Prognoseladewert: ", aktuellerLadewert, " => Batteriekapazität: ", BattKapaWatt_akt, "BatterieLuecke: ", BatterieLuecke, "Abzug: ", PrognoseAbzugswert)
    
                    # Wenn über die PV-Planung manuelle Ladung angewählt wurde
                    MaxladungDurchPV_Planung = ""
                    if (PV_Reservierung_steuern == 1) and (reservierungdata.get('ManuelleSteuerung')):
                        FesteLadeleistung = MaxLadung * reservierungdata.get('ManuelleSteuerung')
                        if (reservierungdata.get('ManuelleSteuerung') != 0):
                            MaxladungDurchPV_Planung = "Manuelle Ladesteuerung in PV-Planung ausgewählt."

                    # Wenn die Variable "FesteLadeleistung" größer "0" ist, wird der Wert fest als Ladeleistung in Watt geschrieben einstellbare Wattzahl
                    if FesteLadeleistung > 0:
                        DATA = setLadewert(FesteLadeleistung)
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
                         DATA = setLadewert(aktuellerLadewert)
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
                            DATA = setLadewert(MaxLadung)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]
                            LadewertGrund = "BattStatusProz < MindBattLad"
    
                        else:
    
                            if (TagesPrognoseGesamt > Grundlast) and ((TagesPrognoseGesamt - Grundlast_Summe) < BattKapaWatt_akt):
                                # Auch hier die Schaltverzögerung anbringen und dann MaxLadung, also immer nach oben.
                                if BattKapaWatt_akt + Grundlast_Summe - TagesPrognoseGesamt < WRSchreibGrenze_nachOben:
                                    # Nach Prognoseberechnung darf es trotzdem nach oben gehen aber nicht von MaxLadung nach unten !
                                    WRSchreibGrenze_nachUnten = 100000
                                    DATA = setLadewert(aktuellerLadewert)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    # Nur wenn newPercent_schreiben = 0 dann LadewertGrund mit Hinweis übreschreiben
                                    if newPercent_schreiben == 0:
                                        LadewertGrund = " TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt (Unterschied weniger als Schreibgrenze)"
                                else:
                                    # volle Ladung ;-)
                                    aktuellerLadewert = MaxLadung
                                    DATA = setLadewert(MaxLadung)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    LadewertGrund = "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt"
    
                            # PrognoseAbzugswert - 100 um Schaltverzögerung wieder nach unten zu erreichen
                            elif (TagesPrognoseUeberschuss_voll < BattKapaWatt_akt) and (PrognoseAbzugswert - 100 <= Grundlast):
                                # Auch hier die Schaltverzögerung anbringen und dann MaxLadung, also immer nach oben.
                                if BattKapaWatt_akt - TagesPrognoseUeberschuss_voll < WRSchreibGrenze_nachOben:
                                    # Nach Prognoseberechnung darf es trotzdem nach oben gehen aber nicht von MaxLadung nach unten !
                                    WRSchreibGrenze_nachUnten = 100000
                                    DATA = setLadewert(aktuellerLadewert)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    # Nur wenn newPercent_schreiben = 0 dann LadewertGrund mit Hinweis übreschreiben
                                    if newPercent_schreiben == 0:
                                        LadewertGrund = "PrognoseAbzugswert nahe Grundlast (Unterschied weniger als Schreibgrenze)"
                                else:
                                    # volle Ladung ;-)
                                    aktuellerLadewert = MaxLadung
                                    DATA = setLadewert(MaxLadung)
                                    newPercent = DATA[0]
                                    newPercent_schreiben = DATA[1]
                                    LadewertGrund = "PrognoseAbzugswert kleiner Grundlast und Schreibgrenze"

                            else: 
                                DATA = setLadewert(aktuellerLadewert)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]

                

                    if print_level >= 1:
                        try:
                            print("************* BEGINN: ", datetime.now(),"************* ")
                            print("\n######### L A D E S T E U E R U N G #########\n")
                            print("aktuellePrognose:           ", aktuelleVorhersage)
                            print("RestTagesPrognose:          ", TagesPrognoseGesamt)
                            print("PrognoseAbzugswert/Stunde:  ", PrognoseAbzugswert)
                            print("TagesPrognose - Abzugswerte:", TagesPrognoseUeberschuss)
                            print("Grundlast_Summe für Tag:    ", Grundlast_Summe)
                            print("aktuellePVProduktion/Watt:  ", aktuellePVProduktion)
                            print("aktuelleEinspeisung/Watt:   ", aktuelleEinspeisung)
                            print("aktuelleBatteriePower/Watt: ", aktuelleBatteriePower)
                            print("aktuelleBattKapazität/Watt: ", BattKapaWatt_akt)
                            print("Batteriestatus in Prozent:  ", BattStatusProz,"%")
                            print("LadewertGrund: ", LadewertGrund)
                            print("Bisheriger Ladewert/Watt:   ", alterLadewert)
                            print("Bisheriger Ladewert/Prozent:", oldPercent/100,"%")
                            print("Neuer Ladewert/Watt:        ", aktuellerLadewert)
                            print("Neuer Ladewert/Prozent:     ", newPercent/100,"%")
                            print("newPercent_schreiben:       ", newPercent_schreiben)
                            # dataBatteryStats = gen24.read_section('StorageDevice')
                            # print(f'Battery Stats: {dataBatteryStats}') 
                            print()
                        except Exception as e:
                            print()
                            print("Fehler in den Printbefehlen, Ausgabe nicht möglich!")
                            print("Fehlermeldung:", e)
                            print()



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
                            Schreib_Ausgabe = Schreib_Ausgabe + "Folgender Wert wurde geschrieben: " + str(newPercent) + "\n"
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
                            Ladelimit = gen24.write_data('StorageControlMode', 3 )
                            bereits_geschrieben = 1
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode 3 neu geschrieben.\n"
                            Push_Schreib_Ausgabe += "StorageControlMode 3 neu geschrieben.\n"
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei StorageControlMode schreiben: " + str(valueNew)
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode neu wurde NICHT geschrieben, da NICHT \"schreiben\" übergeben wurde:\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)
    
                    ######## E N T L A D E S T E U E R U N G  ab hier wenn eingeschaltet!

                    # Variablen 'Entladung' aus config.ini lesen
                    Batterieentlandung_steuern = eval(config['Entladung']['Batterieentlandung_steuern'])
                    WREntladeSchreibGrenze_Watt = eval(config['Entladung']['WREntladeSchreibGrenze_Watt'])

                    if  Batterieentlandung_steuern == 1:
                        MaxEntladung = 100

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADUNG >>>>>>>>>>>>>"

                        # EntladeSteuerungFile lesen
                        entladesteurungsdata = loadPVReservierung(config['Entladung']['Akku_EntladeSteuerungsFile'])
                        # Manuellen Entladewert lesen
                        if (entladesteurungsdata.get('ManuelleEntladesteuerung')):
                            MaxEntladung = entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']
                            DEBUG_Ausgabe+="\nDEBUG MaxEntladung = entladesteurungsdata:" + str(MaxEntladung)

                        GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower
                        aktStd = datetime.strftime(now, "%H:00")

                        # Verbrauchsgrenze Entladung lesen
                        if (entladesteurungsdata[aktStd].get('Res_Feld1')):
                            VerbrauchsgrenzeEntladung = entladesteurungsdata[aktStd]['Res_Feld1']
                        else:
                            VerbrauchsgrenzeEntladung = 0

                        DEBUG_Ausgabe+="\nDEBUG VerbrauchsgrenzeEntladung: " + str(VerbrauchsgrenzeEntladung)
                        # Feste Entladegrenze lesen
                        if (entladesteurungsdata[aktStd].get('Res_Feld2')):
                            FesteEntladegrenze = entladesteurungsdata[aktStd]['Res_Feld2']
                        else:
                            FesteEntladegrenze = 0

                        DEBUG_Ausgabe+="\nDEBUG FesteEntladegrenze: " + str(FesteEntladegrenze)

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
                            print("Manuelle Entladesteuerung: ", entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1'], "%")
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
                                DEBUG_Ausgabe+="\nDEBUG Meldung Entladegrenze schreiben: " + str(valueNew)
                                Schreib_Ausgabe = Schreib_Ausgabe + "Folgender Wert wurde geschrieben für Batterieentladung: " + str(Neu_BatteryMaxDischargePercent) + "%\n"
                                Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe 
                            else:
                                Schreib_Ausgabe = Schreib_Ausgabe + "Für Batterieentladung wurde NICHT " + str(Neu_BatteryMaxDischargePercent) +"% geschrieben, da NICHT \"schreiben\" übergeben wurde: \n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Unterschied Alte und Neue Werte der Batterieentladung kleiner ("+ str(WREntladeSchreibGrenze_Watt) + "W), NICHTS zu schreiben!!\n"

                        if print_level >= 1:
                            print(Schreib_Ausgabe)

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADUNG >>>>>>>>>>>>>"

                    # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
                    if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
                        apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
                        print("PushMeldung an ", Push_Message_Url, " gesendet.")


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

