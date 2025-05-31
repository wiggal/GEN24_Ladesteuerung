from datetime import datetime
import json
from sys import argv
import requests
import FUNCTIONS.PrognoseLadewert
import FUNCTIONS.Steuerdaten
import FUNCTIONS.functions
import FUNCTIONS.GEN24_API
import FUNCTIONS.SQLall
import FUNCTIONS.httprequest


if __name__ == '__main__':
        basics = FUNCTIONS.functions.basics()
        config = basics.loadConfig(['default', 'charge'])
        request = FUNCTIONS.httprequest.request()
        sqlall = FUNCTIONS.SQLall.sqlall()
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"


        host_ip = basics.getVarConf('gen24','hostNameOrIp', 'str')
        user = basics.getVarConf('gen24','user', 'str')
        password = basics.getVarConf('gen24','password', 'str')
        # Hier Hochkommas am Anfang und am Ende enternen
        password = password[1:-1]

        try:
            WR_URL = 'http://'+host_ip
            response = requests.get(WR_URL)
            response.raise_for_status()  # Auslösen einer Ausnahme, wenn der Statuscode nicht 2xx ist
            alterLadewert = 0
            # Auf Firmware 1.36.5-1 prüfen und evtl. Pfad anpassen
            result_get_time_of_use_array = request.get_time_of_use(host_ip, user, password)
            result_get_time_of_use = result_get_time_of_use_array[0]
            http_request_path = result_get_time_of_use_array[1]
            for element in result_get_time_of_use:
                if element['Active'] == True and element['ScheduleType'] == 'CHARGE_MAX':
                    alterLadewert = element['Power']

            # WebUI-Parameter aus CONFIG/Prog_Steuerung.sqlite lesen
            SettingsPara = FUNCTIONS.Steuerdaten.readcontroldata()
            print_level = basics.getVarConf('env','print_level','eval')
            Parameter = SettingsPara.getParameter(argv, 'ProgrammStrg')
            Options = Parameter[2]
        
            Ausgabe_Parameter = ''
            if(Parameter[1] != "" and print_level >= 1):
                Ausgabe_Parameter = "DEBUG Parameteränderung durch WebUI-Settings: "  + str(Parameter[1])
                if(Parameter[0] == "exit0"):
                    # Batteriemangement zurücksetzen
                    if result_get_time_of_use != []:
                        response = request.send_request(http_request_path + 'config/timeofuse', method='POST', payload ='{"timeofuse":[]}')
                        print("Batteriemanagementeinträge gelöscht!")
                    # Ende Programm
                if(Parameter[0] == "exit0") or (Parameter[0] == "exit1"):
                    print(now, "ProgrammSTOPP durch WebUI-Settings: ", Parameter[1])
                    exit()
                    # Ende Programm
            else:
                # Aufrufparameter ausgeben
                Ausgabe_Parameter = "DEBUG Aufrufparameter: "  + str(Parameter[2])

            # Nur ausführen, wenn WR erreichbar
            try:            
                    DEBUG_Ausgabe= "\nDEBUG <<<<<< E I N >>>>>>>\nDEBUG"
    
                    ###############################
    
                    weatherfile = basics.getVarConf('env','filePathWeatherData','str')
                    weatherdata = basics.loadWeatherData(weatherfile)

    
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
                    PV_Reservierung_steuern = basics.getVarConf('Reservierung','PV_Reservierung_steuern','eval')
                    Batterieentlandung_steuern = basics.getVarConf('Entladung','Batterieentlandung_steuern','eval')
                    WREntladeSchreibGrenze_Watt = basics.getVarConf('Entladung','WREntladeSchreibGrenze_Watt','eval')
                    Notstromreserve_steuern = basics.getVarConf('Notstrom','Notstromreserve_steuern','eval')
                    EigenverbOpt_steuern = basics.getVarConf('EigenverbOptimum','EigenverbOpt_steuern','eval')
                    MaxEinspeisung = basics.getVarConf('EigenverbOptimum','MaxEinspeisung','eval')

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

                    api = FUNCTIONS.GEN24_API.gen24api
                    API = api.get_API()
                    Battery_Status = API['BAT_MODE']
                    # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 2.0, AKKU AUS
                    # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 0.0, AKKU EIN
                    # Angenommene Werte, wenn AKKU offline
                    if (Battery_Status == 2):
                        print()
                        print("*********** Batterie ist offline, aktueller Ladestand wird auf 5% gesetzt!!! *********\n")
                        BattganzeKapazWatt = basics.getVarConf('gen24','battery_capacity_Wh', 'eval') # Kapazität in Wh aus dynprice.ini
                        BattganzeLadeKapazWatt = BattganzeKapazWatt
                        BattStatusProz = 5
                        BattKapaWatt_akt = BattganzeKapazWatt * 0.95
                        aktuelleBatteriePower = 0
                    else:
                        BattganzeLadeKapazWatt = (API['BattganzeLadeKapazWatt'])
                        BattganzeKapazWatt = (API['BattganzeKapazWatt'])
                        BattStatusProz = API['BattStatusProz']
                        BattKapaWatt_akt = API['BattKapaWatt_akt']
                        aktuelleBatteriePower = API['aktuelleBatteriePower']

                    aktuelleEinspeisung = API['aktuelleEinspeisung'] * -1
                    aktuellePVProduktion = API['aktuellePVProduktion']
                    GesamtverbrauchHaus = aktuellePVProduktion - aktuelleEinspeisung + aktuelleBatteriePower

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
    
                    format_aktStd = "%Y-%m-%d %H:00:00"
                    aktStd = datetime.strftime(now, "%H:00")
                    Akt_Std = int(datetime.strftime(now, "%H"))
    
                    #######################################
                    ## Ab hier geht die Berechnung los
                    #######################################
    
                    TagesPrognoseGesamt = 0
                    aktuellerLadewert = 0
                    Grundlast_Summe = 0
                    aktuelleVorhersage = 0
                    LadewertGrund = ""

                    # Klasse ProgLadewert initieren
                    progladewert = FUNCTIONS.PrognoseLadewert.progladewert(weatherdata, WR_Kapazitaet, reservierungdata, MaxLadung, Einspeisegrenze, aktuelleBatteriePower)
                    # evtl. Ladung des Akku auf SOC_Proz_Grenze begrenzen, und damit BattKapaWatt_akt reduzieren
                    Sdt_24H = datetime.now().hour
                    PrognoseMorgen = progladewert.getPrognoseMorgen(0,24-Sdt_24H)[0]/1000
                    PrognoseLimit_SOC = basics.getVarConf('Ladeberechnung','PrognoseLimit_SOC','eval')
                    Akkuschonung_Werte = basics.getVarConf('Ladeberechnung','Akkuschonung_Werte','str')
                    # Akkuschonung_Werte in ein Dictionary umwandeln, ersten Wert extrahieren und in float umwandeln
                    SOC_data = json.loads(Akkuschonung_Werte)
                    SOC_Proz_Grenze = float(next(iter(SOC_data.keys())))
                    BattKapaWatt_akt_SOC = BattKapaWatt_akt
                    if PrognoseLimit_SOC >= 0 and PrognoseMorgen > PrognoseLimit_SOC:
                        BattKapaWatt_akt_SOC = int(BattKapaWatt_akt - BattganzeKapazWatt*((100-SOC_Proz_Grenze)/100))

                    # WRSchreibGrenze_nachUnten ab 90% Batteriestand prozentual erhöhen (ersetzen von BatterieVoll!!)
                    if ( BattStatusProz > 90 ):
                        WRSchreibGrenze_nachUnten = int(WRSchreibGrenze_nachUnten * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachUnten: " + str(WRSchreibGrenze_nachUnten) +"\n"
                        WRSchreibGrenze_nachOben = int(WRSchreibGrenze_nachOben * (1 + ( BattStatusProz - 90 ) / 7))
                        DEBUG_Ausgabe += "DEBUG ## Batt >90% ## WRSchreibGrenze_nachOben: " + str(WRSchreibGrenze_nachOben) +"\n"

                    # BattVollUm setzen evtl. mit DIFF zum Sonnenuntergang
                    BattVollUm = basics.getVarConf('Ladeberechnung','BattVollUm','eval')
                    Sonnenuntergang = progladewert.getSonnenuntergang(PV_Leistung_Watt)
                    if BattVollUm <= 0:
                       BattVollUm = Sonnenuntergang + BattVollUm
                    # Bei Akkuschonung BattVollUm eine Stunde vor verlegen
                    if Akkuschonung > 0:
                        BattVollUm = BattVollUm - 1


                    # Geamtprognose und Ladewert berechnen mit Funktion getLadewert
                    PrognoseUNDUeberschuss = progladewert.getLadewert(BattVollUm, Grundlast, alterLadewert, BattKapaWatt_akt)
                    TagesPrognoseGesamt = PrognoseUNDUeberschuss[0]
                    Grundlast_Summe = PrognoseUNDUeberschuss[1]
                    aktuellerLadewert = PrognoseUNDUeberschuss[2]
                    LadewertGrund = PrognoseUNDUeberschuss[3]
                    # Ladewert auf Schreibgrenzen prüfen
                    DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                    WR_schreiben = DATA[1]

                    # Aktuelle Prognose berechnen
                    AktuellenLadewert_Array = progladewert.getAktPrognose(BattKapaWatt_akt)
                    aktuelleVorhersage = AktuellenLadewert_Array[0]
                    DEBUG_Ausgabe += AktuellenLadewert_Array[1]

                    # DEBUG_Ausgabe der Ladewertermittlung 
                    DEBUG_Ausgabe += ", PrognoseLadewert: " + str(aktuellerLadewert) + "\n"


                    # Wenn über die PV-Planung manuelle Ladung angewählt wurde
                    MaxladungDurchPV_Planung = ""
                    ManuelleStrg_Akkuschon_aus = 0
                    ManuelleSteuerung = reservierungdata.get('ManuelleSteuerung')
                    # Prüfen, ob Einträge schon abgelaufen
                    try: 
                        Ablaufdatum = int(reservierungdata_tmp['ManuelleSteuerung']['Options'])
                    except: 
                        Ablaufdatum = 0
                    if (Ablaufdatum > int(datetime.now().timestamp())):
                        if (PV_Reservierung_steuern == 1) and (ManuelleSteuerung >= 0):
                            FesteLadeleistung = BattganzeLadeKapazWatt * ManuelleSteuerung/100
                            ManuelleStrg_Akkuschon_aus = 1
                            MaxladungDurchPV_Planung = "Sliderwert in PV-Planung ausgewählt."
                        # Wenn über die PV-Planung MaxLadung gewählt wurde (-2), MaxLadung setzen
                        if (PV_Reservierung_steuern == 1) and (ManuelleSteuerung == -2):
                            FesteLadeleistung = MaxLadung
                            ManuelleStrg_Akkuschon_aus = 1
                            MaxladungDurchPV_Planung = "MaxLadung in PV-Planung ausgewählt."

                    # Wenn die Variable "FesteLadeleistung" größergleich "0" ist, wird der Wert fest als Ladeleistung geschrieben
                    if FesteLadeleistung >= 0:
                        #DATA = progladewert.setLadewert(FesteLadeleistung, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)  #entWIGGlung kann das weg?
                        aktuellerLadewert = FesteLadeleistung
                        ManuelleStrg_Akkuschon_aus = 1
                        # wegen Rundung
                        if abs(aktuellerLadewert - alterLadewert) < 3:
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
                            WR_schreiben = DATA[1]
                            LadewertGrund = "BattStatusProz < MindBattLad"
    
                    # Wenn Akkuschonung > 0 ab 80% Batterieladung mit Ladewert runter fahren, Werte auch für Zwangsladung bestimmen
                    if Akkuschonung > 0 or Batterieentlandung_steuern > 1:
                        Akkuschonung_dict = progladewert.getAkkuschonWert(BattStatusProz, BattganzeLadeKapazWatt, alterLadewert, aktuellerLadewert)
                        AkkuschonungLadewert = Akkuschonung_dict[0]
                        HysteProdFakt = Akkuschonung_dict[1]
                        BattStatusProz_Grenze = Akkuschonung_dict[2]
                        AkkuSchonGrund = Akkuschonung_dict[3]
                        DEBUG_Ausgabe += Akkuschonung_dict[4]

                        if BattStatusProz >= BattStatusProz_Grenze and ManuelleStrg_Akkuschon_aus == 0:
                            # Um das setzen der Akkuschonung zu verhindern, wenn aktuellePVProduktion zu wenig oder der Akku wieder entladen wird.
                            if (AkkuschonungLadewert < aktuellerLadewert or AkkuschonungLadewert < alterLadewert + 10) and aktuellePVProduktion * HysteProdFakt > AkkuschonungLadewert:
                                aktuellerLadewert = AkkuschonungLadewert
                                WRSchreibGrenze_nachUnten = aktuellerLadewert / 5
                                WRSchreibGrenze_nachOben = aktuellerLadewert / 5
                                DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                                WR_schreiben = DATA[1]
                                LadewertGrund = "Akkuschonung: Ladestand >= " + AkkuSchonGrund
                        if ManuelleStrg_Akkuschon_aus == 1:
                            DEBUG_Ausgabe += "DEBUG Keine Akkuschonung, da FesteLadeleistung oder LadeStrg-Auswahl!\n"

                    # Ladung des Akku auf XX% (SOC_Proz_Grenze) begrenzen, wenn bestimmte Prognose für die nächsten 24 Std. überschritten
                    # Hysterese anwenden
                    if (alterLadewert == 0): SOC_Proz_Grenze = SOC_Proz_Grenze - 3
                    # Wenn ein DEBUG
                    if PrognoseLimit_SOC >= 0:
                        DEBUG_Ausgabe+="DEBUG\nDEBUG <<<<<<<< Ladebegrenzung auf 80% SOC >>>>>>>>>>>>>"
                        DEBUG_Ausgabe += "\nDEBUG PrognoseMorgen: " + str(PrognoseMorgen)
                        DEBUG_Ausgabe += ", PrognoseLimit_SOC: " + str(PrognoseLimit_SOC)
                        DEBUG_Ausgabe += ", BattStatusProz_Grenze: " + str(SOC_Proz_Grenze)
                    if ManuelleStrg_Akkuschon_aus == 1:
                        DEBUG_Ausgabe += "\nDEBUG Keine Begrenzung, da FesteLadeleistung oder LadeStrg-Auswahl!"
                    # Begrenzung nur wenn keine manuelle Steuerung bzw. FesterLadewert (ManuelleStrg_Akkuschon_aus == 0)
                    if BattStatusProz >= SOC_Proz_Grenze and PrognoseLimit_SOC >= 0 and PrognoseMorgen > PrognoseLimit_SOC and ManuelleStrg_Akkuschon_aus == 0:
                        aktuellerLadewert = 0
                        DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, 0, BattganzeLadeKapazWatt, alterLadewert)
                        WR_schreiben = DATA[1]
                        LadewertGrund = "Akkuschonung: Ladebegrenzung auf 80% SOC"
                    if BattKapaWatt_akt_SOC != BattKapaWatt_akt and ManuelleStrg_Akkuschon_aus == 0:
                        DEBUG_Ausgabe += "\nDEBUG BattKapaWatt_akt orginal: " + str(BattKapaWatt_akt)
                        DEBUG_Ausgabe += ", BattKapaWatt_akt um 20% gekürzt: " + str(BattKapaWatt_akt_SOC)
                        DEBUG_Ausgabe+="\nDEBUG <<<< SOC 80% für Ladeberechnung AKTIV!!! >>>>"

                    # Wenn die aktuellePVProduktion < 50 Watt ist, nicht schreiben, 
                    # um 0:00Uhr wird sonst immer Ladewert 0 geschrieben!
                    if aktuellePVProduktion < 50:
                        # Für die Nacht zwingend auf MaxLadung, 
                        # da sonst mogends evtl nicht auf 0 gestelltwerden kann, wegen WRSchreibGrenze_nachUnten
                        if alterLadewert < MaxLadung -10 and Akt_Std > 12:
                            aktuellerLadewert = MaxLadung
                            DATA = progladewert.setLadewert(aktuellerLadewert, WRSchreibGrenze_nachOben, WRSchreibGrenze_nachUnten, BattganzeLadeKapazWatt, alterLadewert)
                            WR_schreiben = DATA[1]
                            LadewertGrund = "Auf MaxLadung stellen, da PVProduktion < 50 Watt!"
                        else:
                            WR_schreiben = 0
                            LadewertGrund = "Nicht schreiben, da PVProduktion < 50 Watt!"

                    # Auf ganze Watt runden
                    aktuellerLadewert = int(aktuellerLadewert)

                    if print_level >= 1:
                        try:
                            print("***** BEGINN: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"),"*****")
                            if(Ausgabe_Parameter != ''): print(Ausgabe_Parameter)
                            print("aktuellePrognose:           ", aktuelleVorhersage)
                            print("TagesPrognose - BattVollUm: ", TagesPrognoseGesamt,"-", BattVollUm)
                            print("Grundlast_Summe für Tag:    ", Grundlast_Summe)
                            print("aktuellePVProduktion/Watt:  ", aktuellePVProduktion)
                            print("aktuelleEinspeisung/Watt:   ", aktuelleEinspeisung)
                            print("aktuelleBatteriePower/Watt: ", aktuelleBatteriePower)
                            print("GesamtverbrauchHaus/Watt:   ", GesamtverbrauchHaus)
                            print("aktuelleBattKapazität/Watt: ", BattKapaWatt_akt)
                            print("Batteriestatus in Prozent:  ", BattStatusProz,"%")
                            print("LadewertGrund: ", LadewertGrund)
                            print("Bisheriger Ladewert/Watt:   ", alterLadewert)
                            print("Neuer Ladewert/Watt:        ", aktuellerLadewert)
                            print()
                        except Exception as e:
                            print()
                            print("Fehler in den Printbefehlen, Ausgabe nicht möglich!")
                            print("Fehlermeldung:", e)
                            print()


                    DEBUG_Ausgabe+="\nDEBUG\nDEBUG BattVollUm:                 " + str(BattVollUm) + "Uhr"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachUnten:  " + str(WRSchreibGrenze_nachUnten) + "W"
                    DEBUG_Ausgabe+="\nDEBUG WRSchreibGrenze_nachOben:   " + str(WRSchreibGrenze_nachOben) + "W"
                    

                    ######## IN  WR Batteriemanagement schreiben, später gemeinsam
                    ######## E N T L A D E S T E U E R U N G  ab hier wenn eingeschaltet!

                    BatteryMaxDischarge = BattganzeLadeKapazWatt
                    Neu_BatteryMaxDischarge = BattganzeLadeKapazWatt
                    BatteryMaxDischarge_Zwangsladung = 0
                    EntladeEintragloeschen = "nein"
                    EntladeEintragDa = "nein"

                    if  Batterieentlandung_steuern > 0:
                        MaxEntladung = BattganzeLadeKapazWatt

                        DEBUG_Ausgabe+="DEBUG\nDEBUG <<<<<<<< ENTLADESTEUERUNG >>>>>>>>>>>>>"
                        for element in result_get_time_of_use:
                            if element['Active'] == True and element['ScheduleType'] == 'DISCHARGE_MAX':
                                BatteryMaxDischarge = element['Power']
                                BatteryMaxDischarge_Zwangsladung = 0
                                EntladeEintragDa = "ja"
                            elif element['Active'] == True and element['ScheduleType'] == 'CHARGE_MIN':
                                BatteryMaxDischarge_Zwangsladung = element['Power']
                                EntladeEintragDa = "ja"

                        # EntladeSteuerungdaten lesen
                        entladesteurungsdata = sqlall.getSQLsteuerdaten('ENTLadeStrg')
                        # Manuellen Entladewert lesen
                        if (entladesteurungsdata.get('ManuelleEntladesteuerung')):
                            MaxEntladung_Prozent=int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1'])
                            MaxEntladung = int(MaxEntladung_Prozent*BattganzeLadeKapazWatt / 100)
                            DEBUG_Ausgabe+="\nDEBUG MaxEntladung = entladesteurungsdata:" + str(MaxEntladung)

                        # Verbrauchsgrenze Entladung lesen
                        if (entladesteurungsdata.get(aktStd)):
                            VerbrauchsgrenzeEntladung = entladesteurungsdata[aktStd]['Res_Feld1']
                        else:
                            VerbrauchsgrenzeEntladung = 0

                        DEBUG_Ausgabe+="\nDEBUG VerbrauchsgrenzeEntladung aus Spalte 1: " + str(VerbrauchsgrenzeEntladung)
                        # Feste Entladegrenze aus Tabelle  ENTLadeStrg lesen
                        if (entladesteurungsdata.get(aktStd)):
                            # Funktion aufrufen, die eine evtl. viertelstündliche zuteilung macht
                            FesteEntladegrenze_tmp = progladewert.get_FesteEntladegrenze(str(entladesteurungsdata[aktStd]['Res_Feld2']))
                            FesteEntladegrenze = FesteEntladegrenze_tmp[0]
                            DEBUG_Ausgabe += FesteEntladegrenze_tmp[1]
                        else:
                            FesteEntladegrenze = 0

                        DEBUG_Ausgabe+="\nDEBUG FesteEntladegrenze aus Spalte 2: " + str(FesteEntladegrenze)

                        # Ladetype = "DISCHARGE_MAX" bei Entladebegrenzung
                        Ladetype = "DISCHARGE_MAX"

                        # Feste Entladebegrenzung ab einem bestimmten Verbrauch
                        Verbrauch_Feste_Entladegrenze = basics.getVarConf('Entladung','Verbrauch_Feste_Entladegrenze','eval')
                        Feste_Entladegrenze = basics.getVarConf('Entladung','Feste_Entladegrenze','eval')

                        # Wenn folgende Bedingungen wahr, Entladung neu schreiben
                        # Verbrauchsgrenze == 2000 && Feste Grenze == 0 (leer)
                        if (GesamtverbrauchHaus > VerbrauchsgrenzeEntladung and VerbrauchsgrenzeEntladung > 0 and FesteEntladegrenze == 0):
                            Neu_BatteryMaxDischarge = int(GesamtverbrauchHaus - VerbrauchsgrenzeEntladung)
                        # Verbrauchsgrenze == 2000 && Feste Grenze == 500 
                        elif (GesamtverbrauchHaus > VerbrauchsgrenzeEntladung and VerbrauchsgrenzeEntladung > 0 and FesteEntladegrenze > 0):
                            Neu_BatteryMaxDischarge = int(FesteEntladegrenze)
                        # Verbrauchsgrenze == 0 (leer) && Feste Grenze == 500
                        elif (VerbrauchsgrenzeEntladung == 0 and FesteEntladegrenze > 0):
                            Neu_BatteryMaxDischarge = int(FesteEntladegrenze)
                        # Verbrauchsgrenze == 0 (leer) && Feste Grenze == -500 #Negativer Wert = Zwangsladung
                        elif (VerbrauchsgrenzeEntladung == 0 and FesteEntladegrenze < 0):
                            BatteryMaxDischarge = BatteryMaxDischarge_Zwangsladung
                            Neu_BatteryMaxDischarge = abs(int(FesteEntladegrenze))
                            # Akkuschonung auch bei Zwangsladung
                            if (AkkuschonungLadewert < Neu_BatteryMaxDischarge and Batterieentlandung_steuern > 1): Neu_BatteryMaxDischarge = AkkuschonungLadewert
                            DEBUG_Ausgabe+="\nDEBUG Akkuschonung auch bei Zwangsladung: " + str(AkkuschonungLadewert)
                            # Zwangsladung kann nur geschrieben werden, wenn aktuellerLadewert > Neu_BatteryMaxDischarge
                            if (Neu_BatteryMaxDischarge > aktuellerLadewert): aktuellerLadewert = Neu_BatteryMaxDischarge + 100
                            # Ladetype = "CHARGE_MIN" bei Zwangsladung
                            Ladetype = "CHARGE_MIN"
                        elif (MaxEntladung_Prozent < 100):
                            Neu_BatteryMaxDischarge = MaxEntladung
                        # Hausverbrauch größer z.B. 10kW und Entladung batterie größer Feste_Entladegrenze => wenn AKKU leer dann nicht
                        # aktuelleBatteriePower > Feste_Entladegrenze/2 = Damit sie nicht einschaltet, wenn Akku bereits leer ist.
                        # Feste_Entladegrenze/2 = sonst schaltet sie beim nächsten Durchlauf wieder aus, da die aktuelleBatteriePower dann kleiner ist.
                        elif (Verbrauch_Feste_Entladegrenze > 0 and GesamtverbrauchHaus > Verbrauch_Feste_Entladegrenze and aktuelleBatteriePower > Feste_Entladegrenze/2 and Ladetype == "DISCHARGE_MAX"):
                            Neu_BatteryMaxDischarge = Feste_Entladegrenze
                        elif (EntladeEintragDa == "ja"):
                            EntladeEintragloeschen = "ja"

                        DEBUG_Ausgabe+="\nDEBUG Batterieentladegrenze NEU: " + str(Neu_BatteryMaxDischarge) + "%"

                        # Entladung_Daempfung, Unterschied muss größer WREntladeSchreibGrenze_Watt sein
                        if (abs(Neu_BatteryMaxDischarge - BatteryMaxDischarge) < WREntladeSchreibGrenze_Watt) and Ladetype != "CHARGE_MIN":
                            Neu_BatteryMaxDischarge = BatteryMaxDischarge

                        ## Werte zum Überprüfen ausgeben
                        if print_level >= 1:
                            print("## ENTLADESTEUERUNG ##\n")
                            print("Feste Entladegrenze in % : ", int(entladesteurungsdata['ManuelleEntladesteuerung']['Res_Feld1']), "%")
                            print("VerbrauchsgrenzeEntladung: ", VerbrauchsgrenzeEntladung, "W")
                            print("Feste Entladegrenze Table: ", FesteEntladegrenze, "W")
                            if (Ladetype == "DISCHARGE_MAX") and (EntladeEintragloeschen == "nein"):
                                print("Batterieentladegrenze ALT: ", BatteryMaxDischarge, "W")
                                print("Batterieentladegrenze NEU: ", Neu_BatteryMaxDischarge, "W")
                            if (Ladetype == "CHARGE_MIN") and (EntladeEintragloeschen == "nein"):
                                print("Zwangsladung ALT:          ", BatteryMaxDischarge, "W")
                                print("Zwangsladung NEU:          ", Neu_BatteryMaxDischarge, "W")
                                print("Ladewert >= Zwangsladung:   ", aktuellerLadewert, "W")
                            if (EntladeEintragloeschen == "ja"):
                                print(">> Entladeeintrag löschen!")
                            print()

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADESTEUERUNG >>>>>>>>>>>>>"


                    ### AB HIER SCHARF wenn Argument "schreiben" übergeben
                    ######## Ladeleistung und Entladeleistung in WR Batteriemanagement schreiben 

                    bereits_geschrieben = 0
                    Schreib_Ausgabe = ""
                    Push_Schreib_Ausgabe = ""
                    # Neuen Ladewert als HTTP_Request schreiben, wenn WR_schreiben == 1 
                    if WR_schreiben == 1 or Neu_BatteryMaxDischarge != BatteryMaxDischarge or EntladeEintragloeschen == "ja":
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< LADEWERTE >>>>>>>>>>>>>"
                        DEBUG_Ausgabe+="\nDEBUG Folgender MAX_Ladewert neu zum Schreiben: " + str(aktuellerLadewert)
                        DEBUG_Ausgabe+="\nDEBUG Folgender MAX_ENT_Ladewert neu zum Schreiben: " + str(Neu_BatteryMaxDischarge)
                        payload_text = ''
                        trenner_komma = ''
                        if ('laden' in Options):
                            trenner_komma = ','
                            payload_text = '{"Active":true,"Power":' + str(aktuellerLadewert) + \
                            ',"ScheduleType":"CHARGE_MAX","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                        elif WR_schreiben == 1 :
                            Schreib_Ausgabe = Schreib_Ausgabe + "Ladesteuerung NICHT geschrieben, da Option \"laden\" NICHT gesetzt!\n"
                        if  ('entladen' in Options) and (Batterieentlandung_steuern > 0) and (EntladeEintragloeschen == "nein"):
                            if(Neu_BatteryMaxDischarge != BatteryMaxDischarge or (payload_text != '' and EntladeEintragDa == "ja")):
                                payload_text += str(trenner_komma) + '{"Active":true,"Power":' + str(Neu_BatteryMaxDischarge) + \
                                ',"ScheduleType":"'+Ladetype+'","TimeTable":{"Start":"00:00","End":"23:59"},"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                        elif ('entladen' not in Options and (Neu_BatteryMaxDischarge != BatteryMaxDischarge or EntladeEintragloeschen == "ja")):
                            Schreib_Ausgabe = Schreib_Ausgabe + "Entladesteuerung NICHT geschrieben, da Option \"entladen\" NICHT gesetzt!\n"
                        # Wenn payload_text NICHT leer dann schreiben
                        if (payload_text != '' or ('entladen' in Options and EntladeEintragloeschen == "ja")):
                            response = request.send_request(http_request_path + 'config/timeofuse', method='POST', payload ='{"timeofuse":[' + str(payload_text) + ']}')
                            bereits_geschrieben = 1
                            if ('laden' in Options) and WR_schreiben == 1:
                                Schreib_Ausgabe = Schreib_Ausgabe + "CHARGE_MAX geschrieben: " + str(aktuellerLadewert) + "W\n"
                            if ('entladen' in Options) and Neu_BatteryMaxDischarge != BatteryMaxDischarge and (EntladeEintragloeschen == "nein"):
                                Schreib_Ausgabe = Schreib_Ausgabe + Ladetype + " geschrieben: " + str(Neu_BatteryMaxDischarge) + "W\n"
                            if ('entladen' in Options) and (EntladeEintragloeschen == "ja"):
                                Schreib_Ausgabe = Schreib_Ausgabe + "Entladeeintrag wurde gelöscht.\n"
                            Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe
                            DEBUG_Ausgabe+="\nDEBUG Meldung bei Ladegrenze schreiben: " + str(response)
                    else:
                        Schreib_Ausgabe = Schreib_Ausgabe + "Änderungen kleiner Schreibgrenze!\n"

                    if print_level >= 1:
                        print(Schreib_Ausgabe)

                    ######## WR Batteriemanagement ENDE

                    ######## Eigenverbrauchs-Optimierung  ab hier wenn eingeschaltet!
                    HYB_BACKUP_RESERVED = None
                    if  EigenverbOpt_steuern > 0:
                        EigenOptERG = progladewert.getEigenverbrauchOpt(host_ip, user, password, BattStatusProz, BattganzeKapazWatt, EigenverbOpt_steuern, MaxEinspeisung)
                        Prognose_24H = EigenOptERG[0]
                        Eigen_Opt_Std = EigenOptERG[1]
                        Eigen_Opt_Std_neu = EigenOptERG[2]
                        Dauer_Nacht_Std = EigenOptERG[3]
                        AkkuZielProz = EigenOptERG[4]
                        DEBUG_Ausgabe += EigenOptERG[5]
                        HYB_BACKUP_RESERVED = EigenOptERG[6]
                        aktuellePVProduktion_tmp = aktuellePVProduktion

                        # Wenn der Akku unter MindBattLad Optimierung auf 0 setzen
                        # Bereich ermoeglicht die Optimierung fuer den Tag zu setzen
                        if (BattStatusProz <= MindBattLad) and Eigen_Opt_Std_neu > 30:
                            Dauer_Nacht_Std = 1
                            aktuellePVProduktion_tmp = 0
                            Eigen_Opt_Std_neu = 30
                            DEBUG_Ausgabe += "DEBUG ##  Akku unter MindBattLad Optimierung auf 30 gesetzt!!!\n"
                        # Bei Eigen_Opt_Std_neu == 0 auf HYB_EM_MODE = 0, Eigenverbrauchs-Optimierung = Automatisch schalten
                        HYB_EM_MODE = 1
                        if (Eigen_Opt_Std_neu == 0):
                            HYB_EM_MODE = 0

                        if (Dauer_Nacht_Std > 0.5 or BattStatusProz < AkkuZielProz) and aktuellePVProduktion_tmp < (Grundlast + MaxEinspeisung) * 1.5:
                            if print_level >= 1:
                                print("## Eigenverbrauchs-Optimierung ##")
                                print("Prognose nächste 24Std: ", Prognose_24H, "KW")
                                print("Eigenverbrauchs-Opt. ALT: ", Eigen_Opt_Std, "W")
                                print("Eigenverbrauchs-Opt. NEU: ", Eigen_Opt_Std_neu, "W")
                                print()

                            Opti_Schreib_Ausgabe = ""

                            if (Eigen_Opt_Std_neu != Eigen_Opt_Std):
                                if ('optimierung' in Options):
                                    response = request.send_request(http_request_path + 'config/batteries', method='POST', payload ='{"HYB_EM_POWER":'+ str(Eigen_Opt_Std_neu) + ',"HYB_EM_MODE":'+str(HYB_EM_MODE)+'}')
                                    bereits_geschrieben = 1
                                    DEBUG_Ausgabe+="\nDEBUG Meldung Eigenverbrauchs-Opt. schreiben: " + str(response)
                                    Opti_Schreib_Ausgabe = Opti_Schreib_Ausgabe + "Eigenverbrauchs-Opt.: " + str(Eigen_Opt_Std_neu) + "W geschrieben\n"
                                    Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Opti_Schreib_Ausgabe
                                else:
                                    Opti_Schreib_Ausgabe = Opti_Schreib_Ausgabe + "Eigenverbrauchs-Opt.: " + str(Eigen_Opt_Std_neu) +"W NICHT geschrieben,\nda Option \"optimierung\"  NICHT gesetzt!\n"
                            else:
                                Opti_Schreib_Ausgabe = Opti_Schreib_Ausgabe + "Eigenverbrauchs-Opt.: Keine Änderung!\n"

                            if print_level >= 1:
                                print(Opti_Schreib_Ausgabe)
                    ######## Eigenverbrauchs-Optimierung  ENDE!!!

                    ######## N O T S T R O M R E S E R V E ab hier setzen, wenn eingeschaltet!
                    if  Notstromreserve_steuern >= 1 and Akt_Std > Sonnenuntergang and Akt_Std < Sonnenuntergang+2:
                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< Notstromreserve >>>>>>>>>>>>>"

                        Notstrom_Werte_tmp = json.loads(basics.getVarConf('Notstrom','Notstrom_Werte','str'))
                        Notstrom_Werte = dict(sorted(Notstrom_Werte_tmp.items(), key=lambda item: int(item[0]), reverse=True))
                        Notstromreserve_Min = basics.getVarConf('Notstrom','Notstromreserve_Min','eval')
                        # Notstromreserve_Min kann nicht kleiner 5% sein
                        if Notstromreserve_Min < 5:
                            Notstromreserve_Min = 5
                        Prognose_24H = progladewert.getPrognoseMorgen()[0]/1000
                        # Aktuelle EntladeGrenze_Max und ProgGrenzeMorgen aus Notstrom_Werte ermitteln
                        EntladeGrenze_Max = Notstromreserve_Min
                        ProgGrenzeMorgen = 0
                        for Notstrom_item in Notstrom_Werte: 
                            if Prognose_24H < int(Notstrom_item):
                                EntladeGrenze_Max = int(Notstrom_Werte[Notstrom_item])
                                ProgGrenzeMorgen = int(Notstrom_item)

                        if HYB_BACKUP_RESERVED == None:
                            HYB_BACKUP_RESERVED = request.get_batteries(host_ip, user, password)[2]
                        # Hysterese wenn Notstrom bereits eingeschaltet
                        if HYB_BACKUP_RESERVED == EntladeGrenze_Max:
                            ProgGrenzeMorgen = int(ProgGrenzeMorgen * 1.2)
                        Neu_HYB_BACKUP_RESERVED = Notstromreserve_Min
                        if (Prognose_24H < ProgGrenzeMorgen and Prognose_24H != 0):
                            Neu_HYB_BACKUP_RESERVED = EntladeGrenze_Max
                        # TEST Notstrom ohne Zwangsladung aus dem Netz
                        if Notstromreserve_steuern > 1 and BattStatusProz < Neu_HYB_BACKUP_RESERVED:
                            print ("TEST Notstrom ohne Zwangsladung aus dem Netz")
                            Neu_HYB_BACKUP_RESERVED = int(BattStatusProz)
                            # aber nicht kleiner 5%
                            if Neu_HYB_BACKUP_RESERVED < 5: Neu_HYB_BACKUP_RESERVED = 5
                        if print_level >= 1:
                            print("## NOTSTROMRESERVE ##")
                            print("Prognose nächste 24Std:     ", int(Prognose_24H), "KW")
                            print("ProgGrenze Morgen:   ", ProgGrenzeMorgen, "KW")
                            print("Batteriereserve:     ", HYB_BACKUP_RESERVED, "%")
                            print("Neu_Batteriereserve: ", Neu_HYB_BACKUP_RESERVED, "%")
                            print()

                        Schreib_Ausgabe = ""

                        if (Neu_HYB_BACKUP_RESERVED != HYB_BACKUP_RESERVED):
                            if ('notstrom' in Options):
                                response = request.send_request(http_request_path + 'config/batteries', method='POST', payload ='{"HYB_BACKUP_CRITICALSOC":5,"HYB_BACKUP_RESERVED":'+ str(Neu_HYB_BACKUP_RESERVED) + '}')
                                bereits_geschrieben = 1
                                DEBUG_Ausgabe+="\nDEBUG Meldung Notstromreserve schreiben: " + str(response)
                                Schreib_Ausgabe = Schreib_Ausgabe + str(Neu_HYB_BACKUP_RESERVED) + "% Notstromreserve geschrieben.\n"
                                Push_Schreib_Ausgabe = Push_Schreib_Ausgabe + Schreib_Ausgabe 
                            else:
                                Schreib_Ausgabe = Schreib_Ausgabe + "Notstromreserve NICHT geschrieben, da Option \"notstrom\" NICHT gesetzt!\n"
                        else:
                            Schreib_Ausgabe = Schreib_Ausgabe + "Notstromreserve, NICHTS zu schreiben!!\n"

                        if print_level >= 1:
                            print(Schreib_Ausgabe)

                        DEBUG_Ausgabe+="\nDEBUG <<<<<<<< ENDE ENTLADEBEGRENZUNG >>>>>>>>>>>>>"

                    ######## Notstromreserve setzen, ENDE

    
                    # Wenn Pushmeldung aktiviert und Daten geschrieben an Dienst schicken
                    Push_Message_EIN = basics.getVarConf('messaging','Push_Message_EIN','eval')
                    if (Push_Schreib_Ausgabe != "") and (Push_Message_EIN == 1):
                        Push_Message_Url = basics.getVarConf('messaging','Push_Message_Url','str')
                        apiResponse = requests.post(Push_Message_Url, data=Push_Schreib_Ausgabe.encode(encoding='utf-8'), headers={ "Title": "Meldung Batterieladesteuerung!", "Tags": "sunny,zap" })
                        print("PushMeldung an ", Push_Message_Url, " gesendet.\n")


                    ### LOGGING, Schreibt mit den übergebenen Daten SQlite-Datei
                    ## nur wenn "schreiben" oder "logging" übergeben worden ist
                    sqlall = FUNCTIONS.SQLall.sqlall()
                    Logging_Schreib_Ausgabe = ""
                    if ('logging' in Options):
                        # In die DB werden die liftime Verbrauchszählerstände gespeichert
                        sqlall.save_SQLite('PV_Daten.sqlite', API['AC_Produktion'], API['DC_Produktion'], API['AC_to_DC'], API['Netzverbrauch'], API['Einspeisung'], \
                        API['Batterie_IN'], API['Batterie_OUT'], aktuelleVorhersage, BattStatusProz)
                        Logging_Schreib_Ausgabe = 'In SQLite-Datei gespeichert!'
                    else:
                        Logging_Schreib_Ausgabe = "Logging NICHT gespeichert, da Option \"logging\" NICHT gesetzt!\n" 

                    if print_level >= 1:
                        print(Logging_Schreib_Ausgabe)
                    # LOGGING ENDE



                    #DEBUG ausgeben
                    if print_level >= 2:
                        DEBUG_Ausgabe+= "\nDEBUG\nDEBUG <<<<<< A U S >>>>>>>\n"
                        print(DEBUG_Ausgabe)
                    if print_level >= 1:
                        print("***** ENDE: ", datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),"*****\n")


            except OSError:
                print("Es ist ein Fehler aufgetreten!!!")


        except requests.exceptions.RequestException as e:
            print(datetime.now())
            print(f"Fehler bei der Verbindung: {e}")
            print(">>>>>>>>>> WR offline")

