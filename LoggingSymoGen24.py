import pickledb
import json
import requests, json
import configparser
from datetime import datetime, timedelta
import pytz
import csv
import SymoGen24Connector
from pathlib import Path

def loadConfig():
        config = configparser.ConfigParser()
        try:
                config.read('config.ini')
        except:
                print('config file not found.')
                exit()
        return config

def loadWeatherData(config):
        data = None
        with open(config['env']['filePathWeatherData']) as json_file:
                data = json.load(json_file)

        return data

if __name__ == '__main__':
        config = loadConfig()
        db = pickledb.load(config['env']['filePathConfigDb'], True)
        
        #now = datetime.now(pytz.timezone(config['env']['timezone']))
        now = datetime.now()
        format = "%Y-%m-%d %H:%M:%S"
        
        gen24 = None
        auto = False
        try:            
                chargeStart = None
                if (db.get('ChargeStart')):
                        chargeStart = datetime.strptime(db.get('ChargeStart'), format)
                        # print(f'Current chargeStart loaded from db: {chargeStart}')
                
                newPercent = None

                ###############################

                data = loadWeatherData(config)
                gen24 = SymoGen24Connector.SymoGen24(config['gen24']['hostNameOrIp'], config['gen24']['port'], auto)
                # print(data)


                format_aktStd = "%Y-%m-%d %H:00:00"
                Aktuelle_Std = datetime.strftime(now, format_aktStd)

                # Prognose fuer naechsten Stunde 

                Watt_Prognose = 0
                if data['result']['watts'].get(Aktuelle_Std):
                    Watt_Prognose = data['result']['watts'].get(Aktuelle_Std)
                else:
                    Watt_Prognose = 0


                ################## JSON per API

                url = requests.get("http://192.168.178.50/solar_api/v1/GetPowerFlowRealtimeData.fcgi")
                text = url.text
                data = json.loads(text)

                # print("Ladung Akku = + : ", (data['Body']['Data']['Site'].get('P_Akku') * -1), " Watt")
                Batterieladung = (data['Body']['Data']['Site'].get('P_Akku') * -1)
                # print("PV Leistung = + : ", data['Body']['Data']['Site'].get('P_PV'), " Watt")
                Aktuelle_Produktion = data['Body']['Data']['Site'].get('P_PV')
                # print("Verbrauch Haus = - : ", data['Body']['Data']['Site'].get('P_Load') * -1, " Watt")
                Verbrauch_Haus = data['Body']['Data']['Site'].get('P_Load') * -1
                # print("Leistung ins Netz = + : ", data['Body']['Data']['Site'].get('P_Grid') * -1, " Watt")
                Leistung_ins_Netz = data['Body']['Data']['Site'].get('P_Grid') * -1
                # print("Batterie Ladestand: ", data['Body']['Data']['Inverters']['1'].get('SOC'), " Prozent")
                Battreiestand_Prozent = data['Body']['Data']['Inverters']['1'].get('SOC')





                ############## CSV_Datei schreiben
                ############ Aktuelle_Produktion aus Register zeitweise 10 fach?????

                Zeit = datetime.strftime(now, "%m-%d %H:%M")
                # Aktuelle_Produktion = int(((gen24.read_data('MPPT_1_DC_Power') + (gen24.read_data('MPPT_2_DC_Power'))))/10)
                Prognose_forecast_solar = int(Watt_Prognose)
                Aktuelle_Ladegrenze = gen24.read_data('BatteryMaxChargePercent')

                # Kopf schreiben, wenn Datei nicht extistiert
                csv_file = Path("Log.csv")
                if not csv_file.is_file():
                    with open(csv_file, 'w', newline='') as student_file:
                        writer = csv.writer(student_file)
                        writer.writerow(["Zeit","Ladung Akku","Verbrauch Haus","Leistung ins Netz","Produktion","Prognose forecast.solar","Aktuelle Ladegrenze","Battreiestand in Prozent"])


                if Aktuelle_Produktion > 10:
                    from csv import writer
                    list_data=[Zeit, Batterieladung, Verbrauch_Haus, Leistung_ins_Netz, Aktuelle_Produktion, Prognose_forecast_solar, Aktuelle_Ladegrenze, Battreiestand_Prozent]
                    with open('Log.csv', 'a', newline='') as f_object:  
                        # Pass the CSV  file object to the writer() function
                        writer_object = writer(f_object)
                        # Result - a writer object
                        # Pass the data in the list as an argument into the writerow() function
                        writer_object.writerow(list_data)  
                        # Close the file object
                        f_object.close()

        finally:
                if (gen24 and not auto):
                        gen24.modbus.close()
