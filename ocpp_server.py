#!/usr/bin/env python3
"""
ocpp_legacy_server.py
Produktionsfertiger OCPP-Legacy-Server (kompatibel mit websockets >=12 und <=11)
Features:
 - WebSocket OCPP listener (WS port 8887)
 - HTTP-API (Port 8080) mit /list, /meter_values, /remote_start, /remote_stop, /set_pv_mode
 - Interne DB-basierte Steuerung: apply_wallbox_settings(cp_id)
 - Automatische Sync nach BootNotification und periodisch (AUTO_SYNC_INTERVAL)
 - Sendet SetChargingProfile NUR wenn sich Werte ändern (Ampere ODER Phasen)
 - Führt Phasenumschaltung über ZWEI SetChargingProfile Calls durch (0A Limit -> Warten -> Ampere Limit + neue Phase)
 - Auffälliges ANSI-Farben-Logging (Console)
 - NEU: Stabilitäts-Guards für Phase Change (MIN_PHASE_DURATION_S) und Stop (MIN_CHARGE_DURATION_S)
 - NEU: **PV-Quellen-Guard**: Phasenumschaltung und Ladestopp (Limit 0A) erfolgen nur, 
   wenn die Steuerung aus dem PV-Überschuss-Modus (pv_mode 1 oder 2) stammt.
 - Logging bei start aus dem WebUI in /tmp/ocpp.log
 
 ==> Einstellungen in der APP
 Modus: Eco Mode AUS
 Einstellungen, Fahrzeug PHASENUMSCHALTUNG: Automatisch
 Internet, OCPP => aktiviert
 Füge SN (seriennummer) zur URL
 WS =< Host: IP:8887

"""

import asyncio
import json
import logging
# Nicht benötigte Logginmeldungen unterdrücken
# mögliche Log-Level: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger("OCPP-Legacy")
logger.setLevel(logging.ERROR)

from datetime import datetime, timezone, timedelta
from aiohttp import web
import FUNCTIONS.functions
basics = FUNCTIONS.functions.basics()
config = basics.loadConfig(['default', 'charge'])

# Hybrid Import für websockets (neu/alt)
try:
    # websockets >=12
    from websockets.server import serve as ws_serve
    USING_NEW_WEBSOCKETS = True
    print("Using NEW websockets.server.serve API")
except Exception:
    # websockets <=11
    from websockets.asyncio.server import serve as ws_serve
    USING_LEGACY_WEBSOCKETS = True
    print("Using LEGACY websockets.asyncio.server.serve API")

# ----------------------------
# Konfiguration Variablen
# ----------------------------
# zukünftig evtl. aus INI-Datei oder DB  #entWIGGlung
# Auto-sync interval in Sekunden
AUTO_SYNC_INTERVAL = 20
# NEUE GUARDS FÜR STABILITÄT
MIN_PHASE_DURATION_S = 180   # 3 Minuten (180 Sekunden) Phase halten
MIN_CHARGE_DURATION_S = 600  #10 Minuten (600 Sekunden) Laden halten
# Ports
WS_PORT = 8887
HTTP_PORT = 8080

# Feste Programminteren Variablen ??  #entWIGGlung
# leichte zeitliche Vorverlegung der Zeitstempel, die Ihr OCPP-Server an die Wallbox sendet
TIME_SHIFT_SECONDS = 5
DEFAULT_CONNECTOR_ID = 1
DEFAULT_IDTAG = "WattpilotUser"
# OCPP Subprotocols (wird an ws_serve übergeben)
OCPP_PROTOCOLS = ['ocpp1.6', 'ocpp2.0.1', 'ocpp1.5']

# ----------------------------
# Auffälliges Console-Logging
# ----------------------------
def cinfo(msg):  print(f"ℹ️  INFO: {msg}")
def cok(msg):    print(f"✅ OK:   {msg}")
def cwarn(msg):  print(f"⚠️- WARN: {msg}")
def cerr(msg):   print(f"❌ ERROR:{msg}")
def cnote(msg):  print(f"✏️  NOTE: {msg}")

# ----------------------------
# In-Memory Stores
# ----------------------------
connected_charge_points = {}     # cp_id -> ChargePointHandler
meter_values_store = {}
status_store = {}
pv_mode = {}
current_limit_store = {} # Letztes gesendetes Ampere-Limit
phase_limit_store = {}   # Letzte gesendete Phasen-Anzahl (1 oder 3)
debug_store = {}
transaction_id_store = {}

# NEUE STORES FÜR STABILITÄT
last_phase_change_timestamp = {} # cp_id -> datetime.datetime
transaction_start_timestamp = {} # cp_id -> datetime.datetime

# ----------------------------
# DB Helper (safe fallback)
# ----------------------------
import FUNCTIONS.SQLall
# Annahme: cwarn, cinfo, basics, connected_charge_points, get_current_power sind an anderer Stelle definiert
# Da die Definition fehlt, nehme ich an, dass dies Utility-Funktionen sind.
# Beispielhafte Definitionen, falls der Code außerhalb des ursprünglichen Projekts ausgeführt wird:
# def cwarn(msg): print(f"WARN: {msg}")
# def cinfo(msg): print(f"INFO: {msg}")
# class basics:
#     @staticmethod
#     def get_inverter_class(class_type):
#         class DummyApi:
#             def get_API(self):
#                 # Simuliere aktuelle Einspeisung (hier: 3500W Überschuss)
#                 return {'aktuelleEinspeisung': -3500}
#         return DummyApi
# connected_charge_points = {}
# def get_current_power(cp_id): return 0

