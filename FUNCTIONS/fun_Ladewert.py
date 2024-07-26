from datetime import datetime, timedelta
import pytz
import requests
import FUNCTIONS.SymoGen24Connector
from ping3 import ping
from sys import argv
from FUNCTIONS.functions import loadConfig, loadWeatherData, loadPVReservierung, getVarConf, save_SQLite
from FUNCTIONS.fun_http import get_eigenv_opt

# Hier die Variablen aus dem Hauptprogramm übergeben und global machen
def globalfrommain(g_now, g_DEBUG_Ausgabe, g_data, g_PV_Reservierung_steuern,\
        g_reservierungdata, g_Grundlast, g_Einspeisegrenze, g_WR_Kapazitaet, g_BattKapaWatt_akt, \
        g_MaxLadung, g_BatSparFaktor, g_PrognoseAbzugswert, g_aktuelleBatteriePower, g_BattganzeLadeKapazWatt, \
        g_LadungAus, g_oldPercent):

        global now, DEBUG_Ausgabe, data, PV_Reservierung_steuern, \
        reservierungdata, Grundlast, Einspeisegrenze, WR_Kapazitaet, BattKapaWatt_akt, \
        MaxLadung, BatSparFaktor, PrognoseAbzugswert, aktuelleBatteriePower, BattganzeLadeKapazWatt, \
        LadungAus, oldPercent

        now = g_now
        DEBUG_Ausgabe = g_DEBUG_Ausgabe
        data = g_data
        PV_Reservierung_steuern = g_PV_Reservierung_steuern
        reservierungdata = g_reservierungdata
        Grundlast = g_Grundlast
        Einspeisegrenze = g_Einspeisegrenze
        WR_Kapazitaet = g_WR_Kapazitaet
        BattKapaWatt_akt = g_BattKapaWatt_akt
        MaxLadung = g_MaxLadung
        BatSparFaktor = g_BatSparFaktor
        PrognoseAbzugswert = g_PrognoseAbzugswert
        aktuelleBatteriePower = g_aktuelleBatteriePower
        BattganzeLadeKapazWatt = g_BattganzeLadeKapazWatt
        LadungAus = g_LadungAus
        oldPercent = g_oldPercent


def getPrognose(Stunde):
        if data['result']['watts'].get(Stunde):
            data_fun = data['result']['watts'][Stunde]
            # Prognose ohne Abzug der Reservierung fürs Logging
            getPrognose_Logging = data_fun
            # Prognose auf PVPower des GEN24 begrenzen
            if (WR_Kapazitaet * 1.14 < data_fun): data_fun = int(WR_Kapazitaet * 1.14 )
            # Wenn Reservierung eingeschaltet und Reservierungswert vorhanden von Prognose abziehen.
            # NUR für berechnung Ladewert, nicht fürs Logging
            if ( PV_Reservierung_steuern == 1 and reservierungdata.get(Stunde)):
                data_fun = data['result']['watts'][Stunde] - reservierungdata[Stunde]
                # Minuswerte verhindern
                if ( data_fun< 0): data_fun = 0
            getPrognose = data_fun
        else:
            getPrognose = 0
            getPrognose_Logging = 0
        return getPrognose, getPrognose_Logging

def getLadewertinGrenzen(Ladewert):
        # aktuellerLadewert zwischen 0 und MaxLadung halten
        if Ladewert < 0: Ladewert = 0
        if (Ladewert > MaxLadung): Ladewert = MaxLadung

        return Ladewert

