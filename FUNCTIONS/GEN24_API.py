import FUNCTIONS.functions
import requests
import json
import sqlite3
        
basics = FUNCTIONS.functions.basics()
sqlall = FUNCTIONS.SQLall.sqlall()

class gen24api:
    def __init__(self):
        self.now = datetime.now()

    # API für die aktuellen Werte zur Berechnung , bei http Zugriff ohne Modbus
    def get_API():
        IP = basics.getVarConf('gen24','hostNameOrIp','str')
        gen24url = "http://"+IP+"/components/readable"
        url = requests.get(gen24url)
        text = url.text
        data = json.loads(text)
        API = {}
        # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 2.0, AKKU AUS
        # "393216 -  channels - BAT_MODE_ENFORCED_U16" : 0.0, AKKU EIN
        API['BAT_MODE'] = data['Body']['Data']['393216']['channels']['BAT_MODE_ENFORCED_U16'] 
        if API['BAT_MODE'] != 2:
            # Aktuelle Werte für Prognoseberechung
            attributes_nameplate = json.loads(data['Body']['Data']['16580608']['attributes']['nameplate'])
            # BattganzeKapazWatt * Akku_Zustand
            Akku_Zustand = data['Body']['Data']['16580608']['channels']['BAT_VALUE_STATE_OF_HEALTH_RELATIVE_U16'] / 100
            API['BattganzeKapazWatt'] = int(attributes_nameplate['capacity_wh'] * Akku_Zustand)
            API['BattganzeLadeKapazWatt'] = attributes_nameplate['max_power_charge_w']
            API['BattStatusProz'] =    round(data['Body']['Data']['16580608']['channels']['BAT_VALUE_STATE_OF_CHARGE_RELATIVE_U16'], 1)
            API['BattKapaWatt_akt'] = int((100 - API['BattStatusProz'])/100 * API['BattganzeKapazWatt']) 
            API['aktuelleEinspeisung'] = int(data['Body']['Data']['16252928']['channels']['SMARTMETER_POWERACTIVE_MEAN_SUM_F64'])
            API['aktuellePVProduktion'] = int(data['Body']['Data']['262144']['channels']['PV_POWERACTIVE_SUM_F64'])
            API['aktuelleBatteriePower'] = int(data['Body']['Data']['262144']['channels']['BAT_POWERACTIVE_F64'])
            API['BatteryMaxDischargePercent'] = ''
            # Zählerstände fürs Logging
            API['AC_Produktion'] =  int(data['Body']['Data']['327680']['channels']['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_U64']/3600)
            API['DC_Produktion'] =  int((data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_01_U64']+ data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_02_U64'])/3600)
            API['Batterie_IN'] =    int(data['Body']['Data']['393216']['channels']['BAT_ENERGYACTIVE_ACTIVECHARGE_SUM_01_U64']/3600)
            API['Batterie_OUT'] =   int(data['Body']['Data']['393216']['channels']['BAT_ENERGYACTIVE_ACTIVEDISCHARGE_SUM_01_U64']/3600)
            API['Netzverbrauch'] =  int(data['Body']['Data']['16252928']['channels']['SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64'])
            API['Einspeisung'] =    int(data['Body']['Data']['16252928']['channels']['SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64'])
            #print("AC_Produktion, DC_Produktion ORG: ", API['AC_Produktion'], API['DC_Produktion'])
    
        # Daten von weiteren GEN24 lesen
        IP_weitere_Gen24 = basics.getVarConf('gen24','IP_weitere_Gen24','str')
        if(IP_weitere_Gen24 != 'no'):
            IP_weitere_Gen24 = IP_weitere_Gen24.replace(" ", "")
            IP_weitere_Gen24 = IP_weitere_Gen24.split(",")
            for weitereIP in IP_weitere_Gen24:
                try:
                    gen24url = "http://"+weitereIP+"/components/readable"
                    url = requests.get(gen24url)
                    text = url.text
                    data = json.loads(text)
                    API['aktuellePVProduktion'] += int(data['Body']['Data']['262144']['channels']['PV_POWERACTIVE_SUM_F64'])
                    API['AC_Produktion'] +=  int(data['Body']['Data']['327680']['channels']['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_U64']/3600)
                    API['DC_Produktion'] += int((data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_01_U64']+ data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_02_U64'])/3600)
                except:
                    print("API von WR ", weitereIP, " nicht erreichbar")
    
        # Daten von Symos lesen und addieren
        IP_weitere_Symo = basics.getVarConf('gen24','IP_weitere_Symo','str')
        if(IP_weitere_Symo != 'no'):
            IP_weitere_Symo = IP_weitere_Symo.replace(" ", "")
            IP_weitere_Symo = IP_weitere_Symo.split(",")
            for weitereIP in IP_weitere_Symo:
                try:
                    gen24url = "http://"+weitereIP+"/components/readable"
                    url = requests.get(gen24url, timeout=2)
                    text = url.text
                    data = json.loads(text)
                    #data = basics.loadWeatherData('Fronius_MrFrees.json')
                    API['aktuellePVProduktion'] += int(data['Body']['Data']['262144']['channels']['PowerReal_PAC_Sum'])
                    API['AC_Produktion'] +=  int(data['Body']['Data']['262144']['channels']['EnergyReal_WAC_Sum_EverSince'])
                    API['DC_Produktion'] += int(data['Body']['Data']['262144']['channels']['EnergyReal_WAC_Sum_EverSince'])
                except:
                    print("API von WR ", weitereIP, " nicht erreichbar, Ersatz AC-Wert schreiben!")
                    API['aktuellePVProduktion'] += 0
                    Produktion_MAX_DB = sqlall.getSQLlastProduktion('PV_Daten.sqlite')
                    #print("Produktion_MAX_DB: ", Produktion_MAX_DB, Produktion_MAX_DB[1] - Produktion_MAX_DB[0])
                    #print("aktuelle Diff DC-AC: ", API['DC_Produktion'] - API['AC_Produktion'] )
                    #print(" Ergebinis: ", (API['DC_Produktion'] - API['AC_Produktion']) - (Produktion_MAX_DB[1] - Produktion_MAX_DB[0]))
                    #print("Neuer AC-WERT: ", (API['DC_Produktion'] - API['AC_Produktion']) - (Produktion_MAX_DB[1] - Produktion_MAX_DB[0]) + Produktion_MAX_DB[0])
                    Offline_AC = ((API['DC_Produktion'] - API['AC_Produktion']) - (Produktion_MAX_DB[1] - Produktion_MAX_DB[0]) + Produktion_MAX_DB[0])
                    API['AC_Produktion'] = Offline_AC
                    API['DC_Produktion'] = Offline_AC


        return(API)
    
    if __name__ == "__main__":
        exit()
