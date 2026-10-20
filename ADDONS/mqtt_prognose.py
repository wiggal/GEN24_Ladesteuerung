# Prognose, geplante Lademengen (einmal, laufend), Rest (Differenz) und Batteriesteuerung per MQTT an einen Broker senden
# Aufruf aus dem Hauptverzeichnis:  ./start_PythonScript.sh ADDONS/mqtt_prognose.py
# Testlauf ohne Senden:             ./start_PythonScript.sh ADDONS/mqtt_prognose.py test
# Anderes Datum für "heute" (Test): ./start_PythonScript.sh ADDONS/mqtt_prognose.py test heute=2026-10-19
# Alte Einzel-Topics löschen:       ./start_PythonScript.sh ADDONS/mqtt_prognose.py aufraeumen
# Konfiguration in CONFIG/mqtt.ini bzw. CONFIG/mqtt_priv.ini
#
# Voraussetzung: python-Paket paho-mqtt (pip install paho-mqtt)
#
# 1. Prognose und Planung (Aufruf als Skript, z.B. über den Scheduler)
#   Quellen:
#     Prognose:  API_forecast.php (Watt je Stunde), Adresse wird aus Web_URL gebildet
#     Planung:   CONFIG/Prog_Steuerung.sqlite, Tabelle steuercodes, Schluessel 'Reservierung'
#                Res_Feld1 = einmal, Res_Feld2 = laufend (jeweils in Watt)
#   Regeln:
#     Rest (diff) = Prognose - einmal - laufend
#     einmal gilt nur für Datum und Stunde der Zeile
#     laufend gilt jeden Tag zur gleichen Uhrzeit, wie in FUNCTIONS/SQLall.py (getSQLsteuerdaten, ab 0.43.7):
#     Wert der Zeile selbst, wenn <> 0, sonst der <> 0 Wert der letzten früheren Zeile zur gleichen Uhrzeit
#   Topics (Werte in kW mit 3 Nachkommastellen, Summen in kWh):
#     Topic_Base/stunden/<tag>   JSON mit datum und forecast_00h, diff_00h, geplant_00h, laufend_00h ... bis 23h
#     Topic_Base/<serie>/<tag>/sum/wert   Tagessummen, serie = prognose, planung_einmal, planung_laufend, differenz
#     tag = heute, morgen, uebermorgen
#   Hinweis: Die Tabelle der Weboberfläche zeigt nur Stunden mit Prognose > 30 W und rundet
#     jede Zeile auf 0,1 kW, hier wird ungerundet summiert, daher kleine Abweichungen bei den Summen.
#
# 2. Status der Batteriesteuerung (Aufruf aus EnergyController.py, siehe mqtt_prognose.readme)
#   Funktion status_senden(werte), Topics Topic_Base/status/<name>, siehe STATUS_NAMEN
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from sys import argv
from datetime import datetime, date, timedelta
from urllib.parse import urljoin
import configparser
import json
import sqlite3
import requests
import FUNCTIONS.functions

basics = FUNCTIONS.functions.basics()


def Prognose_holen(Web_URL, SSL_Verify):
    # Prognose aus API_forecast.php (im Verzeichnis der Startseite) holen
    API_URL = urljoin(Web_URL, 'API_forecast.php')
    antwort = requests.get(API_URL, timeout=20, verify=SSL_Verify)
    antwort.raise_for_status()
    daten = antwort.json()
    ergebnis = daten.get('result')
    if not isinstance(ergebnis, dict):
        meldung = (daten.get('message') or {}).get('text') or "kein 'result' in der Antwort"
        raise ValueError(f"API_forecast.php meldet: {meldung}")
    Prognose = {}
    for Zeitstempel, Watt in ergebnis.items():
        zeit = datetime.strptime(Zeitstempel, "%Y-%m-%d %H:%M:%S")
        Prognose[(zeit.date(), zeit.hour)] = float(Watt)
    return Prognose


