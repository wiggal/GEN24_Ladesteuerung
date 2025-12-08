#!/bin/bash

# --- 1. Pfaddefinition und Initialisierung ---

GEN24_Pfad_tmp=$(dirname "$0")
GEN24_Pfad=$(realpath "$GEN24_Pfad_tmp")
GEN24_html_Pfad="${GEN24_Pfad}/html"
LOGFILE="Crontab.log" 

# WICHTIG: Verwende die vom Frontend erwartete PID-Datei für die Zustandsprüfung
OCPP_PID_FILE="/tmp/ocpp_server.pid"
OCPP_LOG_FILE="/tmp/ocpp.log" 

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

# --- 3. PHP-Webserver-Steuerung ---

WEB_SERVER_PROC="/usr/bin/php -S 0.0.0.0:2424"

# PHP_webserver auf PORT 2424 starten
if [[ "$Einfacher_PHP_Webserver" -eq 1 ]]; then
    if ! pgrep -f "$WEB_SERVER_PROC" > /dev/null; then
        cd "$GEN24_html_Pfad" || { echo "$(date) Fehler: Konnte nicht in das HTML-Verzeichnis wechseln." >> "${GEN24_Pfad}/${LOGFILE}"; exit 1; }
        nohup /usr/bin/php -S 0.0.0.0:2424 2>> /dev/null &
        echo -e "$(date) PHP-Webserver gestartet! \n" >> "${GEN24_Pfad}/${LOGFILE}"
    fi

# PHP_webserver auf PORT 2424 beenden
elif [[ "$Einfacher_PHP_Webserver" -eq 0 ]]; then
    if pgrep -f "$WEB_SERVER_PROC" > /dev/null; then
        pkill -f "$WEB_SERVER_PROC"
        echo -e "$(date) PHP-Webserver beendet! \n" >> "${GEN24_Pfad}/${LOGFILE}"
    fi
fi

# --- 4. Wallbox-OCPP-Server-Steuerung (NUR STARTEN) ---

OCPP_CMD="python3 -u ocpp_server.py"

server_is_running() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2> /dev/null; then
            return 0 # Läuft (durch PID-Datei bestätigt)
        fi
        rm -f "$pid_file" # Aufräumen, falls PID-Datei veraltet
    fi
    
    # Letzte Sicherheit: Prüfen, ob der Prozess trotzdem läuft (ohne PID-Datei)
    if pgrep -f "$OCPP_CMD" > /dev/null; then
         echo -e "$(date) WARNUNG: OCPP-Server läuft, aber PID-Datei fehlt. \n" >> "${GEN24_Pfad}/${LOGFILE}"
         return 0 # Läuft
    fi
    return 1 # Läuft nicht
}

# Wallbox-Server starten (NUR WENN Wallboxsteuerung=1)
if [[ "$Wallboxsteuerung" -eq 1 ]]; then
    if ! server_is_running "$OCPP_PID_FILE"; then
        cd "$GEN24_Pfad" || { echo "$(date) Fehler: Konnte nicht in das Hauptverzeichnis für OCPP wechseln." >> "${GEN24_Pfad}/${LOGFILE}"; exit 1; }

        # Starte den Python-Server und speichere die PID in der GEMEINSAMEN Datei
        PID=$(nohup /usr/bin/python3 -u ocpp_server.py > "$OCPP_LOG_FILE" 2>&1 & echo $!)
        
        if [[ -n "$PID" ]]; then
            echo "$PID" > "$OCPP_PID_FILE"
            echo -e "$(date) OCPP-Server gestartet (PID: $PID)! \n" >> "${GEN24_Pfad}/${LOGFILE}"
        fi
    fi
# Wenn Wallboxsteuerung=0 ist, wird KEIN Stopp-Befehl ausgeführt. 
# Der Server läuft weiter, auch wenn er durch das Frontend gestartet wurde, und sollte nur dort gestoppt werden.
fi

# --- 5. Argumentbehandlung und Python-Skript-Prüfung ---

cd "$GEN24_Pfad" || { echo "$(date) Fehler: Konnte nicht in das Hauptverzeichnis wechseln." >> "${GEN24_Pfad}/${LOGFILE}"; exit 1; }

while getopts "ho:" opt; do
# ... (getopts case-Anweisung bleibt unverändert) ...
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

PYTHON_SCRIPT="$1"

if (( $# == 0)); then
    echo "$(date) Fehler: Bitte Pythonscript als Parameter angeben!" >> "${GEN24_Pfad}/${LOGFILE}"
    exit 1
fi

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "$(date) Fehler: Pythonscript \"$PYTHON_SCRIPT\" existiert nicht!" >> "${GEN24_Pfad}/${LOGFILE}"
    exit 1
fi

if [[ ! -r "$PYTHON_SCRIPT" ]]; then
    echo "$(date) Fehler: Pythonscript \"$PYTHON_SCRIPT\" ist nicht lesbar (bitte chmod +r verwenden)!" >> "${GEN24_Pfad}/${LOGFILE}"
    exit 1
fi

# --- 6. Python-Skript ausführen ---

/usr/bin/python3 "$@" >> "${GEN24_Pfad}/${LOGFILE}" 2>&1
