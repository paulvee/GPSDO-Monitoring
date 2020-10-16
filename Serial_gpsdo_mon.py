#!/usr/bin/python3
#-------------------------------------------------------------------------------
# Name:        serial_gps_mon.py
# Purpose:     Serial monitoring on a RaspberryPi for a GPSDO report
#
#
# Author:      paulv
#
# Created:     20-07-2018
# Copyright:   (c) paulv 2018 2019 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# to install python serial: sudo apt-get install python3-serial
import serial
import logging
import logging.handlers
import sys
import os
import traceback


VERSION = "2.2"     # add support for a RAM disk

# To enable the serial port on the GPIO connector, use raspi-config or:
# sudo nano /boot/config.txt
# enable_uart=1
# reboot

DEBUG = True


# serial port to read the GPSDO reports from the Arduino Nano
#Note that on an RPi model 3, 4 and the Zero-W , the main UART, PL011, is replaced
# by what the foundation calls, a mini-UART. This mini-UART is less capable and
# bound to drop data.

# Enable the serial port with sudo raspi-config
#
# For Pi 3, 4 and Zero-W, swap the mini-UART back to the TL011
# sudo nano /boot/config.txt
# add:
# dtoverlay=disable-bt
#
# disable the modem:
# sudo systemctl disable hciuart


port = "/dev/ttyAMA0" # TL011 UART (the good)
#port = "/dev/serial0"  # mini-UART  (the bad)


serialPort = serial.Serial(port, baudrate=9600, timeout=None)

# data path is on a RAM disk to protect the SD card
# every new day, the log file will be moved to the SD card by a cron job
# to setup a 50Meg ramdisk, add this to /etc/fstab:
#     tempfs /mnt/ramdisk tmpfs defaults,noatime,size=50M,mode=1777 0 0

data_path = "/mnt/ramdisk/"

# -- Logger definitions
LOG_FILENAME = data_path+"ocxo.log"
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
        print("logger version ", VERSION)
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

    if DEBUG:print("Serial GPSDO logger Version {}".format(VERSION))

    init()

    if DEBUG:print("Opened port", port, "for serial tracing")

    try:
        while True:
            while (serialPort.inWaiting() > 0):
                try:
                    ser_input = serialPort.readline().decode('utf-8').rstrip() # strip the cr/lf
                    #ser_input = serialPort.read_until().decode('utf-8')
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
