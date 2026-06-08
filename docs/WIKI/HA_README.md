# GEN24 Ladesteuerung – Home Assistant Addon

Home Assistant Wrapper für [GEN24_Ladesteuerung (EnergyWIGGAL)](https://github.com/wiggal/GEN24_Ladesteuerung) –
ermöglicht Betrieb und Konfiguration direkt aus Home Assistant heraus.

---

## Installation
Das Addon baut den Code direkt aus dem Repository-Inhalt.

### Repository in HA hinzufügen

1. **Einstellungen → Addons → Addon-Store → ⋮ (Drei-Punkte-Menü) → Repositories**
2. URL eintragen:
   ```
   https://github.com/wiggal/GEN24_Ladesteuerung
   ```
3. **Hinzufügen** → Store neu laden
4. „GEN24 Ladesteuerung" erscheint als Addon (evtl. suchen) → **Installieren**


## Update/Aktualisieren des Addons

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

Die Konfiguration erfolgt vollständig im ADDON  **GEN24 Ladesteuerung  → TAB config**.

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
