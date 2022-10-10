# -*- coding: utf-8 -*-
"""
Example script reading measurement values from the EE894 sensor via I2C interface.

Copyright 2022 E+E Elektronik Ges.m.b.H.

Disclaimer:
This application example is non-binding and does not claim to be complete with regard
to configuration and equipment as well as all eventualities. The application example
is intended to provide assistance with the EE894 sensor module design-in and is provided "as is".
You yourself are responsible for the proper operation of the products described.
This application example does not release you from the obligation to handle the product safely
during application, installation, operation and maintenance. By using this application example,
you acknowledge that we cannot be held liable for any damage beyond the liability regulations
described.

We reserve the right to make changes to this application example at any time without notice.
In case of discrepancies between the suggestions in this application example and other E+E
publications, such as catalogues, the content of the other documentation takes precedence.
We assume no liability for the information contained in this document.
"""

# pylint: disable=E0401
from smbus2 import SMBus, i2c_msg
import numpy as np
# pylint: enable=E0401
CRC8_ONEWIRE_POLY = 0x31
CRC8_ONEWIRE_START = 0xFF


def get_status_string(status_code):
    """Return string from status_code. """
    status_string = {
        0: "Successs",
        1: "Not acknowledge error",
        2: "Checksum error",
        3: "The sensor name must be 16 characters long.",
        4: "Wrong CAM Date input",
        5: "Wrong CAM input",
        }

    if status_code < len(status_string):
        return status_string[status_code]
    return "unknown error"

def calc_crc8(buf, start, end):
    ''' calculate crc8 checksum  '''
    crc_val = CRC8_ONEWIRE_START
    for j in range(start, end):
        cur_val = buf[j]
        for _ in range(8):
            if ((crc_val ^ cur_val) & 0x80) != 0:
                crc_val = (crc_val << 1) ^ CRC8_ONEWIRE_POLY
            else:
                crc_val = crc_val << 1
            cur_val = cur_val << 1
    crc_val &= 0xFF
    return crc_val



