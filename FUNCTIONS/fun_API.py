from FUNCTIONS.functions import loadConfig, getVarConf
import requests
import json

# API für die aktuellen Werte zur Berechnung , bei http Zugriff ohne Modbus
def get_API():
    IP = getVarConf('gen24','hostNameOrIp','str')
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

    # Daten von weiteren GEN24 lesen
    IP_weitere_Gen24 = getVarConf('gen24','IP_weitere_Gen24','str')
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

    return(API)

if __name__ == "__main__":
    exit()
