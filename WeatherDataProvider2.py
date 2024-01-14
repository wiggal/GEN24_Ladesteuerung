from datetime import datetime
import requests
import json
import os.path
import pytz
from pathlib import Path
from functions import loadConfig, loadWeatherData, storeWeatherData, getVarConf

def loadLatestWeatherData(config):
    lat = config['forecast.solar']['lat']
    lon = config['forecast.solar']['lon']
    dec = config['forecast.solar']['dec']
    az = config['forecast.solar']['az']
    kwp = config['forecast.solar']['kwp']
    
    url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
    try:
        apiResponse = requests.get(url, timeout=52.50)
        json_data1 = dict(json.loads(apiResponse.text))
        # Hier werden fuer ein evtl. zweites Feld mit anderer Ausrichtung die Prognosewerte eingearbeitet
        if config['pv.strings']['anzahl'] == '2':
            dict_watts = {}
            dict_watt_hours = {}
            lat = config['forecast.solar2']['lat']
            lon = config['forecast.solar2']['lon']
            dec = config['forecast.solar2']['dec']
            az = config['forecast.solar2']['az']
            kwp = config['forecast.solar2']['kwp']

            url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
            apiResponse2 = requests.get(url, timeout=52.50)
            json_data2 = dict(json.loads(apiResponse2.text))
		
            for key, value in json_data1.get('result',{}).get('watts',{}).items():
                dict_watts[key]=value
            for key, value in json_data2.get('result',{}).get('watts',{}).items():
                dict_watts[key]=dict_watts[key]+value
            for key, value in json_data1.get('result',{}).get('watt_hours',{}).items():
                dict_watt_hours[key]=value
            for key, value in json_data2.get('result',{}).get('watt_hours',{}).items():
                dict_watt_hours[key]=dict_watt_hours[key]+value
            json_data1['result']['watts']=dict_watts
            json_data1['result']['watt_hours']=dict_watt_hours
        return(json_data1)
    except:
        return("False")
        
    
if __name__ == '__main__':
    config = loadConfig('config.ini')
    
    dataAgeMaxInMinutes = getVarConf('forecast.solar','dataAgeMaxInMinutes','eval')
    
    format = "%Y-%m-%d %H:%M:%S"    
    now = datetime.now()    
    
    weatherfile = getVarConf('env','filePathWeatherData','str')
    data = loadWeatherData(weatherfile)
    dataIsExpired = True
    if (data):
        dateCreated = None
        if (data['messageCreated']):
            dateCreated = datetime.strptime(data['messageCreated'], format)
        
        if (dateCreated):
            diff = now - dateCreated
            dataAgeInMinutes = diff.total_seconds() / 60
            if (dataAgeInMinutes < dataAgeMaxInMinutes):                
                print_level = getVarConf('Ladeberechnung','print_level','eval')
                if ( print_level != 0 ):
                    print('forecast.solar: Die Minuten aus "dataAgeMaxInMinutes" ', dataAgeMaxInMinutes ,' Minuten sind noch nicht abgelaufen!!')
                    print(f'[Now: {now}] [Data created:  {dateCreated}] -> age in min: {dataAgeInMinutes}')
                dataIsExpired = False

    if (dataIsExpired):
        data = loadLatestWeatherData(config)
        if data['result'] !=  None:
            if not data == "False":
                storeWeatherData(weatherfile, data, now)
        else:
            print("Fehler bei Datenanforderung api.forecast.solar:")
            print(data)

    