def get_wallbox_steuerdaten(cp_id=None):
    """
    Liest aus der Datenbank mittels FUNCTIONS.SQLall.sqlall().getSQLsteuerdaten('wallbox')
    Rückgabe: (amp: float, phases: str, pv_mode: float, is_pv_controlled: bool)
    Wird nur einmal pro Sync-Zyklus/BootNotification/API-Call aufgerufen.
    """
    # Setze Default-Werte für den Fehlerfall
    amp_max = 16.0
    amp_min = 6.0
    phases = "3"
    pv_mode = 0.0
    amp = amp_max

    try:
        # Falls dein Projekt MODULE anders heißt, passe das hier an.
        import FUNCTIONS.SQLall
        sqlall = FUNCTIONS.SQLall.sqlall()
        data = sqlall.getSQLsteuerdaten('wallbox', 'CONFIG/Prog_Steuerung.sqlite')
    except Exception as e:
        cwarn(f"DB-Zugriff fehlgeschlagen oder FUNCTIONS nicht vorhanden: {e}")
        # Wenn DB-Zugriff fehlschlägt, gelten Default-Werte und KEINE PV-Steuerung
        return amp_max, phases, pv_mode, False

    if not data or '1' not in data:
        cwarn("Keine Wallbox-Daten in DB gefunden → Verwende Default 16A / 3 Phasen / PV Off")
        return amp_max, phases, pv_mode, False

    try:
        row = data['1']
        parts = row.get('Options', '').split(',')

        # --- amp_min bestimmen ---
        try:
            amp_min = float(parts[0])
        except (ValueError, IndexError):
            amp_min = 6.0
        # Untere Grenze für amp_min (Protokoll-Limit)
        if amp_min < 6:
            amp_min = 6.0

        # --- amp_max bestimmen (die aus der DB eingeschränkte Stromstärke) ---
        try:
            amp_max = float(parts[1])
        except (ValueError, IndexError):
            amp_max = 16.0
        # Amp_max darf nicht kleiner als amp_min sein
        if amp_max < amp_min:
            amp_max = amp_min
        # amp_max darf höchstens 16 sein (Hard-Limit)
        if amp_max > 16:
            amp_max = 16.0

        phases = str(row.get('Res_Feld2', '0')) # '1', '3' oder '0' (Auto)
        pv_mode = float(row.get('Res_Feld1', '0')) # 0.0=Stop, >0.0=PV-Laden

        cinfo(f"DB-Steuerdaten geladen: amp_max={amp_max}A, phases={phases}, pv_mode={pv_mode}")
    except Exception as e:
        cwarn(f"Fehler beim Parsen der DB-Daten: {e} → Defaults verwendet")
        pv_mode = 0
        phases = "3"
        amp_max = 6
        amp_min = 6

    amp = amp_max # Initialer Wert für den Fall ohne PV-Steuerung

    is_pv_controlled = False # Initialisierung des Flags

    # Hier nun die Aktuelle Einspeisung holen um die PV Modi zu versorgen
    if pv_mode == 1 or pv_mode == 2:
        is_pv_controlled = True # Steuerung erfolgt durch PV-Überschuss

        # API Klasse dynamisch laden
        try:
            InverterApi = basics.get_inverter_class(class_type="Api")
        except ImportError as e:
            cwarn(f"Inverter API konnte nicht geladen werden: {e}")
            # Im Falle eines Fehlers bei der API-Klasse, Fallback auf DB-Werte ohne PV-Steuerung
            return amp_max, phases, pv_mode, False

        inverter_api = InverterApi()
        API = inverter_api.get_API()

        # Aktuellen Ladestrom (W) holen.
        current_charge_power = 0
        if cp_id and cp_id in connected_charge_points:
            current_charge_power = get_current_power(cp_id) # Leistung aus MeterValues holen

        # Überschuss = max(0, -aktuelleEinspeisung) + aktueller Ladestrom (current_charge_power)
        # Dies entspricht: Einspeisung ins Netz + Ladung der Wallbox = Gesamtüberschuss
        ueberschuss = max(0, (-API['aktuelleEinspeisung']+current_charge_power))

        cinfo(f"Aktuelle Einspeisung (negativ=Überschuss): {API['aktuelleEinspeisung']}W, Ladestrom ({current_charge_power}W). Gesamter Überschuss (inkl. Ladung): {ueberschuss}W")

        # Hier Ueberschussladen: Berechnung der maximal möglichen Stromstärke (A)
        amp = 0
        amp_1 = int(ueberschuss / 230 / 1)
        amp_3 = int(ueberschuss / 230 / 3)

        # --- ANGEPASSTE LOGIK: 3P-Wunsch mit 1P-Fallback und Begrenzung durch amp_max ---

        # 1. Fall: Explizit 1-phasig gewollt ('1')
        if phases == "1":
            # Laden nur, wenn 1P-Minimum (6A) erreicht wird
            if amp_1 >= 6:
                amp = min(amp_1, amp_max)
            else:
                amp = 0

        # 2. Fall: 3-phasig gewollt ('3') oder Auto ('0') -> Prüfen auf Fallback
        elif phases == "3" or phases == "0":

            # Prüfen auf 3-Phasen-Laden (Priorität)
            if amp_3 >= 6:
                phases = "3"
                amp = min(amp_3, amp_max)

            # Fallback auf 1-Phasen-Laden, wenn 3P nicht möglich, aber 1P reicht
            elif amp_1 >= 6:
                phases = "1"
                amp = min(amp_1, amp_max)

            # Kein Laden möglich
            else:
                amp = 0

        # --- ENDE ANGEPASSTE LOGIK ---

    # für PV-Modus MIN+PV (pv_mode = 2) immer mindestens amp_min setzen
    if pv_mode == 2:
        if amp < amp_min:
            # Stellt sicher, dass MIN+PV Laden mindestens mit amp_min (max. amp_max) erfolgt
            amp = min(amp_min, amp_max)

    return amp, phases, pv_mode, is_pv_controlled