def getRestTagesPrognoseUeberschuss(BattVollUm):

        global BatSparFaktor, DEBUG_Ausgabe
        # alle Prognosewerte zwischen aktueller Stunde und 22:00 lesen
        format_Tag = "%Y-%m-%d"
        # aktuelle Stunde und aktuelle Minute
        Akt_Std = int(datetime.strftime(now, "%H"))
        Akt_Minute = int(datetime.strftime(now, "%M"))

        # Gesamte Tagesprognose, Tagesüberschuß aus Prognose ermitteln
        # Schleife laeft von Grundlast nach oben, bis der Prognoseueberschuss die aktuelle Batteriekapazität erreicht
        i = Akt_Std
        Pro_Ertrag_Tag = 0
        Grundlast_Sum = 0
        Prognose_array = list()
        groestePrognose = 0
        Stunden_sum = 0.0001
        Zwangs_Ladung = 0
        DEBUG_Ausgabe += "\nDEBUG *************** Berechnung Abzugswert: \n"

        # in Schleife Prognosewerte bis BattVollUm durchlaufen
        while i < BattVollUm:
            Std = datetime.strftime(now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
            Prognose_arr = getPrognose(Std)
            # Prognose - Reserverung
            Prognose = Prognose_arr[0]
            # Prognose gesamt
            Prognose_all = Prognose_arr[1]
            if groestePrognose < Prognose:
                groestePrognose = Prognose
            Grundlast_fun = Grundlast
            Einspeisegrenze_fun = Einspeisegrenze
            Prognose_fun = Prognose
            Stunden_fun = 1

            # wenn nicht zur vollen Stunde, Wert anteilsmaessig
            if i == Akt_Std:
                Prognose_fun = int((Prognose / 60 * (60 - Akt_Minute)))
                Grundlast_fun = int((Grundlast / 60 * (60 - Akt_Minute)))
                Einspeisegrenze_fun = int((Einspeisegrenze / 60 * (60 - Akt_Minute)))
                Stunden_fun = (60-Akt_Minute)/60

            Prognose_array.append(Prognose)
            Pro_Ertrag_Tag += Prognose_all

            # Alles über WR_Kapazitaet bzw. Einspeisegrenze von BattKapaWatt_akt abziehen,
            # da dies nicht für die Prognoseberechnung zur Verfügung steht.
            # Prognose wird in Funktion getPrognose auf WR_Kapazitaet * 1.1 begrenzt
            Zwangs_Ladung_fun = 0
            if ( Prognose_all > WR_Kapazitaet ):
                Zwangs_Ladung_fun = Prognose_all - WR_Kapazitaet
            Zwangs_Ladung_fun2 = (Prognose_fun - Einspeisegrenze_fun - Grundlast_fun)
            if ( Zwangs_Ladung_fun2 > Zwangs_Ladung_fun): Zwangs_Ladung_fun = Zwangs_Ladung_fun2

            Zwangs_Ladung += Zwangs_Ladung_fun
            Stunden_sum += Stunden_fun
            Grundlast_Sum += Grundlast_fun

            DEBUG_Ausgabe += "DEBUG ##Schleife## Stunden_sum: " + str(round(Stunden_sum, 3)) + ", Prognose: " + str(round(Prognose,2)) + ", Pro_Ertrag_Tag: " + str(round(Pro_Ertrag_Tag,2)) + "\n"

            i += 1

        BattKapaWatt_akt_fun = BattKapaWatt_akt - Zwangs_Ladung
        if Stunden_sum < 1: Stunden_sum = 1
        AbzugsWatt = int((Pro_Ertrag_Tag - BattKapaWatt_akt_fun) / Stunden_sum)
        # WIGG
        print(">> ENTWI: Zwangs_Ladung: ", Zwangs_Ladung)
        print(">> Neuer Ladewert * 1.0: ", BattKapaWatt_akt_fun / Stunden_sum * 1.0)
        print(">> Neuer Ladewert * 0.3: ", BattKapaWatt_akt_fun / Stunden_sum * 0.3)
        aktuellerLadewert = int(BattKapaWatt_akt_fun / Stunden_sum * BatSparFaktor)
        LadewertGrund = "Prognoseberechnung"
        # WIGG

        # hier noch die Ladewerte über MaxLadung ermitteln und Überschuss von AbzugsWatt abziehen
        # damit wird bei niedrigen Prognosen mehr geladen, da bei hohen nicht über MaxLadung geladen werden kann
        Pro_Uberschuss = 0
        Schleifenzaehler = 0
        for Prognose_einzel in Prognose_array:
            if (Prognose_einzel - AbzugsWatt > MaxLadung): 
                Pro_Uberschuss += Prognose_einzel - AbzugsWatt - MaxLadung
                Schleifenzaehler += 1
        if (Pro_Uberschuss > 0 and Schleifenzaehler > 0):
            AbzugsWatt = int(AbzugsWatt - Pro_Uberschuss / Schleifenzaehler)
        if (AbzugsWatt < 0):
            AbzugsWatt = 0

        Pro_Uebersch_Tag = BattKapaWatt_akt
        DEBUG_Ausgabe += "DEBUG ##Ergebnis## AbzugsWatt: " + str(round(aktuellerLadewert, 2)) + ",  Pro_Uebersch_Tag: " + str(round(Pro_Uebersch_Tag, 2)) + ", Stunden_sum: "  + str(round(Stunden_sum, 2)) + "\n"

        return int(Pro_Uebersch_Tag), int(Pro_Ertrag_Tag), AbzugsWatt, Grundlast_Sum, groestePrognose, aktuellerLadewert, LadewertGrund

def getPrognoseLadewert():

        global DEBUG_Ausgabe
        format_Tag = "%Y-%m-%d"
        PrognoseGlaettung = 1
        Akt_Std = int(datetime.strftime(now, "%H"))
        Akt_Minute = int(datetime.strftime(now, "%M"))
        Pro_Akt = 0
        Pro_Akt_Log = 0
        i = Akt_Std - PrognoseGlaettung
        loop = 0
        while i <= Akt_Std + PrognoseGlaettung:
            Std = datetime.strftime(now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
            Prognose = getPrognose(Std)[0]
            # Prognose_Log = ohne Abzug der Reservierung
            Prognose_Log = getPrognose(Std)[1]
            Pro_Akt_fun_Log = Prognose_Log
            Pro_Akt_fun = Prognose
            DEBUG_Ausgabe += "\nDEBUG *************** Ladewertmittel LOOP: " + str(loop)
            if loop == 0:
                Pro_Akt_fun_Log = Prognose_Log * (60 - Akt_Minute) / 60
                Pro_Akt_fun = Prognose * (60 - Akt_Minute) / 60
                DEBUG_Ausgabe += "\nDEBUG ########### Pro_Akt_fun: " + str(round(Pro_Akt_fun,2)) + " REST_Akt_Minute: " + str(round(((60 - Akt_Minute) / 60),3))
            if loop == PrognoseGlaettung * 2:
                Pro_Akt_fun_Log = Prognose_Log * (Akt_Minute) / 60
                Pro_Akt_fun = Prognose * (Akt_Minute) / 60
                DEBUG_Ausgabe += "\nDEBUG ########### Pro_Akt_fun: " + str(round(Pro_Akt_fun,2)) + " Akt_Minute: " + str(round(((Akt_Minute) / 60),3))
            Pro_Akt_Log += Pro_Akt_fun_Log
            Pro_Akt += Pro_Akt_fun
            DEBUG_Ausgabe += "\nDEBUG  " + str(Std) + " Pro_Akt_fun: " + str(round(Pro_Akt_fun,2)) + " Prognose_gesamt: " + str(round(Pro_Akt,2)) + "\n"
            loop += 1
            i += 1
        Pro_Akt_Log = int(Pro_Akt_Log / PrognoseGlaettung / 2 )
        Pro_Akt = int(Pro_Akt / PrognoseGlaettung / 2 )

        DEBUG_Ausgabe += "\nDEBUG " + datetime.strftime(now, "%D %H:%M") + " Aktuelle Prognose - Reservierung: " + str(Pro_Akt) + " BatSparFaktor: " + str(BatSparFaktor)
        DEBUG_Ausgabe += ", Batteriekapazität: " + str(BattKapaWatt_akt) + ", Abzug: " + str(PrognoseAbzugswert)

        ### Prognose ENDE
        return  Pro_Akt_Log, DEBUG_Ausgabe


def getEinspeiseGrenzeLadewert(WRSchreibGrenze_nachOben, aktuellerLadewert, aktuelleEinspeisung, aktuellePVProduktion, LadewertGrund, alterLadewert, PV_Leistung_Watt):
        ### Einspeisegrenze ANFANG
        global DEBUG_Ausgabe
        # Hinweis: aktuelleBatteriePower ist beim Laden der Batterie minus
        # Wenn Einspeisung über Einspeisegrenze, dann könnte WR schon abregeln, desshalb WRSchreibGrenze_nachOben addieren
        # Durch Trägheit des WR wird vereinzelt die Einspeisung durch gleichzeitigen Netzbezug größer als die Produktion, dann nicht anwenden
        if (aktuelleEinspeisung - aktuelleBatteriePower > Einspeisegrenze) and aktuelleEinspeisung < aktuellePVProduktion:
            if (aktuelleEinspeisung - aktuelleBatteriePower - alterLadewert > Einspeisegrenze):
                EinspeisegrenzUeberschuss = int(aktuelleEinspeisung + alterLadewert - Einspeisegrenze + (WRSchreibGrenze_nachOben + 5))
            else:
                EinspeisegrenzUeberschuss = int(aktuelleEinspeisung + alterLadewert - Einspeisegrenze)

            # Damit durch die Pufferaddition nicht die maximale PV_Leistung überschritten wird
            if EinspeisegrenzUeberschuss > PV_Leistung_Watt - Einspeisegrenze:
                EinspeisegrenzUeberschuss = PV_Leistung_Watt - Einspeisegrenze

            EinspeisegrenzUeberschuss = getLadewertinGrenzen(EinspeisegrenzUeberschuss)

            if EinspeisegrenzUeberschuss > aktuellerLadewert and alterLadewert <= (MaxLadung + 100):
                DEBUG_Ausgabe += "\nDEBUG EinspeisegrenzUeberschuss: " + str(EinspeisegrenzUeberschuss) + " aktuellerLadewert: " + str(aktuellerLadewert) + " alterLadewert: " + str(alterLadewert)
                aktuellerLadewert = int(EinspeisegrenzUeberschuss)
                LadewertGrund = "PV_Leistungsüberschuss > Einspeisegrenze"

        aktuellerLadewert = getLadewertinGrenzen(aktuellerLadewert)
        ### Einspeisegrenze ENDE
        return  aktuellerLadewert, LadewertGrund, DEBUG_Ausgabe

def getAC_KapaLadewert(WRSchreibGrenze_nachOben, aktuellerLadewert, aktuellePVProduktion, LadewertGrund, alterLadewert, PV_Leistung_Watt):
        # Wenn  PV-Produktion + aktuelleBatteriePower (in Akku = minus!!)> WR_Kapazitaet (AC)
        if aktuellePVProduktion + 100 > WR_Kapazitaet + alterLadewert:
            kapazitaetsueberschuss = alterLadewert + WRSchreibGrenze_nachOben + 10
            if (WR_Kapazitaet + 100 < aktuellePVProduktion + aktuelleBatteriePower):
                aktuellerLadewert = kapazitaetsueberschuss
                LadewertGrund = "PV-Produktion > AC_Kapazitaet WR"
        # Ansonsten übergebene Werte wieder zurück
        aktuellerLadewert = getLadewertinGrenzen(aktuellerLadewert)
        return  aktuellerLadewert, LadewertGrund

def setLadewert(fun_Ladewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten):
        fun_Ladewert = getLadewertinGrenzen(fun_Ladewert)

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

def getSonnenuntergang(PV_Leistung_Watt):
    i = 0
    Sonnenuntergang = 25
    while i < 24:
        Std_morgen = datetime.strftime(now + timedelta(hours=i), "%Y-%m-%d %H:00:00")
        Std_morgen_only = int(datetime.strftime(now + timedelta(hours=i), "%H"))
        Prognose = getPrognose(Std_morgen)[0]
        if Std_morgen_only > 14 and Prognose <= PV_Leistung_Watt / 100:
            if Std_morgen_only < Sonnenuntergang:
                Sonnenuntergang = Std_morgen_only
        i  += 1
    return(Sonnenuntergang)
    
def getPrognoseMorgen(MaxEinspeisung=0):
    i = 0
    Prognose_Summe = 0
    Ende_Nacht_Std = 0
    while i < 24:
        # ab aktueller Stunde die nächsten 24 Stunden aufaddieren, da ab 24 Uhr sonst keine Morgenprognose
        Std_morgen = datetime.strftime(now + timedelta(hours=i), "%Y-%m-%d %H:00:00")
        Prognose_Summe += getPrognose(Std_morgen)[0]
        # Wenn Prognosesumme > 50W, dann beginnt die Produktion am nächsten TAG,
        # da erst Abends gestartet wird (Produktion < 10W)
        if Prognose_Summe > MaxEinspeisung and Ende_Nacht_Std == 0:
            Ende_Nacht_Std = Std_morgen
        i  += 1
    return(Prognose_Summe, Ende_Nacht_Std)
    
def getParameter(argv):
    Parameter = ""
    Meldung = ""
    if len(argv) > 1 :
        Parameter = argv[1]
    # Prog_Steuerung.json lesen
    Prog_Steuer_code_tmp = loadPVReservierung('Prog_Steuerung.json')
    Prog_Steuer_code = int(Prog_Steuer_code_tmp['Steuerung'])
    # print("Prog_Steuer_code: ", Prog_Steuer_code)
    if Prog_Steuer_code == 1:
        Meldung = "AUS"
        Parameter = 'exit'
    if Prog_Steuer_code == 2:
        Meldung = "Analyse in Crontab.log"
        Parameter = 'analyse'
    if Prog_Steuer_code == 3:
        Meldung = "NUR Logging"
        Parameter = 'logging'
    if Prog_Steuer_code == 4:
        Meldung = "WR-Steuerung und Logging"
        Parameter = 'schreiben'
    return(Parameter, Meldung)

def getEigenverbrauchOpt(host_ip, user, password, BattStatusProz, BattganzeKapazWatt, MaxEinspeisung=0):
    DEBUG_Eig_opt ="\n\nDEBUG <<<<<<<< Eigenverbrauchs-Optimierung  >>>>>>>>>>>>>\n"
    GrundlastNacht = getVarConf('EigenverbOptimum','GrundlastNacht','eval')
    AkkuZielProz = getVarConf('EigenverbOptimum','AkkuZielProz','eval')
    PrognoseGrenzeMorgen = getVarConf('EigenverbOptimum','PrognoseGrenzeMorgen','eval')
    PrognoseMorgen_arr = getPrognoseMorgen(MaxEinspeisung)
    PrognoseMorgen = PrognoseMorgen_arr[0]/1000
    Ende_Nacht_Std = PrognoseMorgen_arr[1]
    Eigen_Opt_Std_arry = get_eigenv_opt(host_ip, user, password)
    Eigen_Opt_Std = Eigen_Opt_Std_arry[0]

    if Ende_Nacht_Std == 0 : Ende_Nacht_Std = datetime.strftime(now, "%Y-%m-%d %H:%M:%S")
    Dauer_Nacht = (datetime.strptime(Ende_Nacht_Std, '%Y-%m-%d %H:%M:%S') - (now  - timedelta(hours=1)))
    Dauer_Nacht_Std = Dauer_Nacht.total_seconds()/3600
    if Dauer_Nacht_Std <= 0: Dauer_Nacht_Std = 1 # sonst Divison durch Null 
    Akku_Rest_Watt = ((BattStatusProz - AkkuZielProz) * BattganzeKapazWatt/100) - (Dauer_Nacht_Std * GrundlastNacht)
    Eigen_Opt_Std_neu = int(Akku_Rest_Watt/Dauer_Nacht_Std)
    # Schaltverzögerung (hysterese) 
    if abs(Eigen_Opt_Std) < Eigen_Opt_Std_neu: Eigen_Opt_Std_neu -= 50
    # Eigen_Opt_Std_neu auf 100 runden
    Eigen_Opt_Std_neu = int(round(Eigen_Opt_Std_neu, -2))
    if Akku_Rest_Watt < 0: Eigen_Opt_Std_neu = 0
    DEBUG_Eig_opt += "DEBUG ## Dauer_Nacht_Std: " + str(round(Dauer_Nacht_Std, 2)) + ", Akku_Rest_Watt: " + str(int(Akku_Rest_Watt)) +  \
                "\nDEBUG ## Eigen_Opt_genau: " + str(int(Akku_Rest_Watt/Dauer_Nacht_Std)) + ", Eigen_Opt_Std_neu: " + str(Eigen_Opt_Std_neu) + "\n"
    # Hier auf MaxEinspeisung begrenzen.
    if Eigen_Opt_Std_neu > MaxEinspeisung : Eigen_Opt_Std_neu = MaxEinspeisung
    # PrognoseGrenzeMorgen pruefen
    if (PrognoseMorgen < PrognoseGrenzeMorgen and PrognoseMorgen != 0):
        Eigen_Opt_Std_neu = 0
    # In der letzten Stunde vor dem Morgengrauen und wenn AkkuZielProz nicht unterschritten, Eigen_Opt_Std für Tag stellen
    if Dauer_Nacht_Std < 2:
        # Die aktuelle Einspeisung nicht mehr verändern
        Eigen_Opt_Std_neu = Eigen_Opt_Std
        if BattStatusProz > AkkuZielProz:
            if (PrognoseMorgen < PrognoseGrenzeMorgen):
                DEBUG_Eig_opt += "DEBUG ## >>> Bei PrognoseMorgen < PrognoseGrenzeMorgen halbe MaxEinspeisung während des Tages"
                DEBUG_Eig_opt += "\nDEBUG ## >>> PrognoseMorgen: " + str(PrognoseMorgen) + ", PrognoseGrenzeMorgen: " + str(PrognoseGrenzeMorgen) 
                Eigen_Opt_Std_neu = (MaxEinspeisung)/2
            if (PrognoseMorgen < PrognoseGrenzeMorgen/2):
                DEBUG_Eig_opt += "DEBUG ## >>> Bei PrognoseMorgen < Hälfte von PrognoseGrenzeMorgen, keine Einspeisung während des Tages"
                DEBUG_Eig_opt += "\nDEBUG ## >>> PrognoseMorgen: " + str(PrognoseMorgen) + ", PrognoseGrenzeMorgen: " + str(PrognoseGrenzeMorgen) 
                Eigen_Opt_Std_neu = 0
            if (PrognoseMorgen >= PrognoseGrenzeMorgen):
                DEBUG_Eig_opt += "DEBUG ## >>> Bei PrognoseMorgen > PrognoseGrenzeMorgen MaxEinspeisung während des Tages"
                DEBUG_Eig_opt += "\nDEBUG ## >>> PrognoseMorgen: " + str(PrognoseMorgen) + ", PrognoseGrenzeMorgen: " + str(PrognoseGrenzeMorgen) 
                Eigen_Opt_Std_neu = MaxEinspeisung 
        else:
            if (PrognoseMorgen < PrognoseGrenzeMorgen/2):
                DEBUG_Eig_opt += "DEBUG ## >>> Bei PrognoseMorgen < Hälfte von PrognoseGrenzeMorgen, keine Einspeisung während des Tages"
                DEBUG_Eig_opt += "\nDEBUG ## >>> PrognoseMorgen: " + str(PrognoseMorgen) + ", PrognoseGrenzeMorgen: " + str(PrognoseGrenzeMorgen) 
                Eigen_Opt_Std_neu = 0
            else:
                Eigen_Opt_Std_neu = 50
                DEBUG_Eig_opt += "DEBUG ## >>> BattStatusProz: " + str(BattStatusProz) + ", ist kleiner als AkkuZielProz: " + str(AkkuZielProz) 

    # Wenn Eigen_Opt_Std_arry[1] = 0, Eigenverbrauchs-Optimierung = Automatisch = 0
    if Eigen_Opt_Std_arry[1] == 0: Eigen_Opt_Std = 0

    # Einspeisung muss immer Minus sein!!
    Eigen_Opt_Std_neu = abs(Eigen_Opt_Std_neu) * -1

    return PrognoseMorgen, Eigen_Opt_Std, Eigen_Opt_Std_neu, Dauer_Nacht_Std, AkkuZielProz, DEBUG_Eig_opt

