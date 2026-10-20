# Geplanten Verbrauch (einmal, laufend) über MQTT in die Webanwendung übernehmen
# Aufruf aus dem Hauptverzeichnis, z.B. jede Minute im Scheduler:  ./start_PythonScript.sh ADDONS/mqtt_steuerung.py
# Testlauf ohne Schreiben:                                         ./start_PythonScript.sh ADDONS/mqtt_steuerung.py test
# Konfiguration in CONFIG/mqtt.ini bzw. CONFIG/mqtt_priv.ini (gleiche Broker-Daten wie mqtt_prognose.py)
#
# Befehls-Topics (retained senden, Werte in kW, 0 löscht den Eintrag):
#   Topic_Base/set/geplant/<tag>/<HH>h    einmal, <tag> = heute, morgen, uebermorgen oder ein Datum YYYY-MM-DD
#   Topic_Base/set/laufend/<HH>h          laufend, gilt ab heute jeden Tag zur gleichen Uhrzeit
#   Beispiel: Topic_Base/set/geplant/heute/14h = 3   ->  heute um 14:00 Uhr 3 kW einplanen
# Rückmeldung je Befehl: Topic_Base/ack/<gleicher Pfad wie der Befehl>
#
# Funktionsweise:
#   Der letzte gesehene Wert jedes Befehls-Topics wird in ADDONS/mqtt_steuerung_last.json gespeichert.
#   Nur wenn sich der Wert am Broker gegenüber dem gespeicherten Wert geändert hat, wird er übernommen,
#   und nur wenn er sich vom Wert in CONFIG/Prog_Steuerung.sqlite unterscheidet, wird geschrieben.
#   So kann die Weboberfläche parallel bedient werden, der zuletzt geänderte Wert gilt.
#   Geschrieben wird in die Tabelle steuercodes, Schluessel 'Reservierung', nur einzelne Zeilen
#   (die Weboberfläche löscht beim Speichern alle Zeilen des Schluessels und schreibt sie neu).
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from sys import argv
from datetime import datetime, date, timedelta
import json
import re
import sqlite3
import time
import FUNCTIONS.functions
import ADDONS.mqtt_prognose

basics = FUNCTIONS.functions.basics()

STATUS_DATEI = os.path.join(SCRIPT_DIR, 'mqtt_steuerung_last.json')
SQL_Datei = 'CONFIG/Prog_Steuerung.sqlite'


def Befehle_holen(Topic_Base, Wartezeit=3):
    # Befehls-Topics vom Broker lesen, Rückgabe = Dictionary {Pfad nach Topic_Base/set/: Wert}
    Broker_Address = basics.getVarConf('mqtt', 'Broker_Address', 'str')
    Broker_Port = basics.getVarConf('mqtt', 'Broker_Port', 'eval')
    Befehle = {}
    Vorsilbe = Topic_Base.strip('/') + '/set/'

    def on_connect(client, userdata, flags, rc, *args):
        client.subscribe(Vorsilbe + '#', qos=1)

    def on_message(client, userdata, msg):
        if msg.topic.startswith(Vorsilbe):
            Befehle[msg.topic[len(Vorsilbe):]] = msg.payload.decode('utf-8', errors='replace').strip()

    client = ADDONS.mqtt_prognose.Client_erzeugen()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(Broker_Address, Broker_Port, 60)
    client.loop_start()
    # retained Nachrichten kommen unmittelbar nach dem Abonnieren
    time.sleep(Wartezeit)
    client.loop_stop()
    client.disconnect()
    return Befehle


