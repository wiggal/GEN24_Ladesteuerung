from datetime import datetime, timedelta
import pytz
import requests
import SymoGen24Connector
from ping3 import ping
from sys import argv
from functions import loadConfig, loadWeatherData, loadPVReservierung, getVarConf, save_SQLite

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
        Pro_Uebersch_vorher = 0
        DEBUG_Ausgabe_Schleife = "\nDEBUG <<<<<< Meldungen aus Schleife >>>>>>>\n"
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

            if Pro_Uebersch < 0:
                Pro_Uebersch = 0

            if Pro_Uebersch > MaxLadung:
                Pro_Uebersch = MaxLadung

            Pro_Uebersch_org = int(Pro_Uebersch)
            # Wenn Prognose höher und nicht über WRSchreibGrenze_nachOben alte Prognose belassen
            if (Pro_Uebersch > Pro_Uebersch_vorher) and (Pro_Uebersch < Pro_Uebersch_vorher + WRSchreibGrenze_nachOben):
                Pro_Uebersch = Pro_Uebersch_vorher
            # Wenn Prognose niedriger und nicht unter WRSchreibGrenze_nachUnten alte Prognose belassen
            if (Pro_Uebersch < Pro_Uebersch_vorher) and (Pro_Uebersch > Pro_Uebersch_vorher - WRSchreibGrenze_nachUnten):
                Pro_Uebersch = Pro_Uebersch_vorher
                # Wenn nicht mehr genügend überschuss vorhanden ist
                if Pro_Uebersch > (Prognose - Grundlast):
                    Pro_Uebersch = (Prognose - Grundlast)

            Pro_Uebersch_vorher = Pro_Uebersch
            DEBUG_Ausgabe_Schleife += "## Std., Prognose, Pro_Uebersch_org, Pro_Uebersch " + str(i) + " " + str(int(Prognose)) + " " + str(int(Pro_Uebersch_org)) + " " + str(int(Pro_Uebersch)) +"\n"

            if Pro_Uebersch_voll > MaxLadung:
                Pro_Uebersch_voll = MaxLadung

            if Pro_Uebersch > 0:
                Pro_Uebersch_Tag += Pro_Uebersch

            if Pro_Uebersch_voll > 0:
                Pro_Uebersch_Tag_voll += Pro_Uebersch_voll

            i  += 1


        # Hier noch den aktuellen Ladewert der Schleife ermitteln und im return mitgeben
        # Prognose nur bis BattVollUm berechnen
        LadewertStd = datetime.strftime(now, format_aktStd)
        LadewertStd_naechste = datetime.strftime(now + timedelta(minutes = (60)), format_aktStd)
        Pro_Akt1 = (getPrognose(LadewertStd))
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
        if aktuelleEinspeisung > Einspeisegrenze:
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


        return int(Pro_Uebersch_Tag), int(Pro_Ertrag_Tag), aktuellerLadewert, Grundlast_Sum, Pro_Akt, LadewertGrund, int(Pro_Uebersch_Tag_voll), DEBUG_Ausgabe_Schleife

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

def getPrognoseMorgen():
    i = 0
    Prognose_Summe = 0
    while i < 24:
        Std_morgen = datetime.strftime(now + timedelta(days=1), "%Y-%m-%d")+" "+ str('%0.2d' %(i)) +":00:00"
        Prognose_Summe += getPrognose(Std_morgen)
        i  += 1
    return(Prognose_Summe)
    

