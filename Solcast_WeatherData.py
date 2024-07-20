import requests
import json
import os.path
import pytz
import time
from pathlib import Path
from datetime import datetime, timedelta
from FUNCTIONS.functions import loadConfig, loadWeatherData, storeWeatherData, getVarConf

def loadLatestWeatherData():
    # Varablen definieren
    format = "%Y-%m-%d %H:%M:%S"
    dict_watts = {}
    dict_watts['result'] = {}
    dict_watts['result']['watts'] = {}
    heute = datetime.strftime(now, "%Y-%m-%d")
    morgen = datetime.strftime(now + timedelta(days=1), "%Y-%m-%d")
    sommerzeit = time.localtime().tm_isdst

    Abfragebereich = ['forecasts', 'estimated_actuals']
    # Wenn no_history == 1 nur forecasts abrufen
    if no_history == 1:
        Abfragebereich = ['forecasts']

    #die Daten müssen 2x abgerufen werden forecasts (Zukunft) und estimated_actuals (aktuell und Vergangenheit 
    for datenloop in Abfragebereich:

        try:
            url = 'https://api.solcast.com.au/rooftop_sites/{}/{}?format=json&api_key={}'.format(resource_id, datenloop, api_key)
            # Hier wieder ABHOLEN EIN
            try:
                apiResponse = requests.get(url, timeout=99.50)
                json_data1 = dict(json.loads(apiResponse.text))
            except requests.exceptions.Timeout:
                print("### ERROR:  Timeout von api.solcast.com.au")
                exit()
            
            if Strings == 2:
                url = 'https://api.solcast.com.au/rooftop_sites/{}/{}?format=json&api_key={}'.format(resource_id2, datenloop, api_key)
                try:
                    apiResponse2 = requests.get(url, timeout=99.50)
                    json_data2 = dict(json.loads(apiResponse2.text))
                except requests.exceptions.Timeout:
                    print("### ERROR:  Timeout von api.solcast.com.au")
                    exit()
                
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
                            key_neu = datetime.strftime(datetime.strptime(key_neu_1, format) + timedelta(hours=Zeitzone+sommerzeit), format)
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
                
                if Strings == 2:
                    Puffer = ['2000-01-01',5]
                    try:
                        for wetterwerte in json_data2[datenloop]:
                            key_neu_1 = (wetterwerte['period_end'][:19]).replace('T',' ',1)
                            if ('00:00' in key_neu_1 and (heute in key_neu_1 or morgen in key_neu_1)):
                                key_neu = datetime.strftime(datetime.strptime(key_neu_1, format) + timedelta(hours=Zeitzone+sommerzeit), format)
                                #hier Werte mit NULLEN weg
                                if (wetterwerte['pv_estimate'] == 0):
                                    if (Puffer[1] == 0):
                                        Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor2)]
                                        continue
                                    else:
                                        Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor2)]
                                        dict_watts['result']['watts'][key_neu] = dict_watts['result']['watts'][key_neu] + int(wetterwerte['pv_estimate']*1000*KW_Faktor2)
                                        continue
                                else:
                                    if (Puffer[1] == 0):
                                        dict_watts['result']['watts'][Puffer[0]] = Puffer[1]
                                    Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor2)]
                                    dict_watts['result']['watts'][key_neu] = dict_watts['result']['watts'][key_neu] + int(wetterwerte['pv_estimate']*1000*KW_Faktor2)
                    except:
                        continue
                
        except requests.exceptions.RequestException as error:
            json_data1 = error

    
    # Wenn no_history == 1 historische Daten aus weatherData.json holen
    if no_history == 1:
        try:
            with open(weatherfile, 'r') as datei:
                json_data_old = json.load(datei)
                #print(json_data_old)

            for wetterwerte_old in json_data_old['result']['watts']:
                if heute in wetterwerte_old and wetterwerte_old not in dict_watts['result']['watts']:
                    dict_watts['result']['watts'][wetterwerte_old] = int(json_data_old['result']['watts'][wetterwerte_old])
                    #print (wetterwerte_old)
        except:
            print("Fehler beim Lesen von ", weatherfile)



    #solcast_2.json Nun wieder nach Datum und Stunden sortieren
    dict_watts['result']['watts'] = dict(sorted(dict_watts['result']['watts'].items()))
    return(dict_watts, json_data1)

if __name__ == '__main__':
    config = loadConfig(['default', 'weather'])
    # Benoetigte Variablen definieren und prüfen
    Strings = getVarConf('pv.strings', 'anzahl', 'eval')
    dataAgeMaxInMinutes = getVarConf('solcast.com', 'dataAgeMaxInMinutes', 'eval')
    Zeitzone = getVarConf('solcast.com', 'Zeitzone', 'eval')
    no_history = getVarConf('solcast.com', 'no_history', 'eval')
    KW_Faktor = getVarConf('solcast.com2', 'KW_Faktor', 'eval')
    KW_Faktor2 = getVarConf('solcast.com', 'KW_Faktor', 'eval')
    weatherfile = getVarConf('solcast.com', 'weatherfile', 'str')
    api_key = getVarConf('solcast.com', 'api_key', 'str')
    resource_id = getVarConf('solcast.com', 'resource_id', 'str')
    resource_id2 = getVarConf('solcast.com2', 'resource_id', 'str')
    
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
                print_level = getVarConf('env','print_level','eval')
                if ( print_level != 0 ):
                    print('solcast.com: Die Minuten aus "dataAgeMaxInMinutes" ', dataAgeMaxInMinutes ,' Minuten sind noch nicht abgelaufen!!')
                    print(f'[Now: {now}] [Data created:  {dateCreated}] -> age in min: {dataAgeInMinutes}')
                dataIsExpired = False

    if (dataIsExpired):
        data = loadLatestWeatherData()
        if(data[0]['result']['watts'] != {}):
            if not data == "False":
                storeWeatherData(weatherfile, data[0], now)
        else:
            print("Fehler bei Datenanforderung api.solcast.com.au:")
            print(data[1])
