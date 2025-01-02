import hashlib
import json
import requests
    
class request:
    def __init__(self):
        pass

    global DEBUG_Ausgabe_fun_http
    
    def hash_utf8(self, x):
        if isinstance(x, str):
            x = x.encode("utf-8")
        return hashlib.md5(x).hexdigest()
    
    
    def get_auth_header(self, method, path, nonce, cnonce):
        realm = 'Webinterface area'
        ncvalue = "00000001"
        A1 = f"{user}:{realm}:{password}"
        A2 = f"{method}:{path}"
        HA1 = self.hash_utf8(A1)
        HA2 = self.hash_utf8(A2)
        noncebit = f"{nonce}:{ncvalue}:{cnonce}:auth:{HA2}"
        respdig = self.hash_utf8(f"{HA1}:{noncebit}")
        auth_header = f'Digest username="{user}", realm="{realm}", nonce="{nonce}", uri="{path}", algorithm="MD5", qop=auth, nc={ncvalue}, cnonce="{cnonce}", response="{respdig}"'
        return auth_header
    
    def get_nonce(self, response):
        #stupid API bug: nonce headers with different capitalization at different end points
        if 'X-WWW-Authenticate' in response.headers:
            auth_string = response.headers['X-WWW-Authenticate']
        elif 'X-Www-Authenticate' in response.headers:
            auth_string = response.headers['X-Www-Authenticate']
        else:
            auth_string=""
    
        auth_list = auth_string.replace(" ", "").replace('"', '').split(',')
        auth_dict = {}
        for item in auth_list:
            key, value = item.split("=")
            auth_dict[key] = value
        return auth_dict['nonce']
    
    def get_time_of_use(self, g_self_address, g_user, g_password):
        global user, password, self_address
        user = g_user.lower()
        password = g_password
        self_address = g_self_address
        response= self.send_request('/config/timeofuse',auth=True)
        if not response:
            return None
    
        result = json.loads(response.text)['timeofuse']
        return result
    
    def get_batteries(self, g_self_address, g_user, g_password):
        global user, password, self_address
        user = g_user.lower()
        password = g_password
        self_address = g_self_address
        response = self.send_request('/config/batteries',auth=True)
        if not response:
            return None
    
        HYB_EM_POWER = json.loads(response.text)['HYB_EM_POWER']
        # wenn HYB_EM_MODE = 0, Eigenverbrauchs-Optimierung = Automatisch
        HYB_EM_MODE = json.loads(response.text)['HYB_EM_MODE']
        HYB_BACKUP_RESERVED = json.loads(response.text)['HYB_BACKUP_RESERVED']
        return HYB_EM_POWER, HYB_EM_MODE, HYB_BACKUP_RESERVED
    
    def send_request(self, path, method='GET',payload="", params=None, headers={}, auth=False):
        global DEBUG_Ausgabe_fun_http
        DEBUG_Ausgabe_fun_http = ''
        cnonce = '7d5190133564493d953a7193d9d120a2'
        nonce = 0
        params=None
        auth=True
    
        for i in range(3):
            url = 'http://' + self_address+ path
            fullpath = path
            if params:
                fullpath += '?' + \
                    "&".join(
                        [f'{k+"="+str(params[k])}' for k in params.keys()])
            DEBUG_Ausgabe_fun_http += "DEBUG ## HTTP_PATH: " + str(fullpath) + "\n"
            if auth:
                headers['Authorization'] = self.get_auth_header(method, fullpath, nonce, cnonce)
                DEBUG_Ausgabe_fun_http += "DEBUG ## HEADERS: " + str(headers) + "\n"
            try:
                response = requests.request(method=method, url=url, params=params, headers=headers,data=payload)
        
                if response.status_code == 200:
                    return response
                elif response.status_code == 401: #unauthorized
                    nonce = self.get_nonce(response)
                    if i > 1:
                        print('[Fronius] Login fehlgeschlagen .. falsche Zugangsdaten?')
                        exit()
                    if (response.status_code==200):
                        print('[Fronius] Login successful')
                    else:
                        DEBUG_Ausgabe_fun_http += "DEBUG ## [Fronius] Login failed' " + str(response) + "\n"
                else:
                    raise RuntimeError(
                        f"Server {self_address} returned {response.status_code}")
            except requests.exceptions.ConnectionError as err:
                print("[Fronius] Connection to Inverter failed on {self.address}. Retrying in 120 seconds")
    
    
