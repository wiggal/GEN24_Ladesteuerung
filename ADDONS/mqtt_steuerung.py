# Webanwendung über MQTT bedienen: geplanter Verbrauch, TAB LadeStrg (Modus, Ladeleistung, Akkuschonung ...) und Settings
# Aufruf aus dem Hauptverzeichnis, z.B. jede Minute im Scheduler:  ./start_PythonScript.sh ADDONS/mqtt_steuerung.py
# Testlauf ohne Schreiben:                                         ./start_PythonScript.sh ADDONS/mqtt_steuerung.py test
# Konfiguration in CONFIG/mqtt.ini bzw. CONFIG/mqtt_priv.ini (gleiche Broker-Daten wie mqtt_prognose.py)
#
# Befehls-Topics (retained senden), alle unterhalb von Topic_Base/set/ :
#   Geplanter Verbrauch (Werte in kW, 0 löscht den Eintrag):
#     geplant/<tag>/<HH>h       einmal, <tag> = heute, morgen, uebermorgen oder ein Datum YYYY-MM-DD
#     laufend/<HH>h             laufend, gilt ab heute jeden Tag zur gleichen Uhrzeit
#   TAB LadeStrg (wie die Eingabefelder der Seite):
#     modus                     auto | autooptions | ladeleistung
#     stunden                   "Stunden bis Auto" 0 bis 100, 0 = keine Übersteuerung der Config-Werte
#     akkuschonung              0 | 1 | 2   (wirkt nur bei autooptions und ladeleistung)
#     ladeleistung              Ladeleistung in W, -1 bis MaxLadung (wirkt nur bei modus ladeleistung)
#     autooptions/<Schlüssel>   Wert eines Feldes aus [AutoOptionsFelder] (html/config.ini), z.B. autooptions/MindBattLad
#   TAB Settings:
#     betrieb                   webui_aus | aus_loeschen | aus_belassen | analyse | ladesteuerung  (auch 0 bis 4)
#     betrieb_optionen          bei betrieb ladesteuerung: logging,laden,entladen,optimierung,notstrom,dynamicprice
# Rückmeldung je Befehl: Topic_Base/ack/<gleicher Pfad wie der Befehl>
#
# Funktionsweise:
#   Der letzte gesehene Wert jedes Befehls-Topics wird in ADDONS/mqtt_steuerung_last.json gespeichert.
#   Nur wenn sich der Wert am Broker gegenüber dem gespeicherten Wert geändert hat, wird er übernommen,
#   und nur wenn er sich vom Wert in CONFIG/Prog_Steuerung.sqlite unterscheidet, wird geschrieben.
#   So kann die Weboberfläche parallel bedient werden, der zuletzt geänderte Wert gilt.
#   Geschrieben wird in die Tabelle steuercodes, nur einzelne Zeilen
#   (die Weboberfläche löscht beim Speichern alle Zeilen des Schluessels und schreibt sie neu).
#   Die Werte für LadeStrg werden wie beim Speichern auf der Seite LadeStrg in die Zeilen des Schluessels
#   'ChargeOption' geschrieben (ManuelleSteuerung, Akkuschonung, FesteLadeleistung, Felder aus [AutoOptionsFelder]).
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from sys import argv
from datetime import datetime, date, timedelta
import json
import configparser
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


# Modus-Kennung in der Zeile ManuelleSteuerung (wie 1_tab_LadeSteuerung.php)
MODI = {'auto': -1, 'autooptions': -4, 'ladeleistung': -3}
# Betriebsart der Seite Settings (Zeile ProgrammStrg, Res_Feld1)
BETRIEB = {'webui_aus': 0, 'aus_loeschen': 1, 'aus_belassen': 2, 'analyse': 3, 'ladesteuerung': 4}
BETRIEB_OPTIONEN = ['logging', 'laden', 'entladen', 'optimierung', 'notstrom', 'dynamicprice']
CHARGE_PFADE = ('modus', 'stunden', 'akkuschonung', 'ladeleistung')
BETRIEB_PFADE = ('betrieb', 'betrieb_optionen')


def AutoOptionsFelder_lesen():
    # Felder des Auto-Options-Panels aus [AutoOptionsFelder] in html/config.ini und html/config_priv.ini lesen
    cp = configparser.ConfigParser(strict=False, interpolation=None)
    for Datei in ('html/config.ini', 'html/config_priv.ini'):
        try:
            cp.read(Datei, encoding='utf-8')
        except configparser.Error:
            pass  # bis zur fehlerhaften Zeile wurde bereits gelesen
    Felder = {}
    if cp.has_section('AutoOptionsFelder'):
        Block = cp['AutoOptionsFelder']
        for Nr in sorted({k.split('.')[0] for k in Block if '.' in k}):
            Key = Block.get(f'{Nr}.key')
            if not Key or Block.get(f'{Nr}.sichtbar', 'ein') != 'ein':
                continue
            Optionen = [o.split(':')[0].strip() for o in Block.get(f'{Nr}.optionen', '').split(',') if o.strip()]
            Felder[Key] = {'typ': Block.get(f'{Nr}.typ', 'prozent'), 'db_id': Block.get(f'{Nr}.db_id'),
                           'section': Block.get(f'{Nr}.section', 'Ladeberechnung'), 'optionen': Optionen}
    return Felder


