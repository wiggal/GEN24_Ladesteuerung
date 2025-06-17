## Grundsätzliche Einstellungen in `default_priv.ini`:
**`[env]`  
Hier folgen einige grundlegende Einstellungen.**  
`filePathWeatherData = weatherData.json`  
Hier wird die Datei bestimmt, in der die PV-Vorhersage gespeichert ist.  
`Einfacher_PHP_Webserver = 0`  
Durch Einfacher_PHP_Webserver = 1 wird beim ersten Aufruf von start_PythonScript.sh der einfache PHP_Webserver auf Port 2424 gestartet.
Wenn Apache Webserver benutzt werden soll Einfacher_PHP_Webserver = 0 setzen.  
`print_level = 1`  
print_level steuert die Ausgabe beim Lauf der Ladesteuerung (http_SymoGen24Controller2.py)
print_level 0=keine Ausgabe 1=Ausgabe 2=DEBUG Ausgabe  

**`[gen24]`  
In diesem Block werden die Wechselrichter definiert.**  
`hostNameOrIp = 192.168.178.111`  
Hier wird die IP-Adressen des GEN24 Wechselrichter bestimmt.  
`IP_weitere_Gen24 = no` 
`IP_weitere_Symo = no`  
Hier können die IP-Adressen weiterer GEN24 bzw. Symos, durch Komma getrennt, definiert werden, um deren Produktion in die Steuerung bzw. ins Logging einzubeziehen.   
no = kein weiterer GEN24 bzw. Symos vorhanden.
`user = customer`  
Benutzername zum Login am GEN24, wird in den meisten Fällen `customer` sein.  
`password = 'XXXXXXXX'`  
Kennword für den Benutzer `customer`, das Kennwort muss in einfache Hochkommas gesetzt werden, wegen evtl. Sonderzeichen.  
Sollte das Kennwort ein '%' Zeichen enthalten bitte zwei '%%' eintragen.  

**`[messaging]`  
Hier Einstellungen zum Handypushup.**  
`Push_Message_EIN = 0`  
Hier können Pushmessages zu den Schreibvorgängen über den Dienst ntfy.sh auf die Handyapp ntfy gesendet werden.  
Push_Message_EIN (1=EIN/0=AUS)  
`Push_Message_Url = https://ntfy.sh/XXXXXXXXX`  
Hier muss die Adresse des über die App erstellten Themennamen eingetragen werden.  

