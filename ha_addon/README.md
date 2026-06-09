# EnergyWIGGAL – Home Assistant App

Home Assistant Wrapper für [EnergyWIGGAL](https://github.com/wiggal/GEN24_Ladesteuerung) –
ermöglicht Betrieb und Konfiguration direkt aus Home Assistant heraus. [WIKI](https://wiggal.github.io/GEN24_Ladesteuerung/)

---

## Installation
Die App baut den Code direkt aus dem Repository-Inhalt.

### Repository in HA hinzufügen

1. **Einstellungen → Apps → App-Store → ⋮ (Drei-Punkte-Menü) → Repositories**
2. URL eintragen:
   ```
   https://github.com/wiggal/GEN24_Ladesteuerung
   ```
3. **Hinzufügen** → Store neu laden
4. „EnergyWIGGAL" erscheint als App (evtl. suchen) → **Installieren**


## Update/Aktualisieren der App

- Ein Update erfolgt durch einen `git pull` auf das Repository.
- Bei Fehlern in lokalen Repository kann mit dem Schalter `Repo neu klonen` 
  unter Konfiguration, das Repository neu geholt (`git clone`) werden.
- **Achtung** der Schalter muss nach dem Update wieder zurückgesetzt werden.
- Konfiguration und Datenbanken in `/config/gen24_ladesteuerung/` bleiben unberührt.

## Deinstallation

- Auch nach einer Deinstallation bleiben die Daten im persistenten Bereich erhalten,
  wenn sie nicht mehr benötigt werden, sollten sie manuell mit folgendem Befehl gelöscht werden.
- `rm -rf /root/config/gen24_ladesteuerung`

---

## Konfiguration

Die Konfiguration erfolgt vollständig in der App  **EnergyWIGGAL  → TAB config**.

---

## Persistente Datenhaltung

Alle Daten liegen im HA-APP-Datenspeicher – **sie überleben eine Deinstallation**

```
config/gen24_ladesteuerung/     (auf dem HA-Host)
├── CONFIG
│   ├── Prog_Steuerung.sqlite
│   ├── charge_priv.ini
│   ├── default_priv.ini
│   ├── dynprice_priv.ini
│   ├── weather_priv.ini
│   └── winter_priv.ini
├── GEN24/.....             ← Prepositorydaten
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

## Dateistruktur im Repository

```
GEN24_Ladesteuerung/
├── repository.yaml          ← macht das Repo zum HA-App-Store
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
