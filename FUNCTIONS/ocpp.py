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

WS_PORT = 8887
HTTP_PORT = 8886
TIME_SHIFT_SECONDS = 5
DEFAULT_CONNECTOR_ID = 1
DEFAULT_IDTAG = "WattpilotUser"
OCPP_PROTOCOLS = ['ocpp1.6', 'ocpp2.0.1', 'ocpp1.5']

# ----------------------------
# Auffälliges Console-Logging
# ----------------------------
# 0=ERROR/WARN, 1=+/OK 2=+INFO, 3=+NOTE
def clog(level, prefix, msg):
    if log_level >= level:
        ts = datetime.now().strftime("%y%m%d %H:%M:%S")
        print(f"{ts} {prefix} {msg}")

def cerr(msg):   clog(0, "❌ ERROR:", msg)
def cwarn(msg):  clog(0, "⚠️ WARN:", msg)
def cok(msg):    clog(1, "✅ OK:", msg)
def cinfo(msg):  clog(2, "ℹ️ INFO:", msg)
def cnote(msg):  clog(3, "✏️ NOTE:", msg)

# Import basics/config zum Lesen der INI-Dateien
import FUNCTIONS.functions
basics = FUNCTIONS.functions.basics()
config = basics.loadConfig(['default'])
# Logginglevel auf default.ini
log_level = basics.getVarConf('wallbox','log_level', 'eval')

# Hybrid Import für websockets (neu/alt)
try:
    # websockets >=12
    from websockets.server import serve as ws_serve
    USING_NEW_WEBSOCKETS = True
    cinfo(f"Using NEW websockets.server.serve API")