def Befehl_pruefen(Pfad, Wert, heute, Max_kW):
    # Befehl prüfen und zerlegen, Rückgabe = (Art, Datum oder None, Stunde, Watt), bei Fehler ValueError
    Teile = Pfad.split('/')
    if len(Teile) == 3 and Teile[0] == 'geplant':
        Art, Tag, Std = 'geplant', Teile[1], Teile[2]
    elif len(Teile) == 2 and Teile[0] == 'laufend':
        Art, Tag, Std = 'laufend', None, Teile[1]
    else:
        raise ValueError("unbekanntes Topic")
    Treffer = re.fullmatch(r'(\d{1,2})h', Std)
    if not Treffer or int(Treffer.group(1)) > 23:
        raise ValueError("Stunde muss 00h bis 23h sein")
    Stunde = int(Treffer.group(1))
    Datum = None
    if Art == 'geplant':
        if Tag in ('heute', 'morgen', 'uebermorgen'):
            Datum = heute + timedelta(days=['heute', 'morgen', 'uebermorgen'].index(Tag))
        else:
            try:
                Datum = date.fromisoformat(Tag)
            except ValueError:
                raise ValueError("Tag muss heute, morgen, uebermorgen oder YYYY-MM-DD sein")
            if Datum < heute or Datum > heute + timedelta(days=2):
                raise ValueError("Datum muss zwischen heute und übermorgen liegen")
    try:
        kW = float(Wert.replace(',', '.'))
    except ValueError:
        raise ValueError("Wert ist keine Zahl")
    if kW < 0 or kW > Max_kW:
        raise ValueError(f"Wert muss zwischen 0 und {Max_kW} kW liegen")
    return Art, Datum, Stunde, int(round(kW * 1000))


def geplant_schreiben(con, Datum, Stunde, Watt, heute):
    # einmal (Res_Feld1) für Datum und Stunde setzen, Rückgabe = True wenn geschrieben
    Zeit = f"{Datum.isoformat()} {Stunde:02d}:00:00"
    Zeile = con.execute("SELECT Res_Feld1 FROM steuercodes WHERE Schluessel = 'Reservierung' AND Zeit = ?", (Zeit,)).fetchone()
    if Zeile is not None:
        if int(float(Zeile[0] or 0)) == Watt:
            return False
        con.execute("UPDATE steuercodes SET Res_Feld1 = ? WHERE Schluessel = 'Reservierung' AND Zeit = ?", (Watt, Zeit))
        return True
    if Watt == 0:
        return False
    # neue Zeile, ID wie in der Weboberfläche: Tageszähler (heute = 1) und Uhrzeit
    ID = f"{(Datum - heute).days + 1}-{Stunde:02d}:00"
    con.execute("REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES (?, 'Reservierung', ?, ?, 0, '')",
                (ID, Zeit, Watt))
    return True


def laufend_schreiben(con, Stunde, Watt, heute):
    # laufend (Res_Feld2) ab heute setzen: Zeile von heute bekommt den Wert, alle anderen Zeilen dieser Stunde 0,
    # damit nur dieser Wert gilt, Rückgabe = True wenn geschrieben
    geaendert = False
    Zeilen = con.execute("SELECT Zeit, Res_Feld2 FROM steuercodes WHERE Schluessel = 'Reservierung' "
                         "AND strftime('%H', Zeit) = ?", (f"{Stunde:02d}",)).fetchall()
    Zeit_heute = f"{heute.isoformat()} {Stunde:02d}:00:00"
    vorhanden = False
    for Zeit, Feld2 in Zeilen:
        Ziel = Watt if Zeit == Zeit_heute else 0
        vorhanden = vorhanden or Zeit == Zeit_heute
        if int(float(Feld2 or 0)) != Ziel:
            con.execute("UPDATE steuercodes SET Res_Feld2 = ? WHERE Schluessel = 'Reservierung' AND Zeit = ?", (Ziel, Zeit))
            geaendert = True
    if not vorhanden and Watt != 0:
        con.execute("REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES (?, 'Reservierung', ?, 0, ?, '')",
                    (f"1-{Stunde:02d}:00", Zeit_heute, Watt))
        geaendert = True
    return geaendert


