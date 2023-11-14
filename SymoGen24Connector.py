# Da Programm nur mit pyModbusTCP Version 0.1.10 lauffähig hier abprüfen
import pyModbusTCP
if (pyModbusTCP.__version__ != '0.1.10'):
    print(" pyModbusTCP Version =", pyModbusTCP.__version__ ,"!")
    print(" Bitte pyModbusTCP Version 0.1.10 installieren!")
    exit()

from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
from datetime import datetime
import numpy as np
from functions import loadConfig, getVarConf

class SymoGen24:
    def __init__(self, ipaddr, port, auto=True):
        if (auto):
            self.modbus = ModbusClient(host=ipaddr, port=port, auto_open=True, auto_close=True)
            self.modbus.unit_id(1)
            # Testen ob Modbus aktiv
            if not self.modbus.open():
                print(datetime.now())
                print("Modbus nicht Aktiv!!!")
                print()
                exit()

            # self.modbus.debug(True)
        else:
            self.modbus = ModbusClient()
            self.modbus.host(ipaddr)
            self.modbus.port(port)
            self.modbus.unit_id(1)
            if not self.modbus.open():
                print(datetime.now())
                print("Modbus nicht Aktiv!!!")
                print()
                exit()
        
        sunspecid = self.read_uint16(40070)

        if sunspecid != 103:
            print("Warning: Invalid SunspecID, wrong device ?")
        
        # Format:
        # "name : [register address, data type, unit 1]
        self.registers = {
            "CommonBlockRegister": {
                "SunspecSID" : [40001, "uint32", 1],
                "SunspecID" : [40070, "uint16", 1],
                "AC_Phase-A_Current" : [40072, "float", 1],
                "AC_Phase-B_Current" : [40076, "float", 1],
                "AC_Phase-C_Current" : [40078, "float", 1],
                "AC_Voltage_Phase-AB" : [40080, "float", 1],
                "AC_Voltage_Phase-BC" : [40082, "float", 1],
                "AC_Voltage_Phase-CA" : [40084, "float", 1],
                "AC_Voltage_Phase-A-N" : [40086, "float", 1],
                "AC_Voltage_Phase-B-N" : [40088, "float", 1],
                "AC_Voltage_Phase-C-N" : [40090, "float", 1],
                "AC_Output_Power" : [40092, "float", 1],
                "AC_Frequency" : [40094, "float", 1],
                "DC_Power" : [40101, "uint16", 1],
                "AC_Power" : [40088, "uint16", 1],
                "Cabinet_Temperature" : [40110, "float", 1],
                "InOutWRte_RvrtTms_Fallback" : [40359, "uint16", 1],
                "Operating_State" : [40118, "uint16", 1]
            },
            "StorageDevice": {
                "Battery_capa" : [40141, "uint16", 1],
                "Battery_DC_Power_in" : [40315, "uint16", 1],
                "Battery_DC_Power_out" : [40335, "uint16", 1],
                "Battery_SunspecID" : [40344, "uint16", 1],
                "Battery_SoC" : [40352, "uint16", 1],
                "Battery_Status" : [40355, "uint16", 1],
                "BatteryChargeRate" : [40346, "uint16", 1],                
                "BatteryMaxDischargePercent" : [40356, "uint16", 1],
                "BatteryMaxChargePercent" : [40357, "uint16", 1],                
                "StorageControlMode" : [40349, "uint16", 1]   #bitfield16 eigentlich, wird aber nicht abgefangen
            },
            "MultipleMPPT": {
                "MPPT_SunspecID" : [40254, "uint16", 1],
                "MPPT_Current_Scale_Factor" : [40256, "uint16", 1],
                "MPPT_Voltage_Scale_Factor" : [40257, "uint16", 1],
                "MPPT_Power_Scale_Factor" : [40258, "uint16", 1],
                "MPPT_1_DC_Current" : [40273, "uint16", 1],
                "MPPT_1_DC_Voltage" : [40274, "uint16", 1],
                "MPPT_1_DC_Power" : [40275, "uint16", 1],
                "MPPT_1_Temperature" : [40280, "uint16", 1],
                "MPPT_1_State" : [40281, "uint16", 1],
                "MPPT_2_DC_Current" : [40293, "uint16", 1],
                "MPPT_2_DC_Voltage" : [40294, "uint16", 1],
                "MPPT_2_DC_Power" : [40295, "uint16", 1],
                "MPPT_2_Temperature" : [40300, "uint16", 1],
                "MPPT_2_State" : [40301, "uint16", 1]
            },
            "PowerMeter": {
                "Meter_SunspecID" : [40070, "uint16", 200],
                "Meter_Frequency" : [40086, "uint16", 200],
                "Meter_Power_Total" : [40088, "uint16", 200],
                "Meter_Power_L1" : [40089, "uint16", 200],
                "Meter_Power_L2" : [40090, "uint16", 200],
                "Meter_Power_L3" : [40091, "uint16", 200],
                "Meter_Power_Scale_Factor" : [40092, "uint16", 200]
            }
        }
         
    def read_uint16(self, addr):
        regs = self.modbus.read_holding_registers(addr-1, 1)
        if regs:
            return int(regs[0])
        else:
            print("read_uint16() - error")
            return False
      
    def read_uint32(self, addr):
        regs = self.modbus.read_holding_registers(addr-1, 2)
        if regs:
            return int(utils.word_list_to_long(regs, big_endian=True)[0])
        else:
            print("read_uint32() - error")
            return False
        
    def read_float(self, addr):
        regs = self.modbus.read_holding_registers(addr-1, 2)
        if not regs:
            print("read_float() - error")
            return False

        list_32_bits = utils.word_list_to_long(regs, big_endian=True)
        return float(utils.decode_ieee(list_32_bits[0]))

    def read_data(self, parameter):
        sectionMatch = None
        for section, properties in self.registers.items():
            for key, value in properties.items():
                if (key == parameter):
                    sectionMatch = section        
        [register, datatype, unit_id] = self.registers[sectionMatch][parameter]
        
        self.modbus.unit_id(unit_id)
        if datatype == "float":
            return self.read_float(register)
        elif datatype == "uint32":
            return self.read_uint32(register)
        elif datatype == "uint16":
            return self.read_uint16(register)
        else:
            return False
    
    def read_section(self, section):
        list = {}
        for key, value in self.registers[section].items():
            [register, datatype, unit_id] = value
            data = None
            self.modbus.unit_id(unit_id)
            if datatype == "float":
                data = self.read_float(register)
            elif datatype == "uint32":
                data = self.read_uint32(register)
            elif datatype == "uint16":
                data = self.read_uint16(register)
            
            # list |= { key : data }
            list[key] =  data 
        return list

    def write_float(self, addr, value):
        floats_list = [value]
        b32_l = [utils.encode_ieee(f) for f in floats_list] 
        b16_l = utils.long_list_to_word(b32_l, big_endian=False)
        return self.modbus.write_multiple_registers(addr-1, b16_l)

    def write_uint16(self, addr, value):
        return self.modbus.write_single_register(addr-1, value)
   
    def write_data(self, parameter, value):
        sectionMatch = None
        for section, properties in self.registers.items():
            for key, val in properties.items():
                if (key == parameter):
                    sectionMatch = section
        [register, datatype, unit_id] = self.registers[sectionMatch][parameter]
        
        self.modbus.unit_id(unit_id)
        if datatype == "float":
            return self.write_float(register, value)
        elif datatype == "uint16":
            # print(register, value)
            return self.write_uint16(register, value)
        else:
            return False

    def print_all(self):
        print("Show all registers:")
        for section, properties in self.registers.items():
            for name, params in properties.items():
                value = self.read_data(name)
                print("{0:d}: {1:s} - {2:2.1f}".format(params[0], name, value))
    
    # To search for undocument registers.... 
    def print_raw(self):
        print("Raw read 1000-2000:")
        for i in range(1000,2000,1):
            value = self.read_float(i)
            if value:
                print("{0:d}: {1:2.1f}".format(i, value))
            #else:
            #    print("{0:d}: error".format(i))

    def get_mppt_power(self):
        mpppt_1_power = self.read_data('MPPT_1_DC_Power')
        if mpppt_1_power == 65535:
            mpppt_1_power = 0
        mpppt_2_power = self.read_data('MPPT_2_DC_Power')
        if mpppt_2_power == 65535:
            mpppt_2_power = 0
        power_scale_tmp = np.float64(np.int16(self.read_data('MPPT_Power_Scale_Factor')))
        return int((mpppt_1_power + mpppt_2_power) * (10 ** power_scale_tmp))

    def get_meter_power(self):
        meter_power_total = self.read_data('Meter_Power_Total')
        meter_power_scale_tmp = np.float64(np.int16(self.read_data('Meter_Power_Scale_Factor')))
        return int(np.int16(meter_power_total) * (10 ** meter_power_scale_tmp))
        
    def get_batterie_power(self):
        batterie_power_total = self.read_data('Battery_DC_Power_out') - self.read_data('Battery_DC_Power_in')
        batterie_power_scale_tmp = np.float64(np.int16(self.read_data('MPPT_Power_Scale_Factor')))
        return int(batterie_power_total * (10 ** batterie_power_scale_tmp))

    def get_API(self):
        import requests
        import json
        config = loadConfig('config.ini')
        gen24url = "http://"+config['gen24']['hostNameOrIp']+"/components/readable"
        url = requests.get(gen24url)
        text = url.text
        data = json.loads(text)
        API = {}
        API['AC_Produktion'] = int(data['Body']['Data']['327680']['channels']['ACBRIDGE_ENERGYACTIVE_PRODUCED_SUM_U64']/3600)
        API['DC_Produktion'] = int((data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_01_U64']+ data['Body']['Data']['393216']['channels']['PV_ENERGYACTIVE_ACTIVE_SUM_02_U64'])/3600)
        API['Netzverbrauch'] = int(data['Body']['Data']['16252928']['channels']['SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64'])
        API['Einspeisung'] =  int(data['Body']['Data']['16252928']['channels']['SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64'])
        API['Batterie_IN'] = int(data['Body']['Data']['393216']['channels']['BAT_ENERGYACTIVE_ACTIVECHARGE_SUM_01_U64']/3600)
        API['Batterie_OUT'] = int(data['Body']['Data']['393216']['channels']['BAT_ENERGYACTIVE_ACTIVEDISCHARGE_SUM_01_U64']/3600)
        return(API)

        
# Test program
if __name__ == "__main__":
    
    config = loadConfig('config.ini')
    host_ip = getVarConf('gen24','hostNameOrIp', 'str')
    host_port = getVarConf('gen24','port', 'str')
    gen24 = SymoGen24(host_ip, host_port)

    # print("MPPT-Zeit: ", datetime.now())
    # Sunspec ID (should be 113)
    # print(gen24.read_uint16(40070))
    # Current AC Output Power
    # print(gen24.read_float(40092))
    
    # print(gen24.read_data("SunspecID"))
    # print(gen24.read_section('PowerMeter'))
        
    gen24.print_all()
    # gen24.print_raw()

    # print("40069", gen24.read_uint16(40069))
    # print("40357", gen24.read_uint16(40357))
    # print("40358", gen24.read_uint16(40358))

    # print(gen24.modbus.unit_id())
    
    # gen24.modbus.unit_id(200)

    # print(gen24.read_uint16(40070))
    # print(gen24.read_float(40098))

    print("Battery_DC_Power_in", gen24.read_data("Battery_DC_Power_in"))
    print("Battery_DC_Power_out", gen24.read_data("Battery_DC_Power_out"))
    print("Meter_Power_Scale_Factor", gen24.read_data("Meter_Power_Scale_Factor"))
    # print("Meter_Power_Total", gen24.read_data("Meter_Power_Total"))
    
    print("PV_Produktion ", gen24.get_mppt_power())
    # print("Meter_Power ", gen24.get_meter_power())
    print("Batterie_Power ", gen24.get_batterie_power())
    print("API_Werte: ", gen24.get_API())
    # PV_Produktion = gen24.get_mppt_power()
    # Meter_Power = gen24.get_meter_power()
    # print(datetime.now(), ",", PV_Produktion, ",", Meter_Power * -1)
    
    # gen24.modbus.unit_id(1)

