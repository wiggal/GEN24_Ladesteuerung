#!/usr/bin/env python3
"""
ocpp_server.py 
Startet den OCPPManager FUNCTIONS/ocpp.py

OCPP-Server (kompatibel mit websockets >=12 und <=11)
Features:
 - WebSocket OCPP listener (WS port 8887)
 - HTTP-API (Port 8080) mit /list, /meter_values, /remote_start, /remote_stop, /set_pv_mode
 - Interne DB-basierte Steuerung: apply_wallbox_settings(cp_id)
 - Automatische Sync nach BootNotification und periodisch (AUTO_SYNC_INTERVAL)
 - Sendet SetChargingProfile NUR wenn sich Werte ändern (Ampere ODER Phasen)
 - Führt Phasenumschaltung über ZWEI SetChargingProfile Calls durch (0A Limit -> Warten -> Ampere Limit + neue Phase)
 - Auffälliges ANSI-Farben-Logging (Console)
 - Stabilitäts-Guards für Phase Change (MIN_PHASE_DURATION_S) und Stop (MIN_CHARGE_DURATION_S)
 - **PV-Quellen-Guard**: Phasenumschaltung und Ladestopp (Limit 0A) erfolgen nur, 
   wenn die Steuerung aus dem PV-Überschuss-Modus (pv_mode 1 oder 2) stammt.
 - Logging beim Start /tmp/ocpp.log und Logrotation
 
 ==> Einstellungen in der Fronius-Wattpilot-APP
 Modus: Eco Mode AUS
 Einstellungen, Fahrzeug PHASENUMSCHALTUNG: Automatisch
 Internet, OCPP => aktiviert
 Füge SN (seriennummer) zur URL
 WS =< Host: IP:8887

"""

import asyncio
import os
import sys
from FUNCTIONS.ocpp import OCPPManager

PID_FILE = "/tmp/ocpp_server.pid"
LOG_FILE = "/tmp/ocpp.log"
LOG_MAX_BYTES = 3 * 1024 * 1024  # 3MB
LOG_BACKUP    = "/tmp/ocpp.log.1"

class RotatingStream:
    """
    Datei-Stream-Wrapper der bei print() automatisch rotiert.
    Sobald die Log-Datei > LOG_MAX_BYTES ist, wird sie nach ocpp.log.1
    kopiert und geleert (copytruncate – kein Neustart nötig).
    """
    def __init__(self, path: str):
        self.path = path
        self._f = open(path, "a", buffering=1, encoding="utf-8")

    def _rotate_if_needed(self):
        try:
            if os.path.getsize(self.path) > LOG_MAX_BYTES:
                self._f.flush()
                import shutil
                shutil.copy2(self.path, LOG_BACKUP)
                self._f.seek(0)
                self._f.truncate()
        except Exception:
            pass  # Rotation nie abstürzen lassen

    def write(self, data: str):
        self._rotate_if_needed()
        self._f.write(data)

    def flush(self):
        self._f.flush()

    def fileno(self):
        return self._f.fileno()

def setup_logging():
    """Leitet stdout/stderr auf den rotierenden Stream um."""
    stream = RotatingStream(LOG_FILE)
    sys.stdout = stream
    sys.stderr = stream

    # Externe Bibliotheken (websockets, urllib3) ebenfalls in die Log-Datei
    # umleiten und PING/PONG / HTTP-Connection-Spam auf WARNING-Level filtern
    import logging
    logging.basicConfig(stream=stream, level=logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def remove_pid():
    try:
        os.remove(PID_FILE)
    except OSError:
        pass

if __name__ == "__main__":
    setup_logging()
    write_pid()
    try:
        manager = OCPPManager()
        asyncio.run(manager.start())
    except KeyboardInterrupt:
        print("Server wird beendet (KeyboardInterrupt).")
    except Exception as e:
        print(f"Uncaught exception: {e}")
    finally:
        remove_pid()
