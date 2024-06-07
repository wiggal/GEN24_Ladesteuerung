from FUNCTIONS.functions import loadConfig
import requests
import json

# API für die aktuellen Werte zur Berechnung , bei http Zugriff ohne Modbus
def get_API_aktuell():
    config = loadConfig('config.ini')
    gen24url = "http://"+config['gen24']['hostNameOrIp']+"/components/readable"
    url = requests.get(gen24url)
    text = url.text
    data = json.loads(text)
    API_aktuell = {}
    attributes_nameplate = json.loads(data['Body']['Data']['16580608']['attributes']['nameplate'])
    API_aktuell['BattganzeLadeKapazWatt'] = attributes_nameplate['max_power_charge_w']
    API_aktuell['BattganzeKapazWatt'] = attributes_nameplate['capacity_wh']
    API_aktuell['BattStatusProz'] =    round(data['Body']['Data']['16580608']['channels']['BAT_VALUE_STATE_OF_CHARGE_RELATIVE_U16'], 1)
    API_aktuell['BattKapaWatt_akt'] = int((100 - API_aktuell['BattStatusProz'])/100 * API_aktuell['BattganzeKapazWatt']) 
    API_aktuell['aktuelleEinspeisung'] = int(data['Body']['Data']['16711680']['channels']['SMARTMETER_POWERAPPARENT_MEAN_SUM_F64'])
    API_aktuell['aktuellePVProduktion'] = int(data['Body']['Data']['262144']['channels']['PV_POWERACTIVE_SUM_F64'])
    API_aktuell['aktuelleBatteriePower'] = int(data['Body']['Data']['262144']['channels']['BAT_POWERACTIVE_F64'])
    API_aktuell['BatteryMaxDischargePercent'] = ''
    return(API_aktuell)

# API fürs Logging
def get_API():
    config = loadConfig('config.ini')
    gen24url = "http://"+config['gen24']['hostNameOrIp']+"/components/readable"
    url = requests.get(gen24url)
    text = url.text
    data = json.loads(text)
    API = {}
    API['AC_Produktion'] =  int(data['Body']['Data']['327680']['channels']['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_U64']/3600)
    API['DC_Produktion'] = int((data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_01_U64']+ data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_02_U64'])/3600)
    API['Batterie_IN'] =    int(data['Body']['Data']['393216']['channels']['BAT_ENERGYACTIVE_ACTIVECHARGE_SUM_01_U64']/3600)
    API['Batterie_OUT'] =   int(data['Body']['Data']['393216']['channels']['BAT_ENERGYACTIVE_ACTIVEDISCHARGE_SUM_01_U64']/3600)
    API['Netzverbrauch'] =  int(data['Body']['Data']['16252928']['channels']['SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64'])
    API['Einspeisung'] =    int(data['Body']['Data']['16252928']['channels']['SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64'])
    return(API)

        
if __name__ == "__main__":
    exit()
