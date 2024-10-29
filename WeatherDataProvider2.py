from datetime import datetime
import requests
import json
import os.path
import pytz
from pathlib import Path
import FUNCTIONS.functions

def loadLatestWeatherData():
    lat = basics.getVarConf('forecast.solar','lat','eval')
    lon = basics.getVarConf('forecast.solar','lon','eval')
    dec = basics.getVarConf('forecast.solar','dec','eval')
    az = basics.getVarConf('forecast.solar','az','eval')
    kwp = basics.getVarConf('forecast.solar','kwp','eval')
    anzahl_strings = basics.getVarConf('pv.strings','anzahl','eval')
    
    try:
        url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
        try:
            apiResponse = requests.get(url, timeout=52.50)
            apiResponse.raise_for_status()
            if apiResponse.status_code != 204:
                json_data1 = dict(json.loads(apiResponse.text))
            else:
                print("### ERROR:  Keine forecasts-Daten von api.forecast.solar")
                exit()
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout von api.forecast.solar")
            exit()
        #print(json_data1, "\n")
        # Hier werden fuer ein evtl. zweites Feld mit anderer Ausrichtung die Prognosewerte eingearbeitet
        # Koordinaten müssen gleich sein, wegen zeitgleichem Sonnenauf- bzw. untergang 
        if anzahl_strings == 2:
            dict_watts = {}
            dict_watt_hours = {}
            dec = basics.getVarConf('forecast.solar2','dec','eval')
            az = basics.getVarConf('forecast.solar2','az','eval')
            kwp = basics.getVarConf('forecast.solar2','kwp','eval')

            url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
            try:
                apiResponse2 = requests.get(url, timeout=52.50)
                apiResponse2.raise_for_status()
                if apiResponse2.status_code != 204:
                    json_data2 = dict(json.loads(apiResponse2.text))
                else:
                    print("### ERROR:  Keine estimated_actuals-Daten von api.forecast.solar")
                    exit()
            except requests.exceptions.Timeout:
                print("### ERROR:  Timeout von api.forecast.solar")
                exit()
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
        data = loadLatestWeatherData()
        if isinstance(data['result'], dict):
            if not data == "False":
                database = basics.getVarConf('Logging','Logging_file','str')
                MaximalPrognosebegrenzung = basics.getVarConf('env','MaximalPrognosebegrenzung','eval')
                if (MaximalPrognosebegrenzung == 1):
                    data = basics.checkMaxPrognose(data, database)
                basics.storeWeatherData(weatherfile, data, now, 'forecast.solar')
        else:
            print("Fehler bei Datenanforderung api.forecast.solar:")
            print(data)

    
