import pickledb
import json
import configparser
from datetime import datetime, timedelta
import pytz
import SymoGen24Connector

def loadConfig():
        config = configparser.ConfigParser()
        try:
                config.read('config.ini')
        except:
                print('config file not found.')
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

def getRestTagesPrognoseUeberschuss( AbzugWatt, MinVerschiebewert ):

        # alle Prognodewerte zwischen aktueller Stunde und 22:00 lesen
        format_Tag = "%Y-%m-%d"
        # aktuelle Stunde + MinVerschiebewert
        Akt_Std_Versch = int((datetime.strftime(now + timedelta(minutes = MinVerschiebewert), "%H")))
        Akt_Minute_Versch = int(datetime.strftime(now + timedelta(minutes = MinVerschiebewert), "%M"))
        i = Akt_Std_Versch
        Pro_Uebersch_Tag = 0
        Pro_Ertrag_Tag = 0
        Grundlast_Sum = 0

        while i < 22:
            Std = datetime.strftime(now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
            if data['result']['watts'].get(Std):
                    Pro = data['result']['watts'].get(Std)
            else:
                    Pro = 0

            Pro_Uebersch = Pro - AbzugWatt

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

        # Aktuelle PV-Leistung beruecksichtigen
        aktuelleProduktion =  int((gen24.read_data('MPPT_1_DC_Power') + gen24.read_data('MPPT_2_DC_Power'))/10)
        aktuellerUeberschuss = (aktuelleProduktion - Einspeizegerenze - Grundlast) 
        # print("aktuelleProduktion, aktuellerUeberschuss, aktuellerLadewert: ", aktuelleProduktion, aktuellerUeberschuss, aktuellerLadewert)
        if aktuellerUeberschuss > aktuellerLadewert:
            aktuellerLadewert = aktuellerUeberschuss



        if aktuellerLadewert < 10:
            aktuellerLadewert = 10

        # print(LadewertStd, Pro_Akt, Pro_Akt1, Pro_Akt2, AbzugWatt, aktuellerLadewert, Akt_Minute_Versch)


        # Ladeleistung auf 30% Kappung begrenzen
        if (aktuellerLadewert > MaxKapp):
            aktuellerLadewert = MaxKapp

        # Wenn Batterie voll, Volle Ladung
        if (BattStatusProz > 97 ):
            aktuellerLadewert = MaxLadung

        # Wenn  PV-Produktion kleiner Grundlast, Ladeleistung ausschalten
        if aktuelleProduktion < Grundlast:
            aktuellerLadewert = 10

        # print("aktuelleProduktion, Grundlast: ", gen24.read_data('MPPT_1_DC_Power'), gen24.read_data('MPPT_2_DC_Power'), aktuelleProduktion, Grundlast)

        # Bei Minuswerten 10 setzen
        if aktuellerLadewert < 10:
            aktuellerLadewert = 10

        return Pro_Uebersch_Tag, Pro_Ertrag_Tag, aktuellerLadewert, Grundlast_Sum

def setLadewert(fun_Ladewert):
        # Prozent auch hie auf 100 runden damit nicht so oft auf den WR geschrieben wird
        newPercent = (int(fun_Ladewert/BattganzeKapazWatt*100+0.5)) * 100
        # Prozent des Ladewertes auf volle 10 kappen
        if newPercent < 10:
            newPercent = 10

        # mit altem Wert vergleichen
        if ( newPercent == oldPercent ):
            newPercent_schreiben = 0
        else:
            newPercent_schreiben = 1

        return(newPercent, newPercent_schreiben)


def storeSettingsToDb(db):
        latestBatteryMaxPower = db.get('latestBatteryMaxPower')
        db.set('latestBatteryMaxPower', 'value')
        db.dump()

if __name__ == '__main__':
        config = loadConfig()
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
                MinVerschiebewert = eval(config['Ladeberechnung']['MinVerschiebewert'])
                MaxLadung = eval(config['Ladeberechnung']['MaxLadung'])
                Einspeizegerenze = eval(config['Ladeberechnung']['Einspeizegerenze'])
                Grundlast = eval(config['Ladeberechnung']['Grundlast'])
                MindBattLad = eval(config['Ladeberechnung']['MindBattLad'])
                NullLadung = eval(config['Ladeberechnung']['NullLadung'])
                MaxKapp = eval(config['Ladeberechnung']['MaxKapp'])
                ProzLadedaempfung = eval(config['Ladeberechnung']['ProzLadedaempfung'])
                DiffLadedaempfung = eval(config['Ladeberechnung']['DiffLadedaempfung'])
                StartKappGrenze = eval(config['Ladeberechnung']['StartKappGrenze'])
                WattpilotAn = eval(config['Ladeberechnung']['WattpilotAn'])
                Grundlast_Einspeizegerenze = Grundlast + Einspeizegerenze
                BattganzeKapazWatt = (gen24.read_data('Battery_capa'))
                BattStatusProz = gen24.read_data('Battery_SoC')/100
                BattKapaWatt_akt = int((1 - BattStatusProz/100) * BattganzeKapazWatt)

                # 0 = nicht auf WR schreiben, 1 = schon auf WR schreiben
                newPercent_schreiben = 0
                oldPercent = gen24.read_data('BatteryMaxChargePercent')

                format_aktStd = "%Y-%m-%d %H:00:00"


                #######################################
                ## Ab hier gehts los wie Ablaufdiagramm
                #######################################

                if ((BattStatusProz < MindBattLad)):
                    # volle Ladung ;-)
                    DATA = setLadewert(MaxLadung)
                    newPercent = DATA[0]
                    newPercent_schreiben = DATA[1]

                else:
                    
                    i = StartKappGrenze
                    TagesPrognoseUeberschuss = 0
                    TagesPrognoseGesamt = 0
                    # Gesamte Tagesprognose, Tagesüberschuß aus Prognose und aktuellen Ladewert ermitteln
                    # and (i >= 0) damit PrognoseAbzugswert nicht ins Minus laeuft
                    while (TagesPrognoseUeberschuss <= BattKapaWatt_akt) and (i >= 0):
                        PrognoseUNDUeberschuss = getRestTagesPrognoseUeberschuss( i, MinVerschiebewert )
                        TagesPrognoseUeberschuss = PrognoseUNDUeberschuss[0]
                        TagesPrognoseGesamt = PrognoseUNDUeberschuss[1]
                        aktuellerLadewert = PrognoseUNDUeberschuss[2]
                        Grundlast_Summe = PrognoseUNDUeberschuss[3]
                        PrognoseAbzugswert = i
                        i -= 100

                    # Nun habe ich die Werte und muss hier weiter Verzweigen
                    # Diagramm: Resttagesprognose - RestGrundlast größer (aktuelle Batteriekapazität) Aber Tagesprognose nicht 0 sonst ist abends.

                    # Wattpiloteinbindung muss noch programmiert werden
                    # Aktuell nur ueber die Configvariable  WattpilotAn steuerbar
                    if WattpilotAn == 1:
                        DATA = setLadewert(10)
                        newPercent = DATA[0]
                        newPercent_schreiben = DATA[1]

                    else:

                        if (TagesPrognoseGesamt > Grundlast) and ((TagesPrognoseGesamt - Grundlast_Summe) < BattKapaWatt_akt):
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
                    print("aktuellerLadewert: ", aktuellerLadewert)
                    print("PrognoseAbzugswert: ", PrognoseAbzugswert)
                    print("BattKapaWatt_akt: ", BattKapaWatt_akt)
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
                        print("Alte Werte sind gleich den neuen ( ",oldPercent, " == ", newPercent, " ), nichts zu schreiben!!\n")


        finally:
                if (gen24 and not auto):
                        gen24.modbus.close()
