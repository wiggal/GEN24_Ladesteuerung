#!/usr/bin/env python3
"""
FUNCTIONS/ocpp.py — Refactorierte, besser strukturierte Version
"""

from __future__ import annotations
import asyncio
import json
import traceback
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from aiohttp import web

# ----------------------
# Konfiguration / Defaults
# ----------------------
WS_PORT = 8887
HTTP_PORT = 8886
TIME_SHIFT_SECONDS = 5
DEFAULT_CONNECTOR_ID = 1
DEFAULT_IDTAG = "WattpilotUser"
OCPP_PROTOCOLS = ['ocpp1.6', 'ocpp2.0.1', 'ocpp1.5']

# Externe Module (bestehend aus originalem Projekt)
import FUNCTIONS.functions
import FUNCTIONS.SQLall

basics = FUNCTIONS.functions.basics()
config = basics.loadConfig(['default', 'charge'])
# try to read configured log level; fallback handled below
try:
    log_level = basics.getVarConf('wallbox', 'log_level', 'eval')
except Exception:
    log_level = 3

# ----------------------
# print-based logging 
# ----------------------
# 0=ERROR/WARN, 1=+/OK 2=+INFO, 3=+NOTE
# Einfaches Dup-Suppressing in clog — ersetzt die vorherige clog-Definition
_last_clog_content: Optional[str] = None

def clog(level: int, prefix: str, msg: str):
    """
    Unterdrückt unmittelbar aufeinanderfolgende, identische Log-Nachrichten
    """
    global _last_clog_content
    try:
        if log_level >= level:
            content = f"{prefix} {msg}"
            # Wenn dieselbe prefix+msg unmittelbar zuvor geloggt wurde, unterdrücken
            if _last_clog_content == content:
                return
            _last_clog_content = content
            ts = datetime.now().strftime("%m-%d %H:%M:%S")
            print(f"{ts} {content}")
    except Exception:
        # best-effort print, keine weitere Unterdrückung hier
        print(prefix, msg)

def cerr(msg: str):   clog(0, "❌ERROR:", str(msg))
def cwarn(msg: str):  clog(0, "⚠️  WARN:", str(msg))
def cok(msg: str):    clog(1, "✅   OK:", str(msg))
def cinfo(msg: str):  clog(2, "ℹ️  INFO:", str(msg))
def cdebug(msg: str): clog(3, "🐞DEBUG:", str(msg))

def cerr_exc(msg: str):
    """Log exception with traceback via clog."""
    try:
        tb = traceback.format_exc()
        clog(0, "❌ ERROR:", f"{msg}\n{tb}")
    except Exception:
        clog(0, "❌ ERROR:", msg)

# Hybrid websockets import (neu/alt)
try:
    from websockets.server import serve as ws_serve  # websockets>=12
    USING_NEW_WEBSOCKETS = True
except Exception:
    from websockets.asyncio.server import serve as ws_serve  # websockets<=11
    USING_NEW_WEBSOCKETS = False

# ----------------------
# Utility-Helper
# ----------------------
def now_iso_future(seconds: int = TIME_SHIFT_SECONDS) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def timestamp_ms_future(seconds: int = TIME_SHIFT_SECONDS) -> str:
    return str(int((datetime.now(timezone.utc) + timedelta(seconds=seconds)).timestamp() * 1000))

def charging_profile_payload(limit: float, phases: int) -> dict:
    return {
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
                    "limit": float(limit),
                    "numberPhases": int(phases)
                }]
            }
        }
    }

# ----------------------
# Per-CP State
# ----------------------
@dataclass
class ChargePointState:
    cp_id: str
    websocket: Any = None
    status: str = "Unknown"
    meter_values: Dict[str, Any] = field(default_factory=dict)
    current_limit: Optional[float] = None
    phase_limit: Optional[int] = None
    transaction_id: Optional[int] = None
    last_phase_change: datetime = field(default_factory=lambda: datetime.min)
    transaction_start: Optional[datetime] = None
    target_kwh: float = 0.0
    charged_wh: float = 0.0
    last_energy_wh: Optional[float] = None
    phase_candidate: Optional[dict] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False, compare=False)
    last_meter_power_w: float = 0.0        # Istwert aus letztem MeterValues
    last_meter_ts: Optional[datetime] = None  # Zeitstempel des letzten MeterValues
    stop_candidate: Optional[datetime] = None  # Zeitpunkt ab dem Überschuss < Minimum anliegt (Stop-Hysterese)
    stop_pre_phase: Optional[int] = None        # Ursprüngliche Phase vor Stop-Delay (invertierte Phase aktiv)
    start_candidate: Optional[datetime] = None  # Zeitpunkt ab dem Überschuss >= 6A anliegt (Start-Hysterese)
    just_plugged: Optional[datetime] = None      # Zeitstempel des Ansteckens – Start-Hysterese überspringen (verfällt nach JUST_PLUGGED_GRACE_S)
    prev_pv_mode: Optional[float] = None         # PV-Modus des letzten Zyklus – Wechsel von 0/inaktiv → aktiv überspringt Start-Hysterese

    def __getattr__(self, name: str):
        """Fallback für fehlende Felder bei Live-Deployments mit alten State-Objekten."""
        return None

    def append_debug(self, message: dict):
        cdebug(f"[{self.log_cp_id}] {message}")

