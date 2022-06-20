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
    url = 'http://www.solarprognose.de/web/solarprediction/api/v1?access-token={}&item={}&id={}&type={}'.format(accesstoken, item, id, type)
    # Hier wieder ABHOLEN EIN
    apiResponse = requests.get(url, timeout=12.50)
    json_data1 = dict(json.loads(apiResponse.text))
    #json_data1 = {'preferredNextApiRequestAt': {'secondOfHour': 501, 'epochTimeUtc': 1655633301}, 'status': 0, 'iLastPredictionGenerationEpochTime': 1655629442, 'weather_source_text': 'Kurzfristig (3 Tage): Powered by <a href="https://www.weatherapi.com/" title="Free Weather API">WeatherAPI.com</a> und Langfristig (10 Tage): Powered by <a href="https://www.visualcrossing.com/weather-data" target="_blank">Visual Crossing Weather</a>', 'datalinename': 'Mitterbinder Johann', 'data': {'1655607600': [1655607600, 0, 0], '1655611200': [1655611200, 0.72, 0.72], '1655614800': [1655614800, 2.37, 3.09], '1655618400': [1655618400, 3.71, 6.8], '1655622000': [1655622000, 5.374, 12.174], '1655625600': [1655625600, 7.52, 19.694], '1655629200': [1655629200, 8.383, 28.077], '1655632800': [1655632800, 9.543, 37.62], '1655636400': [1655636400, 9.482, 47.102], '1655640000': [1655640000, 8.846, 55.948], '1655643600': [1655643600, 7.632, 63.58], '1655647200': [1655647200, 5.923, 69.503], '1655650800': [1655650800, 3.96, 73.463], '1655654400': [1655654400, 1.95, 75.413], '1655658000': [1655658000, 0.619, 76.032], '1655661600': [1655661600, 0.223, 76.255], '1655665200': [1655665200, 0, 76.255], '1655690400': [1655690400, 0, 0], '1655694000': [1655694000, 0.264, 0.264], '1655697600': [1655697600, 0.329, 0.593], '1655701200': [1655701200, 1.173, 1.766], '1655704800': [1655704800, 2.12, 3.886], '1655708400': [1655708400, 5.656, 9.542], '1655712000': [1655712000, 3.626, 13.168], '1655715600': [1655715600, 8.052, 21.22], '1655719200': [1655719200, 7.472, 28.692], '1655722800': [1655722800, 6.624, 35.316], '1655726400': [1655726400, 3.567, 38.883], '1655730000': [1655730000, 3.619, 42.502], '1655733600': [1655733600, 4.008, 46.51], '1655737200': [1655737200, 3.35, 49.86], '1655740800': [1655740800, 1.468, 51.328], '1655744400': [1655744400, 0.748, 52.076], '1655748000': [1655748000, 0.309, 52.385], '1655751600': [1655751600, 0, 52.385]}}

    dict_watts = {}
    dict_watts['result'] = {}
    dict_watts['result']['watts'] = {}

    for key, value in json_data1.get('data',{}).items():
        key_neu = str(datetime.fromtimestamp(value[0]))
        dict_watts['result']['watts'][key_neu] = int(value[1]*1000)
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
        if not data == "False":
            storeWeatherData(weatherfile, data, now)
    