def Charge_Zustand_lesen(con, jetzt, cfg, Felder):
    # Zustand wie ihn die Seite LadeStrg anzeigt: DB-Wert, wenn der Eintrag noch gültig ist, sonst der Config-Wert
    Zeilen = {Zeit: (R1, R2, O) for Zeit, R1, R2, O in con.execute(
        "SELECT Zeit, Res_Feld1, Res_Feld2, Options FROM steuercodes WHERE Schluessel = 'ChargeOption'")}

    def Ablauf(Zeit):
        try:
            return int(float(Zeilen[Zeit][2]))
        except (KeyError, TypeError, ValueError):
            return 0

    def Wert(Zeit, Config_Wert):
        if Zeit in Zeilen and Ablauf(Zeit) >= jetzt and str(Zeilen[Zeit][1]) != '':
            return str(int(float(Zeilen[Zeit][1])))
        return str(Config_Wert)

    Z = {}
    aktiv = Ablauf('ManuelleSteuerung') >= jetzt
    Modus_Nr = int(float(Zeilen['ManuelleSteuerung'][0])) if 'ManuelleSteuerung' in Zeilen else -1
    Z['modus'] = 'auto' if not aktiv else ('autooptions' if Modus_Nr == -4 else ('auto' if Modus_Nr == -1 else 'ladeleistung'))
    Z['ablauf'] = Ablauf('ManuelleSteuerung') if aktiv else 0
    Z['rest_stunden'] = max(0.0, (Z['ablauf'] - jetzt) / 3600)
    Z['akkuschonung'] = Wert('Akkuschonung', cfg('Ladeberechnung', 'Akkuschonung'))
    Z['ladeleistung'] = Wert('FesteLadeleistung', cfg('Ladeberechnung', 'FesteLadeleistung'))
    Z['felder'] = {Key: Wert(Key, cfg(F['section'], Key)) for Key, F in Felder.items()}
    return Z


def Feld_pruefen(Typ, Optionen, Wert):
    # Wert eines Auto-Options-Feldes prüfen, Rückgabe = Wert als Text
    if Typ in ('liste', 'radio'):
        if Wert not in Optionen:
            raise ValueError("erlaubt: " + ", ".join(Optionen))
        return Wert
    try:
        Zahl = int(float(Wert.replace(',', '.')))
    except ValueError:
        raise ValueError("Wert ist keine Zahl")
    if Typ == 'prozent' and not 0 <= Zahl <= 100:
        raise ValueError("Wert muss zwischen 0 und 100 liegen")
    return str(Zahl)


def zeile_schreiben(con, ID, Schluessel, Zeit, Feld1, Feld2, Options):
    # eine Zeile ersetzen, wenn sie sich geändert hat, Rückgabe = True wenn geschrieben
    alt = con.execute("SELECT Res_Feld1, Res_Feld2, Options FROM steuercodes WHERE ID = ? AND Schluessel = ?",
                      (ID, Schluessel)).fetchone()
    if alt is not None and str(alt[0]) == str(Feld1) and str(alt[1]) == str(Feld2) and str(alt[2]) == str(Options):
        return False
    con.execute("REPLACE INTO steuercodes (ID, Schluessel, Zeit, Res_Feld1, Res_Feld2, Options) VALUES (?, ?, ?, ?, ?, ?)",
                (ID, Schluessel, Zeit, Feld1, Feld2, Options))
    return True


