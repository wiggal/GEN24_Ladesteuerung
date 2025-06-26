import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import requests
import datetime
import FUNCTIONS.functions
import FUNCTIONS.WeatherData

# Versuche, zoneinfo zu importieren, für Python 3.9+
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback für ältere Python-Versionen: Dummy-ZoneInfo
    class ZoneInfo:
        def __init__(self, key):
            self.key = key
            # Für den aktuellen Zeitpunkt (Juni) ist CEST (UTC+2) relevant.
            self._offset = datetime.timedelta(hours=2) 
        def utcoffset(self, dt):
            return self._offset
        def tzname(self, dt):
            return "CEST"
        def dst(self, dt):
            return datetime.timedelta(hours=1)


def interpolate_at_offset(data, offset_minuten=0):
    times_iso = data["hourly"]["time"]
    irradiance = data["hourly"]["global_tilted_irradiance"]

    # Zeiten in datetime-Objekte umwandeln
    times_dt = [datetime.datetime.fromisoformat(t) for t in times_iso]

    interpolated_values = []

    for i in range(len(times_dt)):
        offset_time = times_dt[i] + datetime.timedelta(minutes=offset_minuten)

        # Nach Intervall suchen, das die Offset-Zeit umschließt
        interpolated = 0
        for j in range(len(times_dt) - 1):
            t1, t2 = times_dt[j], times_dt[j + 1]
            v1, v2 = irradiance[j], irradiance[j + 1]

            if t1 <= offset_time <= t2 and v1 is not None and v2 is not None:
                ratio = (offset_time - t1).total_seconds() / (t2 - t1).total_seconds()
                interpolated = int(v1 + (v2 - v1) * ratio)
                break  # Interpolation gefunden

        interpolated_values.append(interpolated)

    # Neues Feld ergänzen, Zeit bleibt unverändert
    data["hourly"]["global_tilted_irradiance"] = interpolated_values

    return data

def compute_mean_field(data, prefix, target_field):
    # Falls das Zielfeld schon existiert, nichts tun
    if target_field in data['hourly']:
        return(data)

    # Alle Felder mit dem entsprechenden Prefix finden
    relevant_keys = [
        key for key in data['hourly'].keys()
        if key.startswith(prefix)
    ]

    if not relevant_keys:
        return

    # Die Zeitreihe(n) dieser Felder holen
    series_list = [data['hourly'][key] for key in relevant_keys]

    # Anzahl Zeitschritte von 'time' bestimmen
    time_len = len(data['hourly']['time'])

    # Mittelwert je Zeitschritt berechnen
    averaged = []
    for i in range(time_len):
        values = [
            series[i] for series in series_list
            if i < len(series) and series[i] is not None
        ]
        avg = int(sum(values) / len(values)) if values else None
        averaged.append(avg)

    # Ergebnis zurückschreiben
    data['hourly'][target_field] = averaged

    return(data)