class EE894():
    """Implements communication with EE894 over i2c with a specific address."""
    
    def __init__(self):
        self.i2c_address = 0x33

    def get_all_measurements(self):
        """get allt the Measurments from the Sensor"""
        temperature, humidity = self.get_temp_hum
        co2avg, co2raw, pressure = self.get_co2aver_co2raw_pressure
        return temperature, humidity, co2avg, co2raw, pressure

    def get_temp_hum(self):
        """get temperature and humidity"""
        i2c_response = self.wire_write_read([0xE0, 0x00], 6)
        if ((calc_crc8(i2c_response, 0, 2) != i2c_response[2]) | (calc_crc8(i2c_response, 3, 5) != i2c_response[5])):          
            raise Warning(get_status_string(2))
        else:
            temperature = ((i2c_response[0] << 8) + i2c_response[1]) / 100 - 273.15
            humidity = ((i2c_response[3] << 8) + i2c_response[4]) / 100
            return temperature, humidity

    def get_co2aver_co2raw_pressure(self):
        """get co2 average co2 raw and pressure"""
        i2c_response = self.wire_write_read([0xE0, 0x27], 9)
        if ((calc_crc8(i2c_response, 0, 2) != i2c_response[2]) | (calc_crc8(i2c_response, 3, 5) != i2c_response[5]) | (calc_crc8(i2c_response, 6, 8) != i2c_response[8])):
            raise Warning(get_status_string(2))
        else:
            co2avg = round((i2c_response[0] << 8) + i2c_response[1])
            co2raw = (i2c_response[3] << 8) + i2c_response[4]
            pressure = ((i2c_response[6] << 8) + i2c_response[7]) / 10
            return co2avg, co2raw, pressure

    def read_sensorname(self):
        """get the Sensor name"""
        i2c_response = self.wire_write_read([0x71, 0x54, 0x0A], 16)
        return i2c_response

    def change_sensorname(self, buf):
        """change the Sensor name"""
        if (16 == len(buf)):
            Command = [0x71, 0x54, 0x0A]
            for x in range(16):
                Command.append(ord(buf[x]))
            Command.append(calc_crc8(Command, 2, 19))
            self.wire_write(Command)
        else:
            raise Warning(get_status_string(3))

    def read_CAM_date(self, measured_variable): # measured_variable: 0 => relative humidity, 1 => temperature, 2 => pressure, 3 => CO2, 4 => global date 
        """get CAM(Custom Adjustment mode) Date"""
        Command = [0x71, 0x54, 0x00]
        Command[2] = measured_variable + 5
        i2c_response = self.wire_write_read(Command, 3)
        return i2c_response[0], i2c_response[1], i2c_response[2]

    def change_CAM_date(self, measured_variable, day, month, year): # measured_variable: 0 => relative humidity, 1 => temperature, 2 => pressure, 3 => CO2, 4 => global date 
        """change CAM(Custom Adjustment mode) Date"""
        if((day < 32 and day > 0) and (month < 13 and month > 0) and (year < 100 and year >= 0)):
            Command = [0x71, 0x54, 0x00]
            Command[2] = measured_variable + 5
            Command.append(day)
            Command.append(month)
            Command.append(year)
            Command.append(calc_crc8(Command, 2, 6))
            self.wire_write(Command)
        else:
            raise Warning(get_status_string(4))

    def read_CAM(self, measured_variable): # 0 => relative humidity, 1 => temperature, 2 => pressure, 3 => CO2
        """get CAM(Custom Adjustment mode) Data"""
        Command = [0x71, 0x54, 0x00]
        Command[2] = measured_variable + 1
        i2c_response = self.wire_write_read(Command, 8)
        offset = np.int16((i2c_response[0] << 8) + i2c_response[1])
        gain = (i2c_response[2] << 8) + i2c_response[3]
        lower_limit = (i2c_response[4] << 8) + i2c_response[5]
        upper_limit = (i2c_response[6] << 8) + i2c_response[7]
        return offset, gain, lower_limit, upper_limit
    
    def change_CAM(self, measured_variable, offset, gain, lower_limit, upper_limit): #0 => relative humidity, 1 => temperature, 2 => pressure, 3 => CO2
        """change CAM(Custom Adjustment mode) Data"""
        if((gain < 65536 and gain >= 0) and (lower_limit < 65536 and lower_limit >= 0) and (upper_limit < 65536 and upper_limit >= 0)):
            Command = [0x71, 0x54, 0x00]
            Command[2] = measured_variable + 1
            buf = np.uint16(offset)
            Command.append(buf >> 8)
            Command.append(buf & 0xFF)
            Command.append(gain >> 8)
            Command.append(gain & 0xFF)
            Command.append(lower_limit >> 8)
            Command.append(lower_limit & 0xFF)
            Command.append(upper_limit >> 8)
            Command.append(upper_limit & 0xFF)
            Command.append(calc_crc8(Command, 2, 11))
            self.wire_write(Command)
        else:
            raise Warning(get_status_string(5))

    def change_offset_in_CAM(self, measured_variable, offset):
        """change in CAM(Custom Adjustment mode) offset"""
        old_offset, gain, lower_limit, upper_limit = self.read_CAM(measured_variable)
        self.change_CAM(measured_variable, offset, gain, lower_limit, upper_limit)
        
    def change_gain_in_CAM(self, measured_variable, gain):
        """change in CAM(Custom Adjustment mode) gain"""
        offset, old_gain, lower_limit, upper_limit = self.read_CAM(measured_variable)
        self.change_CAM(measured_variable, offset, gain, lower_limit, upper_limit)

    def change_lower_limit_in_CAM(self, measured_variable, lower_limit):
        """change in CAM(Custom Adjustment mode) lower limit"""
        offset, gain, old_lower_limit, upper_limit = self.read_CAM(measured_variable)
        self.change_CAM(measured_variable, offset, gain, lower_limit, upper_limit)

    def change_upper_limit_in_CAM(self, measured_variable, upper_limit):
        """change in CAM(Custom Adjustment mode) upper limit"""
        offset, gain, lower_limit, old_upper_limit = self.read_CAM(measured_variable)
        self.change_CAM(measured_variable, offset, gain, lower_limit, upper_limit)

    def read_co2_measuring_interval(self):
        ''' reads time interval between measurments '''
        i2c_response = self.wire_write_read([0x71, 0x54, 0x00], 3)
        sec = round((i2c_response[0] << 8) + i2c_response[1]) / 10
        return sec


    def change_co2_measuring_interval(self, measuring_interval):
        ''' change time between measurments '''
        sendByte0 = np.uint8(measuring_interval / 256)
        sendByte1 = np.uint8(measuring_interval % 256)
        Command = [0x71, 0x54, 0x00, sendByte0, sendByte1, 0x00]
        Command[5] = calc_crc8(Command, 2, 5)
        self.wire_write(Command)



    def wire_write_read(self,  buf, receiving_bytes):
        """write a command to the sensor to get different answers like temperature values,..."""
        write_command = i2c_msg.write(self.i2c_address, buf)
        read_command = i2c_msg.read(self.i2c_address, receiving_bytes)
        with SMBus(1) as ee894_communication:
            ee894_communication.i2c_rdwr(write_command, read_command)
        return list(read_command)

    def wire_write(self, buf):
        """write to the sensor"""
        write_command = i2c_msg.write(self.i2c_address, buf)
        with SMBus(1) as ee894_communication:
            ee894_communication.i2c_rdwr(write_command)