def Charge_anwenden(con, Befehle, geaendert, jetzt):
    # Befehle der Gruppe LadeStrg übernehmen, schreibt die Zeilen des Schluessels ChargeOption wie die Seite LadeStrg
    # Rückgabe = ({Pfad: Rückmeldung}, geschrieben)
    cfg_obj = basics.loadConfig(['default', 'charge'])

    def cfg(Block, Key):
        return cfg_obj.get(Block, Key, fallback='0').strip()

    # Felder ohne Config-Wert in charge.ini werden wie auf der Seite LadeStrg übersprungen
    Felder = {K: F for K, F in AutoOptionsFelder_lesen().items() if cfg_obj.has_option(F['section'], K)}
    Z = Charge_Zustand_lesen(con, jetzt, cfg, Felder)
    Max_Ladung = int(float(cfg('Ladeberechnung', 'MaxLadung')))
    Meldung = {}
    modus_vorher = Z['modus']
    stunden_neu = None
    # Beim Wechsel von auto auf einen aktiven Modus gelten auch die am Broker stehenden Werte von akkuschonung,
    # ladeleistung und autooptions/..., wie wenn man sie auf der Seite LadeStrg vor dem Speichern eingetragen hat
    Pfade = sorted(geaendert)
    if modus_vorher == 'auto' and Befehle.get('modus', '').lower() in ('autooptions', 'ladeleistung') and 'modus' in geaendert:
        Pfade = sorted(set(geaendert) | {p for p in Befehle if p in ('akkuschonung', 'ladeleistung') or p.startswith('autooptions/')})
    for Pfad in Pfade:
        Wert = Befehle[Pfad]
        try:
            if Pfad == 'modus':
                if Wert.lower() not in MODI:
                    raise ValueError("erlaubt: auto, autooptions, ladeleistung")
                Z['modus'] = Wert.lower()
            elif Pfad == 'stunden':
                Stunden = float(Wert.replace(',', '.'))
                if not 0 <= Stunden <= 100:
                    raise ValueError("Wert muss zwischen 0 und 100 liegen")
                stunden_neu = Stunden
            elif Pfad == 'akkuschonung':
                if Wert not in ('0', '1', '2'):
                    raise ValueError("erlaubt: 0, 1, 2")
                Z['akkuschonung'] = Wert
            elif Pfad == 'ladeleistung':
                Watt = int(float(Wert.replace(',', '.')))
                if not -1 <= Watt <= Max_Ladung:
                    raise ValueError(f"Wert muss zwischen -1 und {Max_Ladung} W liegen")
                Z['ladeleistung'] = str(Watt)
            elif Pfad.startswith('autooptions/'):
                Key = Pfad.split('/', 1)[1]
                if Key not in Felder or not Felder[Key]['db_id']:
                    raise ValueError("Feld nicht in [AutoOptionsFelder] definiert")
                Z['felder'][Key] = Feld_pruefen(Felder[Key]['typ'], Felder[Key]['optionen'], Wert)
            Meldung[Pfad] = "ok"
        except ValueError as e:
            Meldung[Pfad] = f"fehler {e}"
    if all(M.startswith('fehler') for M in Meldung.values()):
        return Meldung, 0
    # zusätzlich übernommene Werte (nicht geändert) bekommen keine eigene Rückmeldung
    Meldung = {P: M for P, M in Meldung.items() if P in geaendert}

    # Gültigkeit (Zeitstempel): neu berechnen bei neuen Stunden oder beim Wechsel von auto auf einen aktiven Modus,
    # sonst bleibt der bisherige Zeitstempel erhalten
    modus = Z['modus']
    Stunden_Topic = None
    try:
        Stunden_Topic = float(Befehle['stunden'].replace(',', '.')) if 'stunden' in Befehle else None
    except ValueError:
        Stunden_Topic = None
    if Stunden_Topic is not None and not 0 <= Stunden_Topic <= 100:
        Stunden_Topic = None
    if modus == 'auto':
        Ablauf = 0
    elif stunden_neu is not None or modus_vorher == 'auto':
        Stunden = stunden_neu if stunden_neu is not None else (Stunden_Topic if Stunden_Topic is not None else Z['rest_stunden'])
        Ablauf = 0 if Stunden == 0 else int(jetzt + Stunden * 3600)
    else:
        Ablauf = Z['ablauf']
    Allgemein = ""
    if modus != 'auto' and Ablauf == 0:
        Allgemein = ", keine Wirkung, da stunden = 0 (stunden setzen)"
    Pfad_Hinweis = ", wirkt erst bei modus autooptions bzw. ladeleistung" if modus == 'auto' else ""

    geschrieben = 0
    geschrieben += zeile_schreiben(con, '23:59', 'ChargeOption', 'ManuelleSteuerung', MODI[modus],
                                   -1 if modus in ('auto', 'autooptions') else 0, Ablauf)
    geschrieben += zeile_schreiben(con, '23:58', 'ChargeOption', 'Akkuschonung', 0,
                                   int(Z['akkuschonung']) if modus != 'auto' else 0, Ablauf)
    for Key, F in Felder.items():
        if not F['db_id']:
            continue
        Config_Wert = cfg(F['section'], Key)
        geschrieben += zeile_schreiben(con, F['db_id'], 'ChargeOption', Key, 0, Z['felder'][Key],
                                       Ablauf if modus == 'autooptions' and Z['felder'][Key] != Config_Wert else 0)
    geschrieben += zeile_schreiben(con, '23:56', 'ChargeOption', 'FesteLadeleistung', 0, int(Z['ladeleistung']),
                                   Ablauf if modus == 'ladeleistung' and Z['ladeleistung'] != cfg('Ladeberechnung', 'FesteLadeleistung') else 0)
    for Pfad in Meldung:
        if Meldung[Pfad] == 'ok':
            Meldung[Pfad] += Allgemein
            if Pfad in ('stunden', 'akkuschonung', 'ladeleistung') or Pfad.startswith('autooptions/'):
                Meldung[Pfad] += Pfad_Hinweis
    if geschrieben == 0:
        for P in Meldung:
            if Meldung[P].startswith('ok'):
                Meldung[P] += " (unverändert)"
    return Meldung, geschrieben


