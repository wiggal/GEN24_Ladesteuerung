import requests
import json
import os.path
import pytz
import time
from pathlib import Path
from datetime import datetime
from functions import loadConfig, loadWeatherData, storeWeatherData, getVarConf

def loadLatestWeatherData():
    url = 'http://www.solarprognose.de/web/solarprediction/api/v1?access-token={}&item={}&id={}&type={}&algorithm={}'.format(accesstoken, item, id, type, algorithm)
    # Hier wieder ABHOLEN EIN
    apiResponse = requests.get(url, timeout=12.50)
    json_data1 = dict(json.loads(apiResponse.text))
    dict_watts = {}
    dict_watts['result'] = {}
    dict_watts['result']['watts'] = {}

    for key, value in json_data1.get('data',{}).items():
        key_neu = str(datetime.fromtimestamp(value[0]))
        dict_watts['result']['watts'][key_neu] = int(value[1]*1000*KW_Faktor)
    return(dict_watts, json_data1)

if __name__ == '__main__':
    config = loadConfig('config.ini')
    # Benoetigte Variablen aus config.ini definieren und auf Zahlen prüfen
    id = getVarConf('solarprognose', 'id', 'eval')
    KW_Faktor = getVarConf('solarprognose', 'KW_Faktor', 'eval')
    dataAgeMaxInMinutes = getVarConf('solarprognose', 'dataAgeMaxInMinutes', 'eval')
    WaitSec = getVarConf('solarprognose', 'WaitSec', 'eval')
    weatherfile = getVarConf('solarprognose', 'weatherfile', 'str')
    accesstoken = getVarConf('solarprognose', 'accesstoken', 'str')
    item = getVarConf('solarprognose', 'item', 'str')
    type = getVarConf('solarprognose', 'type', 'str')
    algorithm = getVarConf('solarprognose', 'algorithm', 'str')

    time.sleep(WaitSec)
    
    format = "%Y-%m-%d %H:%M:%S"    
    now = datetime.now()    
    
    data = loadWeatherData(weatherfile)
    # print(data['messageCreated'])
    dataIsExpired = True
    if (data):
        dateCreated = None
        if (data['messageCreated']):
            dateCreated = datetime.strptime(data['messageCreated'], format)
        
        if (dateCreated):
            diff = now - dateCreated
            dataAgeInMinutes = diff.total_seconds() / 60
            # print(f'[Now: {now}] [Data created:  {dateCreated}] -> age in min: {dataAgeInMinutes}')
            if (dataAgeInMinutes < dataAgeMaxInMinutes):                
                dataIsExpired = False

    if (dataIsExpired):
        data = loadLatestWeatherData()
        if(data[0]['result']['watts'] != {}):
            if not data == "False":
                storeWeatherData(weatherfile, data[0], now)
        else:
            print("Fehler bei Datenanforderung solarprognose.de:")
            print(data[1])
