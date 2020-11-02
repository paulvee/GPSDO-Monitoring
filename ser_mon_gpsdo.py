#!/usr/bin/python3.7
#-------------------------------------------------------------------------------
# Name:        ser_mon_gpsdo.py
# Purpose:     Serial port monitoring on a RaspberryPi from a GPSDO main TxD
#              The GPSDO has a Bliley OCXO
#
# Author:      paulv
#
# Created:     20-07-2018
# Copyright:   (c) paulv 2018 2019 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# sudo apt-get install python3-serial
import serial
import logging
import logging.handlers
import sys
import os
import traceback
import shlex
import string
import glob


VERSION = "2.2"     # add support for a RAM disk

# To enable the serial port on the GPIO connector, use raspi-config or:
# sudo nano /boot/config.txt
# enable_uart=1
# reboot

DEBUG = True
DAEMON = True   # if false, pipe the std out/error to the console


# serial port to read the GPSDO reports from the Ardujino Nano
#port = "/dev/ttyAMA0"
port = "/dev/serial0"
#port = "/dev/ttyS0"



serialPort = serial.Serial(port, baudrate=9600, timeout=None)

# data path is on a RAM disk to protect the SD card
# every new day, the log file will be moved to the SD card by a cron job
log_path = "/mnt/ramdisk/bliley.log"

# -- Logger definitions
LOG_FILENAME = log_path
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
    global logger, handler, ds_temp_IIR

    if DEBUG:
        print("Bliley GPSDO logger version ", VERSION)
        print ("Setting up the logger functionality")
    logger = logging.getLogger(__name__)
    logger.setLevel(LOG_LEVEL)
    handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=31)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if DAEMON :
        # pipe the stdout and stderr messages to the logger
        sys.stdout = MyLogger(logger, logging.INFO)
        sys.stderr = MyLogger(logger, logging.ERROR)
    return


def main():

    if DEBUG:print("Serial logger Version {}".format(VERSION))

    init()

    if DEBUG:print("Opened port", port, "for serial tracing")

    try:
        while True:
            while (serialPort.inWaiting() > 0):
                try:
                    ser_input = serialPort.readline().decode('utf-8').rstrip() # strip the cr/lf
                    print(ser_input) # this will be captured by the pipe
                except (OSError, serial.serialutil.SerialException):
                    if DEBUG : print("No data available")
                    continue
                except UnicodeDecodeError:
                    if DEBUG: print("decode error")
                    continue

    except KeyboardInterrupt: # Ctrl-C
        print("\nCtrl-C - Terminated")
        os._exit(1)

    except Exception as e:
        sys.stderr.write("Got exception: %s" % (e))
        print(traceback.format_exc())
        os._exit(1)


if __name__ == '__main__':
    main()
