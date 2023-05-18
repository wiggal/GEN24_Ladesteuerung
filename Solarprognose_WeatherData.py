from datetime import datetime, timedelta
import requests
import json
import configparser
import os.path
import pytz
import time
from pathlib import Path
from datetime import datetime

def loadConfig():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
    except:
        print('config file not found.')
        exit()
    return config

def loadWeatherData(weatherfile):
    data = None
    weatherfile = Path(weatherfile)
    if weatherfile.is_file():
        with open(weatherfile) as json_file:
            data = json.load(json_file)
    
    return data
    
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
    return(dict_watts)
        
    

def storeWeatherData(config, data, now):
    outFilePath = weatherfile
    out_file = open(outFilePath, "w")
    format = "%Y-%m-%d %H:%M:%S"
    data.update({'messageCreated': datetime.strftime(now, format)})
    json.dump(data, out_file, indent = 6)
    out_file.close()
    
if __name__ == '__main__':
    config = loadConfig()
    # Hier die Variablen eintragen
    weatherfile = config['solarprognose']['weatherfile']
    accesstoken = config['solarprognose']['accesstoken']
    item = config['solarprognose']['item']
    id = eval(config['solarprognose']['id'])
    type = config['solarprognose']['type']
    KW_Faktor = eval(config['solarprognose']['KW_Faktor'])
    algorithm = config['solarprognose']['algorithm']
    dataAgeMaxInMinutes = eval(config['solarprognose']['dataAgeMaxInMinutes'])
    WaitSec = eval(config['solarprognose']['WaitSec'])

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
        if(data['result']['watts'] != {}):
            if not data == "False":
                storeWeatherData(weatherfile, data, now)
    
