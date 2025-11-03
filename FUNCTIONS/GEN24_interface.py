import requests
import hashlib
import os
import time

# Neue Klasse für http-request nach Umstellungen im Zugriff seit Firmware 1.38.6-1
# Firmwareversionen kleiner 1.36.6-1 wurden nicht getestet
#
# Beispiel zum prüfen der Version
# Changelog => Zeus 3.4.3-21683 = 1.37.6-1 => API PS2.rev-sw = "3.4.3-21683" 


class InverterInterface:
    def __init__(self, host: str, user: str, password: str, Version = '3.4.3-21683', debug: bool = False):
        self.host = host
        self.user = user.lower() # user muss klein geschrieben sein
        self.password = password
        self.session = requests.Session()
        self.realm = None
        self.nonce = None
        self.qop = None
        self.opaque = None
        self.algorithm = "MD5"
        self.nc = 0
        self.debug = debug
        # Ab Version 1.36.5-1 => Zeus 3.3.2-20659 Präfix /api/
        if(self.is_less_than(Version, "3.3.2-20659")):
            self.http_request_path_praefix = "/"
            self.login_path = "/commands/Login"
            self.batterie_path = "/config/batteries"
            self.timeofuse_path = "/config/timeofuse"
        else:
            self.http_request_path_praefix = "/api/"
            self.login_path = "/api/commands/Login"
            self.batterie_path = "/api/config/batteries"
            self.timeofuse_path = "/api/config/timeofuse"
        self._debug("HTTP_Pfade: " + self.login_path+","+self.batterie_path+","+self.timeofuse_path)

    def is_less_than(self, version: str, threshold: str) -> bool:
        def parse_version(v: str):
            main = v.split("-")[0]   # nur Major.Minor.Patch beachten
            return [int(x) for x in main.split(".")]
        return parse_version(version) < parse_version(threshold)

    def _debug(self, msg: str):
        if self.debug:
            print("DEBUG ", msg)

    def _get_auth_params(self, url: str):
        """Fordert 401 an, um die Digest-Parameter zu bekommen"""
        r = self.session.get(url)
        if r.status_code != 401:
            raise Exception(f"Erwartet 401, aber {r.status_code}")
        header = r.headers.get("WWW-Authenticate") or r.headers.get("X-WWW-Authenticate")
        if not header:
            raise Exception("Kein WWW-Authenticate-Header gefunden")
        params = {}
        for item in header.replace("Digest ", "").split(","):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                params[k] = v.strip('"')
        self.realm = params.get("realm")
        self.nonce = params.get("nonce")
        self.qop = params.get("qop")
        self.opaque = params.get("opaque")
        self.algorithm = params.get("algorithm", "MD5")
        self._debug("Header_GET: " + header)
        self._debug(
            f"Auth-Params_neu: realm={self.realm}, nonce={self.nonce}, qop={self.qop}, algorithm={self.algorithm}, opaque={self.opaque}"
        )

    def _hash(self, data: str) -> str:
        if self.algorithm.upper() in ["SHA-256", "SHA256"]:
            return hashlib.sha256(data.encode()).hexdigest()
        else:
            return hashlib.md5(data.encode()).hexdigest()

    def _build_auth_header(self, method: str, uri: str):
        """Baut Digest-Auth-Header"""
        self.nc += 1
        nc_value = f"{self.nc:08x}"
        cnonce = hashlib.md5(os.urandom(8)).hexdigest()

        ha1 = self._hash(f"{self.user}:{self.realm}:{self.password}")
        ha2 = self._hash(f"{method}:{uri}")
        response = self._hash(f"{ha1}:{self.nonce}:{nc_value}:{cnonce}:{self.qop}:{ha2}")

        header = (
            f'Digest username="{self.user}", realm="{self.realm}", '
            f'nonce="{self.nonce}", uri="{uri}", '
            f'response="{response}", qop={self.qop}, '
            f'nc={nc_value}, cnonce="{cnonce}"'
        )
        if self.opaque:
            header += f', opaque="{self.opaque}"'

        self._debug(f"Authorization: {header}")
        return header

    def _request(self, method: str, uri: str, headers=None , data=None, params=None):
        url = f"http://{self.host}{uri}"
        if headers is None:
            headers = {}
        headers["Authorization"] = self._build_auth_header(method, uri)
    
        self._debug(f"Request {method} {url} mit headers: {headers}, params: {params}, data: {data}")

        r = self.session.request(method=method, url=url, headers=headers, params=params, data=data)

        if r.status_code == 401:
            self._get_auth_params(url)
            headers["Authorization"] = self._build_auth_header(method, uri)
            r = self.session.request(method=method, url=url, headers=headers, params=params, data=data)

        r.raise_for_status()
        return r

    def send_request(self, path, method='GET', payload=None, params=None, headers=None, add_praefix=False):
        """Sendet Request mit Digest-Auth """
        if headers is None:
            headers = {}
        last_error = None
        # Hier http_request_path_praefix wenn add_praefix=True
        if (add_praefix):
            path = self.http_request_path_praefix + path
        try:
            r = self._request(method, path, headers=headers, data=payload, params=params)
            if r.status_code == 200:
                return r
        except Exception as e:
            last_error = e
            self._debug(f"Request auf {path} fehlgeschlagen: {e}")
            print("\nLogin fehlgeschlagen: Kennword prüfen, oder nach Umstieg auf 1.38.6-1 Kennwort am GEN24 neu setzen!!\n")
            exit()

    def login(self) -> bool:
        """Login über Digest-Auth"""
        uri = self.login_path
        try:
            r = self._request("GET", uri, params={"user": self.user})
            self._debug(f"Login Response: {r.text[:200]}")
            return True
        except Exception as e:
            self._debug(f"Login fehlgeschlagen: {e}")
            return False

    def get_http_data(self):
        """Time-of-Use-Konfiguration """
        ToU = self.send_request(self.timeofuse_path)
        data_ToU_tmp = ToU.json()
        data_ToU = data_ToU_tmp.get("timeofuse", {})
        ToU_data = [{}, {}, {}]
        for i, entry in enumerate(data_ToU):
            ToU_data[i]['Active'] = entry['Active']
            ToU_data[i]['Power'] = str(entry['Power'])
            ToU_data[i]['ScheduleType'] = entry['ScheduleType']
        """Batterie-Konfig auslesen"""
        BK = self.send_request(self.batterie_path)
        data_BK = BK.json()
        BK_data = {}
        BK_data['HYB_EM_POWER'] = data_BK.get("HYB_EM_POWER")
        BK_data['HYB_EM_MODE'] = data_BK.get("HYB_EM_MODE")
        BK_data['HYB_BACKUP_RESERVED'] = data_BK.get("HYB_BACKUP_RESERVED")
        BK_data['BAT_M0_SOC_MIN'] = data_BK.get("BAT_M0_SOC_MIN")
        return ToU_data, BK_data

    def update_inverter_settings(
        self,
        mode,
        WR_schreiben=None,
        aktuellerLadewert=None,
        Neu_BatteryMaxDischarge=None,
        BatteryMaxDischarge=None,
        EntladeEintragloeschen=None,
        Options=None,
        Batterieentlandung_steuern=None,
        EntladeEintragDa=None,
        Ladetype=None,
        print_level=None,
        DEBUG_Ausgabe="",
        Schreib_Ausgabe="",
        Push_Schreib_Ausgabe="",
        **kwargs
    ):
        """
        Methode zur Aktualisierung von WR-/Batterie-Parametern.
    
        Parameter:
            mode: str – einer von ['timeofuse', 'remove_timeofuse', 'eigenverbrauchsoptimierung', 'BACKUP_RESERVE']
            WR_schreiben, aktuellerLadewert, ... – Parameter für Lade-/Entlade-Logik 
            kwargs – zusätzliche Parameter für andere Modi
    
        Rückgabe:
            Tuple (bereits_geschrieben, Schreib_Ausgabe, Push_Schreib_Ausgabe, DEBUG_Ausgabe)
        """
    
        response = None
        bereits_geschrieben = 0
    
        # ---------------------------
        # MODE 1: TIME-OF-USE / Ladegrenzen
        # ---------------------------
        if mode == "timeofuse":
            DEBUG_Ausgabe += "\nDEBUG <<<<<<<< LADEWERTE >>>>>>>>>>>>>"
            DEBUG_Ausgabe += "\nDEBUG Folgender MAX_Ladewert neu zum Schreiben: " + str(aktuellerLadewert)
            DEBUG_Ausgabe += "\nDEBUG Folgender MAX_ENT_Ladewert neu zum Schreiben: " + str(Neu_BatteryMaxDischarge)
    
            payload_text = ''
            trenner_komma = ''
    
            # 1. Laden
            if 'laden' in Options:
                trenner_komma = ','
                payload_text = (
                    '{"Active":true,"Power":' + str(aktuellerLadewert) +
                    ',"ScheduleType":"CHARGE_MAX","TimeTable":{"Start":"00:00","End":"23:59"},'
                    '"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                )
    
            # 2. Entladen
            if ('entladen' in Options) and (Batterieentlandung_steuern > 0) and (EntladeEintragloeschen == "nein"):
                if Neu_BatteryMaxDischarge != BatteryMaxDischarge or (payload_text != '' and EntladeEintragDa == "ja"):
                    payload_text += str(trenner_komma) + (
                        '{"Active":true,"Power":' + str(Neu_BatteryMaxDischarge) +
                        ',"ScheduleType":"' + str(Ladetype) + '","TimeTable":{"Start":"00:00","End":"23:59"},'
                        '"Weekdays":{"Mon":true,"Tue":true,"Wed":true,"Thu":true,"Fri":true,"Sat":true,"Sun":true}}'
                    )
    
            # 3. Request senden
            if (payload_text != '' or ('entladen' in Options and EntladeEintragloeschen == "ja")):
                response = self.send_request(
                    'config/timeofuse',
                    method='POST',
                    payload='{"timeofuse":[' + str(payload_text) + ']}',
                    add_praefix=True
                )
                bereits_geschrieben = 1
    
                if ('laden' in Options) and WR_schreiben == 1:
                    Schreib_Ausgabe += "CHARGE_MAX geschrieben: " + str(aktuellerLadewert) + "W\n"
                if ('entladen' in Options) and Neu_BatteryMaxDischarge != BatteryMaxDischarge and (EntladeEintragloeschen == "nein"):
                    Schreib_Ausgabe += Ladetype + " geschrieben: " + str(Neu_BatteryMaxDischarge) + "W\n"
                if ('entladen' in Options) and (EntladeEintragloeschen == "ja"):
                    Schreib_Ausgabe += "Entladeeintrag wurde gelöscht.\n"
    
                Push_Schreib_Ausgabe += Schreib_Ausgabe
                DEBUG_Ausgabe += "\nDEBUG Meldung bei Ladegrenze schreiben: " + str(response)
    
        # ---------------------------
        # MODE 2: Entferne Time-of-Use
        # ---------------------------
        elif mode == "remove_timeofuse":
            payload = '{"timeofuse":[]}'
            response = self.send_request('config/timeofuse', method='POST', payload=payload, add_praefix=True)
            bereits_geschrieben = 1
            Schreib_Ausgabe += "Time-of-Use Einträge gelöscht.\n"
    
        # ---------------------------
        # MODE 3: Eigenverbrauchsoptimierung
        # ---------------------------
        elif mode == "eigenverbrauchsoptimierung":
            Eigen_Opt_Std_neu = kwargs.get("Eigen_Opt_Std_neu")
            HYB_EM_MODE = kwargs.get("HYB_EM_MODE")
    
            if Eigen_Opt_Std_neu is None or HYB_EM_MODE is None:
                raise ValueError("Für 'eigenverbrauchsoptimierung' werden 'Eigen_Opt_Std_neu' und 'HYB_EM_MODE' benötigt.")
    
            payload = '{"HYB_EM_POWER":' + str(Eigen_Opt_Std_neu) + ',"HYB_EM_MODE":' + str(HYB_EM_MODE) + '}'
            response = self.send_request('config/batteries', method='POST', payload=payload, add_praefix=True)
            bereits_geschrieben = 1
            Schreib_Ausgabe += f"Eigenverbrauchsoptimierung gesetzt: Power={Eigen_Opt_Std_neu}, Mode={HYB_EM_MODE}\n"
    
        # ---------------------------
        # MODE 4: Backup Reserve
        # ---------------------------
        elif mode == "BACKUP_RESERVE":
            Neu_HYB_BACKUP_RESERVED = kwargs.get("Neu_HYB_BACKUP_RESERVED")
            if Neu_HYB_BACKUP_RESERVED is None:
                raise ValueError("Für 'BACKUP_RESERVE' wird 'Neu_HYB_BACKUP_RESERVED' benötigt.")
    
            payload = '{"HYB_BACKUP_CRITICALSOC":5,"HYB_BACKUP_RESERVED":' + str(Neu_HYB_BACKUP_RESERVED) + '}'
            response = self.send_request('config/batteries', method='POST', payload=payload, add_praefix=True)
            bereits_geschrieben = 1
            Schreib_Ausgabe += f"Backup-Reserve auf {Neu_HYB_BACKUP_RESERVED}% gesetzt.\n"
    
        # ---------------------------
        # Unbekannter Modus
        # ---------------------------
        else:
            raise ValueError(f"Unbekannter Modus: {mode}")
    
        return bereits_geschrieben, Schreib_Ausgabe, Push_Schreib_Ausgabe, DEBUG_Ausgabe
    


# -------------------------------------------------
# Beispiel
# -------------------------------------------------
if __name__ == "__main__":
    fronius = FroniusGEN24("192.168.XXX.XX", "customer", "XXXXXXXXXX", debug=True)

    if fronius.login():
        print("✅ Login erfolgreich")

        batteries = fronius.get_batteries()
        print("Batterie-Config:", batteries)

        timeofuse, path = fronius.get_time_of_use()
        print("Time-of-Use:", timeofuse, "von", path)
    else:
        print("❌ Login fehlgeschlagen")