def Befehle_anwenden(Befehle, letzte, heute, Max_kW, nur_Test=False):
    # Geänderte Befehle prüfen und in die Datenbank schreiben
    # Rückgabe = (Rückmeldungen {Pfad: Text}, Anzahl geschriebener Befehle), letzte wird aktualisiert
    Rueckmeldungen = {}
    geschrieben = 0
    neue = {Pfad: Wert for Pfad, Wert in sorted(Befehle.items()) if letzte.get(Pfad) != Wert}
    if not neue:
        return Rueckmeldungen, 0
    con = sqlite3.connect(SQL_Datei, timeout=15)
    try:
        for Pfad, Wert in neue.items():
            try:
                Art, Datum, Stunde, Watt = Befehl_pruefen(Pfad, Wert, heute, Max_kW)
                if Art == 'geplant':
                    gesetzt = geplant_schreiben(con, Datum, Stunde, Watt, heute)
                else:
                    gesetzt = laufend_schreiben(con, Stunde, Watt, heute)
                Rueckmeldungen[Pfad] = f"ok {Watt / 1000:.3f} kW" + ("" if gesetzt else " (unverändert)")
                geschrieben += 1 if gesetzt else 0
            except ValueError as e:
                Rueckmeldungen[Pfad] = f"fehler {e}"
            letzte[Pfad] = Wert
        if nur_Test:
            con.rollback()
        else:
            con.commit()
    finally:
        con.close()
    return Rueckmeldungen, geschrieben


if __name__ == '__main__':
    config = basics.loadConfig(['mqtt'])
    mqtt_print_level = basics.getVarConf('mqtt', 'mqtt_print_level', 'eval')
    if basics.getVarConf('mqtt', 'Steuerung_empfangen', 'eval') != 1:
        sys.exit(0)
    Topic_Base = basics.getVarConf('mqtt', 'Topic_Base', 'str').strip('/')
    Max_kW = basics.getVarConf('mqtt', 'Geplant_Max_kW', 'eval')
    nur_Test = 'test' in argv
    heute = date.today()
    for arg in argv[1:]:
        if arg.startswith('heute='):
            heute = date.fromisoformat(arg[6:])

    try:
        Befehle = Befehle_holen(Topic_Base)
    except Exception as e:
        print("ERROR mqtt_steuerung: Befehle konnten nicht vom Broker gelesen werden: ", e)
        sys.exit(1)

    try:
        with open(STATUS_DATEI, encoding='utf-8') as f:
            letzte = json.load(f)
    except (FileNotFoundError, ValueError):
        letzte = {}

    try:
        Rueckmeldungen, geschrieben = Befehle_anwenden(Befehle, letzte, heute, Max_kW, nur_Test)
    except Exception as e:
        print("ERROR mqtt_steuerung: Datenbank konnte nicht geschrieben werden: ", e)
        sys.exit(1)

    if Rueckmeldungen:
        # Meldungen nur ausgeben, wenn es Änderungen gab (der Job läuft jede Minute)
        print("*** mqtt_steuerung: ", datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), "***")
        for Pfad, Text in Rueckmeldungen.items():
            print(Pfad, "=", Befehle[Pfad], "->", Text)
        if not nur_Test:
            with open(STATUS_DATEI, 'w', encoding='utf-8') as f:
                json.dump(letzte, f, indent=1, sort_keys=True)
            try:
                nicht_gesendet = ADDONS.mqtt_prognose.MQTT_senden(
                    [(f"{Topic_Base}/ack/{Pfad}", Text) for Pfad, Text in Rueckmeldungen.items()])
                if geschrieben:
                    # Prognose-Topics sofort aktualisieren
                    nicht_gesendet += ADDONS.mqtt_prognose.prognose_senden(heute)
                if nicht_gesendet:
                    print("ERROR mqtt_steuerung: ", nicht_gesendet, " Nachrichten nicht bestätigt")
            except Exception as e:
                print("ERROR mqtt_steuerung: Rückmeldung an den Broker fehlgeschlagen: ", e)
    elif mqtt_print_level >= 2:
        print("mqtt_steuerung: keine Änderungen")
