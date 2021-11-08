# -*- coding: utf-8 -*-
"""
Example script reading measurement values from the EE894 sensor via I2C interface.

Copyright 2021 E+E Elektronik Ges.m.b.H.

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

import time
from smbus2 import SMBus, i2c_msg

ADDRESS = 0x33
CSV_DELIMETER = ","
CRC8_ONEWIRE_POLY = 0x31
CRC8_ONEWIRE_START = 0xFF


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


def read_timeinterval():
    ''' reads time interval between measurments '''
    sec = 0
    write_rsec = i2c_msg.write(ADDRESS, [0x71, 0x54, 0x00])
    read_rsec = i2c_msg.read(ADDRESS, 3)
    with SMBus(1) as ee894_read_time:
        ee894_read_time.i2c_rdwr(write_rsec)
        ee894_read_time.i2c_rdwr(read_rsec)
    reading_sec = list(read_rsec)
    sec = round((reading_sec[0] << 8) + reading_sec[1]) / 10
    return sec


def change_timeinterval(buf):
    ''' change time between measurments '''
    write_change_sec = i2c_msg.write( ADDRESS,
    [0x71, 0x54, buf[0], buf[1], buf[2], calc_crc8(buf, 0, 3)])
    with SMBus(1) as ee894_write_time:          #creating an I2C instance and oppening the bus
        ee894_write_time.i2c_rdwr(write_change_sec)     #send write command
    time.sleep(1)



def main():
    ''' contains the main program  '''
    time.sleep(7)                               #time to wait until the first measurment is done
    change_timeinterval([0x00, 0x00, 0xC8])     #[0]= MEM Adresse,[1] MSB Data, [2] LSB Data
                                                #for more information check data sheet
    print("timeinetrvall:", read_timeinterval(), "s")
    # print a header
    print("temperarture",CSV_DELIMETER,"relative Humidity",CSV_DELIMETER,
          "CO2 average",CSV_DELIMETER,"CO2 raw",CSV_DELIMETER,"pressure",)

    write_command_a = i2c_msg.write(ADDRESS, [0xE0, 0x00])
    read_command_a = i2c_msg.read(ADDRESS, 6)

    write_command_b = i2c_msg.write(ADDRESS, [0xE0, 0x27])
    read_command_b = i2c_msg.read(ADDRESS, 9)

    with SMBus(1) as ee894:                     #creating an I2C instance and opening the bus
        ee894.i2c_rdwr(write_command_a)         #Command A obtain data for temperature and humidity
        ee894.i2c_rdwr(read_command_a)          #for more information check data sheet
        reading = list(read_command_a)
        temperature = ((reading[0] << 8) + reading[1]) / 100 - 273.15
        if calc_crc8(reading, 0, 2) == reading[2]:
            print('%0.2f °C' % temperature, CSV_DELIMETER, end="")
        else:
            print("CRC8 error", CSV_DELIMETER, end="")

        if calc_crc8(reading, 3, 5) == reading[5]:
            humidity = ((reading[3] << 8) + reading[4]) / 100
            print('%0.2f %%RH' % humidity, CSV_DELIMETER, end="")
        else:
            print("CRC8 error", CSV_DELIMETER, end="")

        ee894.i2c_rdwr(write_command_b)         #Command B obtain data for CO2 avg,CO2 raw,pressure
        ee894.i2c_rdwr(read_command_b)          #for more information check data sheet
        reading = list(read_command_b)
        if calc_crc8(reading, 0, 2) == reading[2]:
            co2avg = round((reading[0] << 8) + reading[1])
            print('%d ppm' % co2avg, CSV_DELIMETER, end="")
        else:
            print("CRC8 error", CSV_DELIMETER, end="")

        if calc_crc8(reading, 3, 5) == reading[5]:
            co2raw = (reading[3] << 8) + reading[4]
            print('%d ppm' % co2raw, CSV_DELIMETER, end="")
        else:
            print("CRC8 error", CSV_DELIMETER, end="")

        if calc_crc8(reading, 6, 8) == reading[8]:
            pressure = ((reading[6] << 8) + reading[7]) / 10
            print('%0.1f mbar' % pressure)
        else:
            print("CRC8 error")


if __name__ == "__main__":
    main()
