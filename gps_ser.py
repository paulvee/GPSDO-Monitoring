#!/usr/bin/python2.7
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      paulv
#
# Created:     13-10-2020
# Copyright:   (c) paulv 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import io

import pynmea2  # https://github.com/Knio/pynmea2 : pip install pynmea2
import serial


ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=5.0)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

while 1:
    try:
        line = sio.readline()
        msg = pynmea2.parse(line)
        print(repr(msg))
    except serial.SerialException as e:
        print('Device error: {}'.format(e))
        break
    except pynmea2.ParseError as e:
        print('Parse error: {}'.format(e))
        continue

def main():
    pass

if __name__ == '__main__':
    main()
