# Über dynamische Strompreise günstige Akkunachladung bzw. -entladestop checken
# bei negativen Strompreisen bzw. ab Grenzwert Einspeisung stoppen (2. Stufe)
# Jeden Monat neues Lastprofil ermitteln und in CONFIG/Prog_Steuerung.sqlite speichern
from datetime import datetime, timedelta
#import pytz
#import json
#import requests
#from ping3 import ping
#import FUNCTIONS.PrognoseLadewert
#import FUNCTIONS.Steuerdaten
import FUNCTIONS.functions
import FUNCTIONS.DynamicPrice
import FUNCTIONS.SQLall


if __name__ == '__main__':
    basics = FUNCTIONS.functions.basics()
    config = basics.loadConfig(['default', 'dynprice'])
    sqlall = FUNCTIONS.SQLall.sqlall()
    dynamic = FUNCTIONS.DynamicPrice.dynamic()
    now = datetime.now()
    format = "%Y-%m-%d %H:%M:%S"

    PV_Database = basics.getVarConf('Logging','Logging_file', 'str')
    Lastgrenze = basics.getVarConf('dynprice','Lastgrenze', 'eval')

    # Lastprofile holen
    Lastprofil = dynamic.getLastprofil()

    # Lastprofil neu erzeugen, wenn es älter als zwei Wochen (1209600s) ist.
    if (int(datetime.now().timestamp()) - int(Lastprofil[0][3]) > 1209500):
        print("Erzeuge Lastprofil, da älter als zwei Wochen!")
        dynamic.makeLastprofil(PV_Database, Lastgrenze)

    # ***** Ab hier Berechnung des AKKU-Status
