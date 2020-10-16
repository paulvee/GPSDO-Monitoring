#!/usr/bin/python2.7
#-------------------------------------------------------------------------------
# Name:        gps_bb.py
# Purpose:     Serial port monitoring of a NEO GPS on a RaspberryPi Zero-W by
#               using the pigpio bit-banging software to get access to more
#               serial ports.
#
# Author:      paulv
#
# Created:     20-07-2018
# Copyright:   (c) paulv 2018 2019 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# https://github.com/Knio/pynmea2 to install use : pip install pynmea2
# note that this only seems to work on Python 2.7
import pynmea2 # NMEA message parser

# sudo apt-get install pigpio
# http://abyz.me.uk/rpi/pigpio/index.html
import pigpio  # pigpio library used for serail bit-banging

from time import sleep
import sys
import os
from datetime import datetime, date, time, timedelta
import logging
import logging.handlers
import traceback

DEBUG = False

VERSION = "1.1"   # fixed a bug when there are multiple $'s in a segment

serial_port = 24 # GPIO port


#create instance of pigpio class
pi = pigpio.pi()
if not pi.connected:
    os.system("sudo pigpiod")
    sleep(1)
    pi = pigpio.pi()

pi.set_mode(serial_port, pigpio.INPUT)

# data path is on a RAM disk to protect the SD card
# every new day, the log file will be moved to the SD card by a cron job
data_path = "/mnt/ramdisk/"

# -- Logger definitions
LOG_FILENAME = data_path+"nmea.log"
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

    # pipe the stdout and stderr messages to the logger
    sys.stdout = MyLogger(logger, logging.INFO)
    sys.stderr = MyLogger(logger, logging.ERROR)



def parseGPS(xstr):

    if xstr.find('GGA') > 0:  # looking for the $GGA sentence
        if DEBUG: print("found it")
        try:
            msg = pynmea2.parse(xstr)
        except pynmea2.ParseError as e:
            print('Parse error: {}'.format(e))
            return
        # a simple kludge to get local time
        local_time = ("{}:{}:{}".format(msg.timestamp.hour+2, msg.timestamp.minute, msg.timestamp.second))
        if DEBUG:
            print ("Time: {}  \t Lat: {} {} \t Lon: {} {} \t Altitude: {} {} \t Satellites: {}"\
                .format(local_time,msg.lat,msg.lat_dir,msg.lon,msg.lon_dir,msg.altitude,msg.altitude_units, msg.num_sats))
        else:
            print ("Time:,{},Lat:,{},{},Lon:,{},{},Altitude:,{},{},Satellites:,{}"\
                .format(local_time,msg.lat,msg.lat_dir,msg.lon,msg.lon_dir,msg.altitude,msg.altitude_units, msg.num_sats))

# string slicing & dicing helpers
# https://stackoverflow.com/questions/22586286/python-is-there-an-equivalent-of-mid-right-and-left-from-basic

def right(s, amount):
    return s[amount:]

def left(s, amount):
    return s[:amount]

def mid(s, offset, amount):
    return s[offset-1:offset+amount-1]


def main():
    if DEBUG: print("Bit Banging Serial counter logger Version {}".format(VERSION))

    init()

    if DEBUG: print("opening serial port")

    # from joan:
    # https://raspberrypi.stackexchange.com/questions/27488/pigpio-library-example-for-bit-banging-a-uart
    # turn fatal exceptions off (so that closing an unopened gpio doesn't error)
    pigpio.exceptions = False
    pi.bb_serial_read_close(serial_port)
    # fatal exceptions back on
    pigpio.exceptions = True
    pi.bb_serial_read_open(serial_port, 9600)  # 8 bits is default

    str_s = ""  # holds the string building of segments
    str_r = ""  # holds the left-over from a previous string which may contain
                # the start of a new sentence

    try:
        while True:
            # get some data. The bb_serial_read will read small segments of the string
            # they need to be added together to form a complete NEO sentence.
            (b_count, data) = pi.bb_serial_read(serial_port)
            if DEBUG: print(b_count, data)
            # wait for the start of a new sentence, it starts with a "$"
            if (int(b_count) > 0): # wait for data
                # we have data, now look for the start char "$"
                # decode to ascii first so we can use string functions
                try:
                    data_s = data.decode("utf-8", "ignore") # discard non-ascii data
                    if DEBUG: print(data_s)
                except AttributeError as e:
                    print('*** Decode error: {}'.format(e))
                    continue
                # add the left-over from the previous sentence if there was one
                data_s = str_r + data_s
                if DEBUG: print(data_s)

                if "$" in data_s: # do we have a "$" in this segment
                    if DEBUG: print("start found")
                    pos = data_s.find('$')  # get the position of the "$"
                    # save the start of the sentence
                    str_s = right(data_s, pos)  # strip everything to the left

                    # look to see if there are more "$"'s in this segment
                    # this will mess-up the NMEA sentence parsing
                    # I've only found two $'s in one segment.
                    if str_s.count("$") > 1 :
                        pos = str_s[1:].find('$')  # get the position of the second "$"
                        print(pos)
                        # save the start of the sentence
                        str_s = right(str_s[1:], pos)  # strip everything to the left
                    if DEBUG: print(str_s)

                    # get more data segments to complete the sentence

                    while (int(b_count) > 0):
                        (b_count, data) = pi.bb_serial_read(serial_port)
                        if DEBUG: print(b_count, data)
                        try:
                            data_s = data.decode("utf-8", "ignore")
                        except ValueError.ParseError as e:
                            print('*** Decode error: {}'.format(e))
                            continue

                        # look for the eol "\r\n" of the sentence
                        if "\r" in data_s:
                            if DEBUG: print("found eol")
                            pos = data_s.find('\r')
                            if DEBUG: print("\r position ",pos)
                            str_r = left(data_s, pos)  # use everything to the left of the eol
                            str_s = str_s +  str_r     # finish the sentence
                            if DEBUG: print(str_s)
                            parseGPS(str_s)  # parse the sentence we want to get the date from
                            # save the left-over, which can be the start of a new sentence
                            str_r = right(data_s, pos-1)
                            if DEBUG: print("left over", str_r)
                            break
                        else:
                            # add the segments together
                            str_s = str_s +  data_s
                            if DEBUG: print(str_s)

                else:
                    if DEBUG: print("keep looking for the start of a segment")
                    str_s = ""
                    data_s = ""
                    continue
            else:
                # still waiting for a string with data
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

