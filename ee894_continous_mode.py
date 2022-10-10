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

import time
from ee894_i2c_library import EE894


CSV_DELIMETER = ","

EE_894 = EE894()

try:
    # change device name
    EE_894.change_sensorname("best CO2 Sensor!")
    time.sleep(1)
    # read device name
    print("Sensor name: " + ''.join('{:c}'.format(x) for x in EE_894.read_sensorname())) 
    # change CAM(Costum adjustment Mode)
    EE_894.change_CAM(2, 0, 32768, 0, 65535) # change CAM(Custom Adjustment mode) from pressure (0 => relative humidity, 1 => temperature, 2 => pressure, 3 => CO2)
    time.sleep(1)
    # read CAM(Costum adjustment Mode)
    print("CAM data: " + str(EE_894.read_CAM(2))) #read CAM(Custom Adjustment mode) from pressure
    # change CAM date(Costum adjustment Mode)
    EE_894.change_CAM_date(2, 24, 12, 18) #  0 => relative humidity, 1 => temperature, 2 => pressure, 3 => CO2, 4 => global date
    time.sleep(1)
    # read CAM date(Costum adjustment Mode)
    print("CAM date: " + str(EE_894.read_CAM_date(2)))  
    # change Measuring Interval
    EE_894.change_co2_measuring_interval(150) # 100ms steps
    time.sleep(1)
    # read  Measuring Interval
    print("Measuring Interval: " + str(EE_894.read_co2_measuring_interval())) 

except Warning as exception:
    print("Exception: " + str(exception))

# print a header
print("temperarture",CSV_DELIMETER,"humidity",CSV_DELIMETER,"CO2 average",CSV_DELIMETER,"CO2 raw",CSV_DELIMETER,"pressure")
time.sleep(7)


for i in range(30):
    try:
        temperature, humidity = EE_894.get_temp_hum()
        co2_aver, co2_raw, pressure = EE_894.get_co2aver_co2raw_pressure()
        print('%0.2f °C' % temperature, CSV_DELIMETER, end="")
        print('%0.1f %% RH' % humidity, CSV_DELIMETER, end="")        
        print('%0.0f ppm' % co2_aver, CSV_DELIMETER, end="")
        print('%0.0f ppm' % co2_raw, CSV_DELIMETER, end="")
        print('%0.1f mbar' % pressure)
    except Warning as exception:
        print("Exception: " + str(exception))

    finally:
        time.sleep(15)