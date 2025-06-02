import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import requests
import json
import time
from datetime import datetime, timedelta
import FUNCTIONS.functions
import FUNCTIONS.WeatherData

def loadLatestWeatherData(Quelle, Gewicht):
    # Varablen definieren
    format = "%Y-%m-%d %H:%M:%S"
    dict_watts = {}
    heute = datetime.strftime(now, "%Y-%m-%d")
    morgen = datetime.strftime(now + timedelta(days=1), "%Y-%m-%d")
    sommerzeit = time.localtime().tm_isdst



    try:
        url = 'https://api.solcast.com.au/rooftop_sites/{}/{}?format=json&api_key={}'.format(resource_id, 'forecasts', api_key)
        try:
            apiResponse = requests.get(url, timeout=99.50)
            print("DEBUG Wetter URL: "+url)
            if apiResponse.status_code == 200:
                json_data1 = dict(json.loads(apiResponse.text))
            else:
                print("### ERROR "+str(apiResponse.status_code)+":  Keine forecasts-Daten von api.solcast.com.au")
                exit()
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout von api.solcast.com.au")
            exit()
        
        if Strings == 2:
            url = 'https://api.solcast.com.au/rooftop_sites/{}/{}?format=json&api_key={}'.format(resource_id2, 'forecasts', api_key)
            try:
                apiResponse2 = requests.get(url, timeout=99.50)
                apiResponse2.raise_for_status()
                if apiResponse2.status_code == 200:
                    json_data2 = dict(json.loads(apiResponse2.text))
                else:
                    print("### ERROR "+str(apiResponse.status_code)+":  Keine estimated_actuals-Daten von api.solcast.com.au")
                    exit()
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
                for wetterwerte in json_data1['forecasts']:
                    key_neu_1 = (wetterwerte['period_end'][:19]).replace('T',' ',1)
                    if ('00:00' in key_neu_1 and (heute in key_neu_1 or morgen in key_neu_1)):
                        key_neu = datetime.strftime(datetime.strptime(key_neu_1, format) + timedelta(hours=Zeitzone+sommerzeit), format)
                        #hier Werte mit NULLEN weg
                        if (wetterwerte['pv_estimate'] == 0):
                            if (Puffer[1] == 0):
                                Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor)]
                            else:
                                Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor)]
                                dict_watts[key_neu] = int(wetterwerte['pv_estimate']*1000*KW_Faktor)
                        else:
                            if (Puffer[1] == 0):
                                dict_watts[Puffer[0]] = Puffer[1]
                            Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor)]
                            dict_watts[key_neu] = int(wetterwerte['pv_estimate']*1000*KW_Faktor)
            except:
                print("Keine Daten für String1 von solcast.com.au")
                
            if Strings == 2:
                Puffer = ['2000-01-01',5]
                try:
                    for wetterwerte in json_data2['forecasts']:
                        key_neu_1 = (wetterwerte['period_end'][:19]).replace('T',' ',1)
                        if ('00:00' in key_neu_1 and (heute in key_neu_1 or morgen in key_neu_1)):
                            key_neu = datetime.strftime(datetime.strptime(key_neu_1, format) + timedelta(hours=Zeitzone+sommerzeit), format)
                            #hier Werte mit NULLEN weg
                            if (wetterwerte['pv_estimate'] == 0):
                                if (Puffer[1] == 0):
                                    Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor2)]
                                else:
                                    Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor2)]
                                    dict_watts[key_neu] = dict_watts[key_neu] + int(wetterwerte['pv_estimate']*1000*KW_Faktor2)
                            else:
                                if (Puffer[1] == 0):
                                    dict_watts[Puffer[0]] = Puffer[1]
                                Puffer = [key_neu, int(wetterwerte['pv_estimate']*1000*KW_Faktor2)]
                                dict_watts[key_neu] = dict_watts[key_neu] + int(wetterwerte['pv_estimate']*1000*KW_Faktor2)
                except:
                    print("Keine Daten für String2 von solcast.com.au")

        #solcast_2.json Nun wieder nach Datum und Stunden sortieren
        dict_watts = dict(sorted(dict_watts.items()))
        # hier evtl Begrenzungen der Prognose anbringen
        MaximalPrognosebegrenzung = basics.getVarConf('env','MaximalPrognosebegrenzung','eval')
        if (MaximalPrognosebegrenzung == 1):
            dict_watts = weatherdata.checkMaxPrognose(dict_watts)
        # Daten für SQL erzeugen
        SQL_watts = []
        for key, value in dict_watts.items():
            SQL_watts.append((key, Quelle, int(value), Gewicht, ''))

    except requests.exceptions.RequestException as error:
            json_data1 = error

    return(SQL_watts, json_data1)


if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'weather'])
    weatherdata = FUNCTIONS.WeatherData.WeatherData()
    # Benoetigte Variablen definieren und prüfen
    Strings = basics.getVarConf('pv.strings', 'anzahl', 'eval')
    Zeitzone = basics.getVarConf('solcast.com', 'Zeitzone', 'eval')
    KW_Faktor = basics.getVarConf('solcast.com', 'KW_Faktor', 'eval')
    KW_Faktor2 = basics.getVarConf('solcast.com', 'KW_Faktor2', 'eval')
    api_key = basics.getVarConf('solcast.com', 'api_key', 'str')
    resource_id = basics.getVarConf('solcast.com', 'resource_id', 'str')
    resource_id2 = basics.getVarConf('solcast.com', 'resource_id2', 'str')
    Gewicht = basics.getVarConf('solcast.com','Gewicht','str')
    Quelle = 'solcast.com'
    
    format = "%Y-%m-%d %H:%M:%S"    
    now = datetime.now()    
    
    data_all = loadLatestWeatherData(Quelle, Gewicht)
    data = data_all[0]
    data_err = data_all[1]
    if isinstance(data, list):
        weatherdata.storeWeatherData_SQL(data, Quelle)
        print(f'{Quelle} OK: Prognosedaten vom {now.strftime(format)} in weatherData.sqlite gespeichert.\n')
    else:
        print("Fehler bei Datenanforderung ", Quelle, ":")
        print(data_err)
