import pickledb
import json
import configparser
from datetime import datetime, timedelta
import pytz
import requests
import SymoGen24Connector

def loadConfig(conf_file):
        config = configparser.ConfigParser()
        try:
                config.read_file(open('config.ini'))
                config.read(conf_file)
        except:
                exit()
        return config

def setDbValue(db, name, value):
        valueOld = db.get(name)
        if (valueOld != value):
                db.set(name, value)
        
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


def getRestTagesPrognoseUeberschuss( AbzugWatt, MinVerschiebewert ):

        # alle Prognodewerte zwischen aktueller Stunde und 22:00 lesen
        format_Tag = "%Y-%m-%d"
        # aktuelle Stunde + MinVerschiebewert
        Akt_Std_Versch = int((datetime.strftime(now + timedelta(minutes = MinVerschiebewert), "%H")))
        Akt_Minute_Versch = int(datetime.strftime(now + timedelta(minutes = MinVerschiebewert), "%M"))
        i = Akt_Std_Versch
        Pro_Uebersch_Tag = 0
        Pro_Ertrag_Tag = 0
        Pro_Spitze = 0
        Grundlast_Sum = 0

        while i < BattVollUm:
            Std = datetime.strftime(now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
            if data['result']['watts'].get(Std):
                    Pro = data['result']['watts'].get(Std)
            else:
                    Pro = 0

            Pro_Uebersch = Pro - AbzugWatt

            # Prognosenspitzenwert für Resttag ermitteln
            if Pro > Pro_Spitze:
                Pro_Spitze = Pro

            # wenn nicht zur vollen Stunde, Wert anteilsmaessig
            if i == Akt_Std_Versch:
                Pro = (Pro / 60 * (60 - Akt_Minute_Versch))
                Pro_Uebersch = (Pro_Uebersch / 60 * (60 - Akt_Minute_Versch))

            Pro_Ertrag_Tag += Pro

            if Pro > 0:
                Grundlast_Sum += Grundlast

            if Pro_Uebersch > 0:
                Pro_Uebersch_Tag += Pro_Uebersch

            i  += 1


        # Hier noch den aktuellen Laderwert der Schleife ermitteln und im return mitgeben, mal die ProzLadedaempfung
        LadewertStd = datetime.strftime(now + timedelta(minutes = MinVerschiebewert), format_aktStd)
        LadewertStd_naechste = datetime.strftime(now + timedelta(minutes = (MinVerschiebewert + 60)), format_aktStd)
        
        if data['result']['watts'].get(LadewertStd):
                Pro_Akt1 = (data['result']['watts'].get(LadewertStd))
        else:
                Pro_Akt1 = 0

        if data['result']['watts'].get(LadewertStd_naechste):
                Pro_Akt2 = (data['result']['watts'].get(LadewertStd_naechste))
        else:
                Pro_Akt2 = 0
            
        # zu jeder Minute den genauen Zwischenwert der beiden Stundenprognosen rechnen
        Pro_Akt = int((Pro_Akt1 * (60 - Akt_Minute_Versch) + Pro_Akt2 * Akt_Minute_Versch) / 60)

        # Nun den Aktuellen Ladewert rechnen * ProzLadedaempfung - (DiffLadedaempfung)
        aktuellerLadewert = int((Pro_Akt - AbzugWatt) * ProzLadedaempfung - (DiffLadedaempfung))

        if aktuellerLadewert < 10:
            aktuellerLadewert = 10

        # Aktuelle PV-Leistung beruecksichtigen => Mittelwert aus aktuellerUeberschuss und aktuellerLadewert
        MPPT_Power_Scale_Factor = gen24.read_data('MPPT_Power_Scale_Factor')
        MPPT_1_DC_Power = int(gen24.read_data('MPPT_1_DC_Power'))
        MPPT_2_DC_Power = int(gen24.read_data('MPPT_2_DC_Power'))
        # Wenn MPPT_Power_Scale_Factor = 0 dann ist skalierung = 1.0
        if MPPT_Power_Scale_Factor == 0:
            skalierung = 1
        else:
            skalierung = 10**(MPPT_Power_Scale_Factor-65536)

        aktuelleProduktion =  int((MPPT_1_DC_Power + MPPT_2_DC_Power)*skalierung)
        aktuellerUeberschuss = int(aktuelleProduktion - Einspeizegerenze - Grundlast)
        # if MPPT_Power_Scale_Factor == 0:
        #    print("MPPT_Power_Scale_Factor, skalierung, MPPT_1_DC_Power, MPPT_2_DC_Power, aktuelleProduktion: ", MPPT_Power_Scale_Factor, skalierung, MPPT_1_DC_Power, MPPT_2_DC_Power, aktuelleProduktion)

        if aktuellerUeberschuss > aktuellerLadewert:
            # print("aktuelleProduktion, aktuellerUeberschuss, aktuellerLadewert: ", aktuelleProduktion, aktuellerUeberschuss, aktuellerLadewert)
            # aktuellerLadewert = int((aktuellerUeberschuss * GewichtAktUebersch + aktuellerLadewert) / (GewichtAktUebersch +1))
            aktuellerLadewert = int(aktuellerUeberschuss)


        # Ladeleistung auf 30% Kappung begrenzen
        if (aktuellerLadewert > MaxKapp):
            aktuellerLadewert = MaxKapp

        # Wenn Batterie voll, Volle Ladung
        if (BattStatusProz > BattertieVoll ):
            aktuellerLadewert = MaxLadung

        # Wenn  PV-Produktion kleiner Grundlast, Ladeleistung ausschalten
        if (aktuelleProduktion < Grundlast) and (aktuellerLadewert < Grundlast):
            aktuellerLadewert = 10

        # print("aktuelleProduktion, Grundlast: ", gen24.read_data('MPPT_1_DC_Power'), gen24.read_data('MPPT_2_DC_Power'), aktuelleProduktion, Grundlast)

        # Bei Minuswerten 10 setzen
        if aktuellerLadewert < 10:
            aktuellerLadewert = 10

        return int(Pro_Uebersch_Tag), int(Pro_Ertrag_Tag), aktuellerLadewert, Grundlast_Sum, Pro_Spitze, aktuelleProduktion, Pro_Akt

def setLadewert(fun_Ladewert):
        # Prozent auch hier auf 100 runden damit nicht so oft auf den WR geschrieben wird
        newPercent = (int(fun_Ladewert/BattganzeKapazWatt*100+0.5)) * 100
        # Prozent des Ladewertes auf volle 10 kappen
        if newPercent < 10:
            newPercent = 10

        # mit altem Wert vergleichen
        diffPercent = abs(newPercent - oldPercent)

        # Wenn die Differenz in hundertstel Prozent kleiner als die Schreingrenze nix schreiben
        if ( diffPercent < WRSchreibGrenze ):
            newPercent_schreiben = 0
        else:
            newPercent_schreiben = 1

        return(newPercent, newPercent_schreiben)


def storeSettingsToDb(db):
        latestBatteryMaxPower = db.get('latestBatteryMaxPower')
        db.set('latestBatteryMaxPower', 'value')
        db.dump()

if __name__ == '__main__':
        config = loadConfig('config.ini')

        # Wenn Githubsteuerung = yes config.ini von GitHub holen und nochmal lesen
        if config['GithubSteuerung']['Githubsteuerung'] == 'yes':
            ERG = holeGitHubConfig(config['GithubSteuerung']['Github_Link'], config['GithubSteuerung']['Github_ini_filename'])
            if ERG == "True":
                config = loadConfig(config['GithubSteuerung']['Github_ini_filename'])
            else:
                print(config['GithubSteuerung']['Github_Link'], "nicht vorhanden")


        db = pickledb.load(config['env']['filePathConfigDb'], True)

        #now = datetime.now(pytz.timezone(config['env']['timezone']))
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"
        
        gen24 = None
        auto = False
        try:            
                chargeStart = None
                if (db.get('ChargeStart')):
                        chargeStart = datetime.strptime(db.get('ChargeStart'), format)
                        # print(f'Current chargeStart loaded from db: {chargeStart}')
                
                newPercent = None

                ###############################

                data = loadWeatherData(config)
                gen24 = SymoGen24Connector.SymoGen24(config['gen24']['hostNameOrIp'], config['gen24']['port'], auto)
                # print(data)

                # Benoetigte Variablen definieren
                # Rechenwerte aus Config in Zahlen umwandeln
                print_level = eval(config['Ladeberechnung']['print_level'])
                BattVollUm = eval(config['Ladeberechnung']['BattVollUm'])
                MinVerschiebewert = eval(config['Ladeberechnung']['MinVerschiebewert'])
                MaxLadung = eval(config['Ladeberechnung']['MaxLadung'])
                Einspeizegerenze = eval(config['Ladeberechnung']['Einspeizegerenze'])
                MindestSpitzenwert = eval(config['Ladeberechnung']['MindestSpitzenwert'])
                Grundlast = eval(config['Ladeberechnung']['Grundlast'])
                MindBattLad = eval(config['Ladeberechnung']['MindBattLad'])
                BattertieVoll = eval(config['Ladeberechnung']['BattertieVoll'])
                NullLadung = eval(config['Ladeberechnung']['NullLadung'])
                MaxKapp = eval(config['Ladeberechnung']['MaxKapp'])
                WRSchreibGrenze = eval(config['Ladeberechnung']['WRSchreibGrenze'])
                ProzLadedaempfung = eval(config['Ladeberechnung']['ProzLadedaempfung'])
                DiffLadedaempfung = eval(config['Ladeberechnung']['DiffLadedaempfung'])
                GewichtAktUebersch = eval(config['Ladeberechnung']['GewichtAktUebersch'])
                StartKappGrenze = eval(config['Ladeberechnung']['StartKappGrenze'])
                FesteLadeleistung = eval(config['Ladeberechnung']['FesteLadeleistung'])
                Grundlast_Einspeizegerenze = Grundlast + Einspeizegerenze
                # BattganzeKapazWatt = (gen24.read_data('Battery_capa'))
                BattganzeKapazWatt = (gen24.read_data('BatteryChargeRate'))
                BattStatusProz = gen24.read_data('Battery_SoC')/100
                BattKapaWatt_akt = int((1 - BattStatusProz/100) * BattganzeKapazWatt)

                # 0 = nicht auf WR schreiben, 1 = schon auf WR schreiben
                newPercent_schreiben = 0
                oldPercent = gen24.read_data('BatteryMaxChargePercent')

                format_aktStd = "%Y-%m-%d %H:00:00"


                #######################################
                ## Ab hier gehts los wie Ablaufdiagramm
                #######################################

                TagesPrognoseUeberschuss = 0
                TagesPrognoseGesamt = 0
                aktuellerLadewert = 0
                PrognoseAbzugswert = 0
                Grundlast_Summe = 0

                if ((BattStatusProz < MindBattLad)):
                    # volle Ladung ;-)
                    DATA = setLadewert(MaxLadung)
                    newPercent = DATA[0]
                    newPercent_schreiben = DATA[1]

                else:
                    
                    i = StartKappGrenze
                    # Gesamte Tagesprognose, Tagesüberschuß aus Prognose und aktuellen Ladewert ermitteln
                    # and (i >= 0) damit PrognoseAbzugswert nicht ins Minus laeuft
                    while (TagesPrognoseUeberschuss <= BattKapaWatt_akt) and (i >= 0):
                        PrognoseUNDUeberschuss = getRestTagesPrognoseUeberschuss( i, MinVerschiebewert )
                        TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                        TagesPrognoseGesamt = PrognoseUNDUeberschuss[1]
                        aktuellerLadewert = PrognoseUNDUeberschuss[2]
                        Grundlast_Summe = PrognoseUNDUeberschuss[3]
                        Pro_Spitze = PrognoseUNDUeberschuss[4]
                        aktuelleProduktion = PrognoseUNDUeberschuss[5]
                        aktuelleVorhersage = PrognoseUNDUeberschuss[6]
                        PrognoseAbzugswert = i
                        i -= 100

                    # Nun habe ich die Werte und muss hier weiter Verzweigen

                    # Wenn die Variable "FesteLadeleistung" größer "0" ist, wird der Wert fest als Ladeleistung in Watt geschrieben einstellbare Wattzahl
                    if FesteLadeleistung > 0:
                        DATA = setLadewert(FesteLadeleistung)
                        newPercent = DATA[0]
                        newPercent_schreiben = DATA[1]

                    else:

                        if (TagesPrognoseGesamt > Grundlast) and ((TagesPrognoseGesamt - Grundlast_Summe) < BattKapaWatt_akt):
                            # volle Ladung ;-)
                            DATA = setLadewert(MaxLadung)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]

                        elif Pro_Spitze < MindestSpitzenwert:
                            # volle Ladung ;-)
                            DATA = setLadewert(MaxLadung)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]
    
                        else: 
                            DATA = setLadewert(aktuellerLadewert)
                            newPercent = DATA[0]
                            newPercent_schreiben = DATA[1]

                

                if print_level == 1:
                    print()
                    print(datetime.now())
                    print("TagesPrognoseUeberschuss: ", TagesPrognoseUeberschuss)
                    print("TagesPrognoseGesamt: ", TagesPrognoseGesamt)
                    print("aktuelleProduktion: ", aktuelleProduktion)
                    print("aktuelleVorhersage: ", aktuelleVorhersage)
                    print("PrognoseAbzugswert: ", PrognoseAbzugswert)
                    print("BattKapaWatt_akt: ", BattKapaWatt_akt)
                    print("aktuellerLadewert: ", aktuellerLadewert)
                    print("oldPercent :", oldPercent)
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
                        print("Alte und Neue Werte unterscheiden sich weniger als die Schreingrenze des WR ( abs(",oldPercent, "-", newPercent, ") <", WRSchreibGrenze,"), nichts zu schreiben!!\n")


        finally:
                if (gen24 and not auto):
                        gen24.modbus.close()
