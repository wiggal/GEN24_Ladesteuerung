from datetime import datetime
import requests
import json
import os.path
import pytz
from pathlib import Path
import FUNCTIONS.functions

def loadLatestWeatherData(config):
    lat = config['forecast.solar']['lat']
    lon = config['forecast.solar']['lon']
    dec = config['forecast.solar']['dec']
    az = config['forecast.solar']['az']
    kwp = config['forecast.solar']['kwp']
    
    try:
        url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
        try:
            apiResponse = requests.get(url, timeout=52.50)
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout von api.forecast.solar")
            exit()
        json_data1 = dict(json.loads(apiResponse.text))
        #print(json_data1, "\n")
        # Hier werden fuer ein evtl. zweites Feld mit anderer Ausrichtung die Prognosewerte eingearbeitet
        # Koordinaten müssen gleich sein, wegen zeitgleichem Sonnenauf- bzw. untergang 
        if config['pv.strings']['anzahl'] == '2':
            dict_watts = {}
            dict_watt_hours = {}
            dec = config['forecast.solar2']['dec']
            az = config['forecast.solar2']['az']
            kwp = config['forecast.solar2']['kwp']

            url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
            try:
                apiResponse2 = requests.get(url, timeout=52.50)
            except requests.exceptions.Timeout:
                print("### ERROR:  Timeout von api.forecast.solar")
                exit()
            json_data2 = dict(json.loads(apiResponse2.text))
            #print(json_data2, "\n")
		
            if isinstance(json_data1['result'], dict) and isinstance(json_data2['result'], dict):
                for key, value in json_data1.get('result',{}).get('watts',{}).items():
                    dict_watts[key]=value
                for key, value in json_data2.get('result',{}).get('watts',{}).items():
                    if( key in dict_watts):
                        dict_watts[key]=dict_watts[key]+value
                for key, value in json_data1.get('result',{}).get('watt_hours',{}).items():
                    dict_watt_hours[key]=value
                for key, value in json_data2.get('result',{}).get('watt_hours',{}).items():
                    if( key in dict_watt_hours):
                        dict_watt_hours[key]=dict_watt_hours[key]+value
                json_data1['result']['watts']=dict_watts
                json_data1['result']['watt_hours']=dict_watt_hours
        return(json_data1)
    except OSError:
        exit()
        
    
if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'weather'])
    dataAgeMaxInMinutes = basics.getVarConf('forecast.solar','dataAgeMaxInMinutes','eval')
    
    format = "%Y-%m-%d %H:%M:%S"    
    now = datetime.now()    
    
    weatherfile = basics.getVarConf('forecast.solar','weatherfile','str')
    data = basics.loadWeatherData(weatherfile)
    dataIsExpired = True
    if (data):
        dateCreated = None
        if (data['messageCreated']):
            dateCreated = datetime.strptime(data['messageCreated'], format)
        
        if (dateCreated):
            diff = now - dateCreated
            dataAgeInMinutes = diff.total_seconds() / 60
            if (dataAgeInMinutes < dataAgeMaxInMinutes):                
                print_level = basics.getVarConf('env','print_level','eval')
                if ( print_level != 0 ):
                    print('forecast.solar: Die Minuten aus "dataAgeMaxInMinutes" ', dataAgeMaxInMinutes ,' Minuten sind noch nicht abgelaufen!!')
                    print(f'[Now: {now}] [Data created:  {dateCreated}] -> age in min: {dataAgeInMinutes}')
                dataIsExpired = False

    if (dataIsExpired):
        data = loadLatestWeatherData(config)
        if isinstance(data['result'], dict):
            if not data == "False":
                basics.storeWeatherData(weatherfile, data, now)
        else:
            print("Fehler bei Datenanforderung api.forecast.solar:")
            print(data)

    
