import FUNCTIONS.functions
import requests
import json
        
basics = FUNCTIONS.functions.basics()
sqlall = FUNCTIONS.SQLall.sqlall()

class gen24api:
    def __init__(self):
        self.dummy = 'dummmy'

    def extract_API_values(self, obj, keys):
        """
        Durchsucht obj nach den Schlüsseln aus 'keys' und gibt ein dict zurück.
        """
        results = {}
        def recurse(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in keys:
                        results[k] = v
                    if isinstance(v, (dict, list)):
                        recurse(v)
            elif isinstance(o, list):
                for item in o:
                    recurse(item)

        recurse(obj)
        return results

    # API-Werte lesen unabhängig von den Node-Nummern
    def get_API(self):
        IP = basics.getVarConf('gen24','hostNameOrIp','str')
        gen24url = "http://"+IP+"/components/readable"
        url = requests.get(gen24url)
        data = json.loads(url.text)
        API = {}
        # "393216 OR 0 -  channels - BAT_MODE_ENFORCED_U16" : 2.0, AKKU AUS
        # "393216 OR 0 -  channels - BAT_MODE_ENFORCED_U16" : 0.0, AKKU EIN
        # relevante API-Schlüssel definieren
        GEN24_API_schluessel = [
            "BAT_MODE_ENFORCED_U16",
            "nameplate",
            "BAT_VALUE_STATE_OF_HEALTH_RELATIVE_U16",
            "BAT_VALUE_STATE_OF_CHARGE_RELATIVE_U16",
            "SMARTMETER_POWERACTIVE_MEAN_SUM_F64",
            "PV_POWERACTIVE_MEAN_01_F32",
            "PV_POWERACTIVE_MEAN_02_F32",
            "BAT_POWERACTIVE_MEAN_F32",
            "ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_01_U64",
            "ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_02_U64",
            "ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_03_U64",
            "PV_ENERGYACTIVE_ACTIVE_SUM_01_U64",
            "PV_ENERGYACTIVE_ACTIVE_SUM_02_U64",
            "ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_01_U64",
            "ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_02_U64",
            "ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_03_U64",
            "BAT_ENERGYACTIVE_ACTIVECHARGE_SUM_01_U64",
            "BAT_ENERGYACTIVE_ACTIVEDISCHARGE_SUM_01_U64",
            "SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64",
            "SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64"
        ]
        API_result = self.extract_API_values(data, GEN24_API_schluessel)

        API['BAT_MODE'] = API_result['BAT_MODE_ENFORCED_U16']
        if API['BAT_MODE'] != 2:
            # Benötigte Werte mit den geholten API-Werten rechnen und API zuweisen
            # Aktuelle Werte für Prognoseberechung
            attributes_nameplate = json.loads(API_result['nameplate'])
            API['BattganzeKapazWatt'] = int(attributes_nameplate['capacity_wh'])
            API['BattganzeLadeKapazWatt'] = attributes_nameplate['max_power_charge_w']
            API['udc_mittel'] = int((attributes_nameplate['max_udc'] + attributes_nameplate['min_udc'])/2)
            API['BattStatusProz'] =    round(API_result['BAT_VALUE_STATE_OF_CHARGE_RELATIVE_U16'], 1)
            API['BattKapaWatt_akt'] = int((100 - API['BattStatusProz'])/100 * API['BattganzeKapazWatt']) 
            API['aktuelleEinspeisung'] = int(API_result['SMARTMETER_POWERACTIVE_MEAN_SUM_F64'])
            # PV_POWERACTIVE_MEAN_02_F32 existiert nicht, wenn nur ein String am GEN24 hängt
            try:
                API_STRING2 = API_result['PV_POWERACTIVE_MEAN_02_F32']
            except:
                API_STRING2 = 0
            API['aktuellePVProduktion'] = int(API_result['PV_POWERACTIVE_MEAN_01_F32'] + API_STRING2)
            API['aktuelleBatteriePower'] = int(API_result['BAT_POWERACTIVE_MEAN_F32'])
            # Zählerstände fürs Logging
            API['AC_Produktion'] =  int((API_result['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_01_U64']+API_result['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_02_U64']+\
                                         API_result['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_03_U64'])/3600)
            API['DC_Produktion'] =  int((API_result['PV_ENERGYACTIVE_ACTIVE_SUM_01_U64']+ API_result['PV_ENERGYACTIVE_ACTIVE_SUM_02_U64'])/3600)
            API['AC_to_DC'] = int((API_result['ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_01_U64'] +\
                                   API_result['ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_02_U64'] +\
                                   API_result['ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_03_U64'])/3600)
            API['Batterie_IN'] =    int(API_result['BAT_ENERGYACTIVE_ACTIVECHARGE_SUM_01_U64']/3600)
            API['Batterie_OUT'] =   int(API_result['BAT_ENERGYACTIVE_ACTIVEDISCHARGE_SUM_01_U64']/3600)
            API['Netzverbrauch'] =  int(API_result['SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64'])
            API['Einspeisung'] =    int(API_result['SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64'])


        # Daten von weiteren GEN24 lesen
        IP_weitere_Gen24 = basics.getVarConf('gen24','IP_weitere_Gen24','str')
        if(IP_weitere_Gen24 != 'no'):
            IP_weitere_Gen24 = IP_weitere_Gen24.replace(" ", "")
            IP_weitere_Gen24 = IP_weitere_Gen24.split(",")
            for weitereIP in IP_weitere_Gen24:
                try:
                    gen24url = "http://"+weitereIP+"/components/readable"
                    url = requests.get(gen24url)
                    data = json.loads(url.text)
                    API_result = self.extract_API_values(data, GEN24_API_schluessel)
                    # PV_POWERACTIVE_MEAN_02_F32 existiert nicht, wenn nur ein String am GEN24 hängt
                    try:
                        API_STRING2 = API_result['PV_POWERACTIVE_MEAN_02_F32']
                    except:
                        API_STRING2 = 0
                    API['aktuellePVProduktion'] += int( API_result['PV_POWERACTIVE_MEAN_01_F32'] + API_STRING2)
                    API['AC_Produktion']        += int((API_result['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_01_U64']+API_result['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_02_U64']+\
                                                        API_result['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_03_U64'])/3600)
                    API['DC_Produktion']        += int((API_result['PV_ENERGYACTIVE_ACTIVE_SUM_01_U64']+ API_result['PV_ENERGYACTIVE_ACTIVE_SUM_02_U64'])/3600)
                    API['AC_to_DC']             += int((API_result['ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_01_U64'] +\
                                                        API_result['ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_02_U64'] +\
                                                        API_result['ACBRIDGE_ENERGYACTIVE_ACTIVECONSUMED_SUM_03_U64'])/3600)
                except:
                    print("API von WR ", weitereIP, " nicht erreichbar")

        # Daten von Symos lesen und addieren
        IP_weitere_Symo = basics.getVarConf('gen24','IP_weitere_Symo','str')
        if(IP_weitere_Symo != 'no'):
            IP_weitere_Symo = IP_weitere_Symo.replace(" ", "")
            IP_weitere_Symo = IP_weitere_Symo.split(",")
            SYMO_API_schluessel = [
                "PowerReal_PAC_Sum",
                "EnergyReal_WAC_Sum_EverSince"
            ]
            API_Sym = {}
            API_Sym['aktuellePVProduktion'] = 0
            API_Sym['AC_Produktion'] = 0
            API_Sym['DC_Produktion'] = 0
            for weitereIP in IP_weitere_Symo:
                try:
                    gen24url = "http://"+weitereIP+"/components/readable"
                    url = requests.get(gen24url, timeout=2)
                    data = json.loads(url.text)
                    API_result = self.extract_API_values(data, SYMO_API_schluessel)
                    # Benötigte Werte mit den geholten API-Werten API zuweisen
                    API_Sym['aktuellePVProduktion'] += int(API_result['PowerReal_PAC_Sum'])
                    API_Sym['AC_Produktion'] +=  int(API_result['EnergyReal_WAC_Sum_EverSince'])
                    API_Sym['DC_Produktion'] += int(API_result['EnergyReal_WAC_Sum_EverSince'])
                except:
                    print("API von Symo-WR ", weitereIP, " nicht verfügbar, Ersatz-AC-Wert loggen!")
                    API['aktuellePVProduktion'] += 0
                    Produktion_MAX_DB = sqlall.getSQLlastProduktion('PV_Daten.sqlite')
                    DB_AC = Produktion_MAX_DB[0]
                    DB_DC = Produktion_MAX_DB[1]
                    Offline_AC_DIFF = ((DB_DC - DB_AC) - (API['DC_Produktion'] - API['AC_Produktion']))
                    print("Offline_AC_DIFF: ", Offline_AC_DIFF)
                    if(Offline_AC_DIFF < 0): Offline_AC_DIFF = 0
                    print("Offline_AC_DIFF nicht kleiner 0: ", Offline_AC_DIFF)
                    Offline_AC = (DB_AC + Offline_AC_DIFF)
                    #print(DB_DC, Offline_AC, API['DC_Produktion'], API['AC_Produktion'])
                    API['AC_Produktion'] = Offline_AC
                    API['DC_Produktion'] = DB_DC
                    return(API)

            API['aktuellePVProduktion'] += API_Sym['aktuellePVProduktion']
            API['AC_Produktion'] += API_Sym['AC_Produktion']
            API['DC_Produktion'] += API_Sym['DC_Produktion']


        return(API)
    
    if __name__ == "__main__":
        exit()
