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
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from aiohttp import web

# Hybrid Import für websockets (neu/alt)
try:
    # websockets >=12
    from websockets.server import serve as ws_serve
    USING_NEW_WEBSOCKETS = True
    print("Using NEW websockets.server.serve API")
except Exception:
    # websockets <=11
    from websockets.asyncio.server import serve as ws_serve
    USING_NEW_WEBSOCKETS = False
    print("Using LEGACY websockets.asyncio.server.serve API")

# ----------------------------
# Auffälliges Console-Logging
# ----------------------------
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

def cinfo(msg):  print(f"{Color.BLUE}{Color.BOLD}🟦 INFO:{Color.RESET} {msg}")
def cok(msg):    print(f"{Color.GREEN}{Color.BOLD}🟩 OK:{Color.RESET} {msg}")
def cwarn(msg):  print(f"{Color.YELLOW}{Color.BOLD}🟧 WARN:{Color.RESET} {msg}")
def cerr(msg):   print(f"{Color.RED}{Color.BOLD}🟥 ERROR:{Color.RESET} {msg}")
def cnote(msg):  print(f"{Color.MAGENTA}{Color.BOLD}🟨 NOTE:{Color.RESET} {msg}")

# zusätzlich normales logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OCPP-Legacy")

# ----------------------------
# Konfiguration
# ----------------------------
TIME_SHIFT_SECONDS = 5
DEFAULT_CONNECTOR_ID = 1
DEFAULT_IDTAG = "WattpilotUser"
# Vendor-Key für Phasen (Wird NICHT mehr für ChangeConfiguration verwendet, nur als Referenz)
VENDOR_KEY_PHASES = "num_phases" 
# OCPP Subprotocols (wird an ws_serve übergeben)
OCPP_PROTOCOLS = ['ocpp1.6', 'ocpp2.0.1', 'ocpp1.5']
# Ports
WS_PORT = 8887
HTTP_PORT = 8080
# Auto-sync interval in Sekunden
AUTO_SYNC_INTERVAL = 10

# ----------------------------
# In-Memory Stores
# ----------------------------
connected_charge_points = {}    # cp_id -> ChargePointHandler
meter_values_store = {}
status_store = {}
pv_mode = {}
current_limit_store = {} # Letztes gesendetes Ampere-Limit
phase_limit_store = {}   # Letzte gesendete Phasen-Anzahl (1 oder 3)
debug_store = {}
transaction_id_store = {}

# ----------------------------
# DB Helper (safe fallback)
# ----------------------------
def get_wallbox_steuerdaten():
    """
    Liest aus der Datenbank mittels FUNCTIONS.SQLall.sqlall().getSQLsteuerdaten('wallbox')
    Rückgabe: (amp: float, phases: str, pv_mode: float)
    Falls DB/Modul nicht vorhanden oder Fehler, werden Defaultwerte zurückgegeben.
    """
    try:
        # Falls dein Projekt MODULE anders heißt, passe das hier an.
        import SQLall
        sqlall = SQLall.sqlall()
        data = sqlall.getSQLsteuerdaten('wallbox', '../CONFIG/Prog_Steuerung.sqlite')
    except Exception as e:
        cwarn(f"DB-Zugriff fehlgeschlagen oder FUNCTIONS nicht vorhanden: {e}")
        return 16.0, "3", 0.0

    if not data or '1' not in data:
        cwarn("Keine Wallbox-Daten in DB gefunden → Verwende Default 16A / 3 Phasen / PV Off")
        return 16.0, "3", 0.0
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
        return amp_max, phases, pv_mode
    except Exception as e:
        cwarn(f"Fehler beim Parsen der DB-Daten: {e} → Defaults verwendet")
        return 16.0, "3", 0.0

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
        phase_limit_store[self.cp_id] = None   # Phasen-Limit (z.B. 3)
        transaction_id_store[self.cp_id] = None
        debug_store[self.cp_id] = []

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

                # DB-Werte holen
                amp_max, phases, pv_mode_val = get_wallbox_steuerdaten()

                # Sofort Sync mit DB-Werten starten
                asyncio.create_task(apply_wallbox_settings(self.cp_id, amp_max, phases, pv_mode_val))

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
                await self.send_call_result(unique_id, {"idTagInfo": {"status": "Accepted"}, "transactionId": tx_id})
                logger.info(f"[{self.cp_id}] StartTransaction accepted tx={tx_id}")

            elif action == "StopTransaction":
                transaction_id_store[self.cp_id] = None
                status_store[self.cp_id] = "Available"
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
            logger.error(f"[{self.cp_id}] Unbekannter messageType: {data}")

