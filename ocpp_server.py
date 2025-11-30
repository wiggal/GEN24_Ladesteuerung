#!/usr/bin/env python3
"""
ocpp_server.py 
Startet den OCPPManager aus FUNCTIONS/ocpp.py

OCPP-Server (kompatibel mit websockets >=12 und <=11)
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
from FUNCTIONS.ocpp import OCPPManager

if __name__ == "__main__":
    try:
        manager = OCPPManager()
        asyncio.run(manager.start())
    except KeyboardInterrupt:
        print("Server wird beendet (KeyboardInterrupt).")
    except Exception as e:
        print(f"Uncaught exception: {e}")