def WIGGAL_get_wallbox_steuerdaten(cp_id=None):
    """
    Liest aus der Datenbank mittels FUNCTIONS.SQLall.sqlall().getSQLsteuerdaten('wallbox')
    Rückgabe: (amp: float, phases: str, pv_mode: float, is_pv_controlled: bool)
    Wird nur einmal pro Sync-Zyklus/BootNotification/API-Call aufgerufen.
    """
    try:
        # Falls dein Projekt MODULE anders heißt, passe das hier an.
        import FUNCTIONS.SQLall
        sqlall = FUNCTIONS.SQLall.sqlall()
        data = sqlall.getSQLsteuerdaten('wallbox', 'CONFIG/Prog_Steuerung.sqlite')
    except Exception as e:
        cwarn(f"DB-Zugriff fehlgeschlagen oder FUNCTIONS nicht vorhanden: {e}")
        # Wenn DB-Zugriff fehlschlägt, gelten Default-Werte und KEINE PV-Steuerung
        return 16.0, "3", 0.0, False 

    if not data or '1' not in data:
        cwarn("Keine Wallbox-Daten in DB gefunden → Verwende Default 16A / 3 Phasen / PV Off")
        return 16.0, "3", 0.0, False
    try:
        row = data['1']
        parts = row.get('Options', '').split(',')
        # --- amp_min bestimmen ---
        try:
            amp_min = float(parts[0])
        except (ValueError, IndexError):
            amp_min = 6.0
        # Untere Grenze für amp_min
        if amp_min < 6:
            amp_min = 6.0
        # --- amp_max bestimmen ---
        try:
            amp_max = float(parts[1])
        except (ValueError, IndexError):
            amp_max = 16.0
        # Amp_max darf nicht kleiner als amp_min sein
        if amp_max < amp_min:
            amp_max = amp_min
        # amp_max darf höchstens 16 sein
        if amp_max > 16:
            amp_max = 16.0
        phases = str(row.get('Res_Feld2', '0')) # '1' oder '3'
        pv_mode = float(row.get('Res_Feld1', '0')) # 0.0=Stop, >0.0=PV-Laden
        cinfo(f"DB-Steuerdaten geladen: amp_max={amp_max}A, phases={phases}, pv_mode={pv_mode}")
    except Exception as e:
        cwarn(f"Fehler beim Parsen der DB-Daten: {e} → Defaults verwendet")
        pv_mode = 0
        phases = "3"
        amp_max = 6
    amp = amp_max
    
    is_pv_controlled = False # Initialisierung des neuen Flags

    # Hier nun die Aktuelle Einspeisung holen um die PV Modi zu versorgen  #entWIGGlung
    if pv_mode == 1 or pv_mode == 2:
        is_pv_controlled = True # Steuerung erfolgt durch PV-Überschuss
        # API Klasse dynamisch laden
        try:
            InverterApi = basics.get_inverter_class(class_type="Api")
        except ImportError as e:
            print(e)  
            # Im Falle eines Fehlers bei der API-Klasse, Fallback auf DB-Werte ohne PV-Steuerung
            return amp_max, phases, pv_mode, False 
        inverter_api = InverterApi()
        API = inverter_api.get_API()
        
        # Aktuellen Ladestrom (W) holen. Nur wenn cp_id übergeben wurde.
        current_charge_power = 0
        if cp_id and cp_id in connected_charge_points:
            # Holt die Ladung NUR des Charge Points, der diese Berechnung triggert
            current_charge_power = get_current_power(cp_id) # Leistung aus MeterValues holen

        # Überschuss = max(0, -aktuelleEinspeisung) + aktueller Ladestrom (current_charge_power)
        # Dies entspricht: Einspeisung ins Netz + Ladung der Wallbox = Gesamtüberschuss
        ueberschuss = max(0, (-API['aktuelleEinspeisung']+current_charge_power))

        cinfo(f"Aktuelle Einspeisung (negativ=Überschuss): {API['aktuelleEinspeisung']}W, Ladestrom ({current_charge_power if current_charge_power else 'Unbekannt'}): {current_charge_power}W. Gesamter Überschuss (inkl. Ladung): {ueberschuss}W")

        # Hier Ueberschussladen je nach phases: 0 => auto
        amp = 0
        amp_1 = int(ueberschuss/230/1)
        amp_3 = int(ueberschuss/230/3)
        if (phases == "1"):
            amp = 0 if amp_1 < 6 else min(amp_1, 16)
        if (phases == "3"):
            amp = 0 if amp_3 < 6 else min(amp_3, 16)
        if (phases == "0"):
            if (amp_3 > 6):
                phases = "3"
                amp = min(amp_3, 16)
            if (amp_1 > 6):
                phases = "1"
                amp = min(amp_1, 16)
             
    # für PV-Modus MIN+PV immer mindestens amp_min setzen
    if pv_mode == 2:
        if amp < amp_min:
            amp = amp_min

    return amp, phases, pv_mode, is_pv_controlled