def get_pv_forecast_icon_d2_cloud_layers(quelle, gewicht):
    """
    Ruft die 'global_tilted_irradiance' und die Gesamtbewölkung von Open-Meteo (ICON-D2, usw.) ab
    und berechnet die PV-Produktionsprognose mit verstärktem Bewölkungseinfluss.
    """
    print_level = basics.getVarConf('env','print_level','eval')
    # Werte für alle Strings
    anzahl_strings = basics.getVarConf('pv.strings','anzahl','eval')
    lat = basics.getVarConf('pv.strings','lat','eval')
    lon = basics.getVarConf('pv.strings','lon','eval')
    # Auf erlaubte Modelle prüfen
    valid_models = basics.getVarConf('openmeteo','valid_models','str')
    weather_models = basics.getVarConf('openmeteo','weather_models','str')
    # Faktor des Bewölkungseinflusses
    cloudEffect = basics.getVarConf('openmeteo','cloudEffect','eval')
    # Basis-Effizienzfaktor (systemische Verluste, nicht-optimale Bedingungen)
    base_efficiency_factor = basics.getVarConf('openmeteo','base_efficiency_factor','eval')
    offset_minuten = basics.getVarConf('openmeteo','offset_minuten','eval')

    start_date = now_local.strftime('%Y-%m-%d')
    end_date = (now_local + datetime.timedelta(days=2)).strftime('%Y-%m-%d')

    string_zaehler = 1
    SQL_watts_dict = {}
    while string_zaehler <= anzahl_strings:
        if (string_zaehler == 1): 
           suffix = ''
        else:
           suffix = string_zaehler
        dec = basics.getVarConf('pv.strings',f'dec{suffix}','eval')
        az = basics.getVarConf('pv.strings',f'az{suffix}','eval')
        kwp = basics.getVarConf('pv.strings',f'wp{suffix}','eval') / 1000

        base_url = "https://api.open-meteo.com/v1/forecast"
    
        params = {
            "latitude": lat,
            "longitude": lon,
            # 'global_tilted_irradiance' für die Hauptberechnung, 'cloudcover' für die zusätzliche Anpassung.
            "hourly": "global_tilted_irradiance,cloud_cover",
            "daily": "sunrise,sunset",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "start_date": start_date,
            "end_date": end_date,
            "models": weather_models,
            "tilt": dec,
            "azimuth": az,
            "output": "json",
            "timezone": "Europe/Berlin"
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Abrufen der Daten von Open-Meteo: {e}")
            return []

        # Mittelwerte berechnen
        data = compute_mean_field(data, 'global_tilted_irradiance_', 'global_tilted_irradiance')
        data = compute_mean_field(data, 'cloud_cover_', 'cloud_cover')

        # Offset anwenden, wenn nicht 0
        if (offset_minuten != 0):
            data = interpolate_at_offset(data, offset_minuten)

        pv_forecast_data = []
        if "hourly" in data and "time" in data["hourly"] and "global_tilted_irradiance" in data["hourly"]:
            hourly_times = data["hourly"]["time"]
            hourly_tilted_irradiance = data["hourly"]["global_tilted_irradiance"]
            hourly_cloudcover = data["hourly"].get("cloud_cover", [0] * len(hourly_times)) # Gesamtbewölkung in %

            for i in range(len(hourly_times)):
                timestamp_str = hourly_times[i]
                dt_object = datetime.datetime.fromisoformat(timestamp_str)
                formatted_timestamp = dt_object.strftime('%Y-%m-%d %H:00:00')

                estimated_pv_watts = 0
                if hourly_tilted_irradiance[i] is not None:
                    pv_watts = hourly_tilted_irradiance[i] * kwp * base_efficiency_factor

                    # --- Verstärkung des Bewölkungseinflusses ---
                    cloud_percentage = hourly_cloudcover[i] if hourly_cloudcover[i] is not None else 0
                    # Definition der Anpassungslogik des Bewölkungseinflusses 
                    additional_cloud_reduction_factor = round((1 - (cloud_percentage/100) * 0.8 * cloudEffect),2) 
                    pv_watts_org = pv_watts
                    pv_watts *= additional_cloud_reduction_factor
                    if print_level >= 2:
                        print("DEBUG  Bewölkung %:", formatted_timestamp, cloud_percentage, additional_cloud_reduction_factor, int(pv_watts_org), int(pv_watts))  #entWIGGlung
                    # --- Ende der Verstärkung ---
                
                    estimated_pv_watts = int(round(pv_watts))

                pv_forecast_data.append((formatted_timestamp, quelle, estimated_pv_watts, gewicht, ''))
        else:
            print("Unerwartetes Datenformat von Open-Meteo oder keine 'global_tilted_irradiance' verfügbar.")

        SQL_watts_dict[string_zaehler] = pv_forecast_data
        string_zaehler += 1

    # hier dann evtl pvdaten addieren mit Funktion
    SQL_watts = weatherdata.sum_pv_data(SQL_watts_dict)

    return SQL_watts

if __name__ == "__main__":
    basics = FUNCTIONS.functions.basics()
    weatherdata = FUNCTIONS.WeatherData.WeatherData()
    config = basics.loadConfig(['default', 'weather'])
    ForecastCalcMethod = basics.getVarConf('env','ForecastCalcMethod','str')
    Gewicht = basics.getVarConf('openmeteo','Gewicht','eval')
    lat = basics.getVarConf('pv.strings','lat','eval')
    lon = basics.getVarConf('pv.strings','lon','eval')
    dec = basics.getVarConf('pv.strings','dec','eval')
    az = basics.getVarConf('pv.strings','az','eval')
    kwp = basics.getVarConf('pv.strings','wp','eval') / 1000
    offset_minuten = basics.getVarConf('openmeteo','offset_minuten','eval')
    # Faktor des Bewölkungseinflusses
    cloudEffect = basics.getVarConf('openmeteo','cloudEffect','eval')
    # Basis-Effizienzfaktor (systemische Verluste, nicht-optimale Bedingungen)
    base_efficiency_factor = basics.getVarConf('openmeteo','base_efficiency_factor','eval')
    # Auf erlaubte Modelle prüfen
    valid_models = basics.getVarConf('openmeteo','valid_models','str')
    weather_models = basics.getVarConf('openmeteo','weather_models','str')
    Quelle = 'openmeteo'
    format = "%H:%M:%S"    

    # Leerzeichen prüfen
    if ' ' in weather_models:
        print("❌ Der String enthält Leerzeichen.")
    # In Liste umwandeln
    models = weather_models.split(',')
    # Ungültige Modelle filtern
    invalid_models = [m for m in models if m not in valid_models]
    if invalid_models:
        print("❌ Ungültige Modelle gefunden:", invalid_models)
        exit()

    try:
        local_timezone = ZoneInfo("Europe/Berlin")
        now_local = datetime.datetime.now(local_timezone)
    except Exception:
        current_offset = datetime.timedelta(hours=2) # CEST ist UTC+2
        local_timezone = datetime.timezone(current_offset, name='CEST')
        now_local = datetime.datetime.now(local_timezone)

    data = get_pv_forecast_icon_d2_cloud_layers(Quelle, Gewicht)

    if isinstance(data, list):
        weatherdata.storeWeatherData_SQL(data, Quelle, Gewicht)
        # Ergebnis mit ForecastCalcMethod berechnen und in DB speichern
        weatherdata.store_forecast_result()
        print(f'{Quelle} OK: Prognosedaten und Ergebnisse ({ForecastCalcMethod}) {now_local.strftime(format)} gespeichert.\n')
    else:
        print("Fehler bei Datenanforderung ", Quelle, ":")