# ----------------------------
# Interne Steuer-Logik (Überarbeitet)
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
                if sample.get('measurand') == 'Power.Active.Import' and 'phase' not in sample:
                    try:
                        return float(sample.get('value', 0))
                    except ValueError:
                        return 0
    return 0

async def apply_wallbox_settings(cp_id, amp=16, phases="3", pv_mode_val=0.0):
    """
    Wendest die gewünschten Ampere- und Phasen-Werte über SetChargingProfile an.
    Implementiert eine sichere 0A-Stop-Logik vor Phasenwechseln.
    """
    if cp_id not in connected_charge_points:
        cwarn(f"apply_wallbox_settings: Charge Point {cp_id} nicht verbunden.")
        return False

    cp = connected_charge_points[cp_id]

    # Der aktuell gewünschte Limit-Wert (0A wenn pv_mode=0)
    amp_desired = amp if pv_mode_val != 0.0 else 0.0
    # Die aktuell gewünschte Phasenanzahl (umgewandelt in Zahl 1 oder 3)
    ocpp_phases_value = 1 if phases == "1" else 3 

    # Stores sicherstellen
    current_limit_store.setdefault(cp_id, None)
    phase_limit_store.setdefault(cp_id, None)

    # Zustand prüfen
    amp_changed = current_limit_store.get(cp_id) != amp_desired
    phase_changed = phase_limit_store.get(cp_id) != ocpp_phases_value

    cinfo(f"[{cp_id}] Prüfe Sync: PV-Mode={pv_mode_val}, Wunsch: {amp_desired}A/{ocpp_phases_value}P. Aktuell: {current_limit_store.get(cp_id)}A/{phase_limit_store.get(cp_id)}P")
    
    # -----------------------
    # 1. Ampere ODER Phase muss geändert werden
    # -----------------------
    if amp_changed or phase_changed:
        
        # --- PHASE CHANGE VORBEREITUNG: 0A Limit senden, wenn Phase gewechselt werden muss ---
        if phase_changed:
            cinfo(f"[{cp_id}] Phase Änderung erkannt: {phase_limit_store.get(cp_id)} -> {ocpp_phases_value}. Starte 0A-Stop Prozedur.")
            
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
                                "numberPhases": ocpp_phases_value # Auch die Phase sofort senden!
                            }]
                        }
                    }
                }
                await cp.send_call("SetChargingProfile", payload_stop_zero_amp)
                current_limit_store[cp_id] = 0.0
                phase_limit_store[cp_id] = ocpp_phases_value
                
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
        # 2. Finales Limit senden (mit korrekter Phase)
        # -----------------------
        # Dies wird immer gesendet, wenn sich Ampere ODER Phase geändert hat.
        # Im Falle einer Phasenänderung startet es das Laden ggf. neu mit der neuen Phase.
        
        # Sicherstellen, dass die Ampere- und Phasen-Werte in den Stores auf dem neusten Stand sind, 
        # FALLS das Limit zuvor wegen Phase Change auf 0A gesetzt wurde.
        
        cinfo(f"[{cp_id}] Sende finales Limit: {amp_desired}A an Phase {ocpp_phases_value}.")

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
                        "numberPhases": ocpp_phases_value # Phase ist immer enthalten!
                    }]
                }
            }
        }
        await cp.send_call("SetChargingProfile", payload_final_limit)
        
        # Stores auf finalen Wert setzen
        current_limit_store[cp_id] = amp_desired
        phase_limit_store[cp_id] = ocpp_phases_value 

        cok(f"[{cp_id}] Ampere/Phase erfolgreich gesetzt: {amp_desired}A / {ocpp_phases_value}P")

        # -----------------------
        # 3. Remote Start/Stop Logik
        # -----------------------
        status = status_store.get(cp_id)
        active_tx_id = transaction_id_store.get(cp_id)
        
        if amp_desired > 0.0:
            # Laden starten
            if status in ["Available", "AvailableRequested", "SuspendedEVSE", "Finishing"]:
                await cp.send_call("RemoteStartTransaction", {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG})
                status_store[cp_id] = "ChargingRequested"
                cinfo(f"[{cp_id}] Laden gestartet (amp={amp_desired}A, RemoteStart)")
        else:
            # Laden stoppen (Limit 0A wurde bereits gesendet, RemoteStop als Fallback)
            if active_tx_id:
                await cp.send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                status_store[cp_id] = "AvailableRequested"
                cinfo(f"[{cp_id}] Laden gestoppt (amp=0.0A, RemoteStop als Fallback)")
            elif status not in ["Available", "AvailableRequested"]:
                # Status auf Available setzen, wenn 0A gesetzt wurde und keine Transaktion läuft
                status_store[cp_id] = "Available"
                cnote(f"[{cp_id}] Status auf Available gesetzt.")
        
    else:
        cnote(f"[{cp_id}] Ampere/Phase unverändert ({amp_desired}A / {ocpp_phases_value}P)")

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
        cinfo(f"Verbindung beendet: {cp_id}")

