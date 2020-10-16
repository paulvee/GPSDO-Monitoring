#!/usr/bin/python3
#-------------------------------------------------------------------------------
# Name:        serial_monitorV3.py
# Purpose:     Serial port monitoring on a RaspberryPi to monitor a GPSDO counter
#              using the main UART
#
# Author:      paulv
#
# Created:     20-07-2018
# Copyright:   (c) paulv 2018 2019 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Enable the serial port with sudo raspi-config
#
# For Pi 3, 4 and Zero-W, swap the mini-UART back to the TL011
# sudo nano /boot/config.txt
# add:
# dtoverlay=disable-bt
#
# disable the modem:
# sudo systemctl disable hciuart
#
# install the Python serial driver
# sudo apt-get install python3-serial
import serial
import logging
import logging.handlers
import sys
import os
import traceback
import time

VERSION = "3.1"     # add support for a RAM disk

DEBUG = True

# serial port to read the GPSDO reports from the Arduino Nano
port = "/dev/ttyAMA0" # for PL011
#port = "/dev/serial0"  # for primary UART
#port = "/dev/ttyS0"   # for mini-UART

ser = serial.Serial(port, baudrate=9600, timeout=None)

# data path is on a RAM disk to protect the SD card
# every new day, the log file will be moved to the SD card by a cron job
data_path = "/mnt/ramdisk/"

# -- Logger definitions
LOG_FILENAME = data_path+"counter.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "INFO", "DEBUG", "ERROR" or "WARNING"


class MyLogger(object):
    '''
    Replace stdout and stderr with logging to a file so we can run this script
    even as a daemon and still capture all the stdout and stderr messages in the log.

    '''
    def __init__(self, logger, level):
            """Needs a logger and a logger level."""
            self.logger = logger
            self.level = level

    def write(self, message):
            # Only log if there is a message (not just a new line)
            # typical for serial data with a cr/lf ending
            if message.rstrip() != "":
                self.logger.log(self.level, message.rstrip())

    def flush(self): # prevents warning: 'MyLogger' object has no attribute 'flush'
        return


def init():
    global logger, handler

    if DEBUG:
        print ("Setting up the logger functionality")
    logger = logging.getLogger(__name__)
    logger.setLevel(LOG_LEVEL)
    handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=31)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if DEBUG:
        pass
    else:
        # pipe the stdout and stderr messages to the logger
        sys.stdout = MyLogger(logger, logging.INFO)
        sys.stderr = MyLogger(logger, logging.ERROR)



def main():

    if DEBUG: print("Serial counter logger Version {}".format(VERSION))

    init()

    if DEBUG:print("Opened port {} for serial tracing".format(port))

    try:
        while True:
            try:
                received_data = ser.readline()
                data_rb = received_data.decode('utf-8').rstrip()
                #print (data_rb)
            except (OSError, serial.serialutil.SerialException):
                if DEBUG : print("No data available")
                continue
            except UnicodeDecodeError:
                if DEBUG: print("decode error")
                continue

            try:
                (gate, counter) = data_rb.split(',')
            except Exception as e:
                print("*** Exception: {} : {}".format(e, data_rb))
                continue
            try:
                counter_f = float(counter.rstrip('Hz'))
                if counter_f < 100000 :
                    counter_s = " {:,.4f}".format(counter_f)  # add a leading space
                else:
                    counter_s = "{:,.4f}".format(counter_f)

                d_gate = gate
                if gate == "Gate 1000s" :
                    d_gate = "Gate 1K"
                if gate == "Gate 10000s" :
                    d_gate = "Gate 10K"

                if DEBUG:
                    print("{}\t{}s  Counter = {} Hz".format(data_rb, d_gate, counter_s))
                else:
                    print("{}s  Counter = {} Hz".format(d_gate, counter_s))

            except Exception as e:
                print("*** Exception: {}".format(e))
                continue



    except KeyboardInterrupt: # Ctrl-C
        print("\nCtrl-C - Terminated")
        os._exit(1)

    except Exception as e:
        sys.stderr.write("Got exception: {}".format(e))
        print(traceback.format_exc())
        os._exit(1)


if __name__ == '__main__':
    main()