# ----------------------------
# ChargePoint Handler
# ----------------------------
class ChargePointHandler:
    """Behandelt eine einzelne WebSocket-Verbindung (ein Charge Point)."""

    def __init__(self, cp_id, websocket):
        self.cp_id = cp_id
        self.websocket = websocket

    def get_future_utc_timestamp(self, seconds=TIME_SHIFT_SECONDS):
        return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()

    async def send_call_result(self, unique_id, payload=None):
        """Sendet OCPP CALLRESULT: [3, uniqueId, payload]"""
        if payload is None:
            payload = {}
        msg = [3, unique_id, payload]
        try:
            await self.websocket.send(json.dumps(msg))
            logger.debug(f"Sent CALLRESULT to {self.cp_id}: {msg}")
            debug_store.setdefault(self.cp_id, []).append({"sent": msg, "timestamp": self.get_future_utc_timestamp()})
        except Exception as e:
            logger.exception(f"Fehler beim Senden CALLRESULT an {self.cp_id}: {e}")

    async def send_call(self, action, payload=None):
        """Sendet OCPP CALL: [2, uniqueId, action, payload]"""
        if payload is None:
            payload = {}
        unique_id = str(int((datetime.now(timezone.utc) + timedelta(seconds=TIME_SHIFT_SECONDS)).timestamp() * 1000))
        msg = [2, unique_id, action, payload]
        try:
            await self.websocket.send(json.dumps(msg))
            logger.debug(f"Sent CALL to {self.cp_id}: {msg}")
            debug_store.setdefault(self.cp_id, []).append({"sent": msg, "timestamp": self.get_future_utc_timestamp()})
            return unique_id
        except Exception as e:
            logger.exception(f"Fehler beim Senden CALL an {self.cp_id}: {e}")
            return None

    async def start(self):
        # initial values
        status_store[self.cp_id] = "Available"
        meter_values_store[self.cp_id] = {"power": 0, "current": 0, "energy": 0}
        current_limit_store[self.cp_id] = None # Ampere-Limit (z.B. 16.0)
        phase_limit_store[self.cp_id] = None    # Phasen-Limit (z.B. 3)
        transaction_id_store[self.cp_id] = None
        debug_store[self.cp_id] = []
        
        # Setze den Zeitstempel in die Vergangenheit, um den PHASE_CHANGE_GUARD beim Start zu umgehen.
        # Die Differenz ist größer als MIN_PHASE_DURATION_S , daher ist der erste Wechsel erlaubt.
        last_phase_change_timestamp[self.cp_id] = datetime.now() - timedelta(seconds=MIN_PHASE_DURATION_S + 10)
        transaction_start_timestamp[self.cp_id] = None # Zunächst keine Transaktion

        # async for loop handles incoming messages
        try:
            async for message in self.websocket:
                await self.handle_message(message)
        except Exception as e:
            logger.exception(f"WebSocket-Loop für {self.cp_id} beendet mit Fehler: {e}")

    async def handle_message(self, message):
        """
        Erwartet OCPP-Nachrichten als JSON-Array.
        message[0] = messageTypeId (2=CALL, 3=CALLRESULT, 4=CALLERROR)
        """
        try:
            data = json.loads(message)
            debug_store.setdefault(self.cp_id, []).append({"received": data, "timestamp": self.get_future_utc_timestamp()})
        except Exception as e:
            logger.error(f"Ungültige JSON-Nachricht von {self.cp_id}: {e}")
            return

        if not isinstance(data, list) or len(data) < 2:
            logger.error(f"Ungültiges OCPP-Format von {self.cp_id}: {data}")
            return

        message_type = data[0]
        unique_id = data[1] if len(data) > 1 else None

        # -----------------------
        # Incoming CALL (Client -> Server)
        # -----------------------
        if message_type == 2:
            if len(data) < 4:
                logger.error(f"Ungültiges CALL Format von {self.cp_id}: {data}")
                return
            action = data[2]
            payload = data[3]
            logger.info(f"[{self.cp_id}] Received CALL action={action}")

            if action == "BootNotification":
                # Reply an Client
                await self.send_call_result(unique_id, {
                    "currentTime": self.get_future_utc_timestamp(),
                    "interval": 300,
                    "status": "Accepted"
                })

                # DB-Werte holen (NUR HIER!) - NEU: is_pv_controlled
                amp_max, phases, pv_mode_val, is_pv_controlled = get_wallbox_steuerdaten(cp_id=self.cp_id)

                # Sofort Sync mit DB-Werten starten (Daten werden übergeben)
                asyncio.create_task(apply_wallbox_settings(self.cp_id, amp_max, phases, pv_mode_val, is_pv_controlled))

            elif action == "Heartbeat":
                await self.send_call_result(unique_id, {"currentTime": self.get_future_utc_timestamp()})

            elif action == "StatusNotification":
                status_store[self.cp_id] = payload.get("status", status_store.get(self.cp_id, "Unknown"))
                await self.send_call_result(unique_id)

            elif action == "MeterValues":
                if payload.get("transactionId"):
                    transaction_id_store[self.cp_id] = payload["transactionId"]
                # ACHTUNG: Der MeterValues Store ist eine komplexe Struktur.
                # Wir speichern hier die komplette Payload, um den 'power' Wert abrufen zu können.
                meter_values_store[self.cp_id] = payload
                await self.send_call_result(unique_id)

            elif action == "StartTransaction":
                tx_id = int(datetime.now(timezone.utc).timestamp())
                transaction_id_store[self.cp_id] = tx_id
                status_store[self.cp_id] = "Charging"
                
                # Startzeitpunkt setzen, da eine neue Transaktion beginnt
                transaction_start_timestamp[self.cp_id] = datetime.now()
                
                await self.send_call_result(unique_id, {"idTagInfo": {"status": "Accepted"}, "transactionId": tx_id})
                logger.info(f"[{self.cp_id}] StartTransaction accepted tx={tx_id}")

            elif action == "StopTransaction":
                transaction_id_store[self.cp_id] = None
                status_store[self.cp_id] = "Available"
                
                # Startzeitpunkt zurücksetzen, da Transaktion gestoppt
                transaction_start_timestamp[self.cp_id] = None
                
                await self.send_call_result(unique_id, {"idTagInfo": {"status": "Accepted"}})
                logger.info(f"[{self.cp_id}] StopTransaction accepted")

            else:
                # Unknown call - reply empty
                logger.warning(f"[{self.cp_id}] Unbekannte CALL Aktion: {action}")
                await self.send_call_result(unique_id)

        # -----------------------
        # CALLRESULT (Antwort auf einen Server-Call)
        # -----------------------
        elif message_type == 3:
            # payload may be present in data[2]
            logger.debug(f"[{self.cp_id}] CALLRESULT empfangen: {data}")

        # -----------------------
        # CALLERROR
        # -----------------------
        elif message_type == 4:
            logger.error(f"[{self.cp_id}] CALLERROR empfangen: {data}")

        else:
            logger.error(f"[{cp_id}] Unbekannter messageType: {data}")

# ----------------------------
# Interne Steuer-Logik (Optimiert)
# ----------------------------
def get_current_power(cp_id):
    """Extrahiert den Power.Active.Import Wert aus den MeterValues."""
    meter_data = meter_values_store.get(cp_id)
    if not meter_data or 'meterValue' not in meter_data:
        return 0
    
    # Durchsuchen der sampledValue Listen nach dem Messwert
    for meter_value in meter_data['meterValue']:
        if 'sampledValue' in meter_value:
            for sample in meter_value['sampledValue']:
                # Suche nach dem globalen Wert Power.Active.Import
                if sample.get('measurand') == 'Power.Active.Import' and 'phase' not in sample:
                    try:
                        return float(sample.get('value', 0))
                    except ValueError:
                        return 0
    return 0

