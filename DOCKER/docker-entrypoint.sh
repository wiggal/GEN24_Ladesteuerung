#!/bin/sh

# 1. Initiales Setup
if [ ! -s /home/GEN24/weatherData.sqlite ]; then
    /home/GEN24/start_PythonScript.sh /home/GEN24/FORECAST/Forecast_solar__WeatherData.py
fi
# 2. Python Script im Hintergrund starten
/home/GEN24/start_PythonScript.sh -o /dev/null http_SymoGen24Controller2.py &
# 3. Cronjob laden
crontab /var/tmp/www-data
# 4. Cron starten (im Vordergrund, damit Container nicht beendet)
exec /usr/sbin/crond -f -d 0
