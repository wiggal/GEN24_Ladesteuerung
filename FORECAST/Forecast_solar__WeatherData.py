import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from datetime import datetime
import requests
import json
import FUNCTIONS.functions
import FUNCTIONS.SQLall

def loadLatestWeatherData():
    api_key = basics.getVarConf('forecast.solar','api_key','str')
    forecastactual = basics.getVarConf('forecast.solar','forecastactual','str')
    forecastdamping = basics.getVarConf('forecast.solar','forecastdamping','str')
    api_pers_plus = basics.getVarConf('forecast.solar','api_pers_plus','str')
    horizon = basics.getVarConf('pv.strings','horizon','str')
    lat = basics.getVarConf('pv.strings','lat','eval')
    lon = basics.getVarConf('pv.strings','lon','eval')
    dec = basics.getVarConf('pv.strings','dec','eval')
    az = basics.getVarConf('pv.strings','az','eval')
    kwp = basics.getVarConf('pv.strings','wp','eval') / 1000
    anzahl_strings = basics.getVarConf('pv.strings','anzahl','eval')
    horizon2 = basics.getVarConf('pv.strings','horizon2','str')
    dec2 = basics.getVarConf('pv.strings','dec2','eval')
    az2 = basics.getVarConf('pv.strings','az2','eval')
    kwp2 = basics.getVarConf('pv.strings','wp2','eval') / 1000

    # Unterscheidung zwischen Free, Personal und Personal Plus
    url_anfang ='https://api.forecast.solar'
    url = url_anfang+'/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
    url2 = url_anfang+'/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec2, az2, kwp2)
    if api_key != 'kein':
        url_anfang = 'https://api.forecast.solar/'+api_key
        url = url_anfang+'/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
        url2 = url_anfang+'/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec2, az2, kwp2)
        if anzahl_strings == 2 and api_pers_plus == 'ja':
            url = url_anfang+'/estimate/{}/{}/{}/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp, dec2, az2, kwp2)
            anzahl_strings = 1

    # resolution auf 60 Minuten, horizon und damping an die URL anhängen:
    if api_pers_plus == 'ja' and basics.getVarConf('pv.strings','anzahl','eval') == 2:
        # hier gibt es nur noch eine URL zu veraendern
        url = url+'?resolution=60&horizon1={}&horizon2={}&damping={}'.format(horizon, horizon2, forecastdamping)
    else:
        # hier muessen beide URLs angepasst werden
        url = url+'?resolution=60&horizon={}&damping={}'.format(horizon, forecastdamping)
        url2 = url2+'?resolution=60&horizon={}&damping={}'.format(horizon2, forecastdamping)

    # actual nur wenn ein API key vorhanden ist
    # Achtung: wenn durch eine Personal Subscription ein API Key vorhanden ist, aber keine Personal _PLUS_ Subscription, kann actual nicht bei beiden Abfragen genutzt werden, sonst verfälscht es die Werte, daher immer nur bei der ersten URL
    # diese Behandlung deckt auch Personal Plus API Kunden ab, da dann nur noch eine URL aufgerufen wird, url2 wird dort ignoriert
    if api_key != 'kein' and forecastactual == 'ja':
        sqlall = FUNCTIONS.SQLall.sqlall()
        currentDayProduction = sqlall.getSQLcurrentDayProduction('PV_Daten.sqlite')
        url = url+'&actual=' +"{:.1f}".format(currentDayProduction)

    try:
        try:
            apiResponse = requests.get(url, timeout=52.50)
            print("DEBUG Wetter URL: "+url)
            if apiResponse.status_code == 200:
                json_data1 = dict(json.loads(apiResponse.text))
            else:
                print("### ERROR "+str(apiResponse.status_code)+":  Keine forecasts-Daten von api.forecast.solar")
                exit()
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout von api.forecast.solar")
            exit()

        # Hier werden fuer ein evtl. zweites Feld mit anderer Ausrichtung die Prognosewerte eingearbeitet
        # Koordinaten müssen gleich sein, wegen zeitgleichem Sonnenauf- bzw. untergang 
        if anzahl_strings == 2:
            dict_watts = {}
            dict_watt_hours = {}

            try:
                apiResponse2 = requests.get(url2, timeout=52.50)
                apiResponse2.raise_for_status()
                print("DEBUG Wetter URL2: "+url2)
                if apiResponse2.status_code == 200:
                    json_data2 = dict(json.loads(apiResponse2.text))
                else:
                    print("### ERROR "+str(apiResponse2.status_code)+":  Keine forecasts-Daten String 2 von api.forecast.solar")
                    exit()
            except requests.exceptions.Timeout:
                print("### ERROR:  Timeout von api.forecast.solar")
                exit()
		
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

        #print(json_data1, "\n")
        return(json_data1)
    except OSError:
        exit()
        
    
if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'weather'])
    dataAgeMaxInMinutes = basics.getVarConf('forecast.solar','dataAgeMaxInMinutes','eval')
    
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
                    print('forecast.solar ERROR: Die Minuten aus "dataAgeMaxInMinutes" ', dataAgeMaxInMinutes ,' Minuten sind noch nicht abgelaufen!!')
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
                basics.storeWeatherData(weatherfile, data, now, 'forecast.solar')
                dateCreated_new = data['messageCreated']
                print(f'forecast.solar OK: Prognosedaten vom {dateCreated_new} gespeichert.\n')
        else:
            print("Fehler bei Datenanforderung api.forecast.solar:")
            print(data)