async def apply_wallbox_settings(cp_id, amp, phases, pv_mode_val, is_pv_controlled):
    """
    Wendest die gewünschten Ampere- und Phasen-Werte über SetChargingProfile an.
    Werte werden per Parameter übergeben. Enthält Phase- und Stop-Guards.
    """
    if cp_id not in connected_charge_points:
        cwarn(f"apply_wallbox_settings: Charge Point {cp_id} nicht verbunden.")
        return False

    cp = connected_charge_points[cp_id]

    # Der aktuell gewünschte Limit-Wert (0A wenn pv_mode_val=0.0)
    # Beachte: Ampere wird auf 0A gesetzt, wenn der Modus 0.0 (Stop) ist.
    amp_desired = amp if pv_mode_val != 0.0 else 0.0
    # Die aktuell gewünschte Phasenanzahl (umgewandelt in Zahl 1 oder 3)
    ocpp_phases_value = 1 if phases == "1" else 3 

    # Stores sicherstellen (damit der erste Vergleich funktioniert)
    current_limit_store.setdefault(cp_id, None)
    phase_limit_store.setdefault(cp_id, None)
    # Stabilitäts-Stores sicherstellen (mit Fallback auf jetzt)
    last_phase_change_timestamp.setdefault(cp_id, datetime.now())
    transaction_start_timestamp.setdefault(cp_id, None)
    
    # Zustand prüfen
    amp_changed = current_limit_store.get(cp_id) != amp_desired
    phase_changed = phase_limit_store.get(cp_id) != ocpp_phases_value
    
    # Die tatsächliche Phase, die wir senden werden (Standard: aktuell gesendeter Wert)
    final_ocpp_phases_value = phase_limit_store.get(cp_id)
    if final_ocpp_phases_value is None:
        final_ocpp_phases_value = ocpp_phases_value # Fallback bei Erstverbindung

    cinfo(f"[{cp_id}] Prüfe Sync: PV-Mode={pv_mode_val}, PV-Steuerung={is_pv_controlled}, Wunsch: {amp_desired}A/{ocpp_phases_value}P. Aktuell: {current_limit_store.get(cp_id)}A/{phase_limit_store.get(cp_id)}P")
    
    pv_guard_active = False # Flag für geblockte PV-Aktionen
    
    # -----------------------
    # 1. PHASE CHANGE GUARD (Prüfung)
    # -----------------------
    if phase_changed:
        # NEUE LOGIK: Initialen Wechsel (None -> X) immer zulassen
        is_initial_change = phase_limit_store.get(cp_id) is None

        if phase_changed: # Prüfe, ob phase_changed immer noch True ist (nach PV-Guard Check)
            # Zeitlicher Guard: Gilt für alle nicht-initialen Wechsel, die erlaubt sind.
            time_since_last_change = (datetime.now() - last_phase_change_timestamp.get(cp_id)).total_seconds()

            # 🛑 ÄNDERUNG: Zeitlicher Guard greift nur, wenn:
            # 1. Die Zeit unterschritten wurde (< MIN_PHASE_DURATION_S)
            # 2. Es KEIN initialer Wechsel ist (not is_initial_change)
            # 3. Die Steuerung ÜBER PV erfolgt (is_pv_controlled)
            if time_since_last_change < MIN_PHASE_DURATION_S and not is_initial_change and is_pv_controlled:
                cwarn(f"[{cp_id}] 🛑 PHASE GUARD (Zeit/PV): Phasenwechsel ({phase_limit_store.get(cp_id)}->{ocpp_phases_value}) abgelehnt. Nur {round(time_since_last_change)}s vergangen. Minimum: {MIN_PHASE_DURATION_S}s.")
                # Setze gewünschte Phase zurück auf aktuelle Phase, da Guard aktiv ist
                ocpp_phases_value = phase_limit_store.get(cp_id)
                phase_changed = False # Deaktiviere Phasenwechsel für den Rest der Logik
            else:
                # Der Wechsel ist erlaubt, wenn:
                # 1. Es ein initialer Wechsel ist (is_initial_change=True)
                # 2. Die Zeit OK ist (time_since_last_change >= MIN_PHASE_DURATION_S)
                # 3. KEINE PV-Steuerung aktiv ist (is_pv_controlled=False)
                cnote(f"[{cp_id}] ✅ PHASE CHANGE: Wechsel ({phase_limit_store.get(cp_id)}->{ocpp_phases_value}) erlaubt. (Initial, Zeit ({time_since_last_change}) OK, oder PV-Guard nicht erforderlich).")
                final_ocpp_phases_value = ocpp_phases_value
    
    # -----------------------
    # 2. Laden starten/stoppen (RemoteStart/Stop) Logik
    # -----------------------
    status = status_store.get(cp_id)
    active_tx_id = transaction_id_store.get(cp_id)
    
    if amp_desired > 0.0:
        # Laden starten (Start ist immer erlaubt)
        if status in ["Available", "AvailableRequested", "SuspendedEVSE", "Finishing"]:
            await cp.send_call("RemoteStartTransaction", {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG})
            status_store[cp_id] = "ChargingRequested"
            # 🕑 Setze Startzeitpunkt, wenn Laden beginnt
            if not transaction_start_timestamp.get(cp_id):
                transaction_start_timestamp[cp_id] = datetime.now()
            cinfo(f"[{cp_id}] Laden gestartet (amp={amp_desired}A, RemoteStart)")
            
    else:
        # Laden stoppen (Limit 0A)
        
        can_stop_by_guard = True # Standardmäßig ist Stopp erlaubt
        
        # -----------------------
        # 4a. STOP GUARD (Zeitliche Prüfung, NUR bei PV-Steuerung)
        # -----------------------
        # Der Time Guard gilt NUR, wenn die Steuerung über den PV-Modus (1 oder 2) läuft.
        if is_pv_controlled:
            if transaction_start_timestamp.get(cp_id):
                charging_duration = (datetime.now() - transaction_start_timestamp.get(cp_id)).total_seconds()
                
                # Prüfe, ob die Mindestladezeit unterschritten wurde
                if charging_duration < MIN_CHARGE_DURATION_S:
                    # Guard blockiert den Stopp
                    cwarn(f"[{cp_id}] 🛑 STOP GUARD (Zeit): Stop (0A) abgelehnt. Nur {round(charging_duration)}s geladen. Minimum: {MIN_CHARGE_DURATION_S}s.")
                    can_stop_by_guard = False
                else:
                    cnote(f"[{cp_id}] ✅ STOP Laden erlaubt. (Initial, Zeit ({charging_duration}) OK.")
                    
        else:
            # pv_mode_val=0.0 ABER is_pv_controlled=False (z.B. User hat Eco Mode OFF/Stop gedrückt).
            # Der Stopp wird als explizit und vom User gewünscht betrachtet (Guard wird übersprungen).
            cnote(f"[{cp_id}] Stop (0A) gewünscht durch pv_mode={pv_mode_val}. Guard übersprungen, da PV-Steuerung inaktiv.")


        # -----------------------
        # 4b. Override und Stopp-Ausführung
        # -----------------------
        
        if not can_stop_by_guard:
            # Guard hat Stop verhindert: Override amp_desired von 0.0 auf 6.0A
            fallback_limit = 6.0 
            amp_desired = fallback_limit 
            pv_guard_active = True 
            cwarn(f"[{cp_id}] ❗ STOP GUARD aktiv. Setze Ladelimit auf {fallback_limit}A zur Vermeidung eines Stopps.")
        
        else: # Stopp ist erlaubt (amp_desired ist 0.0)
            if active_tx_id:
                await cp.send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                status_store[cp_id] = "AvailableRequested"
                # 🕑 Setze Startzeitpunkt zurück, wenn Laden stoppt
                transaction_start_timestamp[cp_id] = None 
                cnote(f"[{cp_id}] Laden gestoppt (amp=0.0A, RemoteStop als Fallback)")
            elif status not in ["Available", "AvailableRequested"]:
                status_store[cp_id] = "Available"
                # 🕑 Setze Startzeitpunkt zurück
                transaction_start_timestamp[cp_id] = None 
                cnote(f"[{cp_id}] Status auf Available gesetzt.")


    # Re-check amp_changed, falls Ampere durch Guard von 0.0 auf 6.0 überschrieben wurde
    amp_changed = current_limit_store.get(cp_id) != amp_desired
    
    # -----------------------
    # 3. Finales Limit senden, falls Ampere ODER Phase geändert wurde
    # -----------------------
    if amp_changed or phase_changed:
        
        # --- PHASE CHANGE VORBEREITUNG: 0A Limit senden, wenn Phase gewechselt werden muss ---
        if phase_changed and not is_initial_change: # 0A-Stop nur bei ECHTEN Wechseln (Nicht bei None->X)
            # phase_changed ist hier True, wenn der PV-Quellen-Guard und der Zeit-Guard passiert wurden
            cinfo(f"[{cp_id}] Phase Änderung erkannt: {phase_limit_store.get(cp_id)} -> {final_ocpp_phases_value}. Starte 0A-Stop Prozedur.")
            
            current_power = get_current_power(cp_id)
            if current_power > 50:
                cinfo(f"[{cp_id}] Aktive Leistung {current_power}W. Sende 0A Limit + neue Phase.")
                
                # Senden des 0A Limits ZUSAMMEN mit der NEUEN Phase
                payload_stop_zero_amp = {
                    "connectorId": DEFAULT_CONNECTOR_ID,
                    "csChargingProfiles": {
                        "chargingProfileId": 1,
                        "stackLevel": 1,
                        "chargingProfilePurpose": "TxDefaultProfile",
                        "chargingProfileKind": "Absolute",
                        "recurrencyKind": "Daily",
                        "chargingSchedule": {
                            "chargingRateUnit": "A",
                            "chargingSchedulePeriod": [{
                                "startPeriod": 0, 
                                "limit": 0.0, # 0 Ampere
                                "numberPhases": final_ocpp_phases_value # Phase ist die neue Phase!
                            }]
                        }
                    }
                }
                await cp.send_call("SetChargingProfile", payload_stop_zero_amp)
                current_limit_store[cp_id] = 0.0
                # Der Phasenwert wird HIER auf die neue Phase gesetzt, damit der nächste SetChargingProfile Call sie verwendet
                phase_limit_store[cp_id] = final_ocpp_phases_value
                # 🕑 Setze Zeitstempel für Phase Change, da erfolgreich begonnen
                last_phase_change_timestamp[cp_id] = datetime.now()
                
                # --- WARTE AUF POWER=0 ---
                for i in range(15): # Max 15 Sekunden warten
                    await asyncio.sleep(1)
                    current_power = get_current_power(cp_id)

                    if current_power < 50:
                        cok(f"[{cp_id}] Leistung < 50W nach {i+1}s. Führe Phasenwechsel-Abschluss durch.")
                        break
                else:
                    cwarn(f"[{cp_id}] WARNUNG: Leistung ist nach 15s noch hoch ({current_power}W). Sende finales Limit.")
            else:
                 cnote(f"[{cp_id}] Aktive Leistung {current_power}W. Kein 0A-Stop notwendig.")

        # -----------------------
        # 3. Finales Limit senden (mit korrekter Phase)
        # -----------------------
        
        cinfo(f"[{cp_id}] Sende finales Limit: {amp_desired}A an Phase {final_ocpp_phases_value}.")

        payload_final_limit = {
            "connectorId": DEFAULT_CONNECTOR_ID,
            "csChargingProfiles": {
                "chargingProfileId": 1,
                "stackLevel": 1,
                "chargingProfilePurpose": "TxDefaultProfile",
                "chargingProfileKind": "Absolute",
                "recurrencyKind": "Daily",
                "chargingSchedule": {
                    "chargingRateUnit": "A",
                    "chargingSchedulePeriod": [{
                        "startPeriod": 0, 
                        "limit": amp_desired,
                        "numberPhases": final_ocpp_phases_value # Phase ist entweder die aktuelle oder die neue
                    }]
                }
            }
        }
        await cp.send_call("SetChargingProfile", payload_final_limit)
        
        # Stores auf finalen Wert setzen
        current_limit_store[cp_id] = amp_desired
        phase_limit_store[cp_id] = final_ocpp_phases_value 

        # Wartezeit nach erfolgreichem Phasenwechsel und neuem Limit
        if phase_changed: # Prüfe, ob die Phase in diesem Zyklus erfolgreich geändert wurde
            # Wir warten kurz, damit die Wallbox/API den neuen Ladestatus melden kann, bevor die Regelung neu startet.
            cnote(f"[{cp_id}] ⏳ COOLDOWN: Warte 3 Sekunden nach Phasenwechsel ({final_ocpp_phases_value}P), um API-Sync zu ermöglichen.")
            await asyncio.sleep(3) # 3 Sekunden sollten in den meisten Fällen ausreichen
        
        cok(f"[{cp_id}] Ampere/Phase erfolgreich gesetzt: {amp_desired}A / {final_ocpp_phases_value}P")

    else:
        cnote(f"[{cp_id}] Ampere/Phase unverändert ({amp_desired}A / {final_ocpp_phases_value}P)")

    return True