def Betrieb_anwenden(con, Befehle, geaendert):
    # Betriebsart der Seite Settings übernehmen (Zeile ProgrammStrg, ID 23:09), Rückgabe = ({Pfad: Rückmeldung}, geschrieben)
    Meldung = {}
    alt = con.execute("SELECT Res_Feld1, Options FROM steuercodes WHERE Schluessel = 'ProgrammStrg' AND ID = '23:09'").fetchone()
    Code = int(float(alt[0])) if alt else None
    Optionen = [o for o in (alt[1] if alt and alt[1] else '').split(':') if o]
    Pfade = sorted(geaendert)
    if 'betrieb' in geaendert and 'betrieb_optionen' in Befehle and 'betrieb_optionen' not in geaendert:
        Pfade.append('betrieb_optionen')  # am Broker stehende Optionen mit übernehmen
    for Pfad in Pfade:
        Wert = Befehle[Pfad].strip()
        try:
            if Pfad == 'betrieb':
                if Wert.lower() in BETRIEB:
                    Code = BETRIEB[Wert.lower()]
                elif Wert in ('0', '1', '2', '3', '4'):
                    Code = int(Wert)
                else:
                    raise ValueError("erlaubt: " + ", ".join(BETRIEB) + " (oder 0 bis 4)")
            else:
                Liste = [o.strip().lower() for o in Wert.replace(':', ',').split(',') if o.strip()]
                falsch = [o for o in Liste if o not in BETRIEB_OPTIONEN]
                if falsch:
                    raise ValueError("unbekannt: " + ", ".join(falsch) + "; erlaubt: " + ", ".join(BETRIEB_OPTIONEN))
                Optionen = [o for o in BETRIEB_OPTIONEN if o in Liste]
            Meldung[Pfad] = "ok"
        except ValueError as e:
            Meldung[Pfad] = f"fehler {e}"
    if all(M.startswith('fehler') for M in Meldung.values()):
        return Meldung, 0
    Meldung = {P: M for P, M in Meldung.items() if P in geaendert}
    if Code is None:
        for P in Meldung:
            Meldung[P] = "fehler betrieb muss zuerst gesetzt werden"
        return Meldung, 0
    # wie die Seite Settings: Optionen nur bei Betriebsart 4 (Ladesteuerung nach Optionen)
    Options = ':'.join(Optionen) if Code == 4 else ''
    geschrieben = zeile_schreiben(con, '23:09', 'ProgrammStrg', '23:09', Code, 0, Options)
    if not geschrieben:
        for P in Meldung:
            if Meldung[P].startswith('ok'):
                Meldung[P] += " (unverändert)"
    return Meldung, geschrieben


def Befehle_anwenden(Befehle, letzte, heute, Max_kW, nur_Test=False):
    # Geänderte Befehle prüfen und in die Datenbank schreiben
    # Rückgabe = (Rückmeldungen {Pfad: Text}, Anzahl geschriebener Befehle), letzte wird aktualisiert
    Rueckmeldungen = {}
    geschrieben = 0
    neue = {Pfad: Wert for Pfad, Wert in sorted(Befehle.items()) if letzte.get(Pfad) != Wert}
    if not neue:
        return Rueckmeldungen, 0
    jetzt = time.time()
    con = sqlite3.connect(SQL_Datei, timeout=15)
    try:
        charge = [p for p in neue if p in CHARGE_PFADE or p.startswith('autooptions/')]
        betrieb = [p for p in neue if p in BETRIEB_PFADE]
        for Pfad, Wert in neue.items():
            if Pfad in charge or Pfad in betrieb:
                continue
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
        if charge:
            Meldung, n = Charge_anwenden(con, Befehle, charge, jetzt)
            Rueckmeldungen.update(Meldung)
            geschrieben += n
        if betrieb:
            Meldung, n = Betrieb_anwenden(con, Befehle, betrieb)
            Rueckmeldungen.update(Meldung)
            geschrieben += n
        for Pfad, Wert in neue.items():
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
