# skript von @tz8
import time
import sys
import os

# TODO: timezone vom system holen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from datetime import datetime
import requests
import json
from collections import defaultdict
import FUNCTIONS.functions
import FUNCTIONS.WeatherData

def loadLatestWeatherData(Quelle, Gewicht):
    # Werte für alle Strings
    anzahl_strings = basics.getVarConf('pv.strings','anzahl','eval')
    lat = basics.getVarConf('pv.strings','lat','eval')
    lon = basics.getVarConf('pv.strings','lon','eval')
    inverterEff = basics.getVarConf('akkudoktor','inverterEfficiency','eval')

    string_zaehler = 1
    SQL_watts_dict = {}
    while string_zaehler <= anzahl_strings:
        if (string_zaehler == 1): 
           suffix = ''
        else:
           suffix = string_zaehler
        horizon = basics.getVarConf('pv.strings',f'horizon{suffix}','str')
        dec = basics.getVarConf('pv.strings',f'dec{suffix}','eval')
        az = basics.getVarConf('pv.strings',f'az{suffix}','eval')
        wp = basics.getVarConf('pv.strings',f'wp{suffix}','eval')
        cellco = basics.getVarConf('akkudoktor',f'cellco{suffix}','eval')
        albedo = basics.getVarConf('akkudoktor',f'albedo{suffix}','eval')
        powerInv = basics.getVarConf('akkudoktor',f'powerInverter{suffix}','eval')

        # Fehler wenn az auf 0 gleich Sueden steht, siehe https://github.com/nick81nrw/solApi/pull/5
        if az == 0:
            az = 1

        # Unterscheidung zwischen Free, Personal und Personal Plus
        url_anfang ='https://api.akkudoktor.net'
        url = (
        url_anfang+'/forecast?lat={}&lon={}&power={}&azimuth={}&tilt={}&past_days=0&timecycle=hourly&cellCoEff={}&albedo={}&powerInverter={}&inverterEfficiency={}&horizone={}'
        .format(lat, lon, wp, az, dec, cellco, albedo, powerInv, inverterEff, horizon)
        )
        # Hier werden die Prognosen angefordert (evtl auch für zusätzliche Strings
        try:
            apiResponse = requests.get(url, timeout=52.50)
            print("DEBUG Wetter URL: "+url)
            if apiResponse.status_code == 200:
                pvdaten = dict(json.loads(apiResponse.text))
            else:
                print("### ERROR "+str(apiResponse.status_code)+":  Keine forecasts-Daten von api.akkudoktor.net")
                exit()
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout von api.akkudoktor.net")
            exit()

        dict_watts = defaultdict(int)
        for stunden in pvdaten['values']:
            for stunde in stunden:
                valueDate = datetime.strptime(stunde['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z")
                valuePower = int(stunde['power'])
                if valuePower > 0:
                    dict_watts[valueDate.strftime("%Y-%m-%d %H:%M:%S")] = valuePower

        # Daten für SQL erzeugen
        SQL_watts_tmp = []
        for key, value in dict_watts.items():
            if (value > 10):
                SQL_watts_tmp.append((key, Quelle, value, Gewicht, ''))

        SQL_watts_dict[string_zaehler] = SQL_watts_tmp
        string_zaehler += 1

    # hier dann evtl pvdaten addieren mit Funktion
    SQL_watts = weatherdata.sum_pv_data(SQL_watts_dict)

    return(SQL_watts)
        
    
if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    weatherdata = FUNCTIONS.WeatherData.WeatherData()
    config = basics.loadConfig(['default', 'weather'])
    ForecastCalcMethod = basics.getVarConf('env','ForecastCalcMethod','str')
    Gewicht = basics.getVarConf('akkudoktor','Gewicht','eval')
    Quelle = 'akkudoktor'
    
    format = "%H:%M:%S"    
    now = datetime.now()    
    data = loadLatestWeatherData(Quelle, Gewicht)
    if isinstance(data, list):
        weatherdata.storeWeatherData_SQL(data, Quelle, Gewicht)
        # Ergebnis mit ForecastCalcMethod berechnen und in DB speichern
        weatherdata.store_forecast_result()
        print(f'{Quelle} OK: Prognosedaten und Ergebnisse ({ForecastCalcMethod}) {now.strftime(format)} gespeichert.\n')
    else:
        print("Fehler bei Datenanforderung ", Quelle, ":")
        print(data)