if __name__ == '__main__':
        config = loadConfig('config.ini')
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"

        host_ip = getVarConf('gen24','hostNameOrIp', 'str')
        host_port = getVarConf('gen24','port', 'str')
        if ping(host_ip):
            # Nur ausführen, wenn WR erreichbar
            gen24 = None
            auto = False
            try:            
                    newPercent = None
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< E I N >>>>>>>\n"
    
                    ###############################
    
                    weatherfile = getVarConf('env','filePathWeatherData','str')
                    data = loadWeatherData(weatherfile)

                    gen24 = SymoGen24Connector.SymoGen24(host_ip, host_port, auto)

                    if gen24.read_data('Battery_Status') == 1:
                        print(datetime.now())
                        print("Batterie ist Offline keine Steuerung möglich!!! ")
                        print()
                        exit()
    
                    # Benoetigte Variablen aus config.ini definieren und auf Zahlen prüfen
                    print_level = getVarConf('Ladeberechnung','print_level','eval')
                    BattVollUm = getVarConf('Ladeberechnung','BattVollUm','eval')
                    BatSparFaktor = getVarConf('Ladeberechnung','BatSparFaktor','eval')
                    MaxLadung = getVarConf('Ladeberechnung','MaxLadung','eval')
                    LadungAus = getVarConf('Ladeberechnung','LadungAus','eval')
                    Einspeisegrenze = getVarConf('Ladeberechnung','Einspeisegrenze','eval')
                    WR_Kapazitaet = getVarConf('Ladeberechnung','WR_Kapazitaet','eval')
                    PV_Leistung_Watt = getVarConf('Ladeberechnung','PV_Leistung_Watt','eval')
                    Grundlast = getVarConf('Ladeberechnung','Grundlast','eval')
                    MindBattLad = getVarConf('Ladeberechnung','MindBattLad','eval')
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
                    EntlageGrenze_steuern = getVarConf('Entladung','EntlageGrenze_steuern','eval')
                                       
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
                    BattganzeLadeKapazWatt = (gen24.read_data('BatteryChargeRate')) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattganzeKapazWatt = (gen24.read_data('Battery_capa')) + 1  # +1 damit keine Divison duch Null entstehen kann
                    BattStatusProz = gen24.read_data('Battery_SoC')/100
                    BattKapaWatt_akt = int((1 - BattStatusProz/100) * BattganzeKapazWatt)
                    aktuelleEinspeisung = int(gen24.get_meter_power() * -1)
                    aktuellePVProduktion = int(gen24.get_mppt_power())
                    aktuelleBatteriePower = int(gen24.get_batterie_power())
                    BatteryMaxDischargePercent = int(gen24.read_data('BatteryMaxDischargePercent')/100) 
                    GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower

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
                        WRSchreibGrenze_nachUnten = int(WRSchreibGrenze_nachUnten * (1 + ( BattStatusProz - 90 ) / 5))
                        DEBUG_Ausgabe += "## Batt >90% ## WRSchreibGrenze_nachUnten: " + str(WRSchreibGrenze_nachUnten) +"\n"
                        WRSchreibGrenze_nachOben = int(WRSchreibGrenze_nachOben * (1 + ( BattStatusProz - 90 ) / 5))
                        DEBUG_Ausgabe += "## Batt >90% ## WRSchreibGrenze_nachOben: " + str(WRSchreibGrenze_nachOben) +"\n"

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
                    DEBUG_Ausgabe += PrognoseUNDUeberschuss[7]
                    DEBUG_Ausgabe += "\n"
                    DEBUG_Ausgabe += "TagesPrognoseUeberschuss: " + str(TagesPrognoseUeberschuss)
                    DEBUG_Ausgabe += ", TagesPrognoseUeberschuss_voll: " + str(TagesPrognoseUeberschuss_voll)
                    DEBUG_Ausgabe += ", aktuellerLadewert: " + str(aktuellerLadewert) + "\n"

                    # BatterieLuecke prozentual verteilen, 
                    # Wenn PrognoseAbzugswert == Grundlast, oder aktuellerLadewert > 0
                    BatterieLuecke = BattKapaWatt_akt - TagesPrognoseUeberschuss
                    if (aktuellerLadewert > 0 ) or (PrognoseAbzugswert <= Grundlast):
                        aktuellerLadewert = int(aktuellerLadewert + (BatterieLuecke /(BattVollUm-(int(datetime.strftime(now, "%H"))+int(datetime.strftime(now, "%M"))/60)+0.001)))
                    # Ladeleistung auf MaxLadung begrenzen
                    if (aktuellerLadewert > MaxLadung):
                        aktuellerLadewert = MaxLadung
                    DEBUG_Ausgabe += datetime.strftime(now, "%D %H:%M") + " ( " + str(BatSparFaktor) + ") Prognoseladewert: " + str(aktuellerLadewert)
                    DEBUG_Ausgabe += ", Batteriekapazität: " + str(BattKapaWatt_akt) + ", BatterieLuecke: " + str(BatterieLuecke) + ", Abzug: " + str(PrognoseAbzugswert) + "\n"
    
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
                            print("GesamtverbrauchHaus/Watt:   ", GesamtverbrauchHaus)
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
                    if  EntlageGrenze_steuern == 1:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENTLADEBEGRENZUNG >>>>>>>>>>>>>"

                        MaxEntladung = 100
                        ProgGrenzeMorgen = getVarConf('Entladung','ProgGrenzeMorgen','eval')
                        EntlageGrenze_Min = getVarConf('Entladung','EntlageGrenze_Min','eval')
                        EntlageGrenze_Max = getVarConf('Entladung','EntlageGrenze_Max','eval')
                        PrognoseMorgen = getPrognoseMorgen()/1000
                        Battery_MinRsvPct = int(gen24.read_data('Battery_MinRsvPct')/100)
                        Neu_Battery_MinRsvPct = EntlageGrenze_Min
                        if (PrognoseMorgen < ProgGrenzeMorgen and PrognoseMorgen != 0):
                            Neu_Battery_MinRsvPct = EntlageGrenze_Max
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

                    ### LOGGING, Schreibt mit den übergebenen Daten eine CSV- oder SQlite-Datei
                    ## nur wenn "schreiben" übergeben worden ist
                    Logging_ein = getVarConf('Logging','Logging_ein','eval')
                    if Logging_ein == 1:
                        Logging_Schreib_Ausgabe = ""
                        if len(argv) > 1 and (argv[1] == "schreiben" or argv[1] == "logging"):
                            Logging_file = getVarConf('Logging','Logging_file','str')
                            API_Werte = gen24.get_API()
                            # In die DB werden die liftime Verbrauchszählerstände gespeichert
                            save_SQLite(Logging_file, API_Werte['AC_Produktion'], API_Werte['DC_Produktion'], API_Werte['Netzverbrauch'], API_Werte['Einspeisung'], API_Werte['Batterie_IN'], API_Werte['Batterie_OUT'], aktuelleVorhersage, BattStatusProz)
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

