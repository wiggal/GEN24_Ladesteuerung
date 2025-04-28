# skript von @tz8
import time
import sys
import os

# TODO: timezone vom system holen
timezone_name = time.tzname
print("Zeitzonen-Name:", timezone_name)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from datetime import datetime
import requests
import json
import FUNCTIONS.functions
import FUNCTIONS.SQLall

def loadLatestWeatherData():
    horizon = basics.getVarConf('akkudoktor','horizon','str')
    lat = basics.getVarConf('akkudoktor','lat','eval')
    lon = basics.getVarConf('akkudoktor','lon','eval')
    dec = basics.getVarConf('akkudoktor','dec','eval')
    az = basics.getVarConf('akkudoktor','az','eval')
    wp = basics.getVarConf('akkudoktor','wp','eval')
    cellco = basics.getVarConf('akkudoktor','cellco','eval')
    albedo = basics.getVarConf('akkudoktor','albedo','eval')
    powerInv = basics.getVarConf('akkudoktor','powerInverter','eval')
    inverterEff = basics.getVarConf('akkudoktor','inverterEfficiency','eval')
    anzahl_strings = basics.getVarConf('pv.strings','anzahl','eval')
    # Werte für zweiten String
    horizon2 = basics.getVarConf('akkudoktor2','horizon','str')
    dec2 = basics.getVarConf('akkudoktor2','dec','eval')
    az2 = basics.getVarConf('akkudoktor2','az','eval')
    wp2 = basics.getVarConf('akkudoktor2','wp','eval')
    cellco2 = basics.getVarConf('akkudoktor2','cellco','eval')
    albedo2 = basics.getVarConf('akkudoktor2','albedo','eval')
    powerInv2 = basics.getVarConf('akkudoktor2','powerInverter','eval')

    # Fehler wenn az oder az2 auf 0 gleich Sueden stehen, siehe https://github.com/nick81nrw/solApi/pull/5
    if az == 0:
        az = 1

    if az2 == 0:
        az2 = 1

    # Unterscheidung zwischen Free, Personal und Personal Plus
    url_anfang ='https://api.akkudoktor.net'
    url = url_anfang+'/forecast?lat={}&lon={}&power={}&azimuth={}&tilt={}&timecycle=hourly&cellCoEff={}&albedo={}&powerInverter={}&inverterEfficiency={}&horizone={}'.format(lat, lon, wp, az, dec, cellco, albedo, powerInv, inverterEff, horizon)
    url2 = url_anfang+'/forecast?lat={}&lon={}&power={}&azimuth={}&tilt={}&timecycle=hourly&cellCoEff={}&albedo={}&powerInverter={}&inverterEfficiency={}&horizone={}'.format(lat, lon, wp2, az2, dec2, cellco2, albedo2, powerInv2, inverterEff, horizon2)

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

        forecastData = {
            "result": {
                "watts": {}
            }
        }

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
                    forecastData['result']['watts'][valueDate.strftime("%Y-%m-%d %H:%M:%S")] = valuePower

        # Metadaten hinzufuegen
        datumCreated = datetime.datetime.strptime(apiResponse.headers['date'], "%a, %d %b %Y %H:%M:%S GMT")
        forecastData["messageCreated"] = datumCreated.strftime("%Y-%m-%d %H:%M:%S")
        forecastData["createdfrom"] = "api.akkudoktor.net"

        return(forecastData)
    except OSError:
        exit()
        
    
if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'weather'])
    dataAgeMaxInMinutes = basics.getVarConf('akkudoktor','dataAgeMaxInMinutes','eval')
    
    format = "%Y-%m-%d %H:%M:%S"    
    now = datetime.now()    
    
    weatherfile = basics.getVarConf('env','filePathWeatherData','str')
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
                    print('akkudoktor API ERROR: Die Minuten aus "dataAgeMaxInMinutes" ', dataAgeMaxInMinutes ,' Minuten sind noch nicht abgelaufen!!')
                    print(f'[Now: {now}] [Data created:  {dateCreated}] -> age in min: {dataAgeInMinutes}\n')
                dataIsExpired = False

    if (dataIsExpired):
        data = loadLatestWeatherData()
        if isinstance(data['result'], dict):
            if not data == "False":
                # hier evtl Begrenzungen der Prognose anbringen
                MaximalPrognosebegrenzung = basics.getVarConf('env','MaximalPrognosebegrenzung','eval')
                if (MaximalPrognosebegrenzung == 1):
                    data = basics.checkMaxPrognose(data)
                basics.storeWeatherData(weatherfile, data, now, 'akkudoktor')
                dateCreated_new = data['messageCreated']
                print(f'akkudoktor OK: Prognosedaten vom {dateCreated_new} gespeichert.\n')
        else:
            print("Fehler bei Datenanforderung api.akkudoktor.net:")
            print(data)

    
