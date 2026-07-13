#!/bin/sh

# 0. Datenbanken Prüfen und evtl. anlegen
INST_DIR="/home/GEN24"
export PYTHONPATH="$INST_DIR/FUNCTIONS"

cd "$INST_DIR" || exit 1
# weatherData.sqlite
if [ ! -s "weatherData.sqlite" ]; then
/home/GEN24/DOCKER/docker-entrypoint.sh    python3 -c "from WeatherData import WeatherData; WeatherData().create_database('$INST_DIR/weatherData.sqlite')"
fi
#PV_Daten.sqlite
if [ ! -s "PV_Daten.sqlite" ]; then
    python3 -c "from SQLall import sqlall; sqlall().create_database_PVDaten('$INST_DIR/PV_Daten.sqlite')"
fi
#CONFIG/Prog_Steuerung.sqlite
if [ ! -s "CONFIG/Prog_Steuerung.sqlite" ]; then
    python3 -c "from SQLall import sqlall; sqlall().create_database_ProgSteuerung('$INST_DIR/CONFIG/Prog_Steuerung.sqlite')"
fi
# Scheduler-DB anlegen, wenn sie nicht existiert, Abfrage in PHP-Skript
cd html || exit 1
/usr/bin/php ScheduleManager.php >/dev/null
cd $INST_DIR

# 1. Initiales Setup
if [ ! -s /home/GEN24/weatherData.sqlite ]; then
    /home/GEN24/start_PythonScript.sh /home/GEN24/FORECAST/Forecast_solar__WeatherData.py
fi
# 2. Python3 Script im Hintergrund starten
/home/GEN24/start_PythonScript.sh -o /dev/null EnergyController.py &

# 3. Cronjob laden
crontab /var/tmp/www-data

# 4. Cron starten (im Vordergrund, damit Container nicht beendet)
exec /usr/sbin/crond -f -d 0
