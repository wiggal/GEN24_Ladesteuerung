import requests
import hashlib
import os
import time

# Neue Klasse für http-request nach Umstellungen im Zugriff seit Firmware 1.38.6-1
# Firmwareversionen kleiner 1.36.6-1 wurden nicht getestet
#
# Beispiel zum prüfen der Version
# Changelog => Zeus 3.4.3-21683 = 1.37.6-1 => API PS2.rev-sw = "3.4.3-21683" 


class FroniusGEN24:
    def __init__(self, host: str, user: str, password: str, Version = '3.4.3-21683', debug: bool = False):
        self.host = host
        self.user = user
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
            self.login_path = "/commands/Login"
            self.batterie_path = "/config/batteries"
            self.timeofuse_path = "/config/timeofuse"
        else:
            self.login_path = "/api/commands/Login"
            self.batterie_path = "/api/config/batteries"
            self.timeofuse_path = "/api/config/timeofuse"

    def is_less_than(self, version: str, threshold: str) -> bool:
        def parse_version(v: str):
            main = v.split("-")[0]   # nur Major.Minor.Patch beachten
            return [int(x) for x in main.split(".")]
        return parse_version(version) < parse_version(threshold)

    def _debug(self, msg: str):
        if self.debug:
            print("[DEBUG]", msg)

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
        self._debug(
            f"Auth-Params: realm={self.realm}, nonce={self.nonce}, qop={self.qop}, algorithm={self.algorithm}, opaque={self.opaque}"
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

    def send_request(self, path, method='GET', payload=None, params=None, headers=None):
        """Sendet Request mit Digest-Auth """
        if headers is None:
            headers = {}
        last_error = None
        try:
            r = self._request(method, path, headers=headers, data=payload, params=params)
            if r.status_code == 200:
                return r
        except Exception as e:
            last_error = e
            self._debug(f"Request auf {path} fehlgeschlagen: {e}")

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

    def get_batteries(self):
        """Batterie-Konfig auslesen"""
        path = self.batterie_path
        r = self.send_request(path)
        data = r.json()
        HYB_EM_POWER = data.get("HYB_EM_POWER")
        HYB_EM_MODE = data.get("HYB_EM_MODE")
        HYB_BACKUP_RESERVED = data.get("HYB_BACKUP_RESERVED")
        BAT_M0_SOC_MIN = data.get("BAT_M0_SOC_MIN")
        return HYB_EM_POWER, HYB_EM_MODE, HYB_BACKUP_RESERVED, BAT_M0_SOC_MIN

    def get_time_of_use(self):
        """Time-of-Use-Konfiguration """
        path = self.timeofuse_path
        r = self.send_request(path)
        data = r.json()
        return data.get("timeofuse", {}), r.url


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

