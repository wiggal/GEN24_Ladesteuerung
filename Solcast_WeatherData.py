from datetime import datetime, timedelta
import requests
import json
import configparser
import os.path
import pytz
import time
from pathlib import Path
from datetime import datetime

exit ()

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
    url = 'https://api.solcast.com.au/rooftop_sites/{}/forecasts?format=json&api_key={}'.format(resource_id, api_key)
    # Hier wieder ABHOLEN EIN
    apiResponse = requests.get(url, timeout=12.50)
    json_data1 = dict(json.loads(apiResponse.text))
    format = "%Y-%m-%d %H:%M:%S"
    dict_watts = {}
    dict_watts['result'] = {}
    dict_watts['result']['watts'] = {}

    #wenn zuviele Zugriffe
    try:
        istda = json_data1['response_status']['error_code']
    except:
        print("ERROR: " + json_data1['response_status']['error_code'])
        exit()

    Puffer = ['2000-01-01',5]
    for forecasts in json_data1['forecasts']:
        key_neu_1 = (forecasts['period_end'][:19]).replace('T',' ',1)
        if '00:00' in key_neu_1:
            key_neu = datetime.strftime(datetime.strptime(key_neu_1, format) + timedelta(hours=Zeitzone), format)
            #SPO hier NULLEN weg
            if (forecasts['pv_estimate'] == 0):
                if (Puffer[1] == 0):
                    Puffer = [key_neu, int(forecasts['pv_estimate']*1000*KW_Faktor)]
                    continue
                else:
                    Puffer = [key_neu, int(forecasts['pv_estimate']*1000*KW_Faktor)]
                    dict_watts['result']['watts'][key_neu] = int(forecasts['pv_estimate']*1000*KW_Faktor)
                    continue
            else:
                if (Puffer[1] == 0):
                    dict_watts['result']['watts'][Puffer[0]] = Puffer[1]
                Puffer = [key_neu, int(forecasts['pv_estimate']*1000*KW_Faktor)]
                dict_watts['result']['watts'][key_neu] = int(forecasts['pv_estimate']*1000*KW_Faktor)

    return(dict_watts, json_data1)

def storeWeatherData(wetterfile, data, now):
    outFilePath = wetterfile
    out_file = open(outFilePath, "w")
    format = "%Y-%m-%d %H:%M:%S"
    data.update({'messageCreated': datetime.strftime(now, format)})
    json.dump(data, out_file, indent = 6)
    out_file.close()
    
if __name__ == '__main__':
    config = loadConfig()
    # Benoetigte Variablen aus config.ini definieren und auf Zahlen prüfen
    config_eval_vars = [
                            ['dataAgeMaxInMinutes','solcast.com','dataAgeMaxInMinutes'],
                            ['Zeitzone','solcast.com','Zeitzone'],
                            ['KW_Faktor','solcast.com','KW_Faktor'],
                        ]
    for i in config_eval_vars:
         try:
             locals()[i[0]] = eval(config[i[1]][i[2]])
         except:
             print("ERROR: die Variable [" + i[1] + "][" + i[2] + "] wurde nicht als Zahl definiert!")
             exit()

    # Restliche Variablen aus config.ini prüfen ob vorhanden und definieren
    config_str_vars = [
                            ['weatherfile','solcast.com','weatherfile'],
                            ['api_key','solcast.com','api_key'],
                            ['resource_id','solcast.com','resource_id'],
                        ]
    for i in config_str_vars:
         try:
             locals()[i[0]] = str(config[i[1]][i[2]])
         except:
             print("ERROR: die Variable [" + i[1] + "][" + i[2] + "] wurde in der config.ini NICHT definiert!")
             exit()

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
            if (dataAgeInMinutes < dataAgeMaxInMinutes):                
                dataIsExpired = False

    if (dataIsExpired):
        data = loadLatestWeatherData()
        if(data[0]['result']['watts'] != {}):
            if not data == "False":
                storeWeatherData(weatherfile, data[0], now)
        else:
            print("Fehler bei Datenanforderung api.solcast.com.au:")
            print(data[1])