# ----------------------------
# WebSocket on_connect
# ----------------------------
async def on_connect(websocket, path):
    """
    WebSocket-Eingang: erstellt einen ChargePointHandler pro Verbindung
    Parameter-Signatur ist 'websocket, path' um mit websockets>=12 kompatibel zu sein.
    """
    # determine cp_id: prefer path (/ChargePoint001) else subprotocol else "Unknown"
    cp_id_from_path = path.strip('/') if path else ''
    subprotocol = websocket.subprotocol if hasattr(websocket, 'subprotocol') else None
    cp_id = cp_id_from_path or subprotocol or f"CP-{int(datetime.now().timestamp())}"

    cinfo(f"Neue Verbindung: cp_id={cp_id}, subprotocol={subprotocol}, path='{path}'")
    handler = ChargePointHandler(cp_id, websocket)
    connected_charge_points[cp_id] = handler

    try:
        await handler.start()
    except Exception as e:
        logger.exception(f"Fehler in Verbindung {cp_id}: {e}")
    finally:
        # cleanup
        connected_charge_points.pop(cp_id, None)
        meter_values_store.pop(cp_id, None)
        status_store.pop(cp_id, None)
        current_limit_store.pop(cp_id, None)
        phase_limit_store.pop(cp_id, None)
        debug_store.pop(cp_id, None)
        transaction_id_store.pop(cp_id, None)
        
        # NEUE STORES IM CLEANUP ENTFERNEN
        last_phase_change_timestamp.pop(cp_id, None)
        transaction_start_timestamp.pop(cp_id, None)
        
        cinfo(f"Verbindung beendet: {cp_id}")