# ----------------------------
# HTTP Endpoints
# ----------------------------
async def list_cp(request):
    return web.json_response({"connected": list(connected_charge_points.keys())})

async def meter_values(request):
    cp_id = request.query.get("charge_point_id")
    return web.json_response({
        "meter": meter_values_store.get(cp_id, {}),
        "status": status_store.get(cp_id, "Unknown"),
        "pv_mode": pv_mode.get(cp_id, "off") if 'pv_mode' in globals() else "off",
        "current_limit": current_limit_store.get(cp_id, None),
        "phases": phase_limit_store.get(cp_id, None),
        "transaction_id": transaction_id_store.get(cp_id),
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
    if active_tx_id is None:
        # Nur 0A Limit senden, wenn keine aktive Transaktion existiert
        # Hole aktuelle DB-Daten für Phasen
        amp_max, phases, pv_mode_val = get_wallbox_steuerdaten()
        ocpp_phases_value = 1 if phases == "1" else 3 
        
        # Setze 0A Limit mit aktueller Phase
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
                    "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 0.0, "numberPhases": ocpp_phases_value}]
                }
            }
        }
        await connected_charge_points[cp_id].send_call("SetChargingProfile", payload_stop_zero_amp)
        current_limit_store[cp_id] = 0.0
        phase_limit_store[cp_id] = ocpp_phases_value
        status_store[cp_id] = "AvailableRequested"
        return web.json_response({"success": True, "transactionId": None, "note": "Sent 0A SetChargingProfile instead of RemoteStop"})


    payload = {"transactionId": active_tx_id}
    await connected_charge_points[cp_id].send_call("RemoteStopTransaction", payload)
    status_store[cp_id] = "AvailableRequested"
    return web.json_response({"success": True, "transactionId": active_tx_id})

async def set_pv_mode(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)
    cp_id = data.get("charge_point_id")
    mode = data.get("mode", "off")
    if not cp_id or cp_id not in connected_charge_points:
        return web.json_response({"success": False, "error": "Charge Point not connected"}, status=404)

    # PVMode wird nun lokal im Store und über apply_wallbox_settings gesteuert
    pv_mode[cp_id] = mode
    # Trigger AutoSync, um die Einstellung anzuwenden
    amp, phases, pv_mode_val = get_wallbox_steuerdaten()
    await apply_wallbox_settings(cp_id, amp, phases, pv_mode_val) 
    
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
            for cp_id in list(connected_charge_points.keys()):
                try:
                    # --- PV-Daten aus DB holen ---
                    amp, phases, pv_mode_val = get_wallbox_steuerdaten()

                    # --- PV-Mode + Ampere/Phasen zentral anwenden ---
                    await apply_wallbox_settings(cp_id, amp, phases, pv_mode_val)

                except Exception as e:
                    cerr(f"AutoSync Fehler bei {cp_id}: {e}")

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
