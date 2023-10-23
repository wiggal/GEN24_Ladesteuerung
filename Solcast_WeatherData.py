import requests
import json
import os.path
import pytz
import time
from pathlib import Path
from datetime import datetime, timedelta
from functions import loadConfig, loadWeatherData, storeWeatherData, getVarConf

def loadLatestWeatherData():
    # Varablen definieren
    format = "%Y-%m-%d %H:%M:%S"
    dict_watts = {}
    dict_watts['result'] = {}
    dict_watts['result']['watts'] = {}
    heute = datetime.strftime(now, "%Y-%m-%d")
    morgen = datetime.strftime(now + timedelta(days=1), "%Y-%m-%d")

    #die Daten müssen 2x abgerufen werden forecasts (Zukunft) und estimated_actuals (aktuell und Vergangenheit 
    for datenloop in ["estimated_actuals","forecasts"]:

        try:
            url = 'https://api.solcast.com.au/rooftop_sites/{}/{}?format=json&api_key={}'.format(resource_id, datenloop, api_key)
            # Hier wieder ABHOLEN EIN
            apiResponse = requests.get(url, timeout=15.50)
            json_data1 = dict(json.loads(apiResponse.text))
    
            try:
                # wenn zuviele Zugriffe
                istda = json_data1['response_status']['error_code']
                return(dict_watts, json_data1)
            except:
        
                Puffer = ['2000-01-01',5]
                try:
                    for wetterwerte in json_data1[datenloop]:
                        key_neu_1 = (wetterwerte['period_end'][:19]).replace('T',' ',1)
                        if ('00:00' in key_neu_1 and (heute in key_neu_1 or morgen in key_neu_1)):
                            key_neu = datetime.strftime(datetime.strptime(key_neu_1, format) + timedelta(hours=Zeitzone), format)
                            #hier Werte mit NULLEN weg
                            if (wetterwerte['pv_estimate'] == 0):
                                if (Puffer[1] == 0):
                                    Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor)]
                                    continue
                                else:
                                    Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor)]
                                    dict_watts['result']['watts'][key_neu] = int(wetterwerte['pv_estimate']*1000*KW_Faktor)
                                    continue
                            else:
                                if (Puffer[1] == 0):
                                    dict_watts['result']['watts'][Puffer[0]] = Puffer[1]
                                Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor)]
                                dict_watts['result']['watts'][key_neu] = int(wetterwerte['pv_estimate']*1000*KW_Faktor)
                except:
                    continue
        except requests.exceptions.RequestException as error:
            json_data1 = error

    
    #solcast_2.json Nun wieder nach Datum und Stunden sortieren
    dict_watts['result']['watts'] = dict(sorted(dict_watts['result']['watts'].items()))
    return(dict_watts, json_data1)

if __name__ == '__main__':
    config = loadConfig('config.ini')
    # Benoetigte Variablen aus config.ini definieren und prüfen
    dataAgeMaxInMinutes = getVarConf('solcast.com', 'dataAgeMaxInMinutes', 'eval')
    Zeitzone = getVarConf('solcast.com', 'Zeitzone', 'eval')
    KW_Faktor = getVarConf('solcast.com', 'KW_Faktor', 'eval')
    weatherfile = getVarConf('solcast.com', 'weatherfile', 'str')
    api_key = getVarConf('solcast.com', 'api_key', 'str')
    resource_id = getVarConf('solcast.com', 'resource_id', 'str')
    
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
