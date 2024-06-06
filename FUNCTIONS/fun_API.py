from FUNCTIONS.functions import loadConfig
import requests
import json

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
