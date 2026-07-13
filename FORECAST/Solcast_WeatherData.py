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

def _fetch_solcast(url, label, max_versuche=2, wartezeit=30):
    """
    Ruft eine Solcast-Forecast-URL ab.
    Bei 429 (Server überlastet) wird nach `wartezeit` Sekunden ein
    weiterer Versuch unternommen. Der Fehler wird erst ausgegeben,
    wenn auch der letzte Versuch fehlschlägt.
    Rückgabe: (json_daten, None) bei Erfolg, (None, Fehlermeldung) bei Fehler.
    """
    for versuch in range(1, max_versuche + 1):
        try:
            apiResponse = requests.get(url, timeout=99.50)
            print("DEBUG Wetter URL ("+label+", Versuch "+str(versuch)+"): "+url)
            if apiResponse.status_code == 200:
                return dict(json.loads(apiResponse.text)), None
            elif apiResponse.status_code == 429:
                if versuch < max_versuche:
                    print("### WARNUNG 429: Limit verbraucht oder Solcast-Server überlastet ("+label+"), Versuch "+str(versuch)+"/"+str(max_versuche)+". Warte "+str(wartezeit)+"s und versuche es erneut...")
                    time.sleep(wartezeit)
                    continue
                print("### ERROR 429: Limit verbraucht oder Solcast-Server überlastet ("+label+") - auch nach "+str(max_versuche)+" Versuchen.")
                return None, "429: Limit verbraucht oder Solcast-Server überlastet ("+label+")"
            else:
                print("### ERROR "+str(apiResponse.status_code)+":  Keine forecasts-Daten von api.solcast.com.au ("+label+")")
                return None, "Fehler "+str(apiResponse.status_code)+" ("+label+")"
        except requests.exceptions.Timeout:
            print("### ERROR:  Timeout von api.solcast.com.au ("+label+")")
            return None, "Timeout ("+label+")"
    return None, "Unbekannter Fehler ("+label+")"


def loadLatestWeatherData(Quelle, Gewicht):
    # Varablen definieren
    format = "%Y-%m-%d %H:%M:%S"
    dict_watts = {}
    SQL_watts = []
    heute = datetime.strftime(now, "%Y-%m-%d")
    morgen = datetime.strftime(now + timedelta(days=1), "%Y-%m-%d")
    sommerzeit = time.localtime().tm_isdst



    try:
        url = 'https://api.solcast.com.au/rooftop_sites/{}/{}?format=json&api_key={}'.format(resource_id, 'forecasts', api_key)
        json_data1, fehler1 = _fetch_solcast(url, "String1")
        if json_data1 is None:
            return (None, fehler1)

        if Strings == 2:
            url = 'https://api.solcast.com.au/rooftop_sites/{}/{}?format=json&api_key={}'.format(resource_id2, 'forecasts', api_key)
            json_data2, fehler2 = _fetch_solcast(url, "String2")
            if json_data2 is None:
                return (None, fehler2)

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

        # Daten für SQL erzeugen
        SQL_watts = []
        for key, value in dict_watts.items():
            if (value > 10):
                SQL_watts.append((key, Quelle, int(value), Gewicht, ''))

    except requests.exceptions.RequestException as error:
            json_data1 = error

    return(SQL_watts, json_data1)


if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'weather'])
    ForecastCalcMethod = basics.getVarConf('env','ForecastCalcMethod','str')
    weatherdata = FUNCTIONS.WeatherData.WeatherData()
    # Benoetigte Variablen definieren und prüfen
    Strings = basics.getVarConf('pv.strings', 'anzahl', 'eval')
    Zeitzone = basics.getVarConf('solcast.com', 'Zeitzone', 'eval')
    offset_minuten = int(basics.getVarConf('solcast.com', 'offset_minuten', 'eval'))
    KW_Faktor = basics.getVarConf('solcast.com', 'KW_Faktor', 'eval')
    KW_Faktor2 = basics.getVarConf('solcast.com', 'KW_Faktor2', 'eval')
    api_key = basics.getVarConf('solcast.com', 'api_key', 'str')
    resource_id = basics.getVarConf('solcast.com', 'resource_id', 'str')
    resource_id2 = basics.getVarConf('solcast.com', 'resource_id2', 'str')
    Gewicht = basics.getVarConf('solcast.com','Gewicht','eval')
    Quelle = 'solcast.com'
    
    format = "%H:%M:%S"    
    now = datetime.now()    
    
    data_all = loadLatestWeatherData(Quelle, Gewicht)
    data = data_all[0]
    data_err = data_all[1]
    if isinstance(data, list):
        weatherdata.storeWeatherData_SQL(data, Quelle, Gewicht, '', offset_minuten)
        # Ergebnis mit ForecastCalcMethod berechnen und in DB speichern
        weatherdata.store_forecast_result()
        print(f'{Quelle} OK: Prognosedaten und Ergebnisse ({ForecastCalcMethod}) {now.strftime(format)} gespeichert.\n')
    else:
        print("Fehler bei Datenanforderung ", Quelle, ":")
        print(data_err)