# ----------------------
# ChargePoint WebSocket Handler
# ----------------------
class ChargePointHandler:
    def __init__(self, manager: 'OCPPManager', state: ChargePointState):
        self.manager = manager
        self.state = state
        self.websocket = state.websocket

    async def _send_json(self, payload: Any) -> bool:
        """Schickt JSON über den WebSocket; liefert True bei Erfolg."""
        try:
            await self.websocket.send(json.dumps(payload))
            self.state.append_debug({"sent": payload, "timestamp": now_iso_future()})
            return True
        except Exception:
            cerr_exc(f"Fehler beim Senden an {self.state.cp_id}")
            return False

    async def send_callresult(self, unique_id: str, payload: Optional[dict] = None) -> bool:
        msg = [3, unique_id, payload or {}]
        return await self._send_json(msg)

    async def send_call(self, action: str, payload: Optional[dict] = None) -> Optional[str]:
        uid = timestamp_ms_future()
        msg = [2, uid, action, payload or {}]
        ok = await self._send_json(msg)
        return uid if ok else None

    async def start(self):
        """Haupt-Loop: empfängt Nachrichten vom Charge Point und delegiert."""
        # initial state defaults
        s = self.state
        s.status = "Available"
        s.meter_values = {"power": 0, "current": 0, "energy": 0}
        s.current_limit = None
        s.phase_limit = None
        s.transaction_id = None
        s.debug = []

        # NEU: Zähler beim ersten Verbinden auf 0 setzen
        s.charged_wh = 0.0
        s.last_energy_wh = None

        s.target_kwh = self.manager.DEFAULT_TARGET_KWH
        s.charged_wh = 0.0
        s.last_energy_wh = None
        s.last_phase_change = datetime.min
        s.transaction_start = None

        try:
            async for raw in self.websocket:
                await self._handle(raw)
        except Exception:
            cerr_exc(f"WebSocket-Loop für {s.cp_id} beendet mit Fehler")

    async def _handle(self, raw: str):
        try:
            data = json.loads(raw)
            self.state.append_debug({"received": data, "timestamp": now_iso_future()})
        except Exception:
            cerr(f"Ungültige JSON-Nachricht von {self.state.cp_id}")
            return

        if not isinstance(data, list) or len(data) < 2:
            cerr(f"Ungültiges OCPP-Format von {self.state.cp_id}: {data}")
            return

        typ = data[0]
        uid = data[1] if len(data) > 1 else None

        if typ == 2:  # CP -> Central (CALL)
            if len(data) < 4:
                cerr(f"Ungültiges CALL Format von {self.state.cp_id}: {data}")
                return
            action = data[2]
            payload = data[3]
            cdebug(f"[{self.state.log_cp_id}] Received CALL {action}")

            if action == "BootNotification":
                await self.send_callresult(uid, {"currentTime": now_iso_future(), "interval": 300, "status": "Accepted"})
                # refresh global/config values; apply verzögert damit StatusNotification zuerst eintreffen kann
                self.manager.refresh_wallbox_settings(cp_id=self.state.cp_id, use_cache=True)
                async def _delayed_apply(cp_id, delay=15):
                    await asyncio.sleep(delay)
                    await self.manager.apply_wallbox_settings(cp_id)
                asyncio.create_task(_delayed_apply(self.state.cp_id))
            elif action == "Heartbeat":
                await self.send_callresult(uid, {"currentTime": now_iso_future()})
            elif action == "StatusNotification":
                new_status = payload.get("status", self.state.status)
                old_status = self.state.status
                self.state.status = new_status
                await self.send_callresult(uid)
                # Fahrzeug hat Laden beendet/pausiert → sofort Limit auf 0 setzen
                # aber nur wenn wir selbst gerade kein Laden beabsichtigen (current_limit bereits 0)
                # sonst ist SuspendedEV nur ein kurzer Übergangszustand beim Profilwechsel
                if new_status == "SuspendedEV" and old_status != "SuspendedEV":
                    if (self.state.current_limit or 0.0) == 0.0 and self.state.phase_limit is not None:
                        cinfo(f"[{self.state.log_cp_id}] Fahrzeug hat Laden pausiert (SuspendedEV) – setze Limit auf 0.0A")
                        try:
                            await self.send_call("SetChargingProfile", charging_profile_payload(0.0, self.state.phase_limit))
                            self.state.current_limit = 0.0
                            self.state.append_debug({"note": "status-suspended-ev-immediate-zero", "ts": iso_now()})
                        except Exception:
                            cerr_exc(f"Fehler beim Setzen auf 0A bei SuspendedEV fuer {self.state.cp_id}")
                    else:
                        cdebug(f"[{self.state.log_cp_id}] SuspendedEV ignoriert – current_limit={self.state.current_limit}A (Übergangszustand)")
                # Fahrzeug frisch angesteckt → Start-Hysterese zurücksetzen (sofort starten wenn Überschuss da)
                if new_status in ["SuspendedEVSE", "Preparing"] and old_status in ["Available", "AvailableRequested", None]:
                    self.state.start_candidate = None
                    self.state.just_plugged = datetime.now()
                    cinfo(f"[{self.state.log_cp_id}] Fahrzeug angesteckt ({new_status}) – Start-Hysterese deaktiviert")
                    self.state.append_debug({"note": "start-candidate-reset-on-plug", "ts": iso_now()})
            elif action == "MeterValues":
                if payload.get("transactionId"):
                    self.state.transaction_id = payload["transactionId"]
                self.state.meter_values = payload
                await self.send_callresult(uid)
                asyncio.create_task(self.manager.update_charged_energy_from_meter(self.state.cp_id, payload))
            elif action == "StartTransaction":
                tx_id = int(datetime.now(timezone.utc).timestamp())
                self.state.transaction_id = tx_id
                self.state.status = "Charging"
                self.state.transaction_start = datetime.now()
                try:
                    await self.manager.start_transaction_setup(self.state.cp_id)
                except Exception:
                    cerr_exc(f"StartTransaction setup failed for {self.state.cp_id}")
                await self.send_callresult(uid, {"idTagInfo": {"status": "Accepted"}, "transactionId": tx_id})
            elif action == "StopTransaction":
                self.state.transaction_id = None
                # NICHT self.state.status = "Available" setzen!
                # Die Wallbox schickt danach StatusNotification (z.B. "Finishing" oder "SuspendedEVSE")
                self.state.transaction_start = None
                await self.send_callresult(uid, {"idTagInfo": {"status": "Accepted"}})
            else:
                cwarn(f"[{self.state.log_cp_id}] Unbekannte CALL Aktion: {action}")
                await self.send_callresult(uid)

        elif typ == 3:
            cdebug(f"[{self.state.log_cp_id}] CALLRESULT erhalten: {data}")
        elif typ == 4:
            cerr(f"[{self.state.log_cp_id}] CALLERROR erhalten: {data}")
        else:
            cerr(f"[{self.state.log_cp_id}] Unbekannter messageType: {data}")

