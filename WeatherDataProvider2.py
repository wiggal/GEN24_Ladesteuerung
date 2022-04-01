from datetime import datetime, timedelta
#from dateutil import parser
import pickledb
import requests
import json
import configparser
import os.path
import pytz
from pathlib import Path

def loadConfig():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
    except:
        print('config file not found.')
        exit()
    return config
    
def loadWeatherData(config):
    data = None
    weatherfile = Path(config['env']['filePathWeatherData'])
    if weatherfile.is_file():
        with open(config['env']['filePathWeatherData']) as json_file:
            data = json.load(json_file)
    
    return data
    
def loadLatestWeatherData(config):
    lat = config['forecast.solar']['lat']
    lon = config['forecast.solar']['lon']
    dec = config['forecast.solar']['dec']
    az = config['forecast.solar']['az']
    kwp = config['forecast.solar']['kwp']
    #apiKey = config['forecast.solar']['api_key']
    
    url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
    try:
        apiResponse = requests.get(url, timeout=2.50)
        return dict(json.loads(apiResponse.text))
    except:
        return("False")
        
    

def storeWeatherData(config, data, now):
    outFilePath = config['env']['filePathWeatherData']
    out_file = open(outFilePath, "w")
    format = "%Y-%m-%d %H:%M:%S"
    data.update({'messageCreated': datetime.strftime(now, format)})
    json.dump(data, out_file, indent = 6)
    out_file.close()
    
if __name__ == '__main__':
    config = loadConfig()
    # db = pickledb.load(config['env']['filePathConfigDb'], True)
    
    #tzConfig = pytz.timezone(config['env']['timezone'])    
    dataAgeMaxInMinutes = float(config['forecast.solar']['dataAgeMaxInMinutes'])
    
    #print(f'Timezone: {tzConfig}')
    
    format = "%Y-%m-%d %H:%M:%S"    
    now = datetime.now()    
    
    data = loadWeatherData(config)
    #print(data['message'])
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
        data = loadLatestWeatherData(config)
        if not data == "False":
            storeWeatherData(config, data, now)
    
