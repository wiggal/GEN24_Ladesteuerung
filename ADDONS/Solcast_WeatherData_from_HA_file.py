import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import json
import time
from datetime import datetime, timedelta, date
from FUNCTIONS.functions import basics


def loadLatestWeatherData():
    # Variablen definieren
    dict_watts = {}
    dict_watts['result'] = {}
    dict_watts['result']['watts'] = {}
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
                                if key_neu in dict_watts['result']['watts']:
                                    puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]
                                    dict_watts['result']['watts'][key_neu] = dict_watts['result']['watts'][key_neu] + int(
                                        pv_estimate * 1000 * KW_Faktor)
                                else:
                                    puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]
                                    dict_watts['result']['watts'][key_neu] = int(
                                        pv_estimate * 1000 * KW_Faktor)

                                continue
                        else:
                            if puffer[1] == 0:
                                dict_watts['result']['watts'][puffer[0]] = puffer[1]
                            if key_neu in dict_watts['result']['watts']:
                                puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]
                                dict_watts['result']['watts'][key_neu] = dict_watts['result']['watts'][key_neu] + int(
                                    pv_estimate * 1000 * KW_Faktor)
                            else: # first site
                                puffer = [key_neu, int(pv_estimate * 1000 * KW_Faktor)]

                                dict_watts['result']['watts'][key_neu] = int(
                                    pv_estimate * 1000 * KW_Faktor)

            dict_watts['result']['watts'] = dict(sorted(dict_watts['result']['watts'].items()))

    except FileNotFoundError:
        print("### ERROR:  Solcast-Datei nicht gefunden")
        exit()

    return dict_watts, json_data1


if __name__ == '__main__':
    basics = basics()
    config = basics.loadConfig(['default', 'weather'])
    # Benoetigte Variablen definieren und prüfen
    Zeitzone = basics.getVarConf('solcast.com', 'Zeitzone', 'eval')
    KW_Faktor = basics.getVarConf('solcast.com', 'KW_Faktor', 'eval')
    weatherfile = basics.getVarConf('env', 'filePathWeatherData', 'str')
    solcast_file = basics.getVarConf('solcast.com', 'weatherfile', 'str')
    dataAgeMaxInMinutes = basics.getVarConf('solcast.com', 'dataAgeMaxInMinutes', 'eval')

    date_format = "%Y-%m-%d %H:%M:%S"
    now = datetime.now()

    data = basics.loadWeatherData(weatherfile)
    # print(data['messageCreated'])
    dataIsExpired = True
    if data:
        dateCreated = None
        if data['messageCreated']:
            dateCreated = datetime.strptime(data['messageCreated'], date_format)

        if dateCreated:
            diff = now - dateCreated
            dataAgeInMinutes = diff.total_seconds() / 60
            if dataAgeInMinutes < dataAgeMaxInMinutes:
                print_level = basics.getVarConf('env', 'print_level', 'eval')
                if print_level != 0:
                    print('solcast.com ERROR: Die Minuten aus "dataAgeMaxInMinutes" ', dataAgeMaxInMinutes,
                          ' Minuten sind noch nicht abgelaufen!!')
                    print(f'[Now: {now}] [Data created:  {dateCreated}] -> age in min: {dataAgeInMinutes}\n')
                dataIsExpired = False

    if dataIsExpired:
        data_all = loadLatestWeatherData()
        data = data_all[0]
        data_err = data_all[1]
        # print(data)
        if data['result']['watts'] != {}:
            if not data == "False":
                # hier evtl Begrenzungen der Prognose anbringen
                MaximalPrognosebegrenzung = basics.getVarConf('env', 'MaximalPrognosebegrenzung', 'eval')
                if MaximalPrognosebegrenzung == 1:
                    data = basics.checkMaxPrognose(data)
                if MaximalPrognosebegrenzung == 2:
                    data = basics.Prognoseoptimierung(data)
                basics.storeWeatherData(weatherfile, data, now, 'solcast.com')
                dateCreated_new = data['messageCreated']
                print(f'solcast.com OK: Prognosedaten vom {dateCreated_new} gespeichert.\n')
        else:
            print("Fehler bei Datenanforderung api.solcast.com.au:")