except Exception:
    # websockets <=11
    from websockets.asyncio.server import serve as ws_serve
    USING_LEGACY_WEBSOCKETS = True
    cinfo(f"Using LEGACY websockets.asyncio.server.serve API")

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

        # Neue Stores für Energiemessung/Target
        # Default-Ziel nutzen (jetzt aus Instanz-Attributen)
        self.manager.target_energy_kwh_store.setdefault(self.cp_id, self.manager.DEFAULT_TARGET_KWH)
        self.manager.charged_energy_wh_store.setdefault(self.cp_id, 0.0)
        self.manager.last_energy_wh_store.setdefault(self.cp_id, None)

        # Setze Zeitstempel zurück so der erste Wechsel erlaubt ist
        self.manager.last_phase_change_timestamp[self.cp_id] = datetime.now() - timedelta(seconds=self.manager.MIN_PHASE_DURATION_S + 10)
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

                # Aktualisiere die internen Wallbox-Attribute und wende sie an
                self.manager.refresh_wallbox_settings(self.cp_id)
                asyncio.create_task(self.manager.apply_wallbox_settings(
                    self.cp_id,
                    self.manager.wb_amp,
                    self.manager.wb_phases,
                    self.manager.wb_pv_mode,
                    self.manager.wb_is_pv_controlled,
                    self.manager.wb_amp_min
                ))

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
                # Verarbeite MeterValues asynchron (update charged energy, evtl. stop)
                asyncio.create_task(self.manager.update_charged_energy_from_meter(self.cp_id, payload))

            elif action == "StartTransaction":
                tx_id = int(datetime.now(timezone.utc).timestamp())
                self.manager.transaction_id_store[self.cp_id] = tx_id
                self.manager.status_store[self.cp_id] = "Charging"
                self.manager.transaction_start_timestamp[self.cp_id] = datetime.now()
                # Reset charged energy for new transaction, set baseline last energy if available
                try:
                    await self.manager.start_transaction_setup(self.cp_id)
                except Exception as e:
                    cwarn(f"StartTransaction setup failed for {self.cp_id}: {e}")
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

    def __init__(self, ws_port=WS_PORT, http_port=HTTP_PORT, auto_sync_interval=20):
        # Stores (waren vorher global)
        self.connected_charge_points = {}     # cp_id -> ChargePointHandler
        self.meter_values_store = {}
        self.status_store = {}
        # per-charge-point pv_mode store (do not override: dict)
        self.pv_mode = {}
        self.current_limit_store = {}
        self.phase_limit_store = {}
        self.debug_store = {}
        self.transaction_id_store = {}
        self.last_phase_change_timestamp = {}
        self.transaction_start_timestamp = {}

        # Neue Stores für Energie-Zielverfolgung
        self.target_energy_kwh_store = {}
        self.charged_energy_wh_store = {}
        self.last_energy_wh_store = {}

        # Phase-change candidate store to implement hysteresis/timer only for phase changes
        self.phase_change_candidate = {}

        # Config
        self.ws_port = ws_port
        self.http_port = http_port
        # keep auto_sync_interval as instance attribute (may be updated from DB later)
        self.auto_sync_interval = auto_sync_interval

        # Default-Werte für Wallbox-Steuerdaten als Instanzattribute (präfix wb_)
        self.wb_amp_max = 16.0
        self.wb_amp_min = 6.0
        self.wb_phases = "3"
        self.wb_pv_mode = 0.0
        self.wb_amp = self.wb_amp_max
        self.wb_is_pv_controlled = False
        self.Netzbezug = 0.0
        self.Produktion = 0.0
        self.Batteriebezug = 0.0

        # Die früheren Modul-Constants jetzt als Instanzattribute (können aus DB überschrieben werden)
        self.AUTO_SYNC_INTERVAL = auto_sync_interval
        self.MIN_PHASE_DURATION_S = 180 
        self.MIN_CHARGE_DURATION_S = 600
        self.PHASE_CHANGE_CONFIRM_S = 30 #Bestätigungszeit für Phasenwechsel
        self.residualPower = -300 # Watt +Netzeinspeisung -Netzbezug
        self.DEFAULT_TARGET_KWH = 0 # Lade-Ziel in kWh, Laden stoppt, wenn Wert erreicht ist, 0=ausgeschaltet

    def refresh_wallbox_settings(self, cp_id=None):
        """
        Hilfsfunktion: ruft get_wallbox_steuerdaten auf (DB-Logik) und aktualisiert
        die internen wb_-Attribute, so dass andere Methoden diese direkt lesen können.
        """
        amp, phases, pv_mode, is_pv_controlled, amp_min = self.get_wallbox_steuerdaten(cp_id=cp_id)
        # get_wallbox_steuerdaten speichert bereits in den wb_-Attribs; aber wir stellen sicher:
        self.wb_amp = amp
        self.wb_phases = phases
        self.wb_pv_mode = pv_mode
        self.wb_is_pv_controlled = is_pv_controlled
        self.wb_amp_min = amp_min
        # Use loaded AUTO_SYNC_INTERVAL (if set by DB) for background task
        self.auto_sync_interval = getattr(self, 'AUTO_SYNC_INTERVAL', self.auto_sync_interval)

        # --- Target-KWH-Store mit DB-Default synchronisieren ---
        # Der DB-Wert (self.DEFAULT_TARGET_KWH) ist immer der Masterwert.
        new_default_kwh = self.DEFAULT_TARGET_KWH

        for cid in list(self.connected_charge_points.keys()):
            # Holen Sie den aktuellen Wert aus dem Store (Fallback 0.0)
            current_store_value = self.target_energy_kwh_store.get(cid, 0.0)

            # Setze den Wert und protokolliere nur, wenn eine Änderung vorliegt.
            if current_store_value != new_default_kwh:
                self.target_energy_kwh_store[cid] = new_default_kwh
                # Verwende cinfo, da es ein geplanter Sync ist (kein Fehler)
                cinfo(f"[{ '..' + cid[-4:] }] Ladeziel von {current_store_value} kWh auf neuen DB-Default ({new_default_kwh} kWh) aktualisiert.")

    # ----------------------------
    # DB Helper (ausgelagert)
    # ----------------------------
    def get_wallbox_steuerdaten(self, cp_id=None):
        """
        Liest aus der Datenbank mittels FUNCTIONS.SQLall.sqlall().getSQLsteuerdaten('wallbox')
        Rückgabe: (amp: float, phases: str, pv_mode: float, is_pv_controlled: bool, amp_min: float)
        ...
        """
        # Versuche DB-Lesen
        try:
            sqlall = FUNCTIONS.SQLall.sqlall()
            data = sqlall.getSQLsteuerdaten('wallbox', 'CONFIG/Prog_Steuerung.sqlite')
        except Exception as e:
            cwarn(f"DB-Zugriff fehlgeschlagen oder FUNCTIONS nicht vorhanden: {e}")
            # Return current instance values as fallback
            return getattr(self, 'wb_amp', 0.0), getattr(self, 'wb_phases', "3"), getattr(self, 'wb_pv_mode', 0.0), False, getattr(self, 'wb_amp_min', 6.0)

        # Wenn keine Daten vorhanden sind -> Instanzwerte zurückgeben
        if not data or '1' not in data:
            cwarn("Keine Wallbox-Daten in DB gefunden → Verwende Instanz-Defaults")
            return getattr(self, 'wb_amp', 0.0), getattr(self, 'wb_phases', "3"), getattr(self, 'wb_pv_mode', 0.0), False, getattr(self, 'wb_amp_min', 6.0)

        # Parse Haupt-Zeile (ID=1)
        try:
            row = data.get('1') or data.get(1)
            if row:
                parts = row.get('Options', '').split(',')

                # amp_min aus Options[0]
                try:
                    amp_min_val = float(parts[0])
                except (ValueError, IndexError):
                    amp_min_val = getattr(self, 'wb_amp_min', 6.0)
                if amp_min_val < 6:
                    amp_min_val = 6.0

                # amp_max aus Options[1]
                try:
                    amp_max_val = float(parts[1])
                except (ValueError, IndexError):
                    amp_max_val = getattr(self, 'wb_amp_max', 16.0)
                if amp_max_val < amp_min_val:
                    amp_max_val = amp_min_val
                if amp_max_val > 16:
                    amp_max_val = 16.0

                # phases / pv_mode aus Res_Feld2 / Res_Feld1
                self.wb_phases = str(row.get('Res_Feld2', self.wb_phases))
                try:
                    self.wb_pv_mode = float(row.get('Res_Feld1', self.wb_pv_mode))
                except Exception:
                    # leave existing value
                    pass

                # setze die berechneten Ampere-Grenzen
                self.wb_amp_max = amp_max_val
                self.wb_amp_min = amp_min_val

                cinfo(f"DB-Steuerdaten geladen (ID=1): amp_max={self.wb_amp_max}A, phases={self.wb_phases}, pv_mode={self.wb_pv_mode}, amp_min={self.wb_amp_min}A")
        except Exception as e:
            cwarn(f"Fehler beim Parsen der DB-Daten (ID=1): {e} → Instanz-Defaults verwendet")
            # leave existing wb_* values

        # ---- Lese zusätzliche Steuer-Parameter wie gewünscht (ID=2, ID=3) ----
        try:
            # ID=2: Res_Feld1 = MIN_PHASE_DURATION_S, Res_Feld2 = MIN_CHARGE_DURATION_S, Options = AUTO_SYNC_INTERVAL
            row2 = data.get('2') or data.get(2)
            if row2:
                try:
                    self.MIN_PHASE_DURATION_S = int(float(row2.get('Res_Feld1', self.MIN_PHASE_DURATION_S)))
                except Exception:
                    pass
                try:
                    self.MIN_CHARGE_DURATION_S = int(float(row2.get('Res_Feld2', self.MIN_CHARGE_DURATION_S)))
                except Exception:
                    pass
                try:
                    opt = row2.get('Options', None)
                    if opt is not None and str(opt).strip() != "":
                        self.AUTO_SYNC_INTERVAL = int(float(opt))
                except Exception:
                    pass

            # ID=3: Res_Feld1 residualPower, Res_Feld2 DEFAULT_TARGET_KWH, Options PHASE_CHANGE_CONFIRM_S
            row3 = data.get('3') or data.get(3)
            if row3:
                try:
                    self.residualPower = float(row3.get('Res_Feld1', self.residualPower))
                except Exception:
                    pass
                try:
                    self.DEFAULT_TARGET_KWH = float(row3.get('Res_Feld2', self.DEFAULT_TARGET_KWH))
                except Exception:
                    pass
                try:
                    opt3 = row3.get('Options', None)
                    if opt3 is not None and str(opt3).strip() != "":
                        self.PHASE_CHANGE_CONFIRM_S = int(float(opt3))
                except Exception:
                    pass

            # Nach DB-Lesen auto_sync_interval für Hintergrundtask updaten
            self.auto_sync_interval = getattr(self, 'AUTO_SYNC_INTERVAL', self.auto_sync_interval)

            cinfo(f"DB-Steuerdaten geladen (ID=2): AUTO_SYNC_INTERVAL={getattr(self,'AUTO_SYNC_INTERVAL',None)}, MIN_PHASE_DURATION_S={getattr(self,'MIN_PHASE_DURATION_S',None)}, MIN_CHARGE_DURATION_S={getattr(self,'MIN_CHARGE_DURATION_S',None)}")
            cinfo(f"DB-Steuerdaten geladen (ID=3): PHASE_CHANGE_CONFIRM_S={getattr(self,'PHASE_CHANGE_CONFIRM_S',None)}, residualPower={getattr(self,'residualPower',None)}, DEFAULT_TARGET_KWH={getattr(self,'DEFAULT_TARGET_KWH',None)}")
        except Exception as e:
            cwarn(f"Fehler beim Lesen der Konfiguration aus DB: {e} → Instanz-Defaults verwendet")

        # ---- Berechne zulässigen Ampere-Wert basierend auf PV-Modus und Inverter ----
        amp = self.wb_amp_max
        is_pv_controlled = False

        # Inverter API immer aufrufen, um Netzbezug zu erhalten und in Instanzattribut speichern
        self.Netzbezug = 0.0 # Default-Wert
        self.Produktion = 0.0
        self.Batteriebezug = 0.0
        try:
            InverterApi = basics.get_inverter_class(class_type="Api")
            inverter_api = InverterApi()
            API = inverter_api.get_API()
            # Der Wert wird direkt im Instanzattribut gespeichert
            self.Netzbezug = API.get('aktuelleEinspeisung', 0)
            self.Produktion = API.get('aktuellePVProduktion', 0)
            self.Batteriebezug = API.get('aktuelleBatteriePower', 0)
        except Exception as e:
            cwarn(f"Inverter API konnte nicht geladen werden: {e} → Netzbezug wird auf 0 gesetzt.")
            self.Netzbezug = 0.0 # Sicherstellen, dass der Wert numerisch ist

        current_charge_power = 0
        if cp_id and cp_id in self.connected_charge_points:
            current_charge_power = self.get_current_power(cp_id)
        

        # Überschuss-Berechnung nutzt jetzt self.Netzbezug
        aus_batterie = max(0.0, self.Batteriebezug)
        in_batterie = max(0.0, -self.Batteriebezug)
        hausverbrauch = max(0.0, self.Produktion + self.Batteriebezug + self.Netzbezug - current_charge_power )
        ueberschuss = max(0, (self.Produktion - hausverbrauch + self.Batteriebezug - self.residualPower))  #entWIGGlung FEHLER in der Berechnung??
        cinfo(f"Überschuss: PV: {self.Produktion}, AKKU {self.Batteriebezug}, Netz: {self.Netzbezug}W, Hausverbrauch {hausverbrauch}, Wallbox ({current_charge_power}W), Überschuss: {ueberschuss}W")

        # PV-Steuerlogik nur ausführen, wenn der Modus 1 oder 2 ist
        if self.wb_pv_mode == 1 or self.wb_pv_mode == 2:
            is_pv_controlled = True

            amp = 0
            amp_1 = int(ueberschuss / 230 / 1) if ueberschuss else 0
            amp_3 = int(ueberschuss / 230 / 3) if ueberschuss else 0

            if self.wb_phases == "1":
                amp = min(amp_1, self.wb_amp_max) if amp_1 >= 6 else 0
            elif self.wb_phases == "3" or self.wb_phases == "0":
                # Anpassung für "Phase 0" (Auto): Die Phasenwechsel-Schwellen werden an Min/Max Ampere gebunden.
                if self.wb_phases == "0":
                    # Benutzerwunsch: 1P Start nur mit wb_amp_min und 3P Start nur mit wb_amp_max (pro Phase).
                    required_amp_for_1P = self.wb_amp_min
                    required_amp_for_3P = self.wb_amp_max
                else:
                    # Standard Logik für wb_phases == "3": 6A Minimum
                    required_amp_for_1P = 6.0
                    required_amp_for_3P = 6.0

                if amp_3 >= required_amp_for_3P:
                    self.wb_phases = "3"
                    amp = min(amp_3, self.wb_amp_max)
                elif amp_1 >= required_amp_for_1P:
                    self.wb_phases = "1"
                    amp = min(amp_1, self.wb_amp_max)
                else:
                    amp = 0

        # pv_mode == 2: niemals vollständig abschalten, sondern Minimum erzwingen
        if self.wb_pv_mode == 2:
            if amp < self.wb_amp_min:
                amp = min(self.wb_amp_min, self.wb_amp_max)

        # Werte in Instanzattribute speichern
        self.wb_amp = amp
        self.wb_is_pv_controlled = is_pv_controlled

        return self.wb_amp, self.wb_phases, self.wb_pv_mode, is_pv_controlled, self.wb_amp_min

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

    async def apply_wallbox_settings(self, cp_id, amp, phases, pv_mode_val, is_pv_controlled, amp_min=None):
        """Wendet Ampere- und Phasen-Werte an (SetChargingProfile / RemoteStart/Stop).
           Hysterese/Timer wird ausschließlich auf Phasenwechsel angewendet (self.PHASE_CHANGE_CONFIRM_S).
           pv_mode==2: niemals vollständig auf 0A abschalten, sondern mindestens amp_min setzen.
        """
        if cp_id not in self.connected_charge_points:
            cwarn(f"apply_wallbox_settings: Charge Point { '..' + cp_id[-4:] } nicht verbunden.")
            return False

        cp = self.connected_charge_points[cp_id]

        # Direkter gewünschter Wert (keine Ampere-Hysterese)
        amp_desired = amp if pv_mode_val != 0.0 else 0.0
        ocpp_phases_value = 1 if phases == "1" else 3

        # Init stores
        self.current_limit_store.setdefault(cp_id, None)
        self.phase_limit_store.setdefault(cp_id, None)
        self.last_phase_change_timestamp.setdefault(cp_id, datetime.now())
        self.transaction_start_timestamp.setdefault(cp_id, None)
        self.phase_change_candidate.setdefault(cp_id, None)

        # Ensure energy stores exist
        self.target_energy_kwh_store.setdefault(cp_id, self.DEFAULT_TARGET_KWH)
        self.charged_energy_wh_store.setdefault(cp_id, 0.0)
        self.last_energy_wh_store.setdefault(cp_id, None)
        curr_limit = self.current_limit_store.get(cp_id)
        phase_limit = self.phase_limit_store.get(cp_id)

        # Decide if phase change is requested (desired != current)
        requested_phase = ocpp_phases_value
        phase_changed = (phase_limit != requested_phase)

        # KORREKTUR: Bei Initialisierung (phase_limit is None) sofort den gewünschten Wert übernehmen.
        is_initial_change = phase_limit is None
        final_ocpp_phases_value = phase_limit if not is_initial_change else requested_phase

        cinfo(f"[{ '..' + cp_id[-4:] }] Prüfe Sync: PV-Mode={pv_mode_val}, PV-Steuerung={is_pv_controlled}, Wunsch: {amp_desired}A/{requested_phase}P. Aktuell: {curr_limit}A/{phase_limit}P")

        # -----------------------
        # PHASE-ONLY HYSTERESE/TIMER
        # -----------------------
        is_charging_requested = amp_desired > 0.0

        # Wenden Sie die Hysterese NUR an, wenn eine Phasenänderung gewünscht ist
        # UND keine Initialisierung vorliegt UND eine Ladung mit > 0A gewünscht wird.
        if phase_changed and not is_initial_change and is_charging_requested:
            candidate = self.phase_change_candidate.get(cp_id)
            now = datetime.now()

            # New candidate or different requested phase -> start timer
            if not candidate or candidate.get('requested') != requested_phase:
                self.phase_change_candidate[cp_id] = {'requested': requested_phase, 'since': now}
                phase_changed = False # Blockiere Wechsel
                cnote(f"[{ '..' + cp_id[-4:] }] PHASE-HYSTERESE: Neuer Phasenwunsch {requested_phase} erkannt, starte Bestätigungs-Timer ({self.PHASE_CHANGE_CONFIRM_S}s).")
            else:
                elapsed = (now - candidate['since']).total_seconds()
                if elapsed >= self.PHASE_CHANGE_CONFIRM_S:
                    phase_changed = True # Erlaube Wechsel
                    final_ocpp_phases_value = requested_phase
                    self.phase_change_candidate[cp_id] = None
                    cnote(f"{ '..' + cp_id[-4:] }] PHASE-HYSTERESE: Phasenwechsel {requested_phase} bestätigt nach {int(elapsed)}s.")
                else:
                    phase_changed = False # Blockiere Wechsel
                    cnote(f"[{ '..' + cp_id[-4:] }] PHASE-HYSTERESE: Warte {self.PHASE_CHANGE_CONFIRM_S - int(elapsed)}s bis Phasenwechsel möglich.")
        else:
            # Fall: Phase geändert, aber amp_desired == 0.0 (oder Initialisierung)
            # -> Wechsel sofort erlauben, da keine aktive Ladung betroffen ist.
            if phase_changed and not is_initial_change and not is_charging_requested:
                final_ocpp_phases_value = requested_phase
                phase_changed = True # Wechsel erlauben
                cnote(f"[{ '..' + cp_id[-4:] }] PHASE-HYSTERESE: Umgangen (0A Wunsch). Phase auf {requested_phase}P gesetzt.")

            # Timer cleanup logic (Timer zurücksetzen, falls er lief und eine der oben genannten Bedingungen eintrat)
            if self.phase_change_candidate.get(cp_id):
                self.phase_change_candidate[cp_id] = None
                cnote(f"[{ '..' + cp_id[-4:] }] PHASE-HYSTERESE: Phasenwunsch entfällt/Initialisierung/0A-Wunsch, Timer zurückgesetzt.")

        # pv_mode==2 should not fully stop
        amp_allowed = amp_desired
        if pv_mode_val == 2:
            if amp_allowed < (amp_min or 6.0):
                cnote(f"[{ '..' + cp_id[-4:] }] pv_mode==2: Vermeide Abschaltung, setze Minimum {amp_min}A statt {amp_allowed}A.")
                amp_allowed = max(amp_allowed, amp_min)

        # Zusätzlich: wenn ein Ziel gesetzt ist und bereits erreicht, zwinge Stop (0A)
        target_kwh = self.target_energy_kwh_store.get(cp_id, self.DEFAULT_TARGET_KWH)
        charged_wh = self.charged_energy_wh_store.get(cp_id, 0.0)
        if target_kwh and (charged_wh >= target_kwh * 1000.0):
            cnote(f"[{ '..' + cp_id[-4:] }] Ziel erreicht ({charged_wh/1000.0:.3f} kWh >= {target_kwh} kWh). Stoppe Laden.")
            amp_allowed = 0.0

        # Laden starten/stoppen (use amp_allowed)
        status = self.status_store.get(cp_id)
        active_tx_id = self.transaction_id_store.get(cp_id)

        if amp_allowed > 0.0 and (amp_allowed >= 6.0):
            if status in ["Available", "AvailableRequested", "SuspendedEVSE", "Finishing"]:
                await cp.send_call("RemoteStartTransaction", {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG})
                self.status_store[cp_id] = "ChargingRequested"
                if not self.transaction_start_timestamp.get(cp_id):
                    self.transaction_start_timestamp[cp_id] = datetime.now()
                cinfo(f"[{ '..' + cp_id[-4:] }] Laden gestartet (amp={amp_allowed}A, RemoteStart)")
        else:
            # Stopp-Guard (nur bei PV-Steuerung relevant)
            can_stop_by_guard = True
            if is_pv_controlled:
                if self.transaction_start_timestamp.get(cp_id):
                    charging_duration = (datetime.now() - self.transaction_start_timestamp.get(cp_id)).total_seconds()
                    if charging_duration < self.MIN_CHARGE_DURATION_S:
                        cwarn(f"[{ '..' + cp_id[-4:] }] 🛑 STOP GUARD (Zeit): Stop (0A) abgelehnt. Nur {round(charging_duration)}s geladen. Minimum: {self.MIN_CHARGE_DURATION_S}s.")
                        can_stop_by_guard = False
                    else:
                        cnote(f"[{ '..' + cp_id[-4:] }] ✅ STOP Laden erlaubt. (Ladedauer={round(charging_duration)}s)")
            else:
                cnote(f"[{ '..' + cp_id[-4:] }] Stop (0A) gewünscht durch pv_mode={pv_mode_val}. Guard übersprungen, da PV-Steuerung inaktiv.")

            # Wenn Ziel erreicht, ignorieren Guard und stoppe trotzdem (Ziel überträgt Priorität)
            if target_kwh and (charged_wh >= target_kwh * 1000.0):
                cnote(f"[{ '..' + cp_id[-4:] }] Ziel erreicht -> stoppe ungeachtet des Guards.")
                can_stop_by_guard = True

            if not can_stop_by_guard:
                fallback_limit = amp_min or 6.0
                amp_allowed = fallback_limit
                cwarn(f"[{ '..' + cp_id[-4:] }] ❗ STOP GUARD aktiv. Setze Ladelimit auf {fallback_limit}A zur Vermeidung eines Stopps.")
            else:
                if active_tx_id:
                    await cp.send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                    self.status_store[cp_id] = "AvailableRequested"
                    self.transaction_start_timestamp[cp_id] = None
                    cnote(f"[{ '..' + cp_id[-4:] }] Laden gestoppt (amp=0.0A, RemoteStop als Fallback)")
                elif status not in ["Available", "AvailableRequested"]:
                    self.status_store[cp_id] = "Available"
                    self.transaction_start_timestamp[cp_id] = None
                    cnote(f"[{ '..' + cp_id[-4:] }] Status auf Available gesetzt.")

        # Re-check amp change
        amp_changed = (self.current_limit_store.get(cp_id) != amp_allowed)

        # Wenn Ampere oder Phase geändert => senden
        if amp_changed or phase_changed:
            # Bei Phase wechsel: ggf. 0A Limit senden bevor neue Phase
            if phase_changed and not is_initial_change: # Phase nur ändern, wenn nicht initial
                cinfo(f"[{ '..' + cp_id[-4:] }] Phase Änderung erkannt: {self.phase_limit_store.get(cp_id)} -> {final_ocpp_phases_value}. Starte 0A-Stop Prozedur.")
                current_power = self.get_current_power(cp_id)
                if current_power > 50:
                    cinfo(f"[{ '..' + cp_id[-4:] }] Aktive Leistung {current_power}W. Sende 0A Limit + neue Phase.")
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
                            cok(f"[{ '..' + cp_id[-4:] }] Leistung < 50W nach {i+1}s. Führe Phasenwechsel-Abschluss durch.")
                            break
                    else:
                        cwarn(f"[{ '..' + cp_id[-4:] }] WARNUNG: Leistung ist nach 15s noch hoch ({current_power}W). Sende finales Limit.")
                else:
                    cnote(f"[{ '..' + cp_id[-4:] }] Aktive Leistung {current_power}W. Kein 0A-Stop notwendig.")
            elif phase_changed and is_initial_change:
                 # Nur Logging, da final_ocpp_phases_value bereits requested_phase ist
                 cnote(f"[{ '..' + cp_id[-4:] }] Initiales Phasenlimit auf {final_ocpp_phases_value}P gesetzt (Phase war None).")


            # Sende finales Limit (amp_allowed)
            cinfo(f"[{ '..' + cp_id[-4:] }] Sende finales Limit: {amp_allowed}A an Phase {final_ocpp_phases_value}.")

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
                            "limit": amp_allowed,
                            "numberPhases": final_ocpp_phases_value
                        }]
                    }
                }
            }
            await cp.send_call("SetChargingProfile", payload_final_limit)

            # Stores updaten
            self.current_limit_store[cp_id] = amp_allowed
            self.phase_limit_store[cp_id] = final_ocpp_phases_value

            # last_phase_change_timestamp nur bei tatsächlichem Phasenwechsel aktualisieren
            if phase_changed:
                self.last_phase_change_timestamp[cp_id] = datetime.now()
                cnote(f"[{ '..' + cp_id[-4:] }] ⏳ COOLDOWN: Warte 3 Sekunden nach Phasenwechsel ({final_ocpp_phases_value}P).")
                await asyncio.sleep(3)

            cok(f"[{ '..' + cp_id[-4:] }] Ampere/Phase erfolgreich gesetzt: {amp_allowed}A / {final_ocpp_phases_value}P")
        else:
            cnote(f"[{ '..' + cp_id[-4:] }] Ampere/Phase unverändert ({amp_allowed}A / {final_ocpp_phases_value}P)")

        return True

    # ----------------------------
    # Energie-Target / MeterValues Verarbeitung
    # ----------------------------
    async def start_transaction_setup(self, cp_id):
        """Reset charged energy for a new transaction and set baseline last meter reading if available."""
        self.charged_energy_wh_store[cp_id] = 0.0
        # set baseline if we have a meter reading
        baseline = self._extract_energy_wh_from_meter_store(cp_id)
        if baseline is not None:
            self.last_energy_wh_store[cp_id] = baseline
            cnote(f"[{ '..' + cp_id[-4:] }] StartTransaction: baseline energy set to {baseline}Wh")
        else:
            self.last_energy_wh_store[cp_id] = None
            cnote(f"[{ '..' + cp_id[-4:] }] StartTransaction: no baseline energy available")

    def _extract_energy_wh_from_meter_store(self, cp_id, meter_payload=None):
        """Hilfsroutine: extrahiere aktuellen kumulativen Energy-Wert (Wh) aus meter_values_store oder aus gegebenem payload."""
        payload = meter_payload or self.meter_values_store.get(cp_id)
        if not payload or 'meterValue' not in payload:
            return None
        for meter_value in payload['meterValue']:
            if 'sampledValue' in meter_value:
                for sample in meter_value['sampledValue']:
                    meas = sample.get('measurand', '')
                    if meas.startswith('Energy.'):
                        try:
                            val = float(sample.get('value', 0))
                            unit = (sample.get('unit') or '').lower()
                            if unit == 'kwh':
                                return val * 1000.0
                            else:
                                # assume Wh
                                return val
                        except Exception:
                            continue
        return None

    async def update_charged_energy_from_meter(self, cp_id, meter_payload):
        """Berechnet Delta der kumulativen Energy-Messung und addiert auf charged_energy_wh_store.
           Wenn ein Ziel gesetzt ist und erreicht wird -> stoppe Laden automatisch.
        """
        try:
            energy_wh = self._extract_energy_wh_from_meter_store(cp_id, meter_payload)
            if energy_wh is None:
                return
            last = self.last_energy_wh_store.get(cp_id)
            # Wenn kein letzte Messung vorhanden, initialisieren und nichts buchen
            if last is None:
                self.last_energy_wh_store[cp_id] = energy_wh
                return
            delta = energy_wh - last
            if delta < 0:
                # Zähler-Rollover oder Messsprung -> setze baseline neu
                cwarn(f"[{ '..' + cp_id[-4:] }] Energy counter decreased ({last} -> {energy_wh}). Reset baseline.")
                self.last_energy_wh_store[cp_id] = energy_wh
                return

            # Zähle nur während aktiver Transaktion bzw. Status Charging
            if self.transaction_id_store.get(cp_id) or self.status_store.get(cp_id) == "Charging":
                self.charged_energy_wh_store[cp_id] = self.charged_energy_wh_store.get(cp_id, 0.0) + delta
                self.last_energy_wh_store[cp_id] = energy_wh
                cinfo(f"[{ '..' + cp_id[-4:] }] Geladene Energie erhöht um {round(delta,2)}Wh -> total {round(self.charged_energy_wh_store[cp_id],2)}Wh")
                # Prüfe Ziel
                target_kwh = self.target_energy_kwh_store.get(cp_id, self.DEFAULT_TARGET_KWH)
                if target_kwh and (self.charged_energy_wh_store[cp_id] >= target_kwh * 1000.0):
                    cinfo(f"[{ '..' + cp_id[-4:] }] Ziel erreicht ({self.charged_energy_wh_store[cp_id]/1000.0:.3f} kWh >= {target_kwh} kWh). Stoppe Laden.")
                    # Stoppen: wie remote_stop
                    active_tx_id = self.transaction_id_store.get(cp_id)
                    if active_tx_id:
                        await self.connected_charge_points[cp_id].send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                        self.transaction_id_store[cp_id] = None
                        self.status_store[cp_id] = "AvailableRequested"
                        self.transaction_start_timestamp[cp_id] = None
                    else:
                        ocpp_phases_value = self.phase_limit_store.get(cp_id) or 3
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
            else:
                # Nicht laden: nur baseline aktualisieren
                self.last_energy_wh_store[cp_id] = energy_wh
        except Exception as e:
            cwarn(f"Fehler in update_charged_energy_from_meter für {cp_id}: {e}")

    # ----------------------------
    # WebSocket on_connect
    # ----------------------------
    async def on_connect(self, websocket, path):
        cp_id_from_path = path.strip('/') if path else ''
        subprotocol = websocket.subprotocol if hasattr(websocket, 'subprotocol') else None
        cp_id = cp_id_from_path or subprotocol or f"CP-{int(datetime.now().timestamp())}"

        cinfo(f"Neue Verbindung: cp_id={ '..' + cp_id[-4:] }, subprotocol={subprotocol}, path='{ '/..' + path[-4:]}'")
        handler = ChargePointHandler(self, cp_id, websocket)
        self.connected_charge_points[cp_id] = handler

        try:
            await handler.start()
        except Exception as e:
            logger.exception(f"Fehler in Verbindung { '..' + cp_id[-4:] }: {e}")
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
            self.phase_change_candidate.pop(cp_id, None)
            # cleanup energy stores
            self.target_energy_kwh_store.pop(cp_id, None)
            self.charged_energy_wh_store.pop(cp_id, None)
            self.last_energy_wh_store.pop(cp_id, None)
            cinfo(f"Verbindung beendet: { '..' + cp_id[-4:] }")

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

        candidate = self.phase_change_candidate.get(cp_id)
        candidate_info = None
        if candidate:
            elapsed = (datetime.now() - candidate['since']).total_seconds()
            candidate_info = {"requested": candidate['requested'], "since": candidate['since'].isoformat(), "elapsed_s": round(elapsed,1), "confirm_after_s": self.PHASE_CHANGE_CONFIRM_S}

        charged_wh = self.charged_energy_wh_store.get(cp_id, 0.0)
        target_kwh = self.target_energy_kwh_store.get(cp_id, self.DEFAULT_TARGET_KWH)
        remaining_kwh = None
        if target_kwh and target_kwh > 0:
            remaining_kwh = max(0.0, target_kwh - charged_wh / 1000.0)

        return web.json_response({
            "meter": self.meter_values_store.get(cp_id, {}),
            "status": self.status_store.get(cp_id, "Unknown"),
            "pv_mode": self.pv_mode.get(cp_id, "off"),
            "current_limit": self.current_limit_store.get(cp_id, None),
            "phases": self.phase_limit_store.get(cp_id, None),
            "transaction_id": self.transaction_id_store.get(cp_id),
            "charging_duration_s": round(duration, 1),
            "phase_stable_s": round(phase_duration, 1),
            "debug_messages": self.debug_store.get(cp_id, []),
            "phase_change_candidate": candidate_info,
            # Energie-Infos für Frontend
            "Netzbezug_W": self.Netzbezug,
            "Produktion_W": self.Produktion,
            "Batteriebezug_W": self.Batteriebezug,
            "target_energy_kwh": target_kwh,
            "charged_energy_kwh": round(charged_wh / 1000.0, 4),
            "remaining_kwh": round(remaining_kwh, 4) if remaining_kwh is not None else None
        })

    async def reset_counter(self, request):
        """HTTP-Handler zum Zurücksetzen des Lade-Zählers für einen Charge Point."""
        cp_id = request.query.get("charge_point_id")
        if not cp_id:
            return web.json_response({"error": "Missing charge_point_id"}, status=400)

        success = await self.reset_charged_energy_counter(cp_id)

        if success:
            return web.json_response({"status": "success", "charge_point_id": cp_id, "message": "Charged energy counter reset to 0"})
        else:
            return web.json_response({"status": "error", "charge_point_id": cp_id, "message": "Charge point not found or reset failed"}, status=404)

    # ----------------------------
    # Zähler-Reset-Logik
    # ----------------------------
    async def reset_charged_energy_counter(self, cp_id):
        """Setzt die geladene Energie (charged_energy_wh_store) und die letzte Zählerablesung (last_energy_wh_store) zurück."""
        if cp_id not in self.connected_charge_points:
            cwarn(f"Reset-Zähler: Charge Point { '..' + cp_id[-4:] } ist nicht verbunden.")
            return False

        # Setze die Stores zurück
        self.charged_energy_wh_store[cp_id] = 0.0
        self.last_energy_wh_store[cp_id] = None

        cnote(f"[{ '..' + cp_id[-4:] }] ✅ Geladene Energie und Zähler-Baseline erfolgreich zurückgesetzt.")
        return True

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
                        # refresh settings once and then use wb_-attributes directly
                        self.refresh_wallbox_settings(cp_id=cp_id)
                        await self.apply_wallbox_settings(cp_id, self.wb_amp, self.wb_phases, self.wb_pv_mode, self.wb_is_pv_controlled, self.wb_amp_min)
                    except Exception as e:
                        cerr(f"AutoSync Fehler bei { '..' + cp_id[-4:] }: {e}")

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
            web.post('/reset_counter', self.reset_counter),
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
