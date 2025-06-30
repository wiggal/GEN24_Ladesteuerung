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
    url = 'http://www.solarprognose.de/web/solarprediction/api/v1?access-token={}&item={}&id={}&type={}&algorithm={}'.format(accesstoken, item, id, type, algorithm)
    print("DEBUG Wetter URL: "+url)
    try:
        apiResponse = requests.get(url, timeout=99)
        if apiResponse.status_code == 200:
            json_data1 = dict(json.loads(apiResponse.text))
        else:
            print("### ERROR "+str(apiResponse.status_code)+":  Keine forecasts-Daten von www.solarprognose.de")
            exit()
    except requests.exceptions.Timeout:
        print("### ERROR:  Timeout von www.solarprognose.de")
        exit()
    dict_watts = {}
    for key, value in json_data1.get('data',{}).items():
        key_neu = str(datetime.fromtimestamp(value[0]) + timedelta(hours=Zeitversatz))
        dict_watts[key_neu] = int(value[1]*1000*KW_Faktor)

    # Daten für SQL erzeugen
    SQL_watts = []
    for key, value in dict_watts.items():
        if (value > 10):
            SQL_watts.append((key, Quelle, value, Gewicht, ''))

    return(SQL_watts, json_data1)

if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    weatherdata = FUNCTIONS.WeatherData.WeatherData()
    config = basics.loadConfig(['default', 'weather'])
    Gewicht = basics.getVarConf('solarprognose','Gewicht','eval')
    Quelle = 'solarprognose'
    config = basics.loadConfig(['default', 'weather'])
    ForecastCalcMethod = basics.getVarConf('env','ForecastCalcMethod','str')
    # Benoetigte Variablen definieren und prüfen
    id = basics.getVarConf('solarprognose', 'id', 'eval')
    KW_Faktor = basics.getVarConf('solarprognose', 'KW_Faktor', 'eval')
    WaitSec = basics.getVarConf('solarprognose', 'WaitSec', 'eval')
    accesstoken = basics.getVarConf('solarprognose', 'accesstoken', 'str')
    item = basics.getVarConf('solarprognose', 'item', 'str')
    type = basics.getVarConf('solarprognose', 'type', 'str')
    Zeitversatz = int(basics.getVarConf('solarprognose', 'Zeitversatz', 'eval'))
    algorithm = basics.getVarConf('solarprognose', 'algorithm', 'str')

    time.sleep(WaitSec)
    
    format = "%H:%M:%S"    
    now = datetime.now()    
    
    data_all = loadLatestWeatherData(Quelle, Gewicht)
    data = data_all[0]
    data_err = data_all[1]
    if isinstance(data, list):
        weatherdata.storeWeatherData_SQL(data, Quelle, Gewicht)
        # Ergebnis mit ForecastCalcMethod berechnen und in DB speichern
        weatherdata.store_forecast_result()
        print(f'{Quelle} OK: Prognosedaten und Ergebnisse ({ForecastCalcMethod}) {now.strftime(format)} gespeichert.\n')
    else:
        print("Fehler bei Datenanforderung ", Quelle, ":")
        print(data_err)
