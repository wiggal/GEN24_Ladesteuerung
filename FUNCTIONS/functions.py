# Funktionen für die Gen24_Ladesteuerung
from datetime import datetime
import requests
import configparser
import sqlite3
import importlib
from typing import Type
    
class basics:
    def __init__(self, charge_options=None):
        self.now = datetime.now()
        self.ChargeOption = charge_options or {}


    def loadConfig(self, conf_files):
        # Damit die Variable config auch in der Funktion "getVarConf" vorhanden ist (global config)
        global config
        # Damit kann man auch meherer configs nacheinander lesen
        try:
            config
        except NameError:
            config = configparser.ConfigParser(strict=False)
        # Standard.ini lesen
        for conf_file in conf_files:
            c_file = 'CONFIG/'+conf_file+'.ini'
            try:
                with open(c_file, encoding='utf-8') as f:
                    config.read_file(f)
            except Exception as e:
                print("\nERROR: ", e, "\n")
        # _priv_ini lesen
        for conf_file in conf_files:
            c_file = 'CONFIG/'+conf_file+'_priv.ini'
            try:
                try:
                    with open(c_file, encoding='utf-8') as f:
                        config.read_file(f)
                except FileNotFoundError:
                    # wenn _priv.ini fehlt, kopieren
                    import shutil
                    c_org_file = 'CONFIG/'+conf_file+'.ini'
                    shutil.copyfile(c_org_file, c_file)
                    print(">>>>>>>>> ",c_file, " angelegt!!")
            except Exception as e:
                print("\nERROR: ", e, "\n")
        # Monatsabhängige ini lesen
        if ( 'charge' in conf_files and config.has_section('monats_priv.ini') ):
            aktueller_Monat = str(datetime.strftime(datetime.now(), "%m"))
            for (c_file, monate) in config.items('monats_priv.ini'):
                if int(aktueller_Monat) in [int(m) for m in monate.replace(' ', '').split(',') if m.isdigit()]:
                    c_file = 'CONFIG/'+c_file
                    try:
                        with open(c_file, encoding='utf-8') as f:
                            config.read_file(f)
                    except Exception as e:
                        print("\nERROR: ", e, "\n")

        return config


    def get_inverter_class(self, class_type) -> Type:
        """
        Lädt dynamisch das Inverter-Modul und gibt die Klasse zurück.

        :param InverterTyp: Name des Inverters, z.B. 'gen24' oder 'interface'
        :param class_type: "API" oder "Interface"
        :return: Klasse (nicht Instanz)
        """
        InverterTyp = self.getVarConf('inverter','InverterTyp', 'str')
        # Modul und Klassennamen bestimmen
        if class_type.lower() == "api":
            module_name = f"FUNCTIONS.{InverterTyp.lower()}_api"
            class_name = "InverterApi"
        else:
            module_name = f"FUNCTIONS.{InverterTyp.lower()}_interface"
            class_name = "InverterInterface"

        # Modul dynamisch importieren
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError:
            raise ImportError(
                f"⚠️ Modul '{module_name}' für InverterTyp '{InverterTyp}' nicht gefunden."
            ) from None

        # Klasse aus Modul holen
        try:
            cls: Type = getattr(mod, class_name)
        except AttributeError:
            raise ImportError(
                f"⚠️ Klasse '{class_name}' nicht im Modul '{module_name}' gefunden."
            ) from None

        return cls


    def getVarConf(self, var_block, var, Type):
        error_type = ' in den ini-Dateien '
        try:
            raw_value = config[var_block][var].strip()
            if Type == 'eval':
                error_type = "als Zahl "
                # Nur Kommas in Zahlen durch Punkt ersetzen
                number_str = raw_value.replace(',', '.')
                if '.' in number_str:
                    return_var = float(number_str)
                else:
                    return_var = int(number_str)
            else:
                error_type = ""
                return_var = raw_value  # String bleibt unverändert, inkl. Kommas

            # Vorhandene DB-Einträge aus ManuelleSteuerung vom TAB-LadeSTRG setzen
            if (var in self.ChargeOption):
                db_value = self.ChargeOption[var]['Res_Feld2']
                try:
                    if db_value is None:
                        raise ValueError("kein Wert")
                    if Type == 'eval':
                        db_value = str(db_value).strip().replace(',', '.')
                        db_value = float(db_value) if '.' in db_value else int(db_value)
                    else:
                        db_value = str(db_value)
                    if (db_value != return_var):
                        return_var = db_value
                        print(f"DEBUG: DB_VAR {var} = {return_var}")
                except ValueError:
                    # Leerer/ungültiger WebUI-Wert: ini-Wert verwenden, statt das ganze Programm zu beenden
                    print(f"WARNING: ungültiger WebUI-Wert für {var} ({db_value!r}), ini-Wert {return_var!r} wird verwendet")

        except (KeyError, ValueError):
            print(f"ERROR: die Variable [{var_block}][{var}] wurde NICHT {error_type}definiert!")
            exit(1)
        return return_var

    def loadWeatherData(self):
        conn = sqlite3.connect('weatherData.sqlite')
        cursor = conn.cursor()
    
        query = """
            SELECT Zeitpunkt, Prognose_W
            FROM weatherData
            WHERE
                Prognose_W > 30 AND
                Quelle IS 'Prognose' AND
                DATE(Zeitpunkt) BETWEEN DATE('now', 'localtime') AND DATE('now', 'localtime', '+1 day')
            ORDER BY Zeitpunkt ASC
        """
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
        finally:
            conn.close()
        result = dict(rows)
        return {"result": {"watts": result}}

    def sendPush(self, message, title, tags):
        Push_Message_Url = self.getVarConf('messaging','Push_Message_Url','str')
        try:
            apiResponse = requests.post(Push_Message_Url, data=message.encode(encoding='utf-8'), headers={ "Title": title.encode('latin-1', 'replace').decode('latin-1'), "Tags":  tags}, timeout=10)
            apiResponse.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("ERROR: Push-Nachricht fehlgeschlagen: ", e)
        return(Push_Message_Url)
