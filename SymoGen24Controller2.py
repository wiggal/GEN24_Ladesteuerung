import json
import configparser
from datetime import datetime, timedelta
import pytz
import requests
import SymoGen24Connector
from ping3 import ping

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
        with open(config['env']['filePathWeatherData']) as json_file:
                data = json.load(json_file)

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

            # Stundendaempung rechnen 
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

        # Wenn noch genuegend Prognosewert zum Laden der Batterie uebrig, Batteriekapazitaet aufsparen
        if Pro_LadeKapa_Rest > BattKapaWatt_akt:
            aktuellerLadewert = 10
            LadewertGrund = "Prognoseberechnung > Batteriekapazitaet ",Pro_LadeKapa_Rest, BattKapaWatt_akt

        # Aktuelle Einspeise-Leistung beruecksichtigen
        aktuellerUeberschuss = int(aktuelleEinspeisung + (BattganzeKapazWatt * oldPercent/10000) - Einspeisegrenze)
        if aktuellerUeberschuss > aktuellerLadewert:
            aktuellerLadewert = int(aktuellerUeberschuss)
            LadewertGrund = "aktuelleEinspeisung + aktueller Ladewert > Einspeisegrenze"

        # Ladeleistung auf 30% Kappung begrenzen
        if (aktuellerLadewert > MaxKapp):
            aktuellerLadewert = MaxKapp

        # Wenn  PV-Produktion > WR_Kapazitaet 
        if (aktuellePVProduktion - WR_Kapazitaet > aktuellerLadewert ):
           aktuellerLadewert = int(aktuellePVProduktion - WR_Kapazitaet)
           LadewertGrund = "PV-Produktion > WR_Kapazitaet"

        # Bei Minuswerten 10 setzen
        if aktuellerLadewert < 10:
            aktuellerLadewert = 10

        return int(Pro_Uebersch_Tag), int(Pro_Ertrag_Tag), aktuellerLadewert, Grundlast_Sum, Pro_Spitze, Pro_Akt, LadewertGrund

def setLadewert(fun_Ladewert):
        if fun_Ladewert > MaxLadung:
            fun_Ladewert = MaxLadung

        newPercent = (int(fun_Ladewert/BattganzeKapazWatt*100)) * 100
        # Prozent des Ladewertes auf volle 10 kappen
        if newPercent < 10:
            newPercent = 10

        # Schaltvezögerung
        # mit altem Ladewert vergleichen
        diffLadewert_nachOben = int(fun_Ladewert - oldPercent*BattganzeKapazWatt/10000)
        diffLadewert_nachUnten = int((oldPercent*BattganzeKapazWatt/10000) - fun_Ladewert)

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
    
                    # Benoetigte Variablen definieren
                    # Rechenwerte aus Config in Zahlen umwandeln
                    print_level = eval(config['Ladeberechnung']['print_level'])
                    BattVollUm = eval(config['Ladeberechnung']['BattVollUm'])
                    BatSparFaktor = eval(config['Ladeberechnung']['BatSparFaktor'])
                    MaxLadung = eval(config['Ladeberechnung']['MaxLadung'])
                    Einspeisegrenze = eval(config['Ladeberechnung']['Einspeisegrenze'])
                    WR_Kapazitaet = eval(config['Ladeberechnung']['WR_Kapazitaet'])
                    Grundlast = eval(config['Ladeberechnung']['Grundlast'])
                    MindBattLad = eval(config['Ladeberechnung']['MindBattLad'])
                    BattertieVoll = eval(config['Ladeberechnung']['BattertieVoll'])
                    MaxKapp = eval(config['Ladeberechnung']['MaxKapp'])
                    WRSchreibGrenze_nachOben = eval(config['Ladeberechnung']['WRSchreibGrenze_nachOben'])
                    WRSchreibGrenze_nachUnten = eval(config['Ladeberechnung']['WRSchreibGrenze_nachUnten'])
                    FesteLadeleistung = eval(config['Ladeberechnung']['FesteLadeleistung'])
                    BattganzeKapazWatt = 1
                    BattganzeKapazWatt = (gen24.read_data('BatteryChargeRate'))
                    BattStatusProz = gen24.read_data('Battery_SoC')/100
                    BattKapaWatt_akt = int((1 - BattStatusProz/100) * BattganzeKapazWatt)
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
                            newPercent_schreiben = DATA[1]
                            LadewertGrund = "FesteLadeleistung"
    
                        else:
    
                            if (TagesPrognoseGesamt > Grundlast) and ((TagesPrognoseGesamt - Grundlast_Summe) < BattKapaWatt_akt):
                                # volle Ladung ;-)
                                DATA = setLadewert(MaxLadung)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]
                                LadewertGrund = "TagesPrognoseGesamt - Grundlast_Summe < BattKapaWatt_akt"
    
                            elif (BattStatusProz > BattertieVoll ):
                                # Wenn Batterie voll, Volle Ladung
                                DATA = setLadewert(MaxLadung)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]
                                LadewertGrund = "Batterie voll"
        
                            elif (TagesPrognoseUeberschuss < BattKapaWatt_akt) or (PrognoseAbzugswert == Grundlast):
                                # Auch hier die Schaltverzögerung anbringen, aber nur mit halben Wert
                                Daempfunghier = 0
                                if BattKapaWatt_akt - TagesPrognoseUeberschuss < WRSchreibGrenze_nachUnten / 2:
                                   WRSchreibGrenze_nachUnten = 10000
                                   Daempfunghier = 1
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
                            else: 
                                DATA = setLadewert(aktuellerLadewert)
                                newPercent = DATA[0]
                                newPercent_schreiben = DATA[1]

                

                    if print_level == 1:
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



                    if newPercent_schreiben == 1:
                        ### HIER SCHARF wenn Argument "schreiben" übergeben
                        from sys import argv
                        if len(argv) > 1 and (argv[1] == "schreiben"):
                            valueNew = gen24.write_data('BatteryMaxChargePercent', newPercent)
                            if print_level == 1:
                                    print("Folgender Wert wurde geschrieben: ", newPercent)
                            # Ladelimit aktivieren wenn nicht aktiv
                            if gen24.read_data('StorageControlMode') == 0:
                                Ladelimit = gen24.write_data('StorageControlMode', 1 )
                        else:
                            if print_level == 1:
                                print("Es wurde nix geschrieben, da nicht \"schreiben\" übergeben wurde: \n")
    
                    else:
                        if print_level == 1:
                            print("Alte und Neue Werte unterscheiden sich weniger als die Schreibgrenzen des WR, nichts geschreiben!!\n")
    

            finally:
                    if (gen24 and not auto):
                            gen24.modbus.close()


        else:
            print(datetime.now())
            print("WR offline")