# ----------------------------
# HTTP Endpoints
# ----------------------------
async def list_cp(request):
    return web.json_response({"connected": list(connected_charge_points.keys())})

async def meter_values(request):
    cp_id = request.query.get("charge_point_id")
    
    start_time = transaction_start_timestamp.get(cp_id)
    duration = (datetime.now() - (start_time or datetime.now())).total_seconds() if start_time else 0
    
    last_phase_change = last_phase_change_timestamp.get(cp_id)
    phase_duration = (datetime.now() - (last_phase_change or datetime.now())).total_seconds() if last_phase_change else 0
    
    return web.json_response({
        "meter": meter_values_store.get(cp_id, {}),
        "status": status_store.get(cp_id, "Unknown"),
        "pv_mode": pv_mode.get(cp_id, "off") if 'pv_mode' in globals() else "off",
        "current_limit": current_limit_store.get(cp_id, None),
        "phases": phase_limit_store.get(cp_id, None),
        "transaction_id": transaction_id_store.get(cp_id),
        "charging_duration_s": round(duration, 1), 
        "phase_stable_s": round(phase_duration, 1), 
        "debug_messages": debug_store.get(cp_id, [])
    })

async def remote_start(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)

    cp_id = data.get("charge_point_id")
    if not cp_id or cp_id not in connected_charge_points:
        return web.json_response({"success": False, "error": "Charge Point not connected"}, status=404)

    payload = {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG}
    await connected_charge_points[cp_id].send_call("RemoteStartTransaction", payload)
    status_store[cp_id] = "ChargingRequested"
    
    # Startzeitpunkt setzen, da RemoteStart getriggert wurde
    transaction_start_timestamp[cp_id] = datetime.now()
    
    return web.json_response({"success": True})

