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
import FUNCTIONS.functions
import FUNCTIONS.WeatherData

def loadLatestWeatherData(Quelle, Gewicht):
    horizon = basics.getVarConf('pv.strings','horizon','str')
    lat = basics.getVarConf('pv.strings','lat','eval')
    lon = basics.getVarConf('pv.strings','lon','eval')
    dec = basics.getVarConf('pv.strings','dec','eval')
    az = basics.getVarConf('pv.strings','az','eval')
    wp = basics.getVarConf('pv.strings','wp','eval')
    cellco = basics.getVarConf('akkudoktor','cellco','eval')
    albedo = basics.getVarConf('akkudoktor','albedo','eval')
    powerInv = basics.getVarConf('akkudoktor','powerInverter','eval')
    inverterEff = basics.getVarConf('akkudoktor','inverterEfficiency','eval')
    anzahl_strings = basics.getVarConf('pv.strings','anzahl','eval')
    # Werte für zweiten String
    horizon2 = basics.getVarConf('pv.strings','horizon2','str')
    dec2 = basics.getVarConf('pv.strings','dec2','eval')
    az2 = basics.getVarConf('pv.strings','az2','eval')
    wp2 = basics.getVarConf('pv.strings','wp2','eval')
    cellco2 = basics.getVarConf('akkudoktor','cellco2','eval')
    albedo2 = basics.getVarConf('akkudoktor','albedo2','eval')
    powerInv2 = basics.getVarConf('akkudoktor','powerInverter2','eval')

    # Fehler wenn az oder az2 auf 0 gleich Sueden stehen, siehe https://github.com/nick81nrw/solApi/pull/5
    if az == 0:
        az = 1

    if az2 == 0:
        az2 = 1

    # Unterscheidung zwischen Free, Personal und Personal Plus
    url_anfang ='https://api.akkudoktor.net'
    url = url_anfang+'/forecast?lat={}&lon={}&power={}&azimuth={}&tilt={}&past_days=0&timecycle=hourly&cellCoEff={}&albedo={}&powerInverter={}&inverterEfficiency={}&horizone={}'.format(lat, lon, wp, az, dec, cellco, albedo, powerInv, inverterEff, horizon)
    url2 = url_anfang+'/forecast?lat={}&lon={}&power={}&azimuth={}&tilt={}&past_days=0&timecycle=hourly&cellCoEff={}&albedo={}&powerInverter={}&inverterEfficiency={}&horizone={}'.format(lat, lon, wp2, az2, dec2, cellco2, albedo2, powerInv2, inverterEff, horizon2)

    try:
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

        dict_watts = {}
        pvdaten2 = {}
        # Hier werden fuer ein evtl. zweites Feld mit anderer Ausrichtung die Prognosewerte eingearbeitet
        # Koordinaten müssen gleich sein, wegen zeitgleichem Sonnenauf- bzw. untergang 
        if anzahl_strings == 2:
 
            try:
                apiResponse2 = requests.get(url2, timeout=52.50)
                print("DEBUG Wetter URL2: "+url2)
                if apiResponse2.status_code == 200:
                    pvdaten2 = dict(json.loads(apiResponse2.text))
                else:
                    print("### ERROR "+str(apiResponse2.status_code)+":  Keine forecasts-Daten String 2 von api.akkudoktor.net")
                    exit()
            except requests.exceptions.Timeout:
                print("### ERROR:  Timeout von api.akkudoktor.net")
                exit()
		
        for stunden in pvdaten['values']:
            for stunde in stunden:
                valueDate = datetime.strptime(stunde['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z")
                valuePower2 = 0
                if anzahl_strings == 2:
                    for stunden2 in pvdaten2['values']:
                        for stunde2 in stunden2:
                            if stunde2['datetime'] == stunde['datetime']:
                                valuePower2 = stunde2['power']
                                break

                valuePower = round(stunde['power'] + valuePower2)
                if valuePower > 0:
                    dict_watts[valueDate.strftime("%Y-%m-%d %H:%M:%S")] = valuePower

        # hier evtl Begrenzungen der Prognose anbringen
        MaximalPrognosebegrenzung = basics.getVarConf('env','MaximalPrognosebegrenzung','eval')
        if (MaximalPrognosebegrenzung == 1):
            dict_watts = weatherdata.checkMaxPrognose(dict_watts)

        # Daten für SQL erzeugen
        SQL_watts = []
        for key, value in dict_watts.items():
            if (value > 10):
                SQL_watts.append((key, Quelle, value, Gewicht, ''))

        return(SQL_watts)
    except OSError:
        exit()
        
    
if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    weatherdata = FUNCTIONS.WeatherData.WeatherData()
    config = basics.loadConfig(['default', 'weather'])
    ForecastCalcMethod = basics.getVarConf('env','ForecastCalcMethod','str')
    Gewicht = basics.getVarConf('akkudoktor','Gewicht','str')
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
