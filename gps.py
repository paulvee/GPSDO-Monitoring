#!/usr/bin/python2.7
#-------------------------------------------------------------------------------
# Name:        gps.py
# Purpose:     Serial port monitoring of a ubloc NMEA
#
# Uses:        https://github.com/Knio/pynmea2
# Author:      paulv
#
# Created:     11-10-2020
# Copyright:   (c) paulv 2018 2019 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import serial
import pynmea2  # https://github.com/Knio/pynmea2 : pip install pynmea2
from datetime import datetime, date, time, timedelta


serialPort = serial.Serial("/dev/ttyAMA0", 9600, timeout=0.5)

def parseGPS(str):

    if str.find('GGA') > 0:
        msg = pynmea2.parse(str)

        # a kludge to get local time
        local_time = ("{}:{}:{}".format(msg.timestamp.hour+2, msg.timestamp.minute, msg.timestamp.second))

        print ("Time: {} \t Lat: {} {} \t Lon: {} {} \t Altitude: {} {} \t Satellites: {}"\
            .format(local_time,msg.lat,msg.lat_dir,msg.lon,msg.lon_dir,msg.altitude,msg.altitude_units, msg.num_sats))


def main():
    print("starting processing")
    while True:
        try:
            str = serialPort.readline()
            parseGPS(str)
        except pynmea2.ParseError as e:
            print('Parse error: {}'.format(e))
            continue
        except serial.SerialException as e:
            print('Device error: {}'.format(e))
            break


if __name__ == '__main__':
    main()

