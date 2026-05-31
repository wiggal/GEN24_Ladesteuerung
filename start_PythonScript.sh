#!/bin/bash

# --- 1. Pfaddefinition und Initialisierung ---

GEN24_Pfad_tmp=$(dirname "$0")
GEN24_Pfad=$(realpath "$GEN24_Pfad_tmp")
GEN24_html_Pfad="${GEN24_Pfad}/html"
LOGFILE="Crontab.log"

# WICHTIG: Verwende die vom Frontend erwartete PID-Datei für die Zustandsprüfung
OCPP_PID_FILE="/tmp/ocpp_server.pid"

# --- 2. Konfiguration aus default.ini/default_priv.ini parsen ---

Einfacher_PHP_Webserver="0"
Wallboxsteuerung="0"

# Funktion zum Parsen einer Konfigurationsdatei
parse_config() {
    local config_file="$1"
    local var_name="$2"
    local current_value="$3"

    if [[ -f "$config_file" ]]; then
        VALUE=$(grep -E "^${var_name}[[:space:]]*=" "$config_file" | head -n 1 | cut -d '=' -f 2 | tr -d '[:space:]')
        if [[ -n "$VALUE" ]]; then
            echo "$VALUE"
            return
        fi
    fi
    echo "$current_value"
}

Einfacher_PHP_Webserver=$(parse_config "${GEN24_Pfad}/CONFIG/default.ini" "Einfacher_PHP_Webserver" "$Einfacher_PHP_Webserver")
Einfacher_PHP_Webserver=$(parse_config "${GEN24_Pfad}/CONFIG/default_priv.ini" "Einfacher_PHP_Webserver" "$Einfacher_PHP_Webserver")

Wallboxsteuerung=$(parse_config "${GEN24_Pfad}/CONFIG/default.ini" "wallboxsteuerung" "$Wallboxsteuerung")
Wallboxsteuerung=$(parse_config "${GEN24_Pfad}/CONFIG/default_priv.ini" "wallboxsteuerung" "$Wallboxsteuerung")

# --- 3. Argumente parsen (VOR PHP/OCPP-Steuerung, damit -o für alle Logmeldungen gilt) ---

while getopts "ho:" opt; do
    case "$opt" in
        o)
            LOGFILE="$OPTARG"
            ;;
        h)
            echo "Usage: $0 [-o logging_file] <Python-Skript> [Skript-Argumente]"
            exit 0
            ;;
        *)
            echo "Invalid option: -$opt"
            echo "Usage: $0 [-o logging_file] <Python-Skript> [Skript-Argumente]"
            exit 1
            ;;
    esac
done
shift $((OPTIND - 1))

# LOG_TARGET einmalig berechnen, damit absolute -o-Pfade (z.B. /var/log/x.log) überall korrekt sind
if [[ "$LOGFILE" = /* ]]; then
    LOG_TARGET="$LOGFILE"
else
    LOG_TARGET="${GEN24_Pfad}/${LOGFILE}"
fi

# --- 4. PHP-Webserver-Steuerung ---

WEB_SERVER_PROC="/usr/bin/php -S 0.0.0.0:2424"

# PHP_webserver auf PORT 2424 starten
if [[ "$Einfacher_PHP_Webserver" -eq 1 ]]; then
    if ! pgrep -f "$WEB_SERVER_PROC" > /dev/null; then
        cd "$GEN24_html_Pfad" || { echo "$(date) Fehler: Konnte nicht in das HTML-Verzeichnis wechseln." >> "$LOG_TARGET"; exit 1; }
        nohup /usr/bin/php -S 0.0.0.0:2424 2>> /dev/null &
        echo -e "$(date) PHP-Webserver gestartet! \n" >> "$LOG_TARGET"
    fi

# PHP_webserver auf PORT 2424 beenden
elif [[ "$Einfacher_PHP_Webserver" -eq 0 ]]; then
    if pgrep -f "$WEB_SERVER_PROC" > /dev/null; then
        pkill -f "$WEB_SERVER_PROC"
        echo -e "$(date) PHP-Webserver beendet! \n" >> "$LOG_TARGET"
    fi
fi

# --- 5. Wallbox-OCPP-Server-Steuerung (NUR STARTEN) ---

# Prüft ob PID-Datei vorhanden UND der darin enthaltene Prozess ocpp_server.py läuft
server_is_running() {
    [[ -f "$OCPP_PID_FILE" ]] || return 1
    local pid
    pid=$(cat "$OCPP_PID_FILE")
    grep -q "ocpp_server.py" /proc/"$pid"/cmdline 2>/dev/null
}

# Wallbox-Server starten (NUR WENN Wallboxsteuerung=1)
if [[ "$Wallboxsteuerung" -eq 1 ]]; then
    if ! server_is_running; then
        cd "$GEN24_Pfad" || exit 1
        nohup /usr/bin/python3 -u ocpp_server.py &
    fi
# Wenn Wallboxsteuerung=0 ist, wird KEIN Stopp-Befehl ausgeführt.
# Der Server läuft weiter, auch wenn er durch das Frontend gestartet wurde, und sollte nur dort gestoppt werden.
fi

# --- 6. Python-Skript-Prüfung ---

cd "$GEN24_Pfad" || { echo "$(date) Fehler: Konnte nicht in das Hauptverzeichnis wechseln." >> "$LOG_TARGET"; exit 1; }

if (( $# == 0 )); then
    echo "$(date) Fehler: Bitte Pythonscript als Parameter angeben!" >> "$LOG_TARGET"
    exit 1
fi

PYTHON_SCRIPT="$1"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "$(date) Fehler: Pythonscript \"$PYTHON_SCRIPT\" existiert nicht!" >> "$LOG_TARGET"
    exit 1
fi

if [[ ! -r "$PYTHON_SCRIPT" ]]; then
    echo "$(date) Fehler: Pythonscript \"$PYTHON_SCRIPT\" ist nicht lesbar (bitte chmod +r verwenden)!" >> "$LOG_TARGET"
    exit 1
fi

# --- 7. Python-Skript ausführen ---
/usr/bin/python3 "$@" >> "$LOG_TARGET" 2>&1