async def remote_stop(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)

    cp_id = data.get("charge_point_id")
    if not cp_id or cp_id not in connected_charge_points:
        return web.json_response({"success": False, "error": "Charge Point not connected"}, status=404)

    active_tx_id = transaction_id_store.get(cp_id)
    
    # -----------------------
    # STOP GUARD (API-Prüfung)
    # -----------------------
    # Der API-Stop darf immer gesendet werden, WENN die Min-Ladezeit vorbei ist
    can_stop = True
    if transaction_start_timestamp.get(cp_id):
        charging_duration = (datetime.now() - transaction_start_timestamp.get(cp_id)).total_seconds()
        if charging_duration < MIN_CHARGE_DURATION_S:
            cwarn(f"[{cp_id}] 🛑 API-STOP GUARD: Stop abgelehnt. Nur {round(charging_duration)}s geladen. Minimum: {MIN_CHARGE_DURATION_S}s.")
            can_stop = False

    if not can_stop:
        return web.json_response({"success": False, "error": f"Stop denied by Guard. Min charge time is {MIN_CHARGE_DURATION_S}s."}, status=403)


    if active_tx_id is None:
        # --- OPTIMIERTE LOGIK HIER: Kein redundanter DB-Zugriff bei laufendem Server ---
        
        # 1. Versuche, die zuletzt gesendete Phase aus dem Store zu holen.
        ocpp_phases_value = phase_limit_store.get(cp_id)
        
        if ocpp_phases_value is None:
            # 2. Fallback: Wenn Store leer (z.B. nach Serverneustart vor BootNotification), DB-Zugriff.
            cwarn(f"[{cp_id}] Phase Store leer. Führe Fallback DB-Zugriff für remote_stop durch.")
            # NEU: Nur 4 Rückgabewerte
            amp_max, phases, pv_mode_val, _ = get_wallbox_steuerdaten(cp_id=cp_id)
            ocpp_phases_value = 1 if phases == "1" else 3 
            
        # Setze 0A Limit mit aktueller Phase (entweder aus Store oder DB-Fallback)
        payload_stop_zero_amp = {
            "connectorId": DEFAULT_CONNECTOR_ID,
            "csChargingProfiles": {
                "chargingProfileId": 1,
                "stackLevel": 1,
                "chargingProfilePurpose": "TxDefaultProfile",
                "chargingProfileKind": "Absolute",
                "recurrencyKind": "Daily",
                "chargingSchedule": {
                    "chargingRateUnit": "A",
                    # Wichtig: Limit ist 0.0 (Stop), Phase ist die korrekte Phase
                    "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 0.0, "numberPhases": ocpp_phases_value}]
                }
            }
        }
        await connected_charge_points[cp_id].send_call("SetChargingProfile", payload_stop_zero_amp)
        current_limit_store[cp_id] = 0.0
        phase_limit_store[cp_id] = ocpp_phases_value # Aktualisiere den Store mit dem verwendeten Wert
        status_store[cp_id] = "AvailableRequested"
        
        # Reset Startzeitpunkt
        transaction_start_timestamp[cp_id] = None
        
        return web.json_response({"success": True, "transactionId": None, "note": "Sent 0A SetChargingProfile instead of RemoteStop"})

    # Regulärer RemoteStop bei aktiver Transaktion
    payload = {"transactionId": active_tx_id}
    await connected_charge_points[cp_id].send_call("RemoteStopTransaction", payload)
    status_store[cp_id] = "AvailableRequested"
    
    # Reset Startzeitpunkt
    transaction_start_timestamp[cp_id] = None
    
    return web.json_response({"success": True, "transactionId": active_tx_id})

async def set_pv_mode(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)
    cp_id = data.get("charge_point_id")
    mode = data.get("mode", "off") # Der mode-Parameter ist hier nicht mehr relevant, da die Logik die DB liest
    if not cp_id or cp_id not in connected_charge_points:
        return web.json_response({"success": False, "error": "Charge Point not connected"}, status=404)

    # DB-Werte holen (NUR HIER, da die Werte sofort angewendet werden müssen)
    # NEU: is_pv_controlled
    amp, phases, pv_mode_val, is_pv_controlled = get_wallbox_steuerdaten(cp_id=cp_id)
    
    # Trigger apply_wallbox_settings, um die Einstellung SOFORT anzuwenden
    await apply_wallbox_settings(cp_id, amp, phases, pv_mode_val, is_pv_controlled) 
    
    return web.json_response({"success": True, "mode": mode})

# ----------------------------
# Background AutoSync Task
# ----------------------------
async def autosync_task():
    await asyncio.sleep(2)
    cinfo(f"AutoSync task started, interval={AUTO_SYNC_INTERVAL}s")

    while True:
        if not connected_charge_points:
            cnote("AutoSync: keine verbundenen Charge Points")
        else:
            # --- NEUE LOGIK: PV-Daten (amp, phases, pv_mode etc.)
            # --- werden jetzt FÜR JEDEN CP EINZELN geholt.
            # --- Der globale (fehlerhafte) DB-Aufruf wurde entfernt.

            for cp_id in list(connected_charge_points.keys()):
                try:
                    # 1. DB-Werte für diesen spezifischen CP abrufen
                    #    Wichtig: get_wallbox_steuerdaten() nutzt hier das
                    #    korrekte cp_id, um den aktuellen Ladestrom zu berücksichtigen.
                    amp, phases, pv_mode_val, is_pv_controlled = get_wallbox_steuerdaten(cp_id=cp_id)

                    # 2. Einstellungen für diesen CP anwenden
                    await apply_wallbox_settings(cp_id, amp, phases, pv_mode_val, is_pv_controlled)

                except Exception as e:
                    # Fehlermeldung ist jetzt spezifisch für den CP, der das Problem verursacht hat
                    cerr(f"AutoSync Fehler bei {cp_id}: {e}")
                    # Hier sind keine Fallback-Werte nötig, da der nächste CP
                    # mit einem frischen DB-Aufruf beginnt.

        await asyncio.sleep(AUTO_SYNC_INTERVAL)

# ----------------------------
# Server Start
# ----------------------------
async def main():
    # prepare websockets serve awaitable
    ws = ws_serve(
        on_connect,
        "0.0.0.0",
        WS_PORT,
        subprotocols=OCPP_PROTOCOLS
    )

    # aiohttp web app
    app = web.Application()
    app.add_routes([
        web.get('/list', list_cp),
        web.get('/meter_values', meter_values),
        web.post('/remote_start', remote_start),
        web.post('/remote_stop', remote_stop),
        web.post('/set_pv_mode', set_pv_mode),
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)

    # start autosync background task
    asyncio.create_task(autosync_task())

    # gather ws server + start http site
    await asyncio.gather(
        ws,
        site.start(),
    )

    cinfo(f"OCPP Legacy Server läuft: WS={WS_PORT}, HTTP={HTTP_PORT}")

    # keep running forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        cinfo("Starting ocpp_legacy_server...")
        asyncio.run(main())
    except KeyboardInterrupt:
        cinfo("Server wird beendet (KeyboardInterrupt).")
    except Exception as e:
        cerr(f"Uncaught exception: {e}")
