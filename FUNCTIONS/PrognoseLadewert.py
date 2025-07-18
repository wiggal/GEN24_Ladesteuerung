from datetime import datetime, timedelta
import json
import FUNCTIONS.functions
import FUNCTIONS.httprequest

basics = FUNCTIONS.functions.basics()
request = FUNCTIONS.httprequest.request()
    
class progladewert:
    def __init__(self, data, WR_Kapazitaet, reservierungdata, MaxLadung, Einspeisegrenze, aktuelleBatteriePower):
        self.now = datetime.now()
        self.data = data
        self.WR_Kapazitaet = WR_Kapazitaet
        self.reservierungdata = reservierungdata
        self.MaxLadung = MaxLadung
        self.Einspeisegrenze = Einspeisegrenze
        self.aktuelleBatteriePower = aktuelleBatteriePower

        self.DEBUG_Ausgabe = ''

    def getPrognose(self, Stunde):
            if self.data['result']['watts'].get(Stunde):
                data_fun = self.data['result']['watts'][Stunde]
                # Prognose ohne Abzug der Reservierung fürs Logging
                getPrognose_Logging = data_fun
                # Prognose auf PVPower des GEN24 begrenzen
                if (self.WR_Kapazitaet * 1.14 < data_fun): data_fun = int(self.WR_Kapazitaet * 1.14 )
                # Wenn Reservierung eingeschaltet und Reservierungswert vorhanden von Prognose abziehen.
                # NUR für berechnung Ladewert, nicht fürs Logging
                if (self.reservierungdata.get(Stunde)):
                    data_fun = self.data['result']['watts'][Stunde] - self.reservierungdata[Stunde]
                    # Minuswerte verhindern
                    if ( data_fun< 0): data_fun = 0
                getPrognose = data_fun
            else:
                getPrognose = 0
                getPrognose_Logging = 0
            return getPrognose, getPrognose_Logging
    
    def getLadewertinGrenzen(self, Ladewert):
            # aktuellerLadewert zwischen 0 und MaxLadung halten
            if Ladewert < 0: Ladewert = 0
            if (Ladewert > self.MaxLadung): Ladewert = self.MaxLadung
    
            return Ladewert
    
    from datetime import datetime

    def get_FesteEntladegrenze(self, FesteEntladegrenze_string):
        values = FesteEntladegrenze_string.split(";")
        num_values = len(values)
        # Aktuelle Minute innerhalb der Stunde (0-59)
        current_minute = datetime.now().minute
        # Intervallgröße in Minuten
        interval_size = 60 / num_values
        # Index berechnen (z.B. bei 4 Werten: 0 für 0-14 Min, 1 für 15-29 Min, usw.)
        index = int(current_minute // interval_size)
        # Entsprechenden Wert zurückgeben
        self.DEBUG_Ausgabe += "\nDEBUG FesteEntladegrenze index " + str(index) + " = " + str(values[index])
        return int(values[index]), self.DEBUG_Ausgabe

    def getLadewert(self, BattVollUm, Grundlast, alterLadewert, BattKapaWatt_akt):
    
            # alle Prognosewerte zwischen aktueller Stunde und 22:00 lesen
            format_Tag = "%Y-%m-%d"
            # aktuelle Stunde und aktuelle Minute
            Akt_Std = int(datetime.strftime(self.now, "%H"))
            Akt_Minute = int(datetime.strftime(self.now, "%M"))
    
            # Gesamte Tagesprognose, Tagesüberschuß aus Prognose ermitteln
            i = Akt_Std
            Pro_Ertrag_Tag = 0
            Grundlast_Sum = 0
            groestePrognose = 0
            Stunden_sum = 0.0001
            Zwangs_Ladung = 0
            Progn_ueber_aktuell = 0
            Progn_aktuell = 0
            self.DEBUG_Ausgabe += "\nDEBUG *************** Berechnung Abzugswert: \n"
    
            # in Schleife Prognosewerte bis BattVollUm durchlaufen
            while i < BattVollUm:
                Std = datetime.strftime(self.now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
                Prognose_arr = self.getPrognose(Std)
                # Prognose - Reserverung
                Prognose = Prognose_arr[0]
                # Prognose gesamt
                Prognose_all = Prognose_arr[1]
                Grundlast_fun = Grundlast
                Einspeisegrenze_fun = self.Einspeisegrenze
                Prognose_fun = Prognose
                BattKapaWatt_akt_fun = BattKapaWatt_akt
                Stunden_fun = 1
    
                # wenn nicht zur vollen Stunde, Wert anteilsmaessig
                if i == Akt_Std:
                    Prognose_fun = int((Prognose / 60 * (60 - Akt_Minute)))
                    Grundlast_fun = int((Grundlast / 60 * (60 - Akt_Minute)))
                    Einspeisegrenze_fun = int((self.Einspeisegrenze / 60 * (60 - Akt_Minute)))
                    Stunden_fun = (60-Akt_Minute)/60
                    Progn_aktuell = Prognose
    
                Pro_Ertrag_Tag += Prognose_fun
                # Groesste Prognose ermitteln
                if groestePrognose < Prognose_fun:
                    groestePrognose = Prognose_fun
    
                # Alles über WR_Kapazitaet bzw. Einspeisegrenze von BattKapaWatt_akt abziehen,
                # da dies nicht für die Prognoseberechnung zur Verfügung steht.
                # Prognose wird in Funktion getPrognose auf WR_Kapazitaet * 1.1 begrenzt
                Zwangs_Ladung_fun = 0
                if ( Prognose > self.WR_Kapazitaet ):
                    Zwangs_Ladung_fun = Prognose - self.WR_Kapazitaet
                Zwangs_Ladung_fun2 = (Prognose - self.Einspeisegrenze - Grundlast)
                if ( Zwangs_Ladung_fun2 > Zwangs_Ladung_fun): Zwangs_Ladung_fun = Zwangs_Ladung_fun2

                # Alles über aktueller Prognose aufsummieren für Ladung durch Prognosekappung
                if ( Prognose > Progn_aktuell ):
                    Progn_ueber_aktuell += Prognose - Progn_aktuell
    
                Zwangs_Ladung += Zwangs_Ladung_fun
                Stunden_sum += Stunden_fun
                Grundlast_Sum += Grundlast_fun
    
                self.DEBUG_Ausgabe += "DEBUG ##Schleife## Stunden_sum: " + str(round(Stunden_sum, 3)) + ", Prognose: " + str(round(Prognose,2)) + ", Pro_Ertrag_Tag: " + str(round(Pro_Ertrag_Tag,2)) + "\n"
    
                i += 1
    
            Std = datetime.strftime(self.now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
            Prognose_Std_nach_BattVollUm = self.getPrognose(Std)
            BattKapaWatt_akt_fun = BattKapaWatt_akt - Zwangs_Ladung
            BatSparFaktor = basics.getVarConf('Ladeberechnung','BatSparFaktor','eval')

            # Wenn BatSparFaktor <= 0 Ladeberechnung durch Prognosekappung
            if (BatSparFaktor <= 0):
                self.DEBUG_Ausgabe += "DEBUG >>>>>>>>>Prognosekappung >> Progn_aktuell, Progn_ueber_aktuell: " + str(Progn_aktuell) + " " + str(Progn_ueber_aktuell) + "\n"
                if (Progn_ueber_aktuell > BattKapaWatt_akt):
                    aktuellerLadewert = 0
                else:
                    aktuellerLadewert = (BattKapaWatt_akt - Progn_ueber_aktuell)/Stunden_sum

                LadewertGrund = "Prognoseberechnung Prognosekappung"

            # Wenn BatSparFaktor > 0 Ladeberechnung durch BatSparFaktor
            else:
                if (BattKapaWatt_akt_fun < 0): BattKapaWatt_akt_fun = 0
                if Stunden_sum < 0.1: Stunden_sum = 0.1
    
                # Wenn Ladewert ohne BatSparFaktor größer MaxLadung = MaxLadung, damit der Akku auch voll wird
                aktuellerLadewert_1 = int(BattKapaWatt_akt_fun / Stunden_sum)
                if(aktuellerLadewert_1 > self.MaxLadung):
                    aktuellerLadewert = self.MaxLadung
                else:
                    aktuellerLadewert = int(aktuellerLadewert_1 * BatSparFaktor)
                LadewertGrund = "Prognoseberechnung BatSparFaktor"

                # Um morgens auf Null zu stellen
                org_WRSchreibGrenze_nachOben = basics.getVarConf('Ladeberechnung','WRSchreibGrenze_nachOben','eval')
                if (aktuellerLadewert < org_WRSchreibGrenze_nachOben*0.7 and BatSparFaktor < 1):
                    LadewertGrund = "Ladewert " + str(aktuellerLadewert) + " < Grenze_nachOben * 0.7"
                    aktuellerLadewert = 0
    
            # Prüfungen auf Grenzwerte für beide Berechnungsmethoden
            # Wenn größter Prognosewert je Stunde ist kleiner als GrenzwertGroestePrognose volle Ladung
            aktuellerLadewert = self.getLadewertinGrenzen(aktuellerLadewert)
            GrenzwertGroestePrognose = basics.getVarConf('Ladeberechnung','GrenzwertGroestePrognose','eval')
            if GrenzwertGroestePrognose > groestePrognose:
                aktuellerLadewert = self.MaxLadung
                LadewertGrund = "Größter Prognosewert " + str(groestePrognose) + " ist kleiner als GrenzwertGroestePrognose " + str(GrenzwertGroestePrognose)

            # Hier noch pruefen ob gesamte Prognose minus Grundlastsumme noch für Akkuladung reicht.
            # Schaltverzögerung (Hysterse)
            if (alterLadewert == self.MaxLadung):
                Pro_Ertrag_Tag_tmp = Pro_Ertrag_Tag * 0.7
            else:
                Pro_Ertrag_Tag_tmp = Pro_Ertrag_Tag + Prognose_Std_nach_BattVollUm[0]
            if((Pro_Ertrag_Tag_tmp - Grundlast_Sum) < BattKapaWatt_akt):
                aktuellerLadewert = self.MaxLadung
                LadewertGrund = "TagesPrognose - Grundlast_Summe < aktuelleBattKapazität"
    
            return int(Pro_Ertrag_Tag), Grundlast_Sum, aktuellerLadewert, LadewertGrund
    
    def getAktPrognose(self, BattKapaWatt_akt):
    
            format_Tag = "%Y-%m-%d"
            PrognoseGlaettung = 1
            Akt_Std = int(datetime.strftime(self.now, "%H"))
            Akt_Minute = int(datetime.strftime(self.now, "%M"))
            Pro_Akt = 0
            Pro_Akt_Log = 0
            i = Akt_Std - PrognoseGlaettung
            loop = 0
            while i <= Akt_Std + PrognoseGlaettung:
                Std = datetime.strftime(self.now, format_Tag)+" "+ str('%0.2d' %(i)) +":00:00"
                Prognose_tmp = self.getPrognose(Std)
                Prognose = Prognose_tmp[0]
                # Prognose_Log = ohne Abzug der Reservierung
                Prognose_Log = Prognose_tmp[1]
                Pro_Akt_fun_Log = Prognose_Log
                Pro_Akt_fun = Prognose
                self.DEBUG_Ausgabe += "DEBUG\nDEBUG *************** Ladewertmittel LOOP: " + str(loop)
                if loop == 0:
                    Pro_Akt_fun_Log = Prognose_Log * (60 - Akt_Minute) / 60
                    Pro_Akt_fun = Prognose * (60 - Akt_Minute) / 60
                    self.DEBUG_Ausgabe += "\nDEBUG ########### Pro_Akt_fun: " + str(round(Pro_Akt_fun,2)) + " REST_Akt_Minute: " + str(round(((60 - Akt_Minute) / 60),3))
                if loop == PrognoseGlaettung * 2:
                    Pro_Akt_fun_Log = Prognose_Log * (Akt_Minute) / 60
                    Pro_Akt_fun = Prognose * (Akt_Minute) / 60
                    self.DEBUG_Ausgabe += "\nDEBUG ########### Pro_Akt_fun: " + str(round(Pro_Akt_fun,2)) + " Akt_Minute: " + str(round(((Akt_Minute) / 60),3))
                Pro_Akt_Log += Pro_Akt_fun_Log
                Pro_Akt += Pro_Akt_fun
                self.DEBUG_Ausgabe += "\nDEBUG  " + str(Std) + " Pro_Akt_fun: " + str(round(Pro_Akt_fun,2)) + " Prognose_gesamt: " + str(round(Pro_Akt,2)) + "\n"
                loop += 1
                i += 1
            Pro_Akt_Log = int(Pro_Akt_Log / PrognoseGlaettung / 2 )
            Pro_Akt = int(Pro_Akt / PrognoseGlaettung / 2 )
    
            self.DEBUG_Ausgabe += "DEBUG\nDEBUG AktPrognose-Reservierung: " + str(Pro_Akt)
            self.DEBUG_Ausgabe += ", Batteriekapazität: " + str(BattKapaWatt_akt) 
    
            ### Prognose ENDE
            return  Pro_Akt_Log, self.DEBUG_Ausgabe
    
    
    def setLadewert(self, fun_Ladewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, alterLadewert):
            # Wegen ManuelleSteuerung nicht begrenzen auf MaxLadewert
            #fun_Ladewert = self.getLadewertinGrenzen(fun_Ladewert)
    
            # Schaltvezögerung
            # mit altem Ladewert vergleichen
            diffLadewert_nachOben = int(fun_Ladewert - alterLadewert)
            diffLadewert_nachUnten = int(alterLadewert - fun_Ladewert)
    
            # Wenn die Differenz in hundertstel Prozent kleiner als die Schreibgrenze nix schreiben
            ladewert_schreiben = 0
            if ( diffLadewert_nachOben > WRSchreibGrenze_nachOben ):
                ladewert_schreiben = 1
            if ( diffLadewert_nachUnten > WRSchreibGrenze_nachUnten ):
                ladewert_schreiben = 1
    
            # Wenn MaxLadung erstmals erreicht ist immer schreiben
            if (fun_Ladewert == self.MaxLadung) and (abs(diffLadewert_nachOben) > 3):
                ladewert_schreiben = 1
    
            return(ladewert_schreiben)
    
    def getSonnenuntergang(self, PV_Leistung_Watt):
        i = 0
        Sonnenuntergang = 25
        while i < 24:
            Std_morgen = datetime.strftime(self.now + timedelta(hours=i), "%Y-%m-%d %H:00:00")
            Std_morgen_only = int(datetime.strftime(self.now + timedelta(hours=i), "%H"))
            Prognose = self.getPrognose(Std_morgen)[0]
            if Std_morgen_only > 14 and Prognose <= PV_Leistung_Watt / 50:
                if Std_morgen_only < Sonnenuntergang:
                    Sonnenuntergang = Std_morgen_only
            i  += 1
        return(Sonnenuntergang)
        
    def getPrognoseMorgen(self, MaxEinspeisung=0, i=0):
        Prognose_Summe = 0
        Ende_Nacht_Std = 0
        Stunde_bis = 24+i
        while i < Stunde_bis:
            # ab aktueller Stunde die nächsten 24 Stunden aufaddieren, da ab 24 Uhr sonst keine Morgenprognose
            Std_morgen = datetime.strftime(self.now + timedelta(hours=i), "%Y-%m-%d %H:00:00")
            akt_Std_Ende_Nacht = datetime.strftime(self.now + timedelta(hours=i-1), "%Y-%m-%d %H:00:00")
            Prognose_Summe += self.getPrognose(Std_morgen)[0]
            # Wenn Prognosesumme > 50W, dann beginnt die Produktion am nächsten TAG,
            # da erst Abends gestartet wird (Produktion < 10W)
            if Prognose_Summe > MaxEinspeisung and Ende_Nacht_Std == 0:
                Ende_Nacht_Std = akt_Std_Ende_Nacht
            i  += 1
        return(Prognose_Summe, Ende_Nacht_Std)
        
    def getEigenverbrauchOpt(self, host_ip, user, password, BattStatusProz, BattganzeKapazWatt, EigenverbOpt_steuern, MaxEinspeisung=0):
        DEBUG_Eig_opt ="\nDEBUG\nDEBUG <<<<<<<< Eigenverbrauchs-Optimierung  >>>>>>>>>>>>>"
        GrundlastNacht = basics.getVarConf('EigenverbOptimum','GrundlastNacht','eval')
        AkkuZielProz = basics.getVarConf('EigenverbOptimum','AkkuZielProz','eval')
        RundungEinspeisewert = basics.getVarConf('EigenverbOptimum','RundungEinspeisewert','eval')
        PrognoseGrenzeMorgen = basics.getVarConf('EigenverbOptimum','PrognoseGrenzeMorgen','eval')
        PrognoseMorgen_arr = self.getPrognoseMorgen(MaxEinspeisung)
        PrognoseMorgen = PrognoseMorgen_arr[0]/1000
        Ende_Nacht_Std = PrognoseMorgen_arr[1]
        Eigen_Opt_Std_arry = request.get_batteries(host_ip, user, password)
        Eigen_Opt_Std = Eigen_Opt_Std_arry[0]
        Eigen_Opt_auto = Eigen_Opt_Std_arry[1]
        Backup_Reserve = Eigen_Opt_Std_arry[2]
    
        if Ende_Nacht_Std == 0 : Ende_Nacht_Std = datetime.strftime(self.now, "%Y-%m-%d %H:%M:%S")
        Dauer_Nacht = (datetime.strptime(Ende_Nacht_Std, '%Y-%m-%d %H:%M:%S') - (self.now  - timedelta(hours=1)))
        Dauer_Nacht_Std = Dauer_Nacht.total_seconds()/3600
        if Dauer_Nacht_Std == 0: Dauer_Nacht_Std = 0.01 # sonst Divison durch Null 
        # fast eine Stunde weniger, da dann schon Nacht vorbei ist
        Akku_Rest_Watt = ((BattStatusProz - AkkuZielProz) * BattganzeKapazWatt/100) - ((Dauer_Nacht_Std - 0.8) * GrundlastNacht)
        Eigen_Opt_Std_neu = int(Akku_Rest_Watt/(Dauer_Nacht_Std - 0.8))
        if(Dauer_Nacht_Std < 1.8): Eigen_Opt_Std_neu = int(Akku_Rest_Watt)
        # Schaltverzögerung (hysterese)
        if (abs(Eigen_Opt_Std) < Eigen_Opt_Std_neu): 
            #Eigen_Opt_Std_neu = int(Eigen_Opt_Std_neu * 0.8)
            Eigen_Opt_Std_neu = int(Eigen_Opt_Std_neu - RundungEinspeisewert/2)
        if (abs(Eigen_Opt_Std) > Eigen_Opt_Std_neu): 
            Eigen_Opt_Std_neu = int(Eigen_Opt_Std_neu + RundungEinspeisewert/2)

        # Eigen_Opt_Std_neu runden
        if MaxEinspeisung < RundungEinspeisewert: RundungEinspeisewert = MaxEinspeisung
        Eigen_Opt_Std_neu = int(round(Eigen_Opt_Std_neu / RundungEinspeisewert) * RundungEinspeisewert)
        if Akku_Rest_Watt < 0 or Eigen_Opt_Std_neu < 0: Eigen_Opt_Std_neu = 0
        # Hier auf MaxEinspeisung begrenzen.
        if Eigen_Opt_Std_neu > MaxEinspeisung : Eigen_Opt_Std_neu = MaxEinspeisung
        # PrognoseGrenzeMorgen pruefen
        if (PrognoseMorgen < PrognoseGrenzeMorgen and PrognoseMorgen != 0):
            Eigen_Opt_Std_neu = 0
        # In der letzten Stunde vor dem Morgengrauen und wenn AkkuZielProz nicht unterschritten, Eigen_Opt_Std für Tag stellen
        if Dauer_Nacht_Std < 1:
            # Die aktuelle Einspeisung nicht mehr verändern
            Eigen_Opt_Std_neu = Eigen_Opt_Std
            if BattStatusProz > AkkuZielProz:
                if (PrognoseMorgen < PrognoseGrenzeMorgen):
                    DEBUG_Eig_opt_tmp = "\nDEBUG ## >>> Bei PrognoseMorgen < PrognoseGrenzeMorgen, keine Einspeisung während des Tages"
                    DEBUG_Eig_opt_tmp += "\nDEBUG ## >>> Prognose 24H+: " + str(PrognoseMorgen) + ", PrognoseGrenzeMorgen: " + str(PrognoseGrenzeMorgen) 
                    Eigen_Opt_Std_neu = 30
                else:
                    DEBUG_Eig_opt_tmp = "\nDEBUG ## >>> Bei Prognose 24H+ > PrognoseGrenzeMorgen MaxEinspeisung während des Tages"
                    DEBUG_Eig_opt_tmp += "\nDEBUG ## >>> Prognose 24H+: " + str(PrognoseMorgen) + ", PrognoseGrenzeMorgen: " + str(PrognoseGrenzeMorgen) 
                    Eigen_Opt_Std_neu = MaxEinspeisung 
                DEBUG_Eig_opt += DEBUG_Eig_opt_tmp

            # Wenn EigenverbOpt_steuern 2 Optimierung ueber Tags = 0
            if (EigenverbOpt_steuern == 2):
                Eigen_Opt_Std_neu = 0
                DEBUG_Eig_opt += "\nDEBUG ## >>> EigenverbOpt_steuern == 2, keine Einspeisung während des Tages"

    
        DEBUG_Eig_opt += "\nDEBUG ## Dauer_Nacht_Std: " + str(round(Dauer_Nacht_Std, 2)) + ", Akku_Rest_Watt: " + str(int(Akku_Rest_Watt)) +  \
                    "\nDEBUG ## Eigen_Opt_genau: " + str(int(Akku_Rest_Watt/Dauer_Nacht_Std)) + ", Eigen_Opt_Std_neu: " + str(Eigen_Opt_Std_neu)
        # Wenn  Eigen_Opt_auto = 0, Eigenverbrauchs-Optimierung = Automatisch = 0, Manuell = 1
        if Eigen_Opt_auto == 0: Eigen_Opt_Std = 0
    
        # Einspeisung ist immer Minus, Bezug ist immer Plus!!
        Eigen_Opt_Std_neu = abs(Eigen_Opt_Std_neu) * -1
    
        return PrognoseMorgen, Eigen_Opt_Std, int(Eigen_Opt_Std_neu), Dauer_Nacht_Std, AkkuZielProz, DEBUG_Eig_opt, Backup_Reserve
    
    def getAkkuschonWert(self, BattStatusProz, BattganzeLadeKapazWatt, alterLadewert, aktuellerLadewert):
        HysteProdFakt = 1
        Ladefaktor = 1
        BattStatusProz_Grenze = 100
        DEBUG_Ausgabe = ""
        AkkuSchonGrund = ""
        Schaltverzoegerung_Diff = 2
        if BattStatusProz > 90: Schaltverzoegerung_Diff = 1
        Akkuschonung_Werte_tmp = json.loads(basics.getVarConf('Ladeberechnung','Akkuschonung_Werte','str'))
        Akkuschonung_Werte = dict(sorted(Akkuschonung_Werte_tmp.items(), key=lambda item: int(item[0])))
        DEBUG_Ausgabe += "DEBUG\nDEBUG <<<<<< Meldungen von Akkuschonung >>>>>>> "
        DEBUG_Ausgabe += "\nDEBUG Akkuschonung_Werte: " + str(Akkuschonung_Werte) + "\n"
        for Akkuschon_Proz in Akkuschonung_Werte: 
            # Schaltverzoegerung neu 
            if (BattStatusProz >= int(Akkuschon_Proz) - Schaltverzoegerung_Diff and ( abs((BattganzeLadeKapazWatt * float(Akkuschonung_Werte[Akkuschon_Proz])) - alterLadewert) < 3 )) or BattStatusProz >= int(Akkuschon_Proz):
                Ladefaktor = float(Akkuschonung_Werte[Akkuschon_Proz])
                AkkuSchonGrund = str(Akkuschon_Proz) + '%, Ladewert = ' + str(Akkuschonung_Werte[Akkuschon_Proz]) + 'C'
                BattStatusProz_Grenze = int(Akkuschon_Proz)

        AkkuschonungLadewert = int(BattganzeLadeKapazWatt * Ladefaktor)
        # Bei Akkuschonung Schaltverzögerung (hysterese), wenn Ladewert ist bereits der Akkuschonwert (+/- 3W) BattStatusProz_Grenze 5% runter
        if ( abs(AkkuschonungLadewert - alterLadewert) < 3 ):
            BattStatusProz_Grenze = BattStatusProz_Grenze * 0.95
            HysteProdFakt = 5

        if BattStatusProz >= BattStatusProz_Grenze:
            DEBUG_Ausgabe += "DEBUG AkkuschonungLadewert-alterLadewert: " + str(abs(AkkuschonungLadewert - alterLadewert))
            DEBUG_Ausgabe += "\nDEBUG BattStatusProz_Grenze: " + str(BattStatusProz_Grenze)
            DEBUG_Ausgabe += "\nDEBUG AkkuschonungLadewert: " + str(AkkuschonungLadewert) + "\n"
            DEBUG_Ausgabe += "DEBUG aktuellerLadewert: " + str(aktuellerLadewert) + "\n"
        return AkkuschonungLadewert, HysteProdFakt, BattStatusProz_Grenze, AkkuSchonGrund, DEBUG_Ausgabe 
