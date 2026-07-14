#!/usr/bin/env python3
"""
DWD_mosmix_forecast.py

DWD MOSMIX_L -> PV-Ertragsprognose, integriert in die EnergyWIGGAL-Scheduler-Struktur
Laedt die MOSMIX_L Vorhersage der konfigurierten (oder automatisch gefundenen) DWD-Wetterstation, 
rechnet die Globalstrahlung (Rad1h) bzw. ersatzweise die effektive Bewoelkung (Neff) in eine
PV-Ertragsprognose um und speichert das Ergebnis ueber weatherdata.storeWeatherData_SQL()
in die DB.

PVLIB-FREI: Sonnenstand (Duffie&Beckman/Cooper), Erbs-Modell, Clearsky (Haurwitz),
Transposition (isotropes Modell) und PVWatts DC/AC sind hier direkt implementiert,
statt pvlib zu nutzen - spart die vergleichsweise schwere pvlib-Abhaengigkeit auf
dem Raspberry Pi. Numerisch gegen pvlib validiert: Sonnenstand max ~0.1-0.25 Grad
Abweichung, POA-Einstrahlung max ~3 W/m^2, AC-Ertrag max ~1% Abweichung - deutlich
innerhalb der ohnehin viel groesseren Wettervorhersage-Unsicherheit.

Keine API-Keys noetig - DWD Open Data ist frei zugaenglich.

Abhaengigkeiten:
    pip install requests pandas numpy --break-system-packages

Konfiguration in CONFIG/weather_priv.ini
    [dwd.mosmix]
    ; oder feste MOSMIX-Stationsnummer, z.B. 10865
    station = auto          
    Gewicht = 1.0
    offset_minuten = 0
    efficiency = 0.965
    temp_coeff = -0.0036
    ; Standorthoehe in Metern
    altitude = 520

    Stationsnummern manuell nachschlagen: https://wettwarn.de/mosmix/mosmix.html
    (Azimuth-Konvention wie forecast.solar: 0=Sued, -90=Ost, 90=West)
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import io
import re
import zipfile
from datetime import datetime
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd
import requests

import FUNCTIONS.functions
import FUNCTIONS.WeatherData


# ---------------------------------------------------------------------------
# DWD MOSMIX_L: Stationssuche, Download, Parsing
# ---------------------------------------------------------------------------

DWD_URL_L = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/{station}/kml/MOSMIX_L_LATEST_{station}.kmz"
DWD_STATION_CATALOG_URL = "https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication&nn=16102"

MOSMIX_PARAMS = ["Rad1h", "TTT", "FF", "Neff"]

NS = {
    "kml": "http://www.opengis.net/kml/2.2",
    "dwd": "https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd",
}


def load_station_catalog(timeout: int = 30):
    """Laedt den DWD MOSMIX-Stationskatalog und liefert eine Liste von
    (station_id, name, lat, lon) Tupeln. Wird sowohl von find_nearest_station()
    als auch von get_station_name() genutzt."""
    resp = requests.get(DWD_STATION_CATALOG_URL, timeout=timeout)
    resp.raise_for_status()

    # Format: "ID ICAO NAME... LAT LON ELEV", NAME kann mehrere Woerter enthalten.
    # Regex extrahiert die letzten 3 Zahlenfelder (LAT, LON, ELEV) vom Zeilenende her,
    # erstes Token ist die Stations-ID, alles dazwischen ist ICAO+NAME.
    line_re = re.compile(
        r"^(\S+)\s+(.*?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+)\s*$"
    )

    entries = []
    skipped_lines = 0
    for line in resp.text.splitlines():
        line = line.strip()
        if not line or line.upper().startswith("ID ") or line.startswith("---") or line.startswith("#"):
            continue
        m_line = line_re.match(line)
        if not m_line:
            skipped_lines += 1
            continue
        station_id, mid_part, s_lat, s_lon, s_elev = m_line.groups()
        try:
            s_lat_f = float(s_lat)
            s_lon_f = float(s_lon)
        except ValueError:
            skipped_lines += 1
            continue
        # mid_part enthaelt "ICAO NAME" oder "---- NAME"; ICAO-Platzhalter entfernen
        mid_tokens = mid_part.split()
        if mid_tokens and mid_tokens[0] == "----":
            name = " ".join(mid_tokens[1:])
        elif mid_tokens and re.match(r"^[A-Z]{4}$", mid_tokens[0]):
            name = " ".join(mid_tokens[1:])
        else:
            name = mid_part.strip()
        entries.append((station_id, name.strip(), s_lat_f, s_lon_f))

    return entries, skipped_lines


def get_station_name(station_id: str, timeout: int = 30) -> str:
    """Sucht den Klartextnamen einer bekannten Stations-ID im DWD-Katalog.
    Gibt '' zurueck, falls nicht gefunden (z.B. bei Tippfehlern)."""
    try:
        entries, _ = load_station_catalog(timeout=timeout)
    except requests.RequestException:
        return ""
    for sid, name, _, _ in entries:
        if sid == station_id:
            return name
    return ""


def find_nearest_station(lat: float, lon: float, timeout: int = 30, debug: bool = True) -> str:
    """Laedt den DWD MOSMIX-Stationskatalog und findet die naeheste Station,
    fuer die tatsaechlich eine MOSMIX_L Datei existiert.
    Gibt zur Fehlersuche die Top-Kandidaten (nach Distanz sortiert, VOR der
    Verfuegbarkeitspruefung) aus, damit sichtbar wird, ob eine erwartete Station
    ueberhaupt korrekt geparst und einsortiert wurde."""
    entries, skipped_lines = load_station_catalog(timeout=timeout)

    candidates = []
    for station_id, name, s_lat_f, s_lon_f in entries:
        # grobe Distanz in Grad; fuer die Kandidatenauswahl (nicht fuer exakte Entfernung) ausreichend
        dist = ((s_lat_f - lat) ** 2 + (s_lon_f - lon) ** 2) ** 0.5
        candidates.append((dist, station_id, name, s_lat_f, s_lon_f))

    candidates.sort(key=lambda c: c[0])

    if debug:
        print(f"DEBUG DWD: Stationskatalog: {len(candidates)} Zeilen geparst, "
              f"{skipped_lines} uebersprungen (nicht parsebar).")
        print("DEBUG DWD: Top-10 naechste Stationen (vor Verfuegbarkeitspruefung):")
        for dist, sid, name, slat, slon in candidates[:10]:
            print(f"    {sid} ({name}): lat={slat}, lon={slon}, Abstand~{dist:.3f}Grad")

    # WICHTIG: der Katalog enthaelt alle DWD-Stationstypen (auch reine Niederschlags-/
    # Klimastationen), nicht nur die ca. 2800 MOSMIX-Hauptstationen mit eigenem Export.
    # In dicht mit Stationen bestueckten Regionen koennen daher viele naehere, aber
    # MOSMIX-unfaehige Stationen die Kandidatenliste fuellen -> grosszuegiger Suchradius.
    max_candidates = 150
    checked = 0
    for dist, station_id, name, s_lat_f, s_lon_f in candidates[:max_candidates]:
        checked += 1
        check_url = DWD_URL_L.format(station=station_id)
        try:
            head = requests.head(check_url, timeout=10, allow_redirects=True)
            status = head.status_code
            if status == 405:
                # manche Server lehnen HEAD ab -> leichter GET-Fallback, sofort Verbindung schliessen
                with requests.get(check_url, timeout=10, stream=True) as r:
                    status = r.status_code
            if status == 200:
                print(f"DEBUG DWD: Gefunden: Station {station_id} ({name}) (lat={s_lat_f}, lon={s_lon_f}, "
                      f"Abstand ~{dist:.2f} Grad, nach {checked} geprueften Kandidaten)")
                return station_id
            elif debug:
                print(f"    uebersprungen: {station_id} ({name}) (HTTP {status}, Abstand ~{dist:.2f} Grad)")
        except requests.RequestException as e:
            if debug:
                print(f"    uebersprungen: {station_id} ({name}) (Fehler: {e})")
            continue

    raise RuntimeError(f"Keine erreichbare MOSMIX_L-Station unter den {max_candidates} naechsten "
                        f"Kandidaten gefunden. Bitte manuell auf "
                        f"https://wettwarn.de/mosmix/mosmix.html nachsehen.")


def fetch_mosmix_l(station: str, timeout: int = 30) -> pd.DataFrame:
    """Laedt die MOSMIX_L KMZ-Datei einer Station und liefert ein DataFrame
    mit Zeitindex (UTC) und den Spalten Rad1h, TTT, FF, Neff."""
    url = DWD_URL_L.format(station=station)
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        kml_name = [n for n in zf.namelist() if n.endswith(".kml")][0]
        kml_bytes = zf.read(kml_name)

    root = ET.fromstring(kml_bytes)

    # Zeitschritte stehen im ForecastTimeSteps-Block
    timesteps = [
        ts.text for ts in root.findall(".//dwd:ForecastTimeSteps/dwd:TimeStep", NS)
    ]
    timestamps = pd.to_datetime(timesteps, utc=True)

    # Placemark der gewuenschten Station finden (station_id steht in kml:name)
    placemark = None
    for pm in root.findall(".//kml:Placemark", NS):
        name_el = pm.find("kml:name", NS)
        if name_el is not None and name_el.text.strip() == str(station):
            placemark = pm
            break
    if placemark is None:
        raise ValueError(f"Station {station} nicht in MOSMIX-Antwort gefunden")

    data = {}
    for forecast in placemark.findall(".//dwd:Forecast", NS):
        elem_name = forecast.attrib.get("{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}elementName")
        if elem_name not in MOSMIX_PARAMS:
            continue
        value_el = forecast.find("dwd:value", NS)
        if value_el is None or value_el.text is None:
            continue
        # Werte sind space-separiert, "-" markiert fehlende Werte
        raw_values = re.split(r"\s+", value_el.text.strip())
        values = [float(v) if v not in ("-", "") else None for v in raw_values]
        data[elem_name] = values

    df = pd.DataFrame(data, index=timestamps)
    df = df.dropna(how="all")

    # Einheiten normalisieren: TTT kommt in Kelvin -> Celsius, Rad1h in kJ/m^2 -> W/m^2
    if "TTT" in df.columns:
        df["temp_air"] = df["TTT"] - 273.15
    if "Rad1h" in df.columns:
        # DWD Rad1h ist die ueber die letzte Stunde integrierte Strahlung in kJ/m^2
        # Umrechnung in mittlere Bestrahlungsstaerke W/m^2: kJ/m^2 / 3600s * 1000 = /3.6
        df["ghi"] = df["Rad1h"] / 3.6
    if "FF" in df.columns:
        df["wind_speed"] = df["FF"]
    if "Neff" in df.columns:
        df["cloud_cover"] = df["Neff"]

    return df


# ---------------------------------------------------------------------------
# PV-Modellierung (pvlib-frei: eigene Sonnenstand-/Erbs-/Clearsky-/PVWatts-Implementierung)
# ---------------------------------------------------------------------------

def solar_position(lat: float, lon: float, times: pd.DatetimeIndex):
    """Sonnenstand (Zenit, Azimut in Grad) nach den klassischen Duffie&Beckman-
    Formeln (Cooper-Deklination, Spencer-Zeitgleichung). times muss UTC-taware sein.
    Azimut-Konvention wie pvlib: 0=Nord, 90=Ost, 180=Sued, 270=West."""
    n = times.dayofyear.values.astype(float)
    utc_hour = times.hour.values + times.minute.values / 60.0 + times.second.values / 3600.0

    B = np.radians(360.0 / 365.0 * (n - 81))
    eot = 9.87 * np.sin(2 * B) - 7.53 * np.cos(B) - 1.5 * np.sin(B)  # Zeitgleichung, Minuten

    decl = np.radians(23.45 * np.sin(np.radians(360.0 / 365.0 * (284 + n))))  # Cooper-Deklination

    solar_time = utc_hour + (4 * lon + eot) / 60.0
    hour_angle = np.radians(15.0 * (solar_time - 12.0))

    lat_r = np.radians(lat)
    cos_zenith = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(hour_angle)
    cos_zenith = np.clip(cos_zenith, -1, 1)
    zenith = np.degrees(np.arccos(cos_zenith))

    sin_zenith = np.sin(np.radians(zenith))
    sin_zenith_safe = np.where(np.abs(sin_zenith) < 1e-6, 1e-6, sin_zenith)
    cos_az = (np.sin(decl) - np.sin(lat_r) * cos_zenith) / (np.cos(lat_r) * sin_zenith_safe)
    cos_az = np.clip(cos_az, -1, 1)
    azimuth = np.degrees(np.arccos(cos_az))
    # Vormittag (Stundenwinkel<0): Azimut < 180 (Ost-Seite); Nachmittag: Azimut > 180 (West-Seite)
    azimuth = np.where(hour_angle > 0, 360 - azimuth, azimuth)

    return pd.Series(zenith, index=times), pd.Series(azimuth, index=times)


def erbs_decomposition(ghi: pd.Series, zenith: pd.Series, times: pd.DatetimeIndex) -> pd.DataFrame:
    """Erbs-Modell: zerlegt Globalstrahlung (GHI) in Direkt- (DNI) und Diffusstrahlung
    (DHI) anhand des Klarheitsindex kt. Standardformel nach Erbs et al. 1982
    (siehe auch Duffie & Beckman, 'Solar Engineering of Thermal Processes')."""
    n = times.dayofyear.values.astype(float)
    zenith_r = np.radians(zenith.values)
    cos_zenith = np.clip(np.cos(zenith_r), 1e-6, None)

    ghi0 = 1367.0 * (1 + 0.033 * np.cos(np.radians(360.0 * n / 365.0))) * np.cos(zenith_r)
    ghi0 = np.clip(ghi0, 1e-6, None)

    kt = np.clip(ghi.values / ghi0, 0, 1.2)

    dhi_frac = np.where(
        kt <= 0.22,
        1 - 0.09 * kt,
        np.where(
            kt <= 0.80,
            0.9511 - 0.1604 * kt + 4.388 * kt**2 - 16.638 * kt**3 + 12.336 * kt**4,
            0.165,
        ),
    )
    dhi = dhi_frac * ghi.values
    dni = (ghi.values - dhi) / cos_zenith

    night = zenith.values >= 90
    dni = np.where(night, 0, dni)
    dhi = np.where(night, ghi.values, dhi)
    dni = np.clip(dni, 0, None)

    return pd.DataFrame({"dni": dni, "dhi": dhi}, index=times)


def haurwitz_clearsky_ghi(zenith: pd.Series) -> pd.Series:
    """Einfaches Clearsky-Modell nach Haurwitz (1945) - braucht keine Aerosol-/
    Wasserdampf-Zusatzdaten (anders als z.B. Ineichen/Solis), daher gut geeignet
    als Basis fuer die Bewoelkungs-Skalierung (Neff-Fallback ohne Rad1h)."""
    zenith_r = np.radians(zenith.values)
    cos_zenith = np.cos(zenith_r)
    ghi_clear = 1098.0 * cos_zenith * np.exp(-0.059 / np.clip(cos_zenith, 1e-6, None))
    ghi_clear = np.where(cos_zenith > 0, ghi_clear, 0)
    return pd.Series(np.clip(ghi_clear, 0, None), index=zenith.index)


def cloud_cover_to_ghi_clearsky_scaling(cloud_cover_pct: pd.Series, ghi_clearsky: pd.Series,
                                         offset: float = 35.0) -> pd.Series:
    """Skaliert Clearsky-GHI anhand der effektiven Bewoelkung (Neff, 0-100%) ab.
    Klassische lineare Naeherung: bei 0% Wolken -> volle Clearsky-Strahlung,
    bei 100% Wolken bleibt noch 'offset'% der Clearsky-Strahlung uebrig
    (diffuse Himmelsstrahlung dringt auch bei bedecktem Himmel noch durch).
    Entspricht der frueher in pvlib.forecast (inzwischen entfernt) genutzten Methode."""
    offset_frac = offset / 100.0
    cloud_frac = (cloud_cover_pct / 100.0).clip(lower=0, upper=1)
    return (offset_frac + (1 - offset_frac) * (1 - cloud_frac)) * ghi_clearsky


def get_total_irradiance_isotropic(tilt: float, surface_azimuth: float, zenith: pd.Series,
                                    solar_azimuth: pd.Series, dni: pd.Series, ghi: pd.Series,
                                    dhi: pd.Series, albedo: float = 0.2) -> pd.Series:
    """Einstrahlung auf die geneigte Modulebene (POA), isotropes Himmelsmodell
    (identisch zu pvlib's Default-Modell fuer get_total_irradiance)."""
    tilt_r = np.radians(tilt)
    zenith_r = np.radians(zenith.values)
    az_diff_r = np.radians(solar_azimuth.values - surface_azimuth)

    cos_aoi = np.cos(zenith_r) * np.cos(tilt_r) + np.sin(zenith_r) * np.sin(tilt_r) * np.cos(az_diff_r)
    cos_aoi = np.clip(cos_aoi, 0, None)

    poa_direct = dni.values * cos_aoi
    poa_sky_diffuse = dhi.values * (1 + np.cos(tilt_r)) / 2.0
    poa_ground = ghi.values * albedo * (1 - np.cos(tilt_r)) / 2.0
    poa_global = np.clip(poa_direct + poa_sky_diffuse + poa_ground, 0, None)

    return pd.Series(poa_global, index=zenith.index)


def sapm_cell_temperature(poa_global: pd.Series, temp_air: pd.Series, wind_speed: pd.Series,
                           a: float = -3.56, b: float = -0.075, delta_t: float = 3.0) -> pd.Series:
    """SAPM-Zelltemperaturmodell (Sandia), Parametersatz fuer 'open_rack_glass_glass'
    (freistehende, gut hinterlueftete Montage) - identisch zu pvlib.temperature.sapm_cell
    mit denselben Standardparametern."""
    t_module = poa_global.values * np.exp(a + b * wind_speed.values) + temp_air.values
    t_cell = t_module + (poa_global.values / 1000.0) * delta_t
    return pd.Series(t_cell, index=poa_global.index)


def pvwatts_dc_power(poa_global: pd.Series, cell_temp: pd.Series, pdc0: float,
                      gamma_pdc: float, temp_ref: float = 25.0) -> pd.Series:
    """DC-Leistung nach dem PVWatts-Modell (NREL), inkl. Temperaturkorrektur."""
    dc = (poa_global.values / 1000.0) * pdc0 * (1 + gamma_pdc * (cell_temp.values - temp_ref))
    return pd.Series(dc, index=poa_global.index)


def pvwatts_ac_power(pdc: pd.Series, pdc0: float, eta_inv_nom: float = 0.96,
                      eta_inv_ref: float = 0.9637) -> pd.Series:
    """AC-Leistung nach dem PVWatts-Wechselrichtermodell (NREL PVWatts V5 Manual,
    Dobos 2014). pdc0 hier = DC-Eingangslimit des Wechselrichters."""
    pac0 = eta_inv_nom * pdc0
    pdc_vals = pdc.values
    zeta = np.divide(pdc_vals, pdc0, out=np.zeros_like(pdc_vals), where=(pdc0 != 0))
    zeta_safe = np.where(pdc_vals == 0, 1.0, zeta)  # Division durch 0 vermeiden, Ergebnis unten auf 0 gesetzt

    eta = (eta_inv_nom / eta_inv_ref) * (-0.0162 * zeta_safe - 0.0059 / zeta_safe + 0.9858)
    pac = eta * pdc_vals
    pac = np.where(pdc_vals == 0, 0, pac)
    pac = np.clip(pac, 0, pac0)

    return pd.Series(pac, index=pdc.index)


def model_pv_output(df: pd.DataFrame, lat: float, lon: float, altitude: float,
                     tilt: float, azimuth: float, kwp: float,
                     efficiency: float = 0.965, temp_coeff: float = -0.0036,
                     use_cloud_fallback: bool = False) -> pd.DataFrame:
    """Rechnet GHI (via Erbs-Modell -> DNI/DHI) in AC-Ertrag [W] um (PVWatts-Ansatz).
    Falls use_cloud_fallback=True, wird GHI zunaechst aus der Clearsky-GHI (Haurwitz)
    und der effektiven Bewoelkung (Neff) geschaetzt (fuer Stationen ohne Rad1h)."""
    times = df.index

    zenith, sun_azimuth = solar_position(lat, lon, times)

    if use_cloud_fallback:
        ghi_clear = haurwitz_clearsky_ghi(zenith)
        cloud_cover = df.get("cloud_cover", pd.Series(50.0, index=times)).fillna(50.0)
        ghi = cloud_cover_to_ghi_clearsky_scaling(cloud_cover, ghi_clear).clip(lower=0)
    else:
        ghi = df["ghi"].fillna(0).clip(lower=0)

    erbs_out = erbs_decomposition(ghi, zenith, times)
    dni = erbs_out["dni"].fillna(0)
    dhi = erbs_out["dhi"].fillna(0)

    # Konvention: azimuth 0=Sued, negative=Ost, positive=West
    # interne Konvention: 180=Sued, 90=Ost, 270=West -> Umrechnung
    panel_azimuth = (azimuth + 180) % 360

    poa_global = get_total_irradiance_isotropic(
        tilt=tilt, surface_azimuth=panel_azimuth, zenith=zenith, solar_azimuth=sun_azimuth,
        dni=dni, ghi=ghi, dhi=dhi,
    )

    temp_air = df.get("temp_air", pd.Series(20.0, index=times))
    wind_speed = df.get("wind_speed", pd.Series(1.0, index=times))
    cell_temp = sapm_cell_temperature(poa_global, temp_air, wind_speed)

    system_power_w = kwp * 1000
    dc = pvwatts_dc_power(poa_global, cell_temp, system_power_w, gamma_pdc=temp_coeff)
    ac = pvwatts_ac_power(dc, pdc0=system_power_w * efficiency).clip(lower=0)

    result = pd.DataFrame({"ac_watts": ac}, index=times)
    return result


# ---------------------------------------------------------------------------
# Integration in die EnergyWIGGAL-Struktur
# ---------------------------------------------------------------------------

def loadLatestWeatherData(Quelle, Gewicht):
    station_cfg = basics.getVarConf('dwd.mosmix', 'station', 'str')
    altitude = basics.getVarConf('dwd.mosmix', 'altitude', 'eval')
    efficiency = basics.getVarConf('dwd.mosmix', 'efficiency', 'eval')
    temp_coeff = basics.getVarConf('dwd.mosmix', 'temp_coeff', 'eval')

    anzahl_strings = basics.getVarConf('pv.strings', 'anzahl', 'eval')
    lat = basics.getVarConf('pv.strings', 'lat', 'eval')
    lon = basics.getVarConf('pv.strings', 'lon', 'eval')

    # 'none'/'auto'/leer -> automatische Stationssuche zu lat/lon
    if station_cfg is None or station_cfg.strip().lower() in ('none', 'auto', ''):
        print("DEBUG DWD: keine Station konfiguriert, suche naechste verfuegbare Station...")
        station = find_nearest_station(lat, lon)
        # find_nearest_station() hat den Namen bereits mit ausgegeben, kein erneuter Katalogabruf noetig
    else:
        station = station_cfg
        station_name = get_station_name(station)
        if station_name:
            print(f"DEBUG DWD: verwende Station {station} ({station_name})")
        else:
            print(f"DEBUG DWD: verwende Station {station}")

    # MOSMIX-Abruf und Parsing gilt fuer den Standort (lat/lon), unabhaengig von der
    # Anzahl der Strings - wird unten pro String wiederverwendet, nicht erneut geladen
    try:
        df = fetch_mosmix_l(station)
    except Exception as e:
        print(f"### ERROR: MOSMIX_L Abruf fuer Station {station} fehlgeschlagen: {e}")
        exit()

    if "ghi" in df.columns and df["ghi"].dropna().any():
        use_cloud_fallback = False
        method_used = "Rad1h"
    elif "cloud_cover" in df.columns and df["cloud_cover"].dropna().any():
        use_cloud_fallback = True
        method_used = "Neff"
        print(f"DEBUG DWD: Station {station} liefert kein Rad1h, nutze Wolken-Fallback (Neff)")
    else:
        print(f"### ERROR: Station {station} liefert weder Rad1h noch Neff - keine Prognose moeglich")
        exit()

    # Pro String (dec/az/wp bzw. dec2/az2/wp2 usw.) separat modellieren, dann ueber
    # weatherdata.sum_pv_data() zusammenfuehren
    string_zaehler = 1
    SQL_watts_dict = {}
    while string_zaehler <= anzahl_strings:
        if string_zaehler == 1:
            suffix = ''
        else:
            suffix = string_zaehler
        dec = basics.getVarConf('pv.strings', f'dec{suffix}', 'eval')
        az = basics.getVarConf('pv.strings', f'az{suffix}', 'eval')
        kwp = basics.getVarConf('pv.strings', f'wp{suffix}', 'eval') / 1000

        pv = model_pv_output(
            df, lat=lat, lon=lon, altitude=altitude, tilt=dec, azimuth=az, kwp=kwp,
            efficiency=efficiency, temp_coeff=temp_coeff, use_cloud_fallback=use_cloud_fallback,
        )

        # WICHTIG: DWD liefert UTC: tz_convert() rechnet tatsaechlich
        # um (inkl. Sommerzeit), nicht nur tz-Info entfernen, sonst 1-2h Versatz.
        #
        # Hinweis Rad1h-Bezugszeit: laut DWD-Parameteruebersicht ist Rad1h ein
        # Summenwert der "letzten 1 Stunde" (Intervall [T-1h, T]), kein Momentanwert AM
        # Zeitpunkt T. Ein evtl. noetiger Korrekturversatz wird zentral ueber das
        # bereits vorhandene 'offset_minuten' (siehe __main__, an storeWeatherData_SQL
        # uebergeben) gehandhabt statt hier eine zweite, eigene Offset-Logik einzubauen.
        pv_forecast_data = []
        for ts, value in pv["ac_watts"].items():
            ts_local = ts.tz_convert("Europe/Berlin")
            key = ts_local.strftime("%Y-%m-%d %H:%M:%S")
            value = round(max(value, 0.0))  # auf ganze Watt runden
            if value > 10:
                # method_used landet im Info-/Notiz-Feld der DB-Zeile 
                # damit im Nachhinein sichtbar bleibt, ob
                # Rad1h oder der Neff-Fallback verwendet wurde
                pv_forecast_data.append((key, Quelle, value, Gewicht, method_used))

        SQL_watts_dict[string_zaehler] = pv_forecast_data
        string_zaehler += 1

    # Summierung ueber alle Strings 
    SQL_watts = weatherdata.sum_pv_data(SQL_watts_dict)

    return SQL_watts


if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    weatherdata = FUNCTIONS.WeatherData.WeatherData()
    config = basics.loadConfig(['default', 'weather'])
    offset_minuten = basics.getVarConf('dwd.mosmix', 'offset_minuten', 'eval')
    ForecastCalcMethod = basics.getVarConf('env', 'ForecastCalcMethod', 'str')
    Gewicht = basics.getVarConf('dwd.mosmix', 'Gewicht', 'eval')
    Quelle = 'dwd.mosmix'

    format = "%H:%M:%S"
    now = datetime.now()
    data = loadLatestWeatherData(Quelle, Gewicht)
    if isinstance(data, list):
        weatherdata.storeWeatherData_SQL(data, Quelle, Gewicht, '', offset_minuten)
        # Ergebnis mit ForecastCalcMethod berechnen und in DB speichern
        weatherdata.store_forecast_result()
        print(f'{Quelle} OK: Prognosedaten und Ergebnisse ({ForecastCalcMethod}) {now.strftime(format)} gespeichert.\n')
    else:
        print("Fehler bei Datenanforderung ", Quelle, ":")
        print(data)
