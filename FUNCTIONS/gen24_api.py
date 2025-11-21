import FUNCTIONS.functions
import requests
import json
import re
        
basics = FUNCTIONS.functions.basics()
sqlall = FUNCTIONS.SQLall.sqlall()

class InverterApi:
    def __init__(self):
        self.dummy = 'dummmy'

    def extract_API_values(self, obj, key_patterns):
        results = {}
        sums = {}

        # Summen vorbereiten
        sum_names = {}
        for entry in key_patterns:
            pattern, sum_flag, *maybe = entry
            if sum_flag:
                clean_pattern = re.sub(r'\[\d+-\d+\]', '', pattern)
                sum_name = "SUM_" + re.sub(r'[^A-Za-z0-9_]', '_', clean_pattern)
                sums[sum_name] = 0
                sum_names[pattern] = sum_name

        def recurse(o, inherited_attributes=None):
            if isinstance(o, dict):
                # attributes aus diesem Knoten merken
                current_attributes = o.get("attributes", {})
                if inherited_attributes:
                    # falls bereits Attribute vom Elternknoten vorhanden → übernehmen
                    merged_attributes = inherited_attributes.copy()
                    merged_attributes.update(current_attributes)
                    current_attributes = merged_attributes

                for k, v in o.items():
                    for entry in key_patterns:
                        pattern, sum_flag, *maybe = entry
                        attr_condition = maybe[0] if maybe else None

                        # Prüfen, ob Attribute passen
                        if attr_condition:
                            attr_key, attr_value = attr_condition
                            if current_attributes.get(attr_key) != attr_value:
                                continue  # passt nicht → nächsten key_pattern prüfen

                        # Key prüfen
                        if re.fullmatch(pattern, k):
                            if sum_flag:
                                sums[sum_names[pattern]] += v
                            else:
                                if k not in results:
                                    results[k] = v
                            break

                    # Rekursion, Attribute weitergeben
                    if isinstance(v, (dict, list)):
                        recurse(v, current_attributes)

            elif isinstance(o, list):
                for item in o:
                    recurse(item, inherited_attributes)

        recurse(obj)
        results.update(sums)
        return results

    # API-Werte lesen unabhängig von den Node-Nummern
    def get_API(self):
        IP = basics.getVarConf('inverter','hostNameOrIp','str')
        gen24url = "http://"+IP+"/components/readable"
        url = requests.get(gen24url)
        data = json.loads(url.text)
        API = {}
        # relevante API-Schlüssel definieren: 
        # schluessel [1-3] bei mehrfachschlussel, True für Summenbildung
        # ("label", "<primary>") = attributes.key, Value zur Identifizierung der Hardware, hier des SM am Stromzähler
        GEN24_API_schluessel = [
            ("nameplate", False),                                                           #BYD
            ("BAT_VALUE_STATE_OF_HEALTH_RELATIVE_U16", False),                              #BYD
            ("BAT_VALUE_STATE_OF_CHARGE_RELATIVE_(U16|F32)", False),                              #BYD  Nur vorhanden, wenn Akku an/standby
            ("SMARTMETER_POWERACTIVE_MEAN_SUM_F64", False, ("label", "<primary>")),         #SM <primary>
            ("SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64", False, ("label", "<primary>")),    #SM <primary>
            ("SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64", False, ("label", "<primary>")),    #SM <primary>
            ("BAT_POWERACTIVE_MEAN_F32", False),                                            #WR   Nur vorhanden, wenn Akku an/standby
            ("BAT_ENERGYACTIVE_ACTIVECHARGE_SUM_01_U64", False),                            #WR
            ("BAT_ENERGYACTIVE_ACTIVEDISCHARGE_SUM_01_U64", False),                         #WR
            ("PV_POWERACTIVE_MEAN_0[1-2]_F32", True),                                       #WR
            ("ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_0[1-3]_U64", True),                        #WR
            ("PV_ENERGYACTIVE_ACTIVE_SUM_0[1-2]_U64", True),                                #WR
            ("ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_0[1-3]_U64", True),                  #WR
            ("PS2.rev-sw", False)                                                           #WR
        ]
        API_result = self.extract_API_values(data, GEN24_API_schluessel)

        try:
            API['Version'] = API_result['PS2.rev-sw']
            # Benötigte Werte mit den geholten API-Werten errechnen und API zuweisen
            # Aktuelle Werte für Prognoseberechung
            # Folgende Werte sind nur vorhanden, wenn Akku an/standby
            # Folgende Werte sind nur vorhanden, wenn Akku an/standby
            try:
                # 1. Versuch: F32 (ab FW 1.39.5-1)
                API['BattStatusProz'] = round(API_result['BAT_VALUE_STATE_OF_CHARGE_RELATIVE_F32'], 1)
            except KeyError:
                try:
                    # 2. Versuch: U16 (bis FW 1.39.5-1)
                    API['BattStatusProz'] = round(API_result['BAT_VALUE_STATE_OF_CHARGE_RELATIVE_U16'], 1)
                except KeyError:
                    # 3. Fallback, wenn Akku komplett offline
                    API['BattStatusProz'] = 5
                    print("*********** Batterie ist evtl. offline, aktueller Ladestand wird auf 5% gesetzt!!! *********")

            try:
                API['aktuelleBatteriePower'] = int(API_result['BAT_POWERACTIVE_MEAN_F32'])
            except:
                API['aktuelleBatteriePower'] = 0
                print("*********** Batterie ist evtl. offline, aktuelle BatteriePower wird auf 0 gesetzt!!! *********")
            attributes_nameplate = json.loads(API_result['nameplate'])
            # Batterikapazität / Zustand der Batterie
            API['BattganzeKapazWatt'] = int(attributes_nameplate['capacity_wh'] * API_result['BAT_VALUE_STATE_OF_HEALTH_RELATIVE_U16']/100)
            API['BattganzeLadeKapazWatt'] = attributes_nameplate['max_power_charge_w']
            API['udc_mittel'] = int((attributes_nameplate['max_udc'] + attributes_nameplate['min_udc'])/2)
            API['BattKapaWatt_akt'] = int((100 - API['BattStatusProz'])/100 * API['BattganzeKapazWatt']) 
            API['aktuelleEinspeisung'] = int(API_result['SMARTMETER_POWERACTIVE_MEAN_SUM_F64'])
            API['aktuellePVProduktion'] = int(API_result['SUM_PV_POWERACTIVE_MEAN_0_F32'])
            # Zählerstände fürs Logging
            API['AC_Produktion'] =  int(API_result['SUM_ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_0_U64']/3600)
            API['DC_Produktion'] =  int(API_result['SUM_PV_ENERGYACTIVE_ACTIVE_SUM_0_U64']/3600)
            API['AC_to_DC']      =  int(API_result['SUM_ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_0_U64']/3600)
            API['Batterie_IN']   =  int(API_result['BAT_ENERGYACTIVE_ACTIVECHARGE_SUM_01_U64']/3600)
            API['Batterie_OUT']  =  int(API_result['BAT_ENERGYACTIVE_ACTIVEDISCHARGE_SUM_01_U64']/3600)
            API['Netzverbrauch'] =  int(API_result['SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64'])
            API['Einspeisung']   =  int(API_result['SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64'])
        except Exception as e:
            print("\nERROR: Ein API-Wert konnte nicht gelesen werden, bitte prüfen!")
            print("Fehlerursache:", e)
            print("\nAPI_URL zur Fehlersuche: ", gen24url)
            print("\nBenötigte Werte:\n", GEN24_API_schluessel)
            print("\nVorhandene Werte:\n", API_result)
            exit()


        # Daten von weiteren GEN24 lesen
        IP_weitere_Gen24 = basics.getVarConf('inverter','IP_weitere_Gen24','str')
        if(IP_weitere_Gen24 != 'no'):
            IP_weitere_Gen24 = IP_weitere_Gen24.replace(" ", "")
            IP_weitere_Gen24 = IP_weitere_Gen24.split(",")
            for weitereIP in IP_weitere_Gen24:
                try:
                    gen24url = "http://"+weitereIP+"/components/readable"
                    url = requests.get(gen24url)
                    data2 = json.loads(url.text)
                    API_result = self.extract_API_values(data2, GEN24_API_schluessel)
                    API['aktuellePVProduktion'] += int(API_result['SUM_PV_POWERACTIVE_MEAN_0_F32'])
                    API['AC_Produktion']        += int(API_result['SUM_ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_0_U64']/3600)
                    API['DC_Produktion']        += int(API_result['SUM_PV_ENERGYACTIVE_ACTIVE_SUM_0_U64']/3600)
                    API['AC_to_DC']             += int(API_result['SUM_ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_0_U64']/3600)
                except Exception as e:
                    print("API von WR", weitereIP, "nicht erreichbar, oder fehlerhaft")
                    print("API_URL zur Fehlersuche: ", gen24url)
                    print("Fehlerursache:", e)

        # Daten von Symos lesen und addieren
        IP_weitere_Symo = basics.getVarConf('inverter','IP_weitere_Symo','str')
        if(IP_weitere_Symo != 'no'):
            IP_weitere_Symo = IP_weitere_Symo.replace(" ", "")
            IP_weitere_Symo = IP_weitere_Symo.split(",")
            SYMO_API_schluessel = [
                ("PowerReal_PAC_Sum", False),
                ("EnergyReal_WAC_Sum_EverSince", False)
            ]
            API_Sym = {}
            API_Sym['aktuellePVProduktion'] = 0
            API_Sym['AC_Produktion'] = 0
            API_Sym['DC_Produktion'] = 0
            for weitereIP in IP_weitere_Symo:
                try:
                    symo_url = "http://"+weitereIP+"/components/readable"
                    url = requests.get(symo_url, timeout=2)
                    data_Sy = json.loads(url.text)
                    API_result = self.extract_API_values(data_Sy, SYMO_API_schluessel)
                    # Benötigte Werte mit den geholten API-Werten API zuweisen
                    API_Sym['aktuellePVProduktion'] += int(API_result['PowerReal_PAC_Sum'])
                    API_Sym['AC_Produktion']        += int(API_result['EnergyReal_WAC_Sum_EverSince'])
                    API_Sym['DC_Produktion']        += int(API_result['EnergyReal_WAC_Sum_EverSince'])
                except Exception as e:
                    print("\nAPI von Symo-WR ", weitereIP, " nicht verfügbar, Ersatz-AC-Wert loggen!")
                    print("Fehlerursache:", e)
                    print("\nAPI_URL zur Fehlersuche: ", symo_url)
                    API['aktuellePVProduktion'] += 0
                    Produktion_MAX_DB = sqlall.getSQLlastProduktion('PV_Daten.sqlite')
                    DB_AC = Produktion_MAX_DB[0]
                    DB_DC = Produktion_MAX_DB[1]
                    Offline_AC_DIFF = ((DB_DC - DB_AC) - (API['DC_Produktion'] - API['AC_Produktion']))
                    print("Offline_AC_DIFF: ", Offline_AC_DIFF)
                    if(Offline_AC_DIFF < 0): Offline_AC_DIFF = 0
                    print("Offline_AC_DIFF nicht kleiner 0: ", Offline_AC_DIFF, "\n")
                    Offline_AC = (DB_AC + Offline_AC_DIFF)
                    API['AC_Produktion'] = Offline_AC
                    API['DC_Produktion'] = DB_DC
                    return(API)

            API['aktuellePVProduktion'] += API_Sym['aktuellePVProduktion']
            API['AC_Produktion'] += API_Sym['AC_Produktion']
            API['DC_Produktion'] += API_Sym['DC_Produktion']


        # Hier individuelles Skript Fremd_API_priv.py aus ADDONS aufrufen und Werte addieren
        import traceback
        try:
            import ADDONS.Fremd_API_priv
            # mit data werden die API-Daten des erste GEN24 übergeben
            API_ADDDON = ADDONS.Fremd_API_priv.get_API(data)
            for key in API:
                if key in API_ADDDON:
                    API[key] += API_ADDDON[key]
        except ModuleNotFoundError:
            # Wenn Modul/Datei fehlt still ignorieren
            pass
        except Exception:
            # Alle anderen Fehler mit Traceback zur Fehlersuche ausgeben
            print("\nERROR: Folgender Fehler ist in ADDONS.Fremd_API_priv.py aufgetreten!!")
            traceback.print_exc()
            print("\n")

        return(API)
    
    if __name__ == "__main__":
        exit()
