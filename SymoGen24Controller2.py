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
                print('Wetterdatei fehlt oder ist fehlerhaft, bitte erst Wetterdaten neu laden!!')
                exit()
        return data

def holeGitHubConfig(Link, filename):
    try:
        web_ini = requests.get(Link, allow_redirects=True)
        open(filename, 'wb').write(web_ini.content)
        return("True")
    except:
        return("False")


def getRestTagesPrognoseUeberschuss( AbzugWatt, aktuelleEinspeisung, aktuellePVProduktion ):

        # alle Prognodewerte zwischen aktueller Stunde und 22:00 lesen
        format_Tag = "%Y-%m-%d"
        # aktuelle Stunde und aktuelle Minute
        Akt_Std = int(datetime.strftime(now, "%H"))
        Akt_Minute = int(datetime.strftime(now, "%M"))
        i = Akt_Std
        Pro_Uebersch_Tag = 0
        Pro_Ertrag_Tag = 0
        Pro_LadeKapa_Rest = 0
        Pro_Spitze = 0
        Grundlast_Sum = 0


        while i < BattVollUm:
            Std = datetime.strftime(now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
            if data['result']['watts'].get(Std):
                    Prognose = data['result']['watts'].get(Std)
            else:
                    Prognose = 0

            # Stundendaempung rechnen  mit BatSparFaktor
            tmp_Stundendaempfung = (BattVollUm - i) * BatSparFaktor
            if tmp_Stundendaempfung < 1:
                tmp_Stundendaempfung = 1

            Pro_Uebersch = (Prognose - AbzugWatt) / tmp_Stundendaempfung

            # Prognosenspitzenwert für Resttag ermitteln
            if Prognose > Pro_Spitze:
                Pro_Spitze = Prognose

            # wenn nicht zur vollen Stunde, Wert anteilsmaessig
            if i == Akt_Std:
                Prognose = (Prognose / 60 * (60 - Akt_Minute))
                Pro_Uebersch = (Pro_Uebersch / 60 * (60 - Akt_Minute))

            Pro_Ertrag_Tag += Prognose

            if Prognose > 0:
                Grundlast_Sum += Grundlast

            if Pro_Uebersch > MaxLadung:
                Pro_Uebersch = MaxLadung

            if Pro_Uebersch > 0:
                Pro_Uebersch_Tag += Pro_Uebersch
            else:
                Pro_Uebersch = 0

            # Ab hier Ausgabe zum Vergleich mit der Tabelle Prognosewerte_Vergleichtabelle.ods
            #if i == Akt_Std:
            #    print("ACHTUNG: Im vorletzte Block sind die richtigen Werte zum Vergleich mit der Tabelle Prognosewerte_Vergleichtabelle.ods!!")
            #print("Std, Akt_Minute, Prognose, Pro_Uebersch, tmp_Stundendaempfung :", i, Akt_Minute, int(Prognose), int(Pro_Uebersch), tmp_Stundendaempfung )

            i  += 1


        # Hier noch den aktuellen Ladewert der Schleife ermitteln und im return mitgeben
        LadewertStd = datetime.strftime(now, format_aktStd)
        LadewertStd_naechste = datetime.strftime(now + timedelta(minutes = (60)), format_aktStd)
        
        if data['result']['watts'].get(LadewertStd):
                Pro_Akt1 = (data['result']['watts'].get(LadewertStd))
        else:
                Pro_Akt1 = 0

        if data['result']['watts'].get(LadewertStd_naechste):
                Pro_Akt2 = (data['result']['watts'].get(LadewertStd_naechste))
        else:
                Pro_Akt2 = 0
            
        # zu jeder Minute den genauen Zwischenwert mit den beiden Stundenprognosen rechnen
        Pro_Akt = int((Pro_Akt1 * (60 - Akt_Minute) + Pro_Akt2 * Akt_Minute) / 60)

        # Nun den Aktuellen Ladewert rechnen 

        # BatSparFaktor aus der config.ini = Faktor um Batteriekapazitaet fuer spaeter zu sparen
        # Daempfungsfaktor rechnen 
        Stundendaempfung = (BattVollUm - Akt_Std - (Akt_Minute/60)) * BatSparFaktor
        if Stundendaempfung < 1:
            Stundendaempfung = 1

        # Batterieladewert mit allen Einfluessen aus der Prognose rechnen
        aktuellerLadewert = int((Pro_Akt - AbzugWatt)/Stundendaempfung)
        LadewertGrund = "Prognoseberechnung / Stundendaempfung"

        # BatWaitFaktor hier anwenden
        Tagessumme_Faktor = int((Pro_Ertrag_Tag - Grundlast_Sum) / (BatWaitFaktor_Max - BatWaitFaktor + 1))
        BattKapaProz_akt = int(BattKapaWatt_akt /  BattganzeLadeKapazWatt*100)
        print("Tagessumme_Faktor, BattKapaProz_akt, BatWaitFaktor: ", Tagessumme_Faktor, BattKapaProz_akt, BatWaitFaktor)
        if Tagessumme_Faktor > BattKapaWatt_akt and BatWaitFaktor != 0 and BattKapaProz_akt > 30 and Akt_Std < 13:
            aktuellerLadewert = LadungAus
            LadewertGrund = "Tagesprognose / BatWaitFaktor > Batteriekapazitaet "

        # Aktuelle Einspeise-Leistung beruecksichtigen
        aktuellerUeberschuss = int(aktuelleEinspeisung + (BattganzeLadeKapazWatt * oldPercent/10000) - Einspeisegrenze)
        if aktuellerUeberschuss > aktuellerLadewert and (BattganzeLadeKapazWatt * oldPercent/10000) <= (MaxLadung + 100):
            aktuellerLadewert = int(aktuellerUeberschuss)
            LadewertGrund = "aktuelleEinspeisung + aktueller Ladewert > Einspeisegrenze"

        # Ladeleistung auf 30% Kappung begrenzen
        if (aktuellerLadewert > MaxLadung):
            aktuellerLadewert = MaxLadung

        # Wenn  PV-Produktion > WR_Kapazitaet 
        if (aktuellePVProduktion - WR_Kapazitaet > aktuellerLadewert ):
           aktuellerLadewert = int(aktuellePVProduktion - WR_Kapazitaet)
           LadewertGrund = "PV-Produktion > WR_Kapazitaet"

        # Bei Minuswerten "LadungAus" setzen
        if aktuellerLadewert < LadungAus:
            aktuellerLadewert = LadungAus


        return int(Pro_Uebersch_Tag), int(Pro_Ertrag_Tag), aktuellerLadewert, Grundlast_Sum, Pro_Spitze, Pro_Akt, LadewertGrund

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
    
                    ###############################
    
                    data = loadWeatherData(config)
                    gen24 = SymoGen24Connector.SymoGen24(config['gen24']['hostNameOrIp'], config['gen24']['port'], auto)
                    # print(data)

                    if gen24.read_data('Battery_Status') == 1:
                        print(datetime.now())
                        print("Batterie ist Offline keine Steuerung möglich!!! ")
                        print()
                        exit()
    
                    # Benoetigte Variablen definieren
                    # Rechenwerte aus Config in Zahlen umwandeln
                    print_level = eval(config['Ladeberechnung']['print_level'])
                    BattVollUm = eval(config['Ladeberechnung']['BattVollUm'])
                    BatSparFaktor = eval(config['Ladeberechnung']['BatSparFaktor'])
                    BatWaitFaktor = eval(config['Ladeberechnung']['BatWaitFaktor'])
                    BatWaitFaktor_Max = eval(config['Ladeberechnung']['BatWaitFaktor_Max'])
                    MaxLadung = eval(config['Ladeberechnung']['MaxLadung'])
                    LadungAus = eval(config['Ladeberechnung']['LadungAus'])
                    Einspeisegrenze = eval(config['Ladeberechnung']['Einspeisegrenze'])
                    WR_Kapazitaet = eval(config['Ladeberechnung']['WR_Kapazitaet'])
                    Grundlast = eval(config['Ladeberechnung']['Grundlast'])
                    MindBattLad = eval(config['Ladeberechnung']['MindBattLad'])
                    BatterieVoll = eval(config['Ladeberechnung']['BatterieVoll'])
                    WRSchreibGrenze_nachOben = eval(config['Ladeberechnung']['WRSchreibGrenze_nachOben'])
                    WRSchreibGrenze_nachUnten = eval(config['Ladeberechnung']['WRSchreibGrenze_nachUnten'])
                    FesteLadeleistung = eval(config['Ladeberechnung']['FesteLadeleistung'])
                    Fallback_on = eval(config['Fallback']['Fallback_on'])
                    Cronjob_Minutenabstand = eval(config['Fallback']['Cronjob_Minutenabstand'])
                    Fallback_Zeitabstand_Std = eval(config['Fallback']['Fallback_Zeitabstand_Std'])
                    # BattganzeLadeKapazWatt = (gen24.read_data('BatteryChargeRate')) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattganzeLadeKapazWatt = (gen24.read_data('Battery_capa')) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattStatusProz = gen24.read_data('Battery_SoC')/100
                    BattKapaWatt_akt = int((1 - BattStatusProz/100) * BattganzeLadeKapazWatt)
                    aktuelleEinspeisung = int(gen24.get_meter_power() * -1)
                    aktuellePVProduktion = int(gen24.get_mppt_power())
    
                    # 0 = nicht auf WR schreiben, 1 = schon auf WR schreiben
                    newPercent_schreiben = 0
                    oldPercent = gen24.read_data('BatteryMaxChargePercent')
    
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
                    Pro_Spitze = 0
                    aktuelleVorhersage = 0
                    LadewertGrund = ""
    
                    if ((BattStatusProz < MindBattLad)):
                        # volle Ladung ;-)
                        DATA = setLadewert(MaxLadung)
                        newPercent = DATA[0]
                        newPercent_schreiben = DATA[1]
                        LadewertGrund = "BattStatusProz < MindBattLad"
    
                    else:
                        
                        # Abzugswert sollte nicht kleiner Grundlast sein, sonnst wird PV-Leistung zur Ladung der Batterie berechnet,
                        # die durch die Grundlast im Haus verbraucht wird. => Batterie wird nicht voll
                        i = Grundlast
                        # Gesamte Tagesprognose, Tagesüberschuß aus Prognose und aktuellen Ladewert ermitteln
                        # Schleife laeft von 0 nach oben, bis der Prognoseueberschuss die aktuelle Batteriekapazietaet erreicht
                        while (Schleifenwert_TagesPrognoseUeberschuss > BattKapaWatt_akt):
                            PrognoseUNDUeberschuss = getRestTagesPrognoseUeberschuss( i, aktuelleEinspeisung, aktuellePVProduktion )
                            Schleifenwert_TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                            if(PrognoseUNDUeberschuss[0] >= BattKapaWatt_akt) or (i == Grundlast):
                                PrognoseAbzugswert = i
                                TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                                TagesPrognoseGesamt = PrognoseUNDUeberschuss[1]
                                aktuellerLadewert = PrognoseUNDUeberschuss[2]
                                Grundlast_Summe = PrognoseUNDUeberschuss[3]
                                Pro_Spitze = PrognoseUNDUeberschuss[4]
                                aktuelleVorhersage = PrognoseUNDUeberschuss[5]
                                LadewertGrund = PrognoseUNDUeberschuss[6]
                            i += 100

                        # Nun habe ich die Werte und muss hier weiter Verzweigen
    
                        # Wenn die Variable "FesteLadeleistung" größer "0" ist, wird der Wert fest als Ladeleistung in Watt geschrieben einstellbare Wattzahl
                        if FesteLadeleistung > 0:
                            DATA = setLadewert(FesteLadeleistung)
                            newPercent = DATA[0]
                            if newPercent == oldPercent:
                                newPercent_schreiben = 0
                            else:
                                newPercent_schreiben = 1
                            LadewertGrund = "FesteLadeleistung"
    
                        else:
    
                            if (TagesPrognoseGesamt > Grundlast) and ((TagesPrognoseGesamt - Grundlast_Summe) < BattKapaWatt_akt):
                                # volle Ladung ;-)
                                DATA = setLadewert(MaxLadung)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]
                                LadewertGrund = "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt"
    
                            elif (BattStatusProz > BatterieVoll ):
                                # Wenn Batterie voll, Volle Ladung
                                DATA = setLadewert(MaxLadung)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]
                                LadewertGrund = "Batterie voll"
        
                            elif (TagesPrognoseUeberschuss < BattKapaWatt_akt) or (PrognoseAbzugswert == Grundlast):
                                # Auch hier die Schaltverzögerung anbringen, aber nur mit halben Wert
                                Daempfunghier = 0
                                # Hier immer MaxLadung, also immer nach oben, deshalb keine WRSchreibGrenze_nachUnten nötig
                                # if BattKapaWatt_akt - TagesPrognoseUeberschuss < WRSchreibGrenze_nachUnten / 2:
                                   # WRSchreibGrenze_nachUnten = 10000
                                   # Daempfunghier = 1
                                if BattKapaWatt_akt - TagesPrognoseUeberschuss < WRSchreibGrenze_nachOben / 2:
                                   WRSchreibGrenze_nachOben = 10000
                                   Daempfunghier = 1

                                # volle Ladung ;-)
                                DATA = setLadewert(MaxLadung)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]
                                LadewertGrund = "PrognoseAbzugswert <= Grundlast"

                                # Wenn durch die Dämpfung hier nicht geschrieben wird, Hinweis ausgeben
                                if (newPercent_schreiben == 0) and (Daempfunghier == 1):
                                    LadewertGrund = "PrognoseAbzugswert <= Grundlast (Unterschied zu gering zum Schreiben)"
                                    newPercent = oldPercent
                            else: 
                                DATA = setLadewert(aktuellerLadewert)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]

                

                    if print_level == 1:
                        try:
                            print()
                            print(datetime.now())
                            print("TagesPrognoseUeberschuss: ", TagesPrognoseUeberschuss)
                            print("TagesPrognoseGesamt: ", TagesPrognoseGesamt)
                            print("aktuellePVProduktion: ", aktuellePVProduktion)
                            print("aktuelleEinspeisung: ", aktuelleEinspeisung)
                            print("aktuelleVorhersage: ", aktuelleVorhersage)
                            print("PrognoseAbzugswert: ", PrognoseAbzugswert)
                            print("BattKapaWatt_akt: ", BattKapaWatt_akt)
                            print("aktuellerLadewert: ", aktuellerLadewert)
                            print("LadewertGrund: ", LadewertGrund)
                            print("oldPercent:", oldPercent)
                            print("newPercent: ", newPercent)
                            print("newPercent_schreiben: ", newPercent_schreiben)
                            print("Grundlast_Summe: ", Grundlast_Summe)
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
                    # Neuen Ladewert in Prozent schreiben, wenn newPercent_schreiben == 1
                    if newPercent_schreiben == 1:
                        if len(argv) > 1 and (argv[1] == "schreiben"):
                            valueNew = gen24.write_data('BatteryMaxChargePercent', newPercent)
                            bereits_geschrieben = 1
                            Schreib_Ausgabe = Schreib_Ausgabe + "Folgender Wert wurde geschrieben: " + str(newPercent) + "\n\n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Es wurde nix geschrieben, da NICHT \"schreiben\" übergeben wurde: \n\n"
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Alte und Neue Werte unterscheiden sich weniger als die Schreibgrenzen des WR, NICHTS geschreiben!!\n\n"

                    # Ladungsspeichersteuerungsmodus aktivieren wenn nicht aktiv
                    # kann durch Fallback (z.B. nachts) erfordelich sein, ohne dass Änderung an der Ladeleistung nötig ist
                    if gen24.read_data('StorageControlMode') != 3:
                        if len(argv) > 1 and (argv[1] == "schreiben"):
                            Ladelimit = gen24.write_data('StorageControlMode', 3 )
                            bereits_geschrieben = 1
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode neu geschrieben.\n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "StorageControlMode neu wurde NICHT geschrieben, da NICHT \"schreiben\" übergeben wurde:\n"

                    if print_level == 1:
                        print(Schreib_Ausgabe)
    

                    # FALLBACK des Wechselrichters bei Ausfall der Steuerung
                    if Fallback_on != 0:
                        Fallback_Schreib_Ausgabe = ""
                        akt_Fallback_time = gen24.read_data('InOutWRte_RvrtTms_Fallback')
                        if Fallback_on == 2:
                            Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback ist eingeschaltet.\n"
                            Akt_Zeit_Rest = int(datetime.strftime(now, "%H%M")) % (Fallback_Zeitabstand_Std*100)
                            Fallback_Sekunden = int((Fallback_Zeitabstand_Std * 3600) + (Cronjob_Minutenabstand * 60 * 0.9))
                            # Zur vollen Fallbackstunde wenn noch kein Schreibzugriff war Fallback schreiben
                            if Akt_Zeit_Rest == 0 or akt_Fallback_time != Fallback_Sekunden:
                                if bereits_geschrieben == 0 or akt_Fallback_time != Fallback_Sekunden:
                                    if len(argv) > 1 and (argv[1] == "schreiben"):
                                        fallback_msg = gen24.write_data('InOutWRte_RvrtTms_Fallback', Fallback_Sekunden)
                                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback geschrieben.\n"
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
                                else:
                                    Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "Fallback Deaktivierung NICHT geschrieben, da NICHT \"schreiben\" übergeben wurde:\n"

                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "InOutWRte_RvrtTms_Fallback: " + str(gen24.read_data('InOutWRte_RvrtTms_Fallback')) + "\n"
                        Fallback_Schreib_Ausgabe = Fallback_Schreib_Ausgabe + "StorageControlMode:    " + str(gen24.read_data('StorageControlMode')) + "\n"

                        if print_level == 1:
                            print(Fallback_Schreib_Ausgabe)
                    # FALLBACK ENDE


            finally:
                    if (gen24 and not auto):
                            gen24.modbus.close()


        else:
            print(datetime.now())
            print("WR offline")