def Planung_holen():
    # Reservierungen (einmal, laufend) aus CONFIG/Prog_Steuerung.sqlite lesen
    # Rückgabe: einmal und laufend_roh je (Datum, Stunde), Res_Feld2 ist hier noch der Wert der Zeile selbst
    einmal = {}
    laufend_roh = {}
    SQL_Datei = 'CONFIG/Prog_Steuerung.sqlite'
    if not os.path.exists(SQL_Datei):
        raise FileNotFoundError(f"{SQL_Datei} nicht gefunden")
    con = sqlite3.connect('file:' + SQL_Datei + '?mode=ro', uri=True)
    try:
        zeilen = con.execute("SELECT Zeit, Res_Feld1, Res_Feld2 FROM steuercodes "
                             "WHERE Schluessel = 'Reservierung'").fetchall()
    finally:
        con.close()

    def Zahl(wert):
        try:
            return float(wert)
        except (TypeError, ValueError):
            return 0.0

    for Zeit, Feld1, Feld2 in zeilen:
        try:
            zeit = datetime.strptime(Zeit, "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            continue
        einmal[(zeit.date(), zeit.hour)] = Zahl(Feld1)
        laufend_roh[(zeit.date(), zeit.hour)] = Zahl(Feld2)
    return einmal, laufend_roh


def laufend_ermitteln(laufend_roh, Tag, Stunde):
    # wie getSQLsteuerdaten() in FUNCTIONS/SQLall.py: Wert der Zeile selbst, wenn <> 0,
    # sonst der <> 0 Wert der letzten früheren Zeile zur gleichen Uhrzeit (laufend wird jeden Tag wiederholt)
    Wert = laufend_roh.get((Tag, Stunde), 0.0)
    if Wert != 0:
        return Wert
    fruehere = [d for (d, h), w in laufend_roh.items() if h == Stunde and d < Tag and w != 0]
    if fruehere:
        return laufend_roh[(max(fruehere), Stunde)]
    return 0.0


def kW(Watt):
    return f"{Watt / 1000:.3f}"


def Nachrichten_bauen(Topic_Base, Prognose, einmal, laufend_roh, heute):
    # Liste aus (Topic, Wert) erzeugen: je Tag ein JSON mit allen Stundenwerten und die Tagessummen einzeln
    # Stunden ohne Wert = 0
    Topic_Base = Topic_Base.strip('/')
    Nachrichten = []
    for Tagname, Offset in [('heute', 0), ('morgen', 1), ('uebermorgen', 2)]:
        Tag = heute + timedelta(days=Offset)
        Serien = {'prognose': {}, 'planung_einmal': {}, 'planung_laufend': {}, 'differenz': {}}
        JSON_Daten = {'datum': Tag.isoformat()}
        for Stunde in range(24):
            k = (Tag, Stunde)
            Prog = Prognose.get(k, 0.0)
            Einm = einmal.get(k, 0.0)
            Lauf = laufend_ermitteln(laufend_roh, Tag, Stunde)
            Serien['prognose'][Stunde] = Prog
            Serien['planung_einmal'][Stunde] = Einm
            Serien['planung_laufend'][Stunde] = Lauf
            Serien['differenz'][Stunde] = Prog - Einm - Lauf
            JSON_Daten[f"forecast_{Stunde:02d}h"] = kW(Prog)
            JSON_Daten[f"diff_{Stunde:02d}h"] = kW(Prog - Einm - Lauf)
            JSON_Daten[f"geplant_{Stunde:02d}h"] = kW(Einm)
            JSON_Daten[f"laufend_{Stunde:02d}h"] = kW(Lauf)
        # Zahlen statt Text im JSON
        for key in JSON_Daten:
            if key != 'datum':
                JSON_Daten[key] = float(JSON_Daten[key])
        Nachrichten.append((f"{Topic_Base}/stunden/{Tagname}", json.dumps(JSON_Daten)))
        for Serie, Stunden in Serien.items():
            Nachrichten.append((f"{Topic_Base}/{Serie}/{Tagname}/sum/wert", kW(sum(Stunden.values()))))
    return Nachrichten


def alte_Topics(Topic_Base):
    # Einzel-Topics der ersten Version (je Stunde ein Topic), werden mit "aufraeumen" gelöscht
    Topic_Base = Topic_Base.strip('/')
    Topics = []
    for Tagname in ['heute', 'morgen', 'uebermorgen']:
        for Serie in ['prognose', 'planung_einmal', 'planung_laufend', 'differenz']:
            Topics.append(f"{Topic_Base}/{Serie}/{Tagname}/datum")
            for Stunde in range(24):
                Topics.append(f"{Topic_Base}/{Serie}/{Tagname}/{Stunde:02d}/wert")
    return Topics


def Client_erzeugen():
    # MQTT-Client mit den Daten aus der Config erzeugen (noch nicht verbunden)
    import paho.mqtt.client as mqtt
    Broker_User = basics.getVarConf('mqtt', 'Broker_User', 'str')
    Broker_Password = basics.getVarConf('mqtt', 'Broker_Password', 'str')
    Broker_TLS = basics.getVarConf('mqtt', 'Broker_TLS', 'eval')
    Client_ID = basics.getVarConf('mqtt', 'Client_ID', 'str')
    # paho-mqtt 2.x braucht die Callback-API-Version, 1.x kennt sie nicht
    API_Version = getattr(mqtt, 'CallbackAPIVersion', None)
    if API_Version is not None:
        client = mqtt.Client(API_Version.VERSION2, client_id=Client_ID)
    else:
        client = mqtt.Client(client_id=Client_ID)
    if Broker_User != '':
        client.username_pw_set(Broker_User, Broker_Password or None)
    if Broker_TLS == 1:
        client.tls_set()
    return client


def MQTT_senden(Nachrichten, loeschen=False):
    # Alle Nachrichten (Topic, Wert) an den Broker senden, Rückgabe = Anzahl nicht bestätigter Nachrichten
    # loeschen=True: leerer Wert mit Retain löscht ein retained Topic am Broker
    Broker_Address = basics.getVarConf('mqtt', 'Broker_Address', 'str')
    Broker_Port = basics.getVarConf('mqtt', 'Broker_Port', 'eval')
    Retain = basics.getVarConf('mqtt', 'Retain', 'eval')
    client = Client_erzeugen()
    client.connect(Broker_Address, Broker_Port, 60)
    client.loop_start()
    infos = [client.publish(Topic, Wert, qos=1, retain=(Retain == 1 or loeschen)) for Topic, Wert in Nachrichten]
    for info in infos:
        info.wait_for_publish(timeout=15)
    nicht_gesendet = sum(1 for info in infos if not info.is_published())
    client.loop_stop()
    client.disconnect()
    return nicht_gesendet


def prognose_senden(heute=None):
    # Prognose und Planung neu lesen und alle Prognose-Topics senden, Rückgabe = Anzahl nicht bestätigter Nachrichten
    Topic_Base = basics.getVarConf('mqtt', 'Topic_Base', 'str')
    Web_URL = basics.getVarConf('mqtt', 'Web_URL', 'str')
    Web_SSL_Verify = basics.getVarConf('mqtt', 'Web_SSL_Verify', 'eval')
    Prognose = Prognose_holen(Web_URL, Web_SSL_Verify == 1)
    einmal, laufend_roh = Planung_holen()
    Nachrichten = Nachrichten_bauen(Topic_Base, Prognose, einmal, laufend_roh, heute or date.today())
    return MQTT_senden(Nachrichten)


# Name im Topic, Einheit (nur zur Dokumentation) und Name der Variable in EnergyController.py
STATUS_NAMEN = [
    ('zeit',                     '',     'Zeitpunkt des Laufs (YYYY-MM-DD HH:MM:SS)'),
    ('pv_produktion',            'W',    'aktuellePVProduktion'),
    ('einspeisung',              'W',    'aktuelleEinspeisung (positiv = Einspeisung)'),
    ('batterie_power',           'W',    'aktuelleBatteriePower'),
    ('verbrauch_haus',           'W',    'GesamtverbrauchHaus'),
    ('batterie_soc',             '%',    'BattStatusProz'),
    ('batterie_freie_kapazitaet', 'Wh',  'BattKapaWatt_akt (im Log "aktuelleBattKapazität")'),
    ('ladewert_alt',             'W',    'alterLadewert (Bisheriger Ladewert)'),
    ('ladewert_neu',             'W',    'aktuellerLadewert (Neuer Ladewert)'),
    ('ladewert_grund',           'Text', 'LadewertGrund'),
    ('batt_voll_um',             'Uhr',  'BattVollUm'),
    ('prognose_aktuell',         'W',    'aktuelleVorhersage (aktuellePrognose)'),
    ('prognose_tag',             'Wh',   'TagesPrognoseGesamt (TagesPrognose)'),
    ('grundlast_summe',          'Wh',   'Grundlast_Summe'),
]


def status_senden(werte):
    # Wird aus EnergyController.py aufgerufen, werte = Dictionary mit den Namen aus STATUS_NAMEN
    # Fehler (z.B. Broker nicht erreichbar) werden nur gemeldet und stören die Batteriesteuerung nicht
    try:
        basics.loadConfig(['mqtt'])
        if basics.getVarConf('mqtt', 'Status_senden', 'eval') != 1:
            return
        mqtt_print_level = basics.getVarConf('mqtt', 'mqtt_print_level', 'eval')
        Topic_Base = basics.getVarConf('mqtt', 'Topic_Base', 'str').strip('/')
        Nachrichten = []
        for Name, Einheit, Quelle in STATUS_NAMEN:
            if Name in werte:
                Nachrichten.append((f"{Topic_Base}/status/{Name}", str(werte[Name])))
        nicht_gesendet = MQTT_senden(Nachrichten)
        if nicht_gesendet:
            print("ERROR mqtt_prognose: ", nicht_gesendet, " von ", len(Nachrichten), " Statuswerten nicht bestätigt")
        elif mqtt_print_level >= 1:
            print("MQTT: ", len(Nachrichten), " Statuswerte gesendet")
    except Exception as e:
        print("ERROR mqtt_prognose: Statuswerte konnten nicht gesendet werden: ", e)


if __name__ == '__main__':
    # Versionsnummer lesen
    config_v = configparser.ConfigParser()
    config_v.read('version.ini')
    prg_version = (config_v['Programm']['version'])

    config = basics.loadConfig(['mqtt'])
    mqtt_print_level = basics.getVarConf('mqtt', 'mqtt_print_level', 'eval')
    Topic_Base = basics.getVarConf('mqtt', 'Topic_Base', 'str')
    Web_URL = basics.getVarConf('mqtt', 'Web_URL', 'str')
    Web_SSL_Verify = basics.getVarConf('mqtt', 'Web_SSL_Verify', 'eval')

    nur_Test = 'test' in argv
    heute = date.today()
    for arg in argv[1:]:
        if arg.startswith('heute='):
            heute = date.fromisoformat(arg[6:])

    if mqtt_print_level >= 1:
        print("*** BEGINN mqtt_prognose: ", datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), prg_version, "***")

    if 'aufraeumen' in argv:
        # Retained Einzel-Topics der ersten Version am Broker löschen (leerer Wert)
        Nachrichten = [(Topic, '') for Topic in alte_Topics(Topic_Base)]
    else:
        try:
            Prognose = Prognose_holen(Web_URL, Web_SSL_Verify == 1)
            einmal, laufend_roh = Planung_holen()
        except Exception as e:
            print("ERROR mqtt_prognose: Daten konnten nicht gelesen werden: ", e)
            sys.exit(1)
        Nachrichten = Nachrichten_bauen(Topic_Base, Prognose, einmal, laufend_roh, heute)

    if nur_Test or mqtt_print_level >= 2:
        for Topic, Wert in Nachrichten:
            print(Topic, Wert)

    if not nur_Test:
        try:
            nicht_gesendet = MQTT_senden(Nachrichten, 'aufraeumen' in argv)
        except Exception as e:
            print("ERROR mqtt_prognose: Senden an den Broker fehlgeschlagen: ", e)
            sys.exit(1)
        if nicht_gesendet:
            print("ERROR mqtt_prognose: ", nicht_gesendet, " von ", len(Nachrichten), " Nachrichten nicht bestätigt")
            sys.exit(1)
        if mqtt_print_level >= 1:
            print(len(Nachrichten), " Nachrichten an den MQTT-Broker gesendet")

    if mqtt_print_level >= 1:
        print("*** ENDE mqtt_prognose ***")
