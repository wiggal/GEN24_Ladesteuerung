import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import json
import time
from datetime import datetime, timedelta, date
from FUNCTIONS.functions import basics
from FUNCTIONS.WeatherData import WeatherData


def loadLatestWeatherData(Quelle, Gewicht):
    # Variablen definieren
    dict_watts = {}
    #heute = datetime.strftime(now, "%Y-%m-%d")
    heute = date.today()
    sommerzeit = time.localtime().tm_isdst

    try:
        with open(solcast_file) as f:
            json_data1 = dict(json.load(f))
            json_data1 = dict(json_data1["siteinfo"])
            for sites in json_data1:
                json_data2 = json_data1[sites]
                puffer = ['2000-01-01', 5]
                for idx, wetterwerte in enumerate(json_data2['forecasts']):
                    key_neu_1 = (wetterwerte['period_start'][:19]).replace('T', ' ', 1)
                    if '00:00' in key_neu_1 and (heute <=
                                                 datetime.date(datetime.fromisoformat(key_neu_1))):
                        key_neu = datetime.strftime(
                            datetime.strptime(key_neu_1, date_format) + timedelta(hours=Zeitzone
                                                                                        + sommerzeit), date_format)
                        # hier Mittelwert volle Stunde, halbe Stunde
                        next_wetterwerte = json_data2['forecasts'][(idx + 1) % len(json_data2['forecasts'])]
                        if '30:00' in next_wetterwerte['period_start']:
                            pv_estimate = (wetterwerte['pv_estimate'] + next_wetterwerte['pv_estimate']) / 2
                        else:
                            pv_estimate = wetterwerte['pv_estimate']
                        # hier Werte mit NULLEN weg
                        if pv_estimate == 0:
                            if puffer[1] == 0:
                                puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]
                                continue
                            else:
                                if key_neu in dict_watts:
                                    puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]
                                    dict_watts[key_neu] = dict_watts[key_neu] + int(
                                        pv_estimate * 1000 * KW_Faktor)
                                else:
                                    puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]
                                    dict_watts[key_neu] = int(
                                        pv_estimate * 1000 * KW_Faktor)

                                continue
                        else:
                            if puffer[1] == 0:
                                dict_watts[puffer[0]] = puffer[1]
                            if key_neu in dict_watts:
                                puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]
                                dict_watts[key_neu] = dict_watts[key_neu] + int(
                                    pv_estimate * 1000 * KW_Faktor)
                            else: # first site
                                puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]

                                dict_watts[key_neu] = int(
                                    pv_estimate * 1000 * KW_Faktor)

            dict_watts = dict(sorted(dict_watts.items()))

    except FileNotFoundError:
        print("### ERROR:  Solcast-Datei nicht gefunden")
        exit()

    # hier evtl Begrenzungen der Prognose anbringenAdd commentMore actions
    MaximalPrognosebegrenzung = basics.getVarConf('env', 'MaximalPrognosebegrenzung', 'eval')
    if (MaximalPrognosebegrenzung == 1):
        dict_watts = weatherdata.checkMaxPrognose(dict_watts)
    # Daten für SQL erzeugen
    SQL_watts = []
    for key, value in dict_watts.items():
        SQL_watts.append((key, Quelle, int(value), Gewicht, ''))


    return(SQL_watts, json_data1)

if __name__ == '__main__':
    basics = basics()
    config = basics.loadConfig(['default', 'weather'])
    weatherdata = WeatherData()
    # Benoetigte Variablen definieren und prüfen
    Zeitzone = basics.getVarConf('solcast.com', 'Zeitzone', 'eval')
    KW_Faktor = basics.getVarConf('solcast.com', 'KW_Faktor', 'eval')
    solcast_file = basics.getVarConf('solcast.com', 'weatherfile', 'str')
    Gewicht = basics.getVarConf('solcast.com','Gewicht','str')
    Quelle = 'solcast_ha.com'
    date_format = "%Y-%m-%d %H:%M:%S"
    now = datetime.now()

    data_all = loadLatestWeatherData(Quelle, Gewicht)
    data = data_all[0]
    data_err = data_all[1]
    if isinstance(data, list):
        weatherdata.storeWeatherData_SQL(data, Quelle)
        print(f'{Quelle} OK: Prognosedaten vom {now.strftime(date_format)} in weatherData.sqlite gespeichert.\n')
    else:
        print("Fehler bei Datenanforderung ", Quelle, ":")
        print(data_err)