# ----------------------
# OCPP Manager (zentral)
# ----------------------
class OCPPManager:
    def __init__(self, ws_port: int = WS_PORT, http_port: int = HTTP_PORT, auto_sync_interval: int = 20):
        self.ws_port = ws_port
        self.http_port = http_port
        self.auto_sync_interval = auto_sync_interval

        # Per-CP states
        self.states: Dict[str, ChargePointState] = {}

        # Absolute Hardware-Grenzen (Hardware-Limits)
        self.MIN_WB_AMP = 6.0      # Technisches Minimum (meist 6A)
        self.MAX_WB_AMP = 16.0  # Max (Hardware)

        # Globals / defaults (überschreibbar aus DB)
        self.wb_amp_max = 16.0
        self.wb_amp_min = 6.0
        self.wb_phases = "3"
        self.wb_pv_mode = 0.0
        self.wb_amp = self.wb_amp_max
        self.wb_is_pv_controlled = False

        self.AUTO_SYNC_INTERVAL = auto_sync_interval
        self.MIN_CHARGE_DURATION_S = 600
        self.PHASE_CHANGE_CONFIRM_S = 30
        self.residualPower = -300.0
        self.max_leistung_ha = -100
        self.DEFAULT_TARGET_KWH = 0.0

        # NextTrip (PV-Mode 4) Ladezeiten aus DB (ID=4)
        self.wb_ladezeit_von: str = "22:00"   # Res_Feld1
        self.wb_ladezeit_bis: str = "06:00"   # Res_Feld2

        # Inverter / energy cache (updated each autosync iteration)
        self.Netzbezug = 0.0
        self.Produktion = 0.0
        self.Batteriebezug = 0.0
        self.BattStatusProz = 0.0
        self.hausverbrauch = 0.0

        # Lock to protect manager-wide operations if needed
        self._mgr_lock = asyncio.Lock()

    # ----------------------------
    # DB / Inverter Zugriff (einmal pro iteration)
    # ----------------------------
    def refresh_wallbox_settings(self, cp_id: Optional[str] = None, use_cache: bool = True):
        """
        Liest DB-Konfiguration und Inverter-Werte.
        Wenn use_cache=True (z.B. bei apply_wallbox_settings in Autosync) werden
        bereits gelesene Globals nicht mehrfach überschrieben in derselben iteration.
        cp_id kann angegeben werden, um basis-Werte für einen CP zurückzugeben.
        """
        # DB lesen
        try:
            sqlall = FUNCTIONS.SQLall.sqlall()
            data = sqlall.getSQLsteuerdaten('wallbox', 'CONFIG/Prog_Steuerung.sqlite')
        except Exception:
            cwarn("DB-Lesen fehlgeschlagen; verwende existierende Defaults")
            data = None

        if data:
            try:
                row = data.get('1') or data.get(1)
                if row:
                    parts = (row.get('Options') or "").split(',')
                    try:
                        amp_min_val = max(6.0, float(parts[0]))
                    except Exception:
                        amp_min_val = getattr(self, 'wb_amp_min', 6.0)
                    try:
                        amp_max_val = min(16.0, max(amp_min_val, float(parts[1])))
                    except Exception:
                        amp_max_val = getattr(self, 'wb_amp_max', 16.0)
                    self.wb_phases = str(row.get('Res_Feld2', self.wb_phases))
                    try:
                        self.wb_pv_mode = float(row.get('Res_Feld1', self.wb_pv_mode))
                    except Exception:
                        pass
                    self.wb_amp_max, self.wb_amp_min = amp_max_val, amp_min_val
            except Exception:
                cwarn("Fehler beim Parsen DB ID=1")

            try:
                row2 = data.get('2') or data.get(2)
                if row2:
                    try:
                        self.MIN_CHARGE_DURATION_S = int(float(row2.get('Res_Feld2', self.MIN_CHARGE_DURATION_S)))
                    except Exception:
                        pass
                    try:
                        opt = row2.get('Options')
                        if opt is not None and str(opt).strip():
                            self.AUTO_SYNC_INTERVAL = int(float(opt))
                    except Exception:
                        pass
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
                        opt3 = row3.get('Options')
                        if opt3 is not None and str(opt3).strip():
                            self.PHASE_CHANGE_CONFIRM_S = int(float(opt3))
                    except Exception:
                        pass
                # ID=4: NextTrip Ladezeiten
                row4 = data.get('4') or data.get(4)
                if row4:
                    try:
                        raw_v = row4.get('Res_Feld1')
                        if raw_v is not None:
                            v = str(raw_v).strip()
                            if v:
                                self.wb_ladezeit_von = v
                    except Exception:
                        pass
                    try:
                        raw_b = row4.get('Res_Feld2')
                        if raw_b is not None:
                            b = str(raw_b).strip()
                            if b:
                                self.wb_ladezeit_bis = b
                    except Exception:
                        pass
                    try:
                        raw_ha = row4.get('Options')
                        if raw_ha is not None:
                            self.max_leistung_ha = float(raw_ha)*-1000
                    except Exception:
                        pass
                # update autosync interval
                self.auto_sync_interval = getattr(self, 'AUTO_SYNC_INTERVAL', self.auto_sync_interval)
            except Exception:
                cwarn("Fehler beim Parsen DB ID=2/3")
            if cp_id:
                cinfo(
                    f"[{'..' + cp_id[-4:]}] "
                    f"DB_Conf: "
                    f"{self.wb_pv_mode}, "
                    f"{self.wb_phases}, "
                    f"{amp_min_val}, "
                    f"{amp_max_val}, "
                    f"{self.DEFAULT_TARGET_KWH}, "
                    f"{self.wb_ladezeit_von}–{self.wb_ladezeit_bis}, "
                    f"{self.AUTO_SYNC_INTERVAL}, "
                    f"{self.MIN_CHARGE_DURATION_S}, "
                    f"{self.PHASE_CHANGE_CONFIRM_S}, "
                    f"{self.residualPower}, "
                    f"{self.max_leistung_ha} "
                )


        # Inverter lesen (einmal pro Aufruf)
        try:
            InverterApi = basics.get_inverter_class(class_type="Api")
            inverter_api = InverterApi()
            API = inverter_api.get_API()
            self.Netzbezug = float(API.get('aktuelleEinspeisung', 0) or 0)
            self.Produktion = float(API.get('aktuellePVProduktion', 0) or 0)
            self.Batteriebezug = float(API.get('aktuelleBatteriePower', 0) or 0)
            self.BattStatusProz = float(API.get('BattStatusProz', 0) or 0)
        except Exception:
            cwarn("Inverter API nicht verfügbar; Netz-/PV-Werte auf 0 gesetzt")
            self.Netzbezug = 0.0
            self.Produktion = 0.0
            self.Batteriebezug = 0.0
            self.BattStatusProz = 0.0

        # sync default target_kwh to all existing CPs if changed
        for cid, st in self.states.items():
            if st.target_kwh != self.DEFAULT_TARGET_KWH:
                st.target_kwh = self.DEFAULT_TARGET_KWH
                st.append_debug({"note": "target synced to DEFAULT", "value": self.DEFAULT_TARGET_KWH, "ts": iso_now()})

    # ----------------------------
    # NextTrip: Zeitfenster-Prüfung
    # ----------------------------
    def _is_in_nexttrip_window(self) -> bool:
        """
        Gibt True zurück, wenn die aktuelle Uhrzeit im Zeitfenster
        [wb_ladezeit_von .. wb_ladezeit_bis] liegt.
        Unterstützt Fenster über Mitternacht, z.B. 22:00 – 06:00.
        """
        try:
            now_t = datetime.now().time().replace(second=0, microsecond=0)
            def parse_t(s: str):
                h, m = map(int, s.strip().split(":"))
                from datetime import time as dtime
                return dtime(h, m)
            t_von = parse_t(self.wb_ladezeit_von)
            t_bis = parse_t(self.wb_ladezeit_bis)
            if t_von <= t_bis:
                # normales Fenster z.B. 08:00 – 14:00
                return t_von <= now_t <= t_bis
            else:
                # über Mitternacht z.B. 22:00 – 06:00
                return now_t >= t_von or now_t <= t_bis
        except Exception:
            cwarn(f"NextTrip: Ungültige Zeitangabe von='{self.wb_ladezeit_von}' bis='{self.wb_ladezeit_bis}'")
            return False


    def compute_limits_from_global(self, cp_id: Optional[str] = None) -> Tuple[float, str, float, bool, float]:
        """
        Berechnet Limits basierend auf PV-Überschuss und DB-Vorgaben.
        Änderungen:
        - Phasenwahl (1/3 Wechsel) NUR wenn wb_phases == "0".
        - Bei festen Phasen (1 oder 3) wird die Phase IMMER gehalten, auch im Mode 2.
        - Mode 2 (Min+PV) erzwingt mindestens wb_amp_min (bei 3 Phasen min. 6A).
        """
        # Puffer für 3-Phasen Start (6.0 * 1.02 = 6.12A)
        MIN_START_3P = self.MIN_WB_AMP * 1.02
        amp = 0
        is_pv_controlled = False
        # lokale Variable, um die DB-Einstellung (self.wb_phases) zu erhalten
        phases_to_use = self.wb_phases

        current_charge_power = 0
        # Aktuelle Ladepower mit aktuell gesetzten Werten berechnen
        if cp_id and cp_id in self.states:
            current_charge_power = self.get_current_power(cp_id)  # A × P × U(gemessen), Fallback 230V

        # Inverter-Werte verrechnen
        # Hausakku Ladebegrenzung, rechnen -0.1kW = keine Begrenzung
        if self.max_leistung_ha > 0:
            batterie_anteil = self.Batteriebezug
        else:
            batterie_anteil = max(self.max_leistung_ha, min(self.Batteriebezug, 0.0)) ##WIGGAL

        # batterie_antei darf nicht größer 0 sein
        if batterie_anteil > 0: batterie_anteil = 0

        self.hausverbrauch = max(0.0, self.Produktion + self.Batteriebezug + self.Netzbezug - current_charge_power)
        ueberschuss = int(max(0.0, (self.Produktion - self.hausverbrauch + batterie_anteil - self.residualPower)))

        cinfo(f"[{'..' + cp_id[-4:]}] Ladeberechnung: "
            f"PV={self.Produktion:.0f} W, "
            f"Akku={self.Batteriebezug:.0f} W, "
            f"Netz={self.Netzbezug:.0f} W, "
            f"Haus={self.hausverbrauch:.0f} W, "
            f"CP={current_charge_power:.0f} W, "
            f"Überschuss={ueberschuss:.0f} W")

        if float(self.wb_pv_mode) in (1.0, 2.0):
            # Standard: Im Modus 1.0 (Nur PV) darf die Ladung auf 0 abfallen
            MIN_AMP = 0.0
            # Im Modus 2.0 (Minimalladung) wird MIN_AMP auf das User- oder Hardware-Minimum gesetzt
            if float(self.wb_pv_mode) == 2.0:
                MIN_AMP = max(self.MIN_WB_AMP, self.wb_amp_min)

            is_pv_controlled = True
            amp_1 = int(ueberschuss / 230 / 1) if ueberschuss else 0
            amp_3_float = (ueberschuss / 230 / 3) if ueberschuss else 0 # Wegen Hysterese MIN_START_3P
            amp_3 = int(amp_3_float)

            # --- STRIKTE PHASEN-LOGIK ---
            if self.wb_phases == "0":
                # Nur hier erfolgt eine freie Phasenwahl nach PV-Produktion
                if amp_3_float >= MIN_START_3P:
                    phases_to_use = "3"
                    amp = max(self.MIN_WB_AMP, min(amp_3, self.wb_amp_max, self.MAX_WB_AMP))
                elif amp_1 >= self.wb_amp_min:
                    phases_to_use = "1"
                    amp =  min(self.MAX_WB_AMP, max(amp_1, self.wb_amp_min, self.MIN_WB_AMP))
                else:
                    phases_to_use = "1"
                    amp = MIN_AMP

            elif self.wb_phases == "3":
                # Feste Phase 3: Muss Hardware-Min (6.0) UND User-Min halten
                phases_to_use = "3"
                effective_min_3p = max(self.MIN_WB_AMP, self.wb_amp_min)
                if amp_3 >= effective_min_3p:
                    # Hier wird der Wert strikt zwischen Min und Max gehalten
                    amp = max(self.MIN_WB_AMP, min(amp_3, self.wb_amp_max, self.MAX_WB_AMP))
                else:
                    amp = MIN_AMP

            else:
                # Feste Phase 1: Muss User-Min UND Hardware-Max (16A) halten
                phases_to_use = "1"
                if amp_1 >= self.wb_amp_min:
                    amp = max(self.MIN_WB_AMP, min(amp_1, self.wb_amp_max, self.MAX_WB_AMP))
                else:
                    amp = MIN_AMP
        elif float(self.wb_pv_mode) == 3.0:
            # PV-Mode = 3  -> feste Werte, keine PV-Steuerung
            is_pv_controlled = False
            # Phase 0 = AUTO -> in Mode 3 immer 3-phasig
            if self.wb_phases == "0":
                phases_to_use = "3"
            else:
                phases_to_use = self.wb_phases or "3"
            # nimm den aktuell zulässigen Max-Wert (oder zulässiges Minimum falls kleiner)
            amp = max(self.wb_amp_min or self.MIN_WB_AMP, min(self.wb_amp_max, self.MAX_WB_AMP))

        elif float(self.wb_pv_mode) == 4.0:
            # PV-Mode = 4  -> NextTrip: Laden im Zeitfenster mit Max-Leistung bis Lademenge erreicht
            is_pv_controlled = False
            if self.wb_phases == "0":
                phases_to_use = "3"
            else:
                phases_to_use = self.wb_phases or "3"
            if self._is_in_nexttrip_window():
                amp = max(self.wb_amp_min or self.MIN_WB_AMP, min(self.wb_amp_max, self.MAX_WB_AMP))
                cinfo(
                    f"NextTrip: im Zeitfenster {self.wb_ladezeit_von}–{self.wb_ladezeit_bis} "
                    f"→ {amp}A / {phases_to_use}P"
                )
            else:
                amp = 0.0
                cinfo(
                    f"NextTrip: außerhalb Zeitfenster {self.wb_ladezeit_von}–{self.wb_ladezeit_bis} "
                    f"→ kein Laden"
                )

        self.wb_amp = amp
        self.wb_is_pv_controlled = is_pv_controlled

        return self.wb_amp, phases_to_use, self.wb_pv_mode, is_pv_controlled, self.wb_amp_min

    # ----------------------------
    # Aktuelle Leistung aus Store
    # ----------------------------
    def get_current_power_soll(self, cp_id: str) -> float:
        """Sollwert: gesetztes Limit × Phasen × Spannung."""
        st = self.states.get(cp_id)
        if not st:
            return 0.0
        try:
            return float(st.current_limit or 0.0) * int(st.phase_limit or 0) * self._get_average_voltage(cp_id)
        except Exception:
            return 0.0

    def get_current_power(self, cp_id: str) -> float:
        """Istwert wenn vorhanden, sonst Sollwert — für interne Berechnungen (hausverbrauch etc.)."""
        st = self.states.get(cp_id)
        if not st:
            return 0.0
        if st.last_meter_ts is not None:
            return st.last_meter_power_w
        return self.get_current_power_soll(cp_id)

    # ----------------------------
    # Apply-Wallbox-Settings (Hauptlogik)
    # ----------------------------
    async def apply_wallbox_settings(self, cp_id: str) -> bool:
        """
        Liest gewünschte Werte (aus globalen wb_* bzw. DB), berechnet gewünschtes Limit und Phase
        und sendet ggf. SetChargingProfile / RemoteStart/Stop.
        Synchronisiert state.current_limit / state.phase_limit.
        """
        st = self.states.get(cp_id)
        if not st:
            cwarn(f"apply_wallbox_settings: {cp_id} nicht gefunden")
            return False

        # per-CP lock, um parallele Aufrufe zu serialisieren
        async with st.lock:
            # ensure global settings refreshed once before compute (could be optimized to call only by autosync)
            self.refresh_wallbox_settings(cp_id=cp_id, use_cache=True)
            amp, phases, pv_mode, is_pv_controlled, amp_min = self.compute_limits_from_global(cp_id=cp_id)

            # ---- Nur Werte senden wenn Fahrzeug angesteckt ist ----
            plugged_states = ["Preparing", "Charging", "SuspendedEV", "SuspendedEVSE", "Finishing",
                              "ChargingRequested", "AvailableRequested"]
            if st.status not in plugged_states and not st.transaction_id:
                cinfo(f"[{st.log_cp_id}] Kein Fahrzeug angesteckt (Status={st.status}) – keine Werte gesendet")
                return False
            # ---------------------------------------------------

            # ---- SuspendedEV: Fahrzeug hat Laden pausiert → stop-guard überspringen, Limit auf 0 ----
            if st.status == "SuspendedEV":
                if st.current_limit != 0.0:
                    handler = ChargePointHandler(self, st)
                    await handler.send_call("SetChargingProfile", charging_profile_payload(0.0, st.phase_limit or 3))
                    st.current_limit = 0.0
                    st.append_debug({"note": "suspended-ev-limit-set-zero", "ts": iso_now()})
                    cinfo(f"[{st.log_cp_id}] Fahrzeug angesteckt (Status=SuspendedEV) – SetChargingProfile 0.0A nach OCPP")
                else:
                    cdebug(f"[{st.log_cp_id}] Fahrzeug angesteckt (Status=SuspendedEV) – bereits 0.0A, kein Senden")
                return False
            # -----------------------------------------------------------------------

            # desired values
            amp_desired = amp if pv_mode != 0.0 else 0.0
            requested_phase = 1 if phases == "1" else 3

            # PV-Modus wurde aktiviert (von 0/aus auf aktiven Modus gewechselt) → Start-Hysterese überspringen
            prev_pv = st.prev_pv_mode  # None beim ersten Zyklus
            pv_mode_activated = (prev_pv is not None) and (prev_pv == 0.0) and (pv_mode != 0.0)
            if pv_mode_activated:
                st.start_candidate = None
                st.just_plugged = datetime.now()
                cinfo(f"[{st.log_cp_id}] PV-Modus aktiviert ({prev_pv}→{pv_mode}) – Start-Hysterese übersprungen")
                st.append_debug({"note": "start-hysteresis-skip-pv-activated", "prev": prev_pv, "now": pv_mode, "ts": iso_now()})
            st.prev_pv_mode = pv_mode

            # initialize stores
            st.current_limit = st.current_limit  # no-op but keep explicit
            st.phase_limit = st.phase_limit

            # detect phase change
            phase_changed = (st.phase_limit != requested_phase)
            is_initial_change = (st.phase_limit is None)

            charged_wh = round(st.charged_wh,1) or 0.0
            # verbose info for current state including PV mode and charged Wh
            limit_str = f"{st.current_limit}A/{st.phase_limit}P" if st.current_limit is not None else "unbekannt"
            cinfo(f"[{st.log_cp_id}] PV-Mode={pv_mode}, PV-Steuerung={is_pv_controlled}, Wunsch: {amp_desired}A/{requested_phase}P, Aktuell: {limit_str}, Geladen: {charged_wh}Wh")

            # PHASE HYSTERESE: nur wenn Änderung, nicht initial, Laden > 0 gewünscht
            # UND automatische Phasenwahl aktiv (wb_phases == "0")
            # Bei fester Phaseneinstellung (1 oder 3) keine Hysterese nötig
            # WICHTIG: Während der Stop-Hysterese keine neue Phasenwechsel-Hysterese starten –
            # der Phasenwechsel soll erst nach Abschluss der Stop-Entscheidung erfolgen.
            is_charging_requested = amp_desired > 0.0
            stop_hysteresis_active = (st.stop_candidate is not None)
            candidate = st.phase_candidate
            if phase_changed and not is_initial_change and is_charging_requested and self.wb_phases == "0" and not stop_hysteresis_active:
                now = datetime.now()
                if not candidate or candidate.get('requested') != requested_phase:
                    st.phase_candidate = {'requested': requested_phase, 'since': now}
                    phase_changed = False
                    cinfo(f"[{st.log_cp_id}] Phasenwechsel-Hysterese gestartet – warte {self.PHASE_CHANGE_CONFIRM_S}s vor Wechsel auf {requested_phase}P.")
                    st.append_debug({"note": "phase-hysteresis-start", "requested": requested_phase, "ts": iso_now()})
                else:
                    elapsed = (now - candidate['since']).total_seconds()
                    if elapsed >= self.PHASE_CHANGE_CONFIRM_S:
                        phase_changed = True
                        st.phase_candidate = None
                        st.append_debug({"note": "phase-hysteresis-confirmed", "requested": requested_phase, "ts": iso_now()})
                    else:
                        remaining_s = int(self.PHASE_CHANGE_CONFIRM_S - elapsed)
                        # Log unterdrücken während Start-Hysterese aktiv ist – sonst erscheint
                        # "warte noch Xs" in jedem Zyklus inkl. dem in dem der Start feuert (irreführend).
                        if st.start_candidate is None:
                            cinfo(f"[{st.log_cp_id}] Phasenwechsel-Hysterese aktiv – noch {remaining_s}s / {self.PHASE_CHANGE_CONFIRM_S}s warten.")
                        phase_changed = False
            else:
                # cleanup if not relevant – aber stop_delay-Kandidaten (Phase-Invert beim Stopp) niemals löschen.
                # Bei aktiver Stop-Hysterese auch normale Phasenwechsel-Kandidaten verwerfen.
                if st.phase_candidate and not st.phase_candidate.get('stop_delay'):
                    if stop_hysteresis_active:
                        st.phase_candidate = None
                        st.append_debug({"note": "phase-candidate-dropped-stop-hysteresis", "ts": iso_now()})
                    else:
                        st.phase_candidate = None

            # pv_mode==2: zwinge Minimum
            amp_allowed = amp_desired
            if pv_mode == 2:
                amp_allowed = max(amp_allowed, amp_min or self.wb_amp_min)

            # Ziel erreicht -> stop
            target_kwh = st.target_kwh or self.DEFAULT_TARGET_KWH
            charged_wh = st.charged_wh or 0.0
            if target_kwh and (charged_wh >= target_kwh * 1000.0):
                amp_allowed = 0.0
                st.append_debug({"note": "target reached", "charged_wh": charged_wh, "target_kwh": target_kwh, "ts": iso_now()})

            status = st.status
            active_tx_id = st.transaction_id

            # Start/Stop decision
            if amp_allowed > 0.0 and amp_allowed >= 6.0:
                # Überschuss vorhanden → Stop-Hysterese zurücksetzen
                if active_tx_id and st.stop_candidate is not None:
                    if st.stop_pre_phase:
                        cinfo(f"[{st.log_cp_id}] Stop abgebrochen – Überschuss zurück, stelle Phase {st.stop_pre_phase} wieder her")
                        st.append_debug({"note": "stop-aborted-restore-phase", "phase": st.stop_pre_phase, "ts": iso_now()})
                        st.phase_candidate = {"requested": st.stop_pre_phase, "since": datetime.now()}
                        st.stop_pre_phase = None
                    st.stop_candidate = None
                    # stop_delay-Kandidat ebenfalls verwerfen – der geplante Phasenwechsel
                    # ist hinfällig wenn der Überschuss zurückkommt
                    if st.phase_candidate and st.phase_candidate.get('stop_delay'):
                        st.phase_candidate = None
                        st.append_debug({"note": "stop-delay-candidate-dropped-surplus", "ts": iso_now()})
                    st.append_debug({"note": "stop-candidate-reset-on-surplus", "amp": amp_allowed, "ts": iso_now()})
                    # Phasenwechsel-Hysterese nachholen: der phase_changed-Block oben konnte nicht
                    # greifen weil stop_candidate zu dem Zeitpunkt noch gesetzt war. Jetzt ist er
                    # gecleared → Hysterese jetzt starten falls Phasenwechsel gewünscht und
                    # wb_phases=="0" (automatisch) und noch kein passender Kandidat läuft.
                    if (phase_changed and not is_initial_change and is_charging_requested
                            and self.wb_phases == "0"
                            and (not st.phase_candidate or st.phase_candidate.get('requested') != requested_phase)):
                        st.phase_candidate = {'requested': requested_phase, 'since': datetime.now()}
                        phase_changed = False
                        cinfo(f"[{st.log_cp_id}] Phasenwechsel-Hysterese gestartet (nach Stop-Reset) – warte {self.PHASE_CHANGE_CONFIRM_S}s vor Wechsel auf {requested_phase}P.")
                        st.append_debug({"note": "phase-hysteresis-start-post-stop-reset", "requested": requested_phase, "ts": iso_now()})
                if status in ["Available", "AvailableRequested", "SuspendedEVSE", "Finishing"] and not active_tx_id:
                    # Start-Hysterese: kurze PV-Spitzen nicht sofort starten
                    # – außer Fahrzeug wurde gerade erst angesteckt ODER kein PV-Modus aktiv
                    start_confirm_s = self.PHASE_CHANGE_CONFIRM_S // 3
                    now = datetime.now()
                    JUST_PLUGGED_GRACE_S = 120
                    just_plugged_active = (
                        st.just_plugged is not None and
                        (datetime.now() - st.just_plugged).total_seconds() < JUST_PLUGGED_GRACE_S
                    )
                    if not just_plugged_active and st.just_plugged is not None:
                        st.just_plugged = None  # Grace-Period abgelaufen – normales Verhalten
                    if just_plugged_active or not is_pv_controlled:
                        st.just_plugged = None
                        st.start_candidate = None
                        # Sofort starten – kein Warten (just_plugged oder nicht PV-gesteuert)
                        handler = ChargePointHandler(self, st)
                        await handler.send_call("RemoteStartTransaction", {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG})
                        st.status = "ChargingRequested"
                        if not st.transaction_start:
                            st.transaction_start = datetime.now()
                        note = "start-requested-just-plugged" if just_plugged_active else "start-requested-no-pv-mode"
                        st.append_debug({"note": note, "amp": amp_allowed, "ts": iso_now()})
                    elif st.start_candidate is None:
                        st.start_candidate = now
                        cinfo(f"[{st.log_cp_id}] Start-Hysterese gestartet – warte {start_confirm_s}s vor Start ({amp_allowed}A)")
                        st.append_debug({"note": "start-hysteresis-start", "amp": amp_allowed, "confirm_s": start_confirm_s, "ts": iso_now()})
                    else:
                        elapsed = (now - st.start_candidate).total_seconds()
                        if elapsed < start_confirm_s:
                            remaining_s = int(start_confirm_s - elapsed)
                            cinfo(f"[{st.log_cp_id}] Start-Hysterese aktiv – noch {remaining_s}s / {start_confirm_s}s warten vor Start")
                            st.append_debug({"note": "start-hysteresis-wait", "remaining_s": remaining_s, "ts": iso_now()})
                        else:
                            st.start_candidate = None
                            # Vor RemoteStart: offene Transaktion beenden (Wallbox würde sonst ablehnen)
                            if active_tx_id:
                                cinfo(f"[{st.log_cp_id}] Offene Transaktion {active_tx_id} vor Neustart beenden")
                                handler = ChargePointHandler(self, st)
                                await handler.send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                                st.transaction_id = None
                                st.transaction_start = None
                                active_tx_id = None
                                await asyncio.sleep(2)
                            # request remote start
                            handler = ChargePointHandler(self, st)
                            await handler.send_call("RemoteStartTransaction", {"connectorId": DEFAULT_CONNECTOR_ID, "idTag": DEFAULT_IDTAG})
                            st.status = "ChargingRequested"
                            if not st.transaction_start:
                                st.transaction_start = datetime.now()
                            # Zielphase beim Start direkt übernehmen – andernfalls würde im ersten
                            # Folgezyklus final_phase = st.phase_limit (alte Phase) verwendet und
                            # ein SetChargingProfile mit falscher Phase gesendet.
                            # Phasenwechsel-Hysterese ebenfalls verwerfen: sie wurde vor dem Stop
                            # gestartet und ist für die neue Transaktion nicht mehr relevant.
                            st.phase_limit = requested_phase
                            if st.phase_candidate and not st.phase_candidate.get("stop_delay"):
                                st.phase_candidate = None
                                st.append_debug({"note": "phase-candidate-cleared-on-start", "ts": iso_now()})
                            st.append_debug({"note": "start-requested", "amp": amp_allowed, "ts": iso_now()})
                else:
                    # Transaktion läuft bereits → start_candidate zurücksetzen
                    st.start_candidate = None
            else:
                # Überschuss weggefallen → Start-Hysterese zurücksetzen
                if st.start_candidate is not None:
                    st.start_candidate = None
                    st.append_debug({"note": "start-candidate-reset", "ts": iso_now()})
                # STOP-GUARD prüfung
                # SuspendedEV = Fahrzeug hat aktiv Laden verweigert → stop-guard greift NICHT
                if status == "SuspendedEV":
                    can_stop = True
                    cdebug(f"[{st.log_cp_id}] Stop-Guard übersprungen – Fahrzeug in SuspendedEV")
                else:
                    can_stop = True
                    if is_pv_controlled and st.transaction_start and st.transaction_id:
                        duration = (datetime.now() - st.transaction_start).total_seconds()
                        if duration < self.MIN_CHARGE_DURATION_S:
                            can_stop = False
                            remaining_s = int(self.MIN_CHARGE_DURATION_S - duration)
                            cinfo(f"[{st.log_cp_id}] Stop-Guard aktiv – noch {remaining_s}s warten (Mindestladezeit={self.MIN_CHARGE_DURATION_S}s)")
                            st.append_debug({"note": "stop-guard", "remaining_s": remaining_s, "ts": iso_now()})
                    if target_kwh and (charged_wh >= target_kwh * 1000.0):
                        can_stop = True

                if not can_stop:
                    # Stop-Guard: Stopp verhindern aber Hysterese bereits starten
                    if st.stop_candidate is None:
                        st.stop_candidate = datetime.now()
                    st.stop_pre_phase = None
                    # Nur auf amp_min hochregeln wenn Fahrzeug gerade lädt – nicht wenn schon 0A
                    if (st.current_limit or 0.0) > 0.0:
                        amp_allowed = amp_min or self.wb_amp_min
                    st.append_debug({"note": "stop-guard-applied", "amp": amp_allowed, "ts": iso_now()})
                else:
                    if active_tx_id and amp_allowed == 0.0:
                        if is_pv_controlled:
                            # Stop-Hysterese: kurze PV-Unterschreitungen abfangen
                            now = datetime.now()
                            if st.stop_candidate is None:
                                st.stop_candidate = now
                                amp_allowed = amp_min or self.wb_amp_min
                                cinfo(f"[{st.log_cp_id}] Stop-Hysterese gestartet – warte {self.PHASE_CHANGE_CONFIRM_S}s vor Stopp")
                                st.append_debug({"note": "stop-hysteresis-start", "ts": iso_now()})
                            else:
                                elapsed = (now - st.stop_candidate).total_seconds()
                                if elapsed < self.PHASE_CHANGE_CONFIRM_S:
                                    remaining_s = int(self.PHASE_CHANGE_CONFIRM_S - elapsed)
                                    amp_allowed = amp_min or self.wb_amp_min
                                    cinfo(f"[{st.log_cp_id}] Stop-Hysterese aktiv – noch {remaining_s}s / {self.PHASE_CHANGE_CONFIRM_S}s warten vor Stopp")
                                    st.append_debug({"note": "stop-hysteresis-wait", "remaining_s": remaining_s, "ts": iso_now()})
                                elif not st.stop_pre_phase:
                                    # Hysterese bestätigt: Phase invertieren → triggert Phasenwechsel-Delay
                                    cur_phase = st.phase_limit or 1
                                    inv_phase = 3 if cur_phase == 1 else 1
                                    st.stop_pre_phase = cur_phase
                                    st.phase_candidate = {"requested": inv_phase, "since": datetime.now(), "stop_delay": True}
                                    cinfo(f"[{st.log_cp_id}] Stop-Hysterese bestätigt – Phase {cur_phase}→{inv_phase} (Stop-Delay), warte einen Zyklus")
                                    st.append_debug({"note": "stop-phase-invert", "from": cur_phase, "to": inv_phase, "ts": iso_now()})
                                    # amp_allowed bleibt 0.0 → Phasenwechsel-Delay greift unten
                                else:
                                    # Zweiter Zyklus: Delay abgelaufen, Überschuss weiterhin zu niedrig → stoppen
                                    st.stop_candidate = None
                                    st.stop_pre_phase = None
                                    st.phase_candidate = None
                                    cinfo(f"[{st.log_cp_id}] Stop-Delay abgelaufen, Überschuss weiterhin zu niedrig – stoppe Laden")
                                    handler = ChargePointHandler(self, st)
                                    await handler.send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                                    # kein SetChargingProfile nötig – bereits 0.0A gesetzt, RemoteStop beendet die Transaktion
                                    st.transaction_id = None
                                    st.status = "AvailableRequested"
                                    st.transaction_start = None
                                    st.append_debug({"note": "remote-stop-sent", "ts": iso_now()})
                        else:
                            # PV-Mode=0 oder andere nicht-PV-Modi → sofort stoppen
                            st.stop_candidate = None
                            st.stop_pre_phase = None
                            cinfo(f"[{st.log_cp_id}] Kein PV-Modus – stoppe sofort")
                            handler = ChargePointHandler(self, st)
                            await handler.send_call("RemoteStopTransaction", {"transactionId": active_tx_id})
                            await handler.send_call("SetChargingProfile", charging_profile_payload(0.0, st.phase_limit or 1))
                            st.current_limit = 0.0
                            cok(f"[{st.log_cp_id}] Ampere/Phase erfolgreich gesetzt: 0.0A / {st.phase_limit or 1}P")
                            st.transaction_id = None
                            st.status = "AvailableRequested"
                            st.transaction_start = None
                            st.append_debug({"note": "remote-stop-sent", "ts": iso_now()})
                    elif active_tx_id:
                        # amp_allowed > 0 → Laden gewünscht, Stop-Kandidat zurücksetzen
                        if st.stop_pre_phase:
                            # Überschuss zurück während invertierter Phase aktiv → Originalphase wiederherstellen
                            cinfo(f"[{st.log_cp_id}] Stop abgebrochen – Überschuss zurück, stelle Phase {st.stop_pre_phase} wieder her")
                            st.append_debug({"note": "stop-aborted-restore-phase", "phase": st.stop_pre_phase, "ts": iso_now()})
                            st.phase_candidate = {"requested": st.stop_pre_phase, "since": datetime.now()}
                            st.stop_pre_phase = None
                        st.stop_candidate = None
                    elif status not in ["Available", "AvailableRequested"]:
                        st.stop_candidate = None
                        # Nur auf Available setzen wenn Fahrzeug NICHT angesteckt ist
                        physically_plugged = status in ["SuspendedEVSE", "Preparing", "Finishing", "SuspendedEV"]
                        if not physically_plugged:
                            st.status = "Available"
                            st.transaction_start = None
                            st.append_debug({"note": "status-set-available", "ts": iso_now()})
                        else:
                            # Fahrzeug angesteckt aber kein Laden gewünscht → nur einmal 0A senden
                            phase_for_zero = st.phase_limit or 3
                            if st.current_limit != 0.0:
                                handler = ChargePointHandler(self, st)
                                await handler.send_call("SetChargingProfile", charging_profile_payload(0.0, phase_for_zero))
                                st.current_limit = 0.0
                                cinfo(f"[{st.log_cp_id}] Fahrzeug angesteckt (Status={status}) – SetChargingProfile 0.0A nach OCPP")
                            else:
                                cdebug(f"[{st.log_cp_id}] Fahrzeug angesteckt (Status={status}) – bereits 0.0A, kein Senden")

            # ---------------------------
            # AMPERE-ANPASSUNG WÄHREND DER PHASEN-HYSTERESE (wie Original)
            # ---------------------------
            # Start-Hysterese: amp_allowed auf 0A clampen bevor Änderungsprüfung
            # – nur wenn keine aktive Transaktion läuft
            if st.start_candidate is not None:
                if active_tx_id:
                    st.start_candidate = None
                else:
                    amp_allowed = 0.0
            amp_changed = abs((st.current_limit or 0.0) - amp_allowed) > 0.5
            candidate = st.phase_candidate
            # stop_hysteresis_active neu auswerten – stop_candidate kann im Start/Stop-Block
            # bereits zurückgesetzt worden sein (stop-candidate-reset-on-surplus)
            stop_hysteresis_active = (st.stop_candidate is not None)
            # Während Stop-Hysterese die aktuelle Phase beibehalten – kein Phasenwechsel durch
            # fehlenden Überschuss (compute_limits liefert dann phases="1" auch bei laufender 3P-Ladung).
            # Hier auswerten, da stop_candidate oben bereits korrekt aktualisiert wurde.
            if stop_hysteresis_active and st.phase_limit is not None and not (st.phase_candidate or {}).get('stop_delay'):
                if requested_phase != st.phase_limit:
                    requested_phase = st.phase_limit
                    phase_changed = False
            # Phasenwechsel-Delay während Start- oder Stop-Hysterese überspringen
            if candidate and not candidate.get('stop_delay') and st.start_candidate is None and not stop_hysteresis_active:
                requested_p = candidate.get('requested')
                current_p = st.phase_limit
                if current_p is not None:
                    if requested_p > current_p and amp_allowed != 16.0:
                        if st.current_limit != 16.0:
                            st.append_debug({"note": "phase-up-temporary-16", "ts": iso_now()})
                            amp_allowed = 16.0
                            amp_changed = True
                        else:
                            # bereits 16A gesetzt – kein erneutes Senden
                            amp_allowed = 16.0
                            amp_changed = False
                    elif requested_p < current_p and amp_allowed != 6.0:
                        # Temporäres 6A-Limit nur wenn Transaktion läuft UND bereits aktiv geladen wird
                        # (current_limit > 0). Bei current_limit == 0.0 ist die Transaktion frisch
                        # gestartet ohne bisher gesetztes Profil – in diesem Fall direkt mit dem
                        # tatsächlichen Überschuss-Strom auf der Zielphase starten.
                        already_charging = active_tx_id and (st.current_limit or 0.0) > 0.0
                        if already_charging:
                            if st.current_limit != 6.0:
                                st.append_debug({"note": "phase-down-temporary-6", "ts": iso_now()})
                                amp_allowed = 6.0
                                amp_changed = True
                            else:
                                # bereits 6A gesetzt – kein erneutes Senden
                                amp_allowed = 6.0
                                amp_changed = False
                        # else: kein Eingriff – amp_allowed bleibt beim berechneten Überschuss-Wert
                if amp_changed and (amp_allowed not in [6.0, 16.0]):
                    st.append_debug({"note": "amp-update-blocked-by-hysteresis", "ts": iso_now()})
                    amp_changed = False
            # ---------------------------

            # --- NEUER GUARD: initiales None oder 0 vermeiden, wenn Wunsch 0A ---
            # Wenn der aktuelle Status noch uninitialisiert ist (None) oder bereits 0A
            # und der erlaubte Ampere-Wert 0.0 ist, vermeiden wir das Senden eines
            # SetChargingProfile (z.B. um "Aktuell: NoneA/NoneP" oder unnötiges
            # Umschreiben von 0A zu 0A/anderer Phase zu verhindern), solange kein Laden gewünscht ist.
            current_limit_val = st.current_limit
            current_is_none_or_zero = (current_limit_val is None) or (float(current_limit_val) == 0.0)
            if amp_allowed == 0.0 and current_is_none_or_zero:
                if amp_changed:
                    amp_changed = False
                if phase_changed:
                    phase_changed = False
            # Stop-Hysterese: keinen Phasenwechsel während der Wartephase ausführen
            if stop_hysteresis_active and phase_changed:
                phase_changed = False
                st.append_debug({"note": "phase-change-blocked-stop-hysteresis", "ts": iso_now()})
            # ---------------------------------------------------------------

            final_phase = st.phase_limit if st.phase_limit is not None else requested_phase

            # Wenn Phasenwechsel erlaubt und nicht initial, ggf. 0A senden
            if phase_changed and not is_initial_change:
                current_power = self.get_current_power(cp_id)
                if current_power > 50:
                    handler = ChargePointHandler(self, st)
                    await handler.send_call("SetChargingProfile", charging_profile_payload(0.0, requested_phase))
                    st.current_limit = 0.0
                    st.phase_limit = requested_phase
                    st.last_phase_change = datetime.now()
                    # log the temporary 0A/phase application
                    cok(f"[{st.log_cp_id}] Ampere/Phase erfolgreich gesetzt: {0.0}A / {requested_phase}P")
                    # warte max 15s bis Leistung < 50W
                    for i in range(15):
                        await asyncio.sleep(1)
                        if self.get_current_power(cp_id) < 50:
                            st.append_debug({"note": "power-dropped-below-50", "after_s": i+1, "ts": iso_now()})
                            break
                    # <<< verhindert 2. SetChargingProfile >>>
                    amp_changed = False
                    phase_changed = False

                final_phase = requested_phase
            elif phase_changed and is_initial_change:
                final_phase = requested_phase

            # Wenn Änderung senden
            if amp_changed or phase_changed:
                handler = ChargePointHandler(self, st)
                await handler.send_call("SetChargingProfile", charging_profile_payload(amp_allowed, final_phase))
                st.current_limit = amp_allowed
                st.phase_limit = final_phase
                if phase_changed:
                    st.last_phase_change = datetime.now()
                    await asyncio.sleep(3)
                st.append_debug({"note": "limit-applied", "amp": amp_allowed, "phases": final_phase, "ts": iso_now()})
                # log success like in your example
                cok(f"[{st.log_cp_id}] Ampere/Phase erfolgreich gesetzt: {float(amp_allowed)}A / {int(final_phase)}P")
            else:
                st.append_debug({"note": "no-change", "amp": amp_allowed, "phases": final_phase, "ts": iso_now()})

            # done
            return True

    # ----------------------------
    # Energie / MeterValues
    # ----------------------------
    async def start_transaction_setup(self, cp_id: str):
        st = self.states.get(cp_id)
        if not st:
            return
        baseline = self._extract_energy_wh_from_meter_store(cp_id)
        st.last_energy_wh = baseline
        st.append_debug({"note": "start-transaction-setup", "baseline": baseline, "ts": iso_now()})

    # ----------------------------
    # Energie / Messwerte Extraktion
    # ----------------------------

    def _extract_energy_wh_from_meter_store(self, cp_id: str, meter_payload: Optional[dict] = None) -> Optional[float]:
        payload = meter_payload or (self.states.get(cp_id).meter_values if cp_id in self.states else None)
        if not payload:
            return None
        for mv in payload.get('meterValue', []) or []:
            for s in mv.get('sampledValue', []) or []:
                meas = s.get('measurand', '')
                if meas.startswith('Energy.'):
                    try:
                        val = float(s.get('value') or 0)
                        unit = (s.get('unit') or '').lower()
                        return val * 1000.0 if unit == 'kwh' else val
                    except Exception:
                        continue
        return None

    def _extract_power_w_from_meter_store(self, cp_id: str) -> float:
        """Extrahiert die aktuelle Wirkleistung (Gesamt) in Watt."""
        st = self.states.get(cp_id)
        if not st or not st.meter_values:
            return 0.0

        for mv in st.meter_values.get('meterValue', []):
            for s in mv.get('sampledValue', []):
                # Wir suchen die Gesamtleistung (ohne 'phase' Attribut)
                if s.get('measurand') == 'Power.Active.Import' and 'phase' not in s:
                    try:
                        return float(s.get('value', 0))
                    except (ValueError, TypeError):
                        continue
        return 0.0

    def _get_average_voltage(self, cp_id: str) -> float:  #entWIGGlung
        """Berechnet die durchschnittliche Spannung über alle Phasen."""
        st = self.states.get(cp_id)
        if not st or not st.meter_values:
            return 230.0

        voltages = []
        for mv in st.meter_values.get('meterValue', []):
            for s in mv.get('sampledValue', []):
                if s.get('measurand') == 'Voltage' and s.get('phase') in ['L1', 'L2', 'L3']:
                    try:
                        val = float(s.get('value'))
                        if val > 100:
                            voltages.append(val)
                    except (ValueError, TypeError):
                        continue

        return round(sum(voltages) / len(voltages), 1) if voltages else 230.0

    async def update_charged_energy_from_meter(self, cp_id: str, meter_payload: dict):
        st = self.states.get(cp_id)
        if not st:
            return
        try:
            energy_wh = self._extract_energy_wh_from_meter_store(cp_id, meter_payload)
            if energy_wh is None:
                return
            last = st.last_energy_wh
            if last is None:
                st.last_energy_wh = energy_wh
                return
            delta = energy_wh - last
            if delta < 0:
                st.last_energy_wh = energy_wh
                st.append_debug({"note": "energy-decrease-reset-baseline", "last": last, "now": energy_wh, "ts": iso_now()})
                return
            # nur während Ladung/Transaktion zählen
            if st.transaction_id or st.status == "Charging":
                st.charged_wh = st.charged_wh + delta
                st.last_energy_wh = energy_wh
                target_kwh = st.target_kwh or self.DEFAULT_TARGET_KWH
                if target_kwh and (st.charged_wh >= target_kwh * 1000.0):
                    st.append_debug({"note": "target-reached-meter", "charged_wh": st.charged_wh, "ts": iso_now()})
                    cok(f"[{st.log_cp_id}] Lademenge erreicht: {round(st.charged_wh/1000.0, 3)} kWh / {target_kwh} kWh – stoppe Laden")
                    if st.transaction_id:
                        handler = ChargePointHandler(self, st)
                        await handler.send_call("RemoteStopTransaction", {"transactionId": st.transaction_id})
                        st.transaction_id = None
                        st.status = "AvailableRequested"
                        st.transaction_start = None
                        cok(f"[{st.log_cp_id}] RemoteStopTransaction gesendet → Laden beendet")
                    else:
                        ocpp_phases_value = st.phase_limit or 3
                        handler = ChargePointHandler(self, st)
                        await handler.send_call("SetChargingProfile", charging_profile_payload(0.0, ocpp_phases_value))
                        st.current_limit = 0.0
                        st.phase_limit = ocpp_phases_value
                        st.status = "AvailableRequested"
                        st.transaction_start = None
                        cok(f"[{st.log_cp_id}] Ampere/Phase erfolgreich gesetzt: 0.0A / {ocpp_phases_value}P")
            else:
                st.last_energy_wh = energy_wh
        except Exception:
            cerr_exc(f"Fehler in update_charged_energy_from_meter für {cp_id}")

    # ----------------------------
    # WebSocket on_connect / cleanup
    # ----------------------------
    async def on_connect(self, websocket, path: str):
        cp_id_from_path = path.strip('/') if path else ''
        subprotocol = getattr(websocket, 'subprotocol', None)
        cp_id = cp_id_from_path or subprotocol or f"CP-{int(datetime.now().timestamp())}"
        cinfo(f"Neue Verbindung: cp_id={'..' + cp_id[-4:]} subprotocol={subprotocol} path={'/..' + path[-4:]}")

        # create state & handler
        st = ChargePointState(cp_id=cp_id, websocket=websocket)
        # gekürzte ID fürs Logging
        st.log_cp_id = '..' + cp_id[-4:]
        # ensure default target set
        st.target_kwh = self.DEFAULT_TARGET_KWH
        self.states[cp_id] = st

        handler = ChargePointHandler(self, st)
        try:
            await handler.start()
        except Exception:
            cerr_exc(f"Fehler in Verbindung {cp_id}")
        finally:
            # cleanup
            self.states.pop(cp_id, None)
            cinfo(f"Verbindung beendet: {cp_id}")

    # ----------------------------
    # HTTP Endpoints
    async def list_cp(self, request):
        return web.json_response({"connected": list(self.states.keys())})

    async def meter_values(self, request):
        cp_id = request.query.get("charge_point_id")
        st = self.states.get(cp_id)
        start_time = st.transaction_start if st else None
        duration = (datetime.now() - start_time).total_seconds() if start_time else 0
        last_phase_change = st.last_phase_change if st else None
        phase_duration = (datetime.now() - last_phase_change).total_seconds() if last_phase_change and last_phase_change != datetime.min else 0

        candidate_info = None
        if st and st.phase_candidate:
            since = st.phase_candidate.get('since')
            elapsed = (datetime.now() - since).total_seconds() if since else 0.0
            candidate_info = {"requested": st.phase_candidate['requested'], "since": since.isoformat() if since else None, "elapsed_s": round(elapsed, 1), "confirm_after_s": self.PHASE_CHANGE_CONFIRM_S}

        charged_wh = st.charged_wh if st else 0.0
        target_kwh = st.target_kwh if st else self.DEFAULT_TARGET_KWH
        remaining_kwh = None
        if target_kwh and target_kwh > 0:
            remaining_kwh = max(0.0, target_kwh - charged_wh / 1000.0)
        remaining_kwh_rounded = round(remaining_kwh, 4) if remaining_kwh is not None else None

        # In meter_values():
        power_ist  = self._extract_power_w_from_meter_store(cp_id) if cp_id else 0.0
        power_soll = self.get_current_power_soll(cp_id) if cp_id else 0.0

        if st and st.status not in ["Charging", "SuspendedEV", "SuspendedEVSE"]:
            power_ist  = 0.0
            power_soll = 0.0

        return web.json_response({
            "meter": st.meter_values if st else {},
            "status": st.status if st else "Unknown",
            "power_w_ist":  power_ist,   # gemessen via MeterValues
            "power_w_soll": power_soll,  # current_limit × phases × voltage
            "pv_mode": self.wb_pv_mode,
            "current_limit": st.current_limit if st else None,
            "phases": st.phase_limit if st else None,
            "transaction_id": st.transaction_id if st else None,
            "charging_duration_s": round(duration, 1),
            "phase_stable_s": round(phase_duration, 1),
            "phase_change_candidate": candidate_info,
            "Netzbezug_W": self.Netzbezug,
            "Produktion_W": self.Produktion,
            "Batteriebezug_W": self.Batteriebezug,
            "BattStatusProz": self.BattStatusProz,
            "Hausverbrauch": self.hausverbrauch,
            "target_energy_kwh": target_kwh,
            "charged_energy_kwh": round(charged_wh / 1000.0, 4),
            "remaining_kwh": remaining_kwh_rounded
        })

    async def reset_counter(self, request):
        """HTTP-Handler zum Zurücksetzen des Lade-Zählers mit Apache/CORS Support."""
        # 1. Parameter aus der URL lesen (für GET-Requests)
        cp_id = request.query.get("charge_point_id")
    
        if not cp_id:
            resp = web.json_response({"error": "Missing charge_point_id"}, status=400)
        else:
            # 2. Logik ausführen
            success = await self.reset_charged_energy_counter(cp_id)
    
            if success:
                resp = web.json_response({
                    "status": "success",
                    "charge_point_id": cp_id,
                    "message": "Zaehler erfolgreich auf 0 gesetzt"
                })
            else:
                resp = web.json_response({
                    "status": "error",
                    "message": f"Charge Point {cp_id} nicht gefunden"
                }, status=404)

        # 3. WICHTIG: CORS-Header für Apache hinzufügen
        # Dies verhindert, dass der Browser "Fehlgeschlagen" meldet
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'

        return resp

    async def reset_charged_energy_counter(self, cp_id: str) -> bool:
        """Setzt die geladene Energie im State-Objekt zurück."""
        st = self.states.get(cp_id) # Nutze die neue 'states' Struktur
        if not st:
            cwarn(f"Reset-Zähler: {cp_id} nicht verbunden")
            return False

        # Setze die Werte im Objekt zurück, die von update_charged_energy_from_meter genutzt werden
        st.charged_wh = 0.0
        st.last_energy_wh = None

        st.append_debug({"note": "charged-energy-reset", "ts": iso_now()})
        cok(f"[{st.log_cp_id}] ✅ Zähler erfolgreich zurückgesetzt.")
        return True

    # ---------- Autosync ----------
    async def autosync_task(self):
        # slight startup delay
        await asyncio.sleep(2)
        cinfo(f"AutoSync started, interval={self.auto_sync_interval} s")
        while True:
            try:
                if not self.states:
                    cdebug("AutoSync: keine verbundenen Charge Points")
                else:
                    # refresh DB/Inverter once per cycle
                    self.refresh_wallbox_settings()
                    # apply settings to each CP (serially to avoid heavy parallel DB calls)
                    for cp_id in list(self.states.keys()):
                        try:
                            await self.apply_wallbox_settings(cp_id)
                        except Exception:
                            cerr_exc(f"AutoSync: Fehler bei apply_wallbox_settings für {cp_id}")
            except Exception:
                cerr_exc("AutoSync-Loop Fehler")
            await asyncio.sleep(self.auto_sync_interval)

    # ----------------------------
    # Start Server (WebSocket + HTTP)
    async def start(self):
        ws = ws_serve(self.on_connect, "0.0.0.0", self.ws_port, subprotocols=OCPP_PROTOCOLS)

        app = web.Application()
        app.add_routes([
            web.get('/list', self.list_cp),
            web.get('/meter_values', self.meter_values),
            web.get('/reset_counter', self.reset_counter),
        ])

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.http_port)

        # start autosync task
        asyncio.create_task(self.autosync_task())

        await asyncio.gather(ws, site.start())
        cinfo(f"OCPP Manager läuft: WS={self.ws_port} HTTP={self.http_port}")
        await asyncio.Future()  # never return

async def test_logic():
    manager = OCPPManager()
    # Manuelles Setzen von Test-Werten (statt DB/Inverter)
    # Aufruf der Testlogig im Hauptverzeichnis mit:
    # python3 -m FUNCTIONS.ocpp
    manager.wb_pv_mode = 1.0  # Nur PV = 1, MIN+PV = 2, MAX = 3
    manager.wb_phases = "1"   # Automatische Phasenwahl = 0
    manager.wb_amp_min = 6.0
    manager.wb_amp_max = 16.0
    manager.Produktion = 5600.0 
    manager.Netzbezug = -manager.Produktion + 100.0 # Wir speisen ein => Hausverbrauch = 100 Rest ist Überschuss
    manager.residualPower = -100.0
    
    # Berechnung triggern
    amp, phases, mode, is_pv, amp_min = manager.compute_limits_from_global("TestCP")
    
    print(f"Ergebnis: {amp}A auf {phases} Phasen")

if __name__ == "__main__":
    asyncio.run(test_logic())
