# GEN24 Ladesteuerung – Home Assistant Addon

Home Assistant Wrapper für [GEN24_Ladesteuerung (EnergyWIGGAL)](https://github.com/wiggal/GEN24_Ladesteuerung) –
ermöglicht Betrieb und Konfiguration direkt aus Home Assistant heraus.

---

## Installation

### Repository in HA hinzufügen

1. **Einstellungen → Addons → Addon-Store → ⋮ (Drei-Punkte-Menü) → Repositories**
2. URL eintragen:
   ```
   https://github.com/wiggal/GEN24_Ladesteuerung
   ```
3. **Hinzufügen** → Store neu laden
4. „GEN24 Ladesteuerung" erscheint als Addon (evtl. suchen) → **Installieren**

---

## Konfiguration

Die Konfiguration erfolgt vollständig in  **GEN24 Ladesteuerung  → TAB config**.

---

## Persistente Datenhaltung

Alle Daten liegen im HA-Addon-Datenspeicher – **sie überleben eine Deinstallation**

```
config/gen24_ladesteuerung/     (auf dem HA-Host)
├── CONFIG
│   ├── Prog_Steuerung.sqlite
│   ├── charge_priv.ini
│   ├── default_priv.ini
│   ├── dynprice_priv.ini
│   ├── weather_priv.ini
│   └── winter_priv.ini
├── Crontab.log
├── PV_Daten.sqlite
├── config_priv.ini         ← WebUI-Einstellungen
└── weatherData.sqlite
```
---

## Ports

| Port | Verwendung |
|---|---|
| `2424` | WebUI (auch per HA Ingress erreichbar) |
| `8887` | OCPP WebSocket-Server (Wattpilot) |

---

## Aktualisierung des Addons

Das Addon baut den Code direkt aus dem Repository-Inhalt.
Nach einem `git pull` und einem Neuerstellen im HA-Addon-Store
wird der neue Code eingespielt – Konfiguration und Datenbanken in `/config/gen24_ladesteuerung/` bleiben
unberührt.

---

## Dateistruktur im Repository

```
GEN24_Ladesteuerung/
├── repository.yaml          ← macht das Repo zum HA-Addon-Store
├── ha_addon/                ← dieses Verzeichnis
│   ├── config.yaml
│   ├── Dockerfile
│   ├── build.yaml
│   ├── .dockerignore
│   ├── translations/
│   │   └── de.json
│   └── rootfs/
│       └── …/gen24-app/run  ← Startskript
└── …                        ← restlicher Anwendungscode
```
