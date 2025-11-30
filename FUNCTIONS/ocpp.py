#!/usr/bin/env python3
"""
FUNCTIONS/ocpp.py

Enthält OCPP-bezogene Klassen:
 - OCPPManager: verwaltet Stores, WebSocket-Server, HTTP-API und Autosync
 - ChargePointHandler: pro-WebSocket-Handler, delegiert Nachrichten an den Manager
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from aiohttp import web

# Logging setup (module-local)
logger = logging.getLogger("OCPP-Legacy")
logger.setLevel(logging.ERROR)

# Hilfs-Logger-Funktionen (kleine, auffällige Console-Ausgaben wie im Original)
def cinfo(msg):  print(f"ℹ️  INFO: {msg}")
def cok(msg):    print(f"✅ OK:   {msg}")
def cwarn(msg):  print(f"⚠️- WARN: {msg}")
def cerr(msg):   print(f"❌ ERROR:{msg}")
def cnote(msg):  print(f"✏️  NOTE: {msg}")

# Import basics/config zum Lesen der INI-Dateien  #entWIGGlung elche *.ini
import FUNCTIONS.functions
basics = FUNCTIONS.functions.basics()
config = basics.loadConfig(['default'])

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

# Konstanten   #entWIGGlung Werte später aus INI-Dateien oder DB
AUTO_SYNC_INTERVAL = 20
MIN_PHASE_DURATION_S = 180   # 3 Minuten
MIN_CHARGE_DURATION_S = 600  # 10 Minuten
residualPower = -300  # Watt +Netzeinspeisung -Netzbezug
WS_PORT = 8887
HTTP_PORT = 8080
TIME_SHIFT_SECONDS = 5
DEFAULT_CONNECTOR_ID = 1
DEFAULT_IDTAG = "WattpilotUser"
OCPP_PROTOCOLS = ['ocpp1.6', 'ocpp2.0.1', 'ocpp1.5']

# SQL Helper import
import FUNCTIONS.SQLall

class ChargePointHandler:
    """Behandelt eine einzelne WebSocket-Verbindung (ein Charge Point)."""

    def __init__(self, manager, cp_id, websocket):
        self.manager = manager  # Referenz auf OCPPManager
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
            self.manager.debug_store.setdefault(self.cp_id, []).append({"sent": msg, "timestamp": self.get_future_utc_timestamp()})
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
            self.manager.debug_store.setdefault(self.cp_id, []).append({"sent": msg, "timestamp": self.get_future_utc_timestamp()})
            return unique_id
        except Exception as e:
            logger.exception(f"Fehler beim Senden CALL an {self.cp_id}: {e}")
            return None

    async def start(self):
        # initial values in manager
        self.manager.status_store[self.cp_id] = "Available"
        self.manager.meter_values_store[self.cp_id] = {"power": 0, "current": 0, "energy": 0}
        self.manager.current_limit_store[self.cp_id] = None
        self.manager.phase_limit_store[self.cp_id] = None
        self.manager.transaction_id_store[self.cp_id] = None
        self.manager.debug_store[self.cp_id] = []

        # Setze Zeitstempel zurück so der erste Wechsel erlaubt ist
        self.manager.last_phase_change_timestamp[self.cp_id] = datetime.now() - timedelta(seconds=MIN_PHASE_DURATION_S + 10)
        self.manager.transaction_start_timestamp[self.cp_id] = None

        try:
            async for message in self.websocket:
                await self.handle_message(message)
        except Exception as e:
            logger.exception(f"WebSocket-Loop für {self.cp_id} beendet mit Fehler: {e}")

    async def handle_message(self, message):
        try:
            data = json.loads(message)
            self.manager.debug_store.setdefault(self.cp_id, []).append({"received": data, "timestamp": self.get_future_utc_timestamp()})
        except Exception as e:
            logger.error(f"Ungültige JSON-Nachricht von {self.cp_id}: {e}")
            return

        if not isinstance(data, list) or len(data) < 2:
            logger.error(f"Ungültiges OCPP-Format von {self.cp_id}: {data}")
            return

        message_type = data[0]
        unique_id = data[1] if len(data) > 1 else None

        # Incoming CALL
        if message_type == 2:
            if len(data) < 4:
                logger.error(f"Ungültiges CALL Format von {self.cp_id}: {data}")
                return
            action = data[2]
            payload = data[3]
            logger.info(f"[{self.cp_id}] Received CALL action={action}")

            if action == "BootNotification":
                await self.send_call_result(unique_id, {
                    "currentTime": self.get_future_utc_timestamp(),
                    "interval": 300,
                    "status": "Accepted"
                })

                amp_max, phases, pv_mode_val, is_pv_controlled = self.manager.get_wallbox_steuerdaten(cp_id=self.cp_id)
                asyncio.create_task(self.manager.apply_wallbox_settings(self.cp_id, amp_max, phases, pv_mode_val, is_pv_controlled))

            elif action == "Heartbeat":
                await self.send_call_result(unique_id, {"currentTime": self.get_future_utc_timestamp()})

            elif action == "StatusNotification":
                self.manager.status_store[self.cp_id] = payload.get("status", self.manager.status_store.get(self.cp_id, "Unknown"))
                await self.send_call_result(unique_id)

            elif action == "MeterValues":
                if payload.get("transactionId"):
                    self.manager.transaction_id_store[self.cp_id] = payload["transactionId"]
                self.manager.meter_values_store[self.cp_id] = payload
                await self.send_call_result(unique_id)

            elif action == "StartTransaction":
                tx_id = int(datetime.now(timezone.utc).timestamp())
                self.manager.transaction_id_store[self.cp_id] = tx_id
                self.manager.status_store[self.cp_id] = "Charging"
                self.manager.transaction_start_timestamp[self.cp_id] = datetime.now()
                await self.send_call_result(unique_id, {"idTagInfo": {"status": "Accepted"}, "transactionId": tx_id})
                logger.info(f"[{self.cp_id}] StartTransaction accepted tx={tx_id}")

            elif action == "StopTransaction":
                self.manager.transaction_id_store[self.cp_id] = None
                self.manager.status_store[self.cp_id] = "Available"
                self.manager.transaction_start_timestamp[self.cp_id] = None
                await self.send_call_result(unique_id, {"idTagInfo": {"status": "Accepted"}})
                logger.info(f"[{self.cp_id}] StopTransaction accepted")

            else:
                logger.warning(f"[{self.cp_id}] Unbekannte CALL Aktion: {action}")
                await self.send_call_result(unique_id)

        elif message_type == 3:
            logger.debug(f"[{self.cp_id}] CALLRESULT empfangen: {data}")

        elif message_type == 4:
            logger.error(f"[{self.cp_id}] CALLERROR empfangen: {data}")

        else:
            logger.error(f"[{self.cp_id}] Unbekannter messageType: {data}")

class OCPPManager:
    """Verwaltet Charge Points, HTTP-API, WebSocket-Server und Autosync."""

    def __init__(self, ws_port=WS_PORT, http_port=HTTP_PORT, auto_sync_interval=AUTO_SYNC_INTERVAL):
        # Stores (waren vorher global)
        self.connected_charge_points = {}     # cp_id -> ChargePointHandler
        self.meter_values_store = {}
        self.status_store = {}
        self.pv_mode = {}
        self.current_limit_store = {}
        self.phase_limit_store = {}
        self.debug_store = {}
        self.transaction_id_store = {}
        self.last_phase_change_timestamp = {}
        self.transaction_start_timestamp = {}

        # Config
        self.ws_port = ws_port
        self.http_port = http_port
        self.auto_sync_interval = auto_sync_interval

    # ----------------------------
    # DB Helper (ausgelagert)
    # ----------------------------
    def get_wallbox_steuerdaten(self, cp_id=None):
        """
        Liest aus der Datenbank mittels FUNCTIONS.SQLall.sqlall().getSQLsteuerdaten('wallbox')
        Rückgabe: (amp: float, phases: str, pv_mode: float, is_pv_controlled: bool)
        """
        amp_max = 16.0
        amp_min = 6.0
        phases = "3"
        pv_mode = 0.0
        amp = amp_max

        try:
            sqlall = FUNCTIONS.SQLall.sqlall()
            data = sqlall.getSQLsteuerdaten('wallbox', 'CONFIG/Prog_Steuerung.sqlite')
        except Exception as e:
            cwarn(f"DB-Zugriff fehlgeschlagen oder FUNCTIONS nicht vorhanden: {e}")
            return amp_max, phases, pv_mode, False

        if not data or '1' not in data:
            cwarn("Keine Wallbox-Daten in DB gefunden → Verwende Default 16A / 3 Phasen / PV Off")
            return amp_max, phases, pv_mode, False

        try:
            row = data['1']
            parts = row.get('Options', '').split(',')

            try:
                amp_min = float(parts[0])
            except (ValueError, IndexError):
                amp_min = 6.0
            if amp_min < 6:
                amp_min = 6.0

            try:
                amp_max = float(parts[1])
            except (ValueError, IndexError):
                amp_max = 16.0
            if amp_max < amp_min:
                amp_max = amp_min
            if amp_max > 16:
                amp_max = 16.0

            phases = str(row.get('Res_Feld2', '0'))  # '1', '3' oder '0'
            pv_mode = float(row.get('Res_Feld1', '0'))  # 0.0=Stop, >0.0=PV-Laden

            cinfo(f"DB-Steuerdaten geladen: amp_max={amp_max}A, phases={phases}, pv_mode={pv_mode}")
        except Exception as e:
            cwarn(f"Fehler beim Parsen der DB-Daten: {e} → Defaults verwendet")
            pv_mode = 0
            phases = "3"
            amp_max = 6
            amp_min = 6

        amp = amp_max
        is_pv_controlled = False

        if pv_mode == 1 or pv_mode == 2:
            is_pv_controlled = True
            try:
                InverterApi = basics.get_inverter_class(class_type="Api")
            except Exception as e:
                cwarn(f"Inverter API konnte nicht geladen werden: {e}")
                return amp_max, phases, pv_mode, False

            inverter_api = InverterApi()
            API = inverter_api.get_API()
            Netzbezug = API['aktuelleEinspeisung']

            current_charge_power = 0
            if cp_id and cp_id in self.connected_charge_points:
                current_charge_power = self.get_current_power(cp_id)

            ueberschuss = max(0, (-Netzbezug + current_charge_power - residualPower))
            cinfo(f"Aktuelle Einspeisung (negativ=Netzbezug): {-Netzbezug}W, Ladestrom ({current_charge_power}W), residualPower ({residualPower}W). Überschuss (inkl. Ladung): {ueberschuss}W")

            amp = 0
            amp_1 = int(ueberschuss / 230 / 1) if ueberschuss else 0
            amp_3 = int(ueberschuss / 230 / 3) if ueberschuss else 0

            if phases == "1":
                amp = min(amp_1, amp_max) if amp_1 >= 6 else 0
            elif phases == "3" or phases == "0":
                if amp_3 >= 6:
                    phases = "3"
                    amp = min(amp_3, amp_max)
                elif amp_1 >= 6:
                    phases = "1"
                    amp = min(amp_1, amp_max)
                else:
                    amp = 0

        if pv_mode == 2:
            if amp < amp_min:
                amp = min(amp_min, amp_max)

        return amp, phases, pv_mode, is_pv_controlled

    def get_current_power(self, cp_id):
        """Extrahiert Power.Active.Import aus meter_values_store."""
        meter_data = self.meter_values_store.get(cp_id)
        if not meter_data or 'meterValue' not in meter_data:
            return 0
        for meter_value in meter_data['meterValue']:
            if 'sampledValue' in meter_value:
                for sample in meter_value['sampledValue']:
                    if sample.get('measurand') == 'Power.Active.Import' and 'phase' not in sample:
                        try:
                            return float(sample.get('value', 0))
                        except (ValueError, TypeError):
                            return 0
        return 0

    async def apply_wallbox_settings(self, cp_id, amp, phases, pv_mode_val, is_pv_controlled):
        """Wendet Ampere- und Phasen-Werte an (SetChargingProfile / RemoteStart/Stop)."""
        if cp_id not in self.connected_charge_points:
            cwarn(f"apply_wallbox_settings: Charge Point {cp_id} nicht verbunden.")
            return False

        cp = self.connected_charge_points[cp_id]

        amp_desired = amp if pv_mode_val != 0.0 else 0.0
        ocpp_phases_value = 1 if phases == "1" else 3

        self.current_limit_store.setdefault(cp_id, None)
        self.phase_limit_store.setdefault(cp_id, None)
        self.last_phase_change_timestamp.setdefault(cp_id, datetime.now())
        self.transaction_start_timestamp.setdefault(cp_id, None)

        amp_changed = self.current_limit_store.get(cp_id) != amp_desired
        phase_changed = self.phase_limit_store.get(cp_id) != ocpp_phases_value

        final_ocpp_phases_value = self.phase_limit_store.get(cp_id)
        if final_ocpp_phases_value is None:
            final_ocpp_phases_value = ocpp_phases_value

        cinfo(f"[{cp_id}] Prüfe Sync: PV-Mode={pv_mode_val}, PV-Steuerung={is_pv_controlled}, Wunsch: {amp_desired}A/{ocpp_phases_value}P. Aktuell: {self.current_limit_store.get(cp_id)}A/{self.phase_limit_store.get(cp_id)}P")

        pv_guard_active = False

        # PHASE CHANGE GUARD
        is_initial_change = self.phase_limit_store.get(cp_id) is None
        if phase_changed:
            time_since_last_change = (datetime.now() - self.last_phase_change_timestamp.get(cp_id)).total_seconds()
            if time_since_last_change < MIN_PHASE_DURATION_S and not is_initial_change and is_pv_controlled:
                cwarn(f"[{cp_id}] 🛑 PHASE GUARD (Zeit/PV): Phasenwechsel ({self.phase_limit_store.get(cp_id)}->{ocpp_phases_value}) abgelehnt. Nur {round(time_since_last_change)}s vergangen. Minimum: {MIN_PHASE_DURATION_S}s.")
                ocpp_phases_value = self.phase_limit_store.get(cp_id)
                phase_changed = False
            else:
                cnote(f"[{cp_id}] ✅ PHASE CHANGE erlaubt. (Initial={is_initial_change}, Zeit seit Wechsel={round(time_since_last_change)}s)")

        # Laden starten/stoppen
        status = self.status_store.get(cp_id)
        active_tx_id = self.transaction_id_store.get(cp_id)

        if amp_desired > 0.0:
            if status in ["Available", "AvailableRequested", "SuspendedEVSE", "Finishing"]:
                await cp.send_call("RemoteStartTransaction", {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG})
                self.status_store[cp_id] = "ChargingRequested"
                if not self.transaction_start_timestamp.get(cp_id):
                    self.transaction_start_timestamp[cp_id] = datetime.now()
                cinfo(f"[{cp_id}] Laden gestartet (amp={amp_desired}A, RemoteStart)")
        else:
            # Stopp-Guard (nur bei PV-Steuerung relevant)
            can_stop_by_guard = True
            if is_pv_controlled:
                if self.transaction_start_timestamp.get(cp_id):
                    charging_duration = (datetime.now() - self.transaction_start_timestamp.get(cp_id)).total_seconds()
                    if charging_duration < MIN_CHARGE_DURATION_S:
                        cwarn(f"[{cp_id}] 🛑 STOP GUARD (Zeit): Stop (0A) abgelehnt. Nur {round(charging_duration)}s geladen. Minimum: {MIN_CHARGE_DURATION_S}s.")
                        can_stop_by_guard = False
                    else:
                        cnote(f"[{cp_id}] ✅ STOP Laden erlaubt. (Ladedauer={round(charging_duration)}s)")
            else:
                cnote(f"[{cp_id}] Stop (0A) gewünscht durch pv_mode={pv_mode_val}. Guard übersprungen, da PV-Steuerung inaktiv.")

            if not can_stop_by_guard:
                fallback_limit = 6.0
                amp_desired = fallback_limit
                pv_guard_active = True
                cwarn(f"[{cp_id}] ❗ STOP GUARD aktiv. Setze Ladelimit auf {fallback_limit}A zur Vermeidung eines Stopps.")
            else:
                if active_tx_id:
                    await cp.send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                    self.status_store[cp_id] = "AvailableRequested"
                    self.transaction_start_timestamp[cp_id] = None
                    cnote(f"[{cp_id}] Laden gestoppt (amp=0.0A, RemoteStop als Fallback)")
                elif status not in ["Available", "AvailableRequested"]:
                    self.status_store[cp_id] = "Available"
                    self.transaction_start_timestamp[cp_id] = None
                    cnote(f"[{cp_id}] Status auf Available gesetzt.")

        # Re-check amp_changed falls Guard Ampere geändert hat
        amp_changed = self.current_limit_store.get(cp_id) != amp_desired

        # Wenn Ampere oder Phase geändert => senden
        if amp_changed or phase_changed:
            # Bei Phase wechsel: ggf. 0A Limit senden bevor neue Phase
            if phase_changed and not is_initial_change:
                cinfo(f"[{cp_id}] Phase Änderung erkannt: {self.phase_limit_store.get(cp_id)} -> {final_ocpp_phases_value}. Starte 0A-Stop Prozedur.")
                current_power = self.get_current_power(cp_id)
                if current_power > 50:
                    cinfo(f"[{cp_id}] Aktive Leistung {current_power}W. Sende 0A Limit + neue Phase.")
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
                                    "limit": 0.0,
                                    "numberPhases": final_ocpp_phases_value
                                }]
                            }
                        }
                    }
                    await cp.send_call("SetChargingProfile", payload_stop_zero_amp)
                    self.current_limit_store[cp_id] = 0.0
                    self.phase_limit_store[cp_id] = final_ocpp_phases_value
                    self.last_phase_change_timestamp[cp_id] = datetime.now()

                    # Warte max 15s auf Leistung < 50W
                    for i in range(15):
                        await asyncio.sleep(1)
                        current_power = self.get_current_power(cp_id)
                        if current_power < 50:
                            cok(f"[{cp_id}] Leistung < 50W nach {i+1}s. Führe Phasenwechsel-Abschluss durch.")
                            break
                    else:
                        cwarn(f"[{cp_id}] WARNUNG: Leistung ist nach 15s noch hoch ({current_power}W). Sende finales Limit.")
                else:
                    cnote(f"[{cp_id}] Aktive Leistung {current_power}W. Kein 0A-Stop notwendig.")

            # Sende finales Limit
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
                            "numberPhases": final_ocpp_phases_value
                        }]
                    }
                }
            }
            await cp.send_call("SetChargingProfile", payload_final_limit)

            # Stores updaten
            self.current_limit_store[cp_id] = amp_desired
            self.phase_limit_store[cp_id] = final_ocpp_phases_value

            if phase_changed:
                cnote(f"[{cp_id}] ⏳ COOLDOWN: Warte 3 Sekunden nach Phasenwechsel ({final_ocpp_phases_value}P).")
                await asyncio.sleep(3)

            cok(f"[{cp_id}] Ampere/Phase erfolgreich gesetzt: {amp_desired}A / {final_ocpp_phases_value}P")
        else:
            cnote(f"[{cp_id}] Ampere/Phase unverändert ({amp_desired}A / {final_ocpp_phases_value}P)")

        return True

    # ----------------------------
    # WebSocket on_connect
    # ----------------------------
    async def on_connect(self, websocket, path):
        cp_id_from_path = path.strip('/') if path else ''
        subprotocol = websocket.subprotocol if hasattr(websocket, 'subprotocol') else None
        cp_id = cp_id_from_path or subprotocol or f"CP-{int(datetime.now().timestamp())}"

        cinfo(f"Neue Verbindung: cp_id={cp_id}, subprotocol={subprotocol}, path='{path}'")
        handler = ChargePointHandler(self, cp_id, websocket)
        self.connected_charge_points[cp_id] = handler

        try:
            await handler.start()
        except Exception as e:
            logger.exception(f"Fehler in Verbindung {cp_id}: {e}")
        finally:
            # cleanup
            self.connected_charge_points.pop(cp_id, None)
            self.meter_values_store.pop(cp_id, None)
            self.status_store.pop(cp_id, None)
            self.current_limit_store.pop(cp_id, None)
            self.phase_limit_store.pop(cp_id, None)
            self.debug_store.pop(cp_id, None)
            self.transaction_id_store.pop(cp_id, None)
            self.last_phase_change_timestamp.pop(cp_id, None)
            self.transaction_start_timestamp.pop(cp_id, None)
            cinfo(f"Verbindung beendet: {cp_id}")

    # ----------------------------
    # HTTP Endpoints (methods return handlers)
    # ----------------------------
    async def list_cp(self, request):
        return web.json_response({"connected": list(self.connected_charge_points.keys())})

    async def meter_values(self, request):
        cp_id = request.query.get("charge_point_id")

        start_time = self.transaction_start_timestamp.get(cp_id)
        duration = (datetime.now() - (start_time or datetime.now())).total_seconds() if start_time else 0

        last_phase_change = self.last_phase_change_timestamp.get(cp_id)
        phase_duration = (datetime.now() - (last_phase_change or datetime.now())).total_seconds() if last_phase_change else 0

        return web.json_response({
            "meter": self.meter_values_store.get(cp_id, {}),
            "status": self.status_store.get(cp_id, "Unknown"),
            "pv_mode": self.pv_mode.get(cp_id, "off"),
            "current_limit": self.current_limit_store.get(cp_id, None),
            "phases": self.phase_limit_store.get(cp_id, None),
            "transaction_id": self.transaction_id_store.get(cp_id),
            "charging_duration_s": round(duration, 1),
            "phase_stable_s": round(phase_duration, 1),
            "debug_messages": self.debug_store.get(cp_id, [])
        })

    async def remote_start(self, request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)

        cp_id = data.get("charge_point_id")
        if not cp_id or cp_id not in self.connected_charge_points:
            return web.json_response({"success": False, "error": "Charge Point not connected"}, status=404)

        payload = {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG}
        await self.connected_charge_points[cp_id].send_call("RemoteStartTransaction", payload)
        self.status_store[cp_id] = "ChargingRequested"
        self.transaction_start_timestamp[cp_id] = datetime.now()

        return web.json_response({"success": True})

    async def remote_stop(self, request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)

        cp_id = data.get("charge_point_id")
        if not cp_id or cp_id not in self.connected_charge_points:
            return web.json_response({"success": False, "error": "Charge Point not connected"}, status=404)

        active_tx_id = self.transaction_id_store.get(cp_id)

        # API STOP-GUARD
        can_stop = True
        if self.transaction_start_timestamp.get(cp_id):
            charging_duration = (datetime.now() - self.transaction_start_timestamp.get(cp_id)).total_seconds()
            if charging_duration < MIN_CHARGE_DURATION_S:
                cwarn(f"[{cp_id}] 🛑 API-STOP GUARD: Stop abgelehnt. Nur {round(charging_duration)}s geladen. Minimum: {MIN_CHARGE_DURATION_S}s.")
                can_stop = False

        if not can_stop:
            return web.json_response({"success": False, "error": f"Stop denied by Guard. Min charge time is {MIN_CHARGE_DURATION_S}s."}, status=403)

        if active_tx_id is None:
            ocpp_phases_value = self.phase_limit_store.get(cp_id)
            if ocpp_phases_value is None:
                cwarn(f"[{cp_id}] Phase Store leer. Führe Fallback DB-Zugriff für remote_stop durch.")
                amp_max, phases, pv_mode_val, _ = self.get_wallbox_steuerdaten(cp_id=cp_id)
                ocpp_phases_value = 1 if phases == "1" else 3

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
            await self.connected_charge_points[cp_id].send_call("SetChargingProfile", payload_stop_zero_amp)
            self.current_limit_store[cp_id] = 0.0
            self.phase_limit_store[cp_id] = ocpp_phases_value
            self.status_store[cp_id] = "AvailableRequested"
            self.transaction_start_timestamp[cp_id] = None
            return web.json_response({"success": True, "transactionId": None, "note": "Sent 0A SetChargingProfile instead of RemoteStop"})

        payload = {"transactionId": active_tx_id}
        await self.connected_charge_points[cp_id].send_call("RemoteStopTransaction", payload)
        self.status_store[cp_id] = "AvailableRequested"
        self.transaction_start_timestamp[cp_id] = None
        return web.json_response({"success": True, "transactionId": active_tx_id})

    async def set_pv_mode(self, request):
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)

        cp_id = data.get("charge_point_id")
        mode = data.get("mode", "off")
        if not cp_id or cp_id not in self.connected_charge_points:
            return web.json_response({"success": False, "error": "Charge Point not connected"}, status=404)

        amp, phases, pv_mode_val, is_pv_controlled = self.get_wallbox_steuerdaten(cp_id=cp_id)
        await self.apply_wallbox_settings(cp_id, amp, phases, pv_mode_val, is_pv_controlled)
        return web.json_response({"success": True, "mode": mode})

    # ----------------------------
    # AutoSync background task
    # ----------------------------
    async def autosync_task(self):
        await asyncio.sleep(2)
        cinfo(f"AutoSync task started, interval={self.auto_sync_interval}s")

        while True:
            if not self.connected_charge_points:
                cnote("AutoSync: keine verbundenen Charge Points")
            else:
                for cp_id in list(self.connected_charge_points.keys()):
                    try:
                        amp, phases, pv_mode_val, is_pv_controlled = self.get_wallbox_steuerdaten(cp_id=cp_id)
                        await self.apply_wallbox_settings(cp_id, amp, phases, pv_mode_val, is_pv_controlled)
                    except Exception as e:
                        cerr(f"AutoSync Fehler bei {cp_id}: {e}")

            await asyncio.sleep(self.auto_sync_interval)

    # ----------------------------
    # Start Server (WebSocket + HTTP)
    # ----------------------------
    async def start(self):
        ws = ws_serve(
            self.on_connect,
            "0.0.0.0",
            self.ws_port,
            subprotocols=OCPP_PROTOCOLS
        )

        app = web.Application()
        app.add_routes([
            web.get('/list', self.list_cp),
            web.get('/meter_values', self.meter_values),
            web.post('/remote_start', self.remote_start),
            web.post('/remote_stop', self.remote_stop),
            web.post('/set_pv_mode', self.set_pv_mode),
        ])

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.http_port)

        asyncio.create_task(self.autosync_task())

        await asyncio.gather(
            ws,
            site.start(),
        )

        cinfo(f"OCPP Manager läuft: WS={self.ws_port}, HTTP={self.http_port}")
        await asyncio.Future()
