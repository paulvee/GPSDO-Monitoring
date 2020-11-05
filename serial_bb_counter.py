#!/usr/bin/python3.7
#-------------------------------------------------------------------------------
# Name:        Serial_bb.py
# Purpose:     Serial port monitoring on a RaspberryPi Zero-W by
#               using the pigpio bit-banging software to get access to more
#               serial ports.
#               This code is based on Yannick's counter version 1.02
#               Available here: https://github.com/YannickTurcotte/GPSDO-Counter
#
#               The systemd service file is : ser_mon_counter.service
#
# Author:      paulv
#
# Created:     20-10-2020
# Copyright:   (c) paulv 2018 2019 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------


# sudo apt-get install pigpio
# http://abyz.me.uk/rpi/pigpio/index.html
import pigpio  # pigpio library used for serial bit-banging
from time import sleep
import sys
import os
import time
import logging
import logging.handlers
import traceback
import json


DEBUG = False
DAEMON = True # if False, pipe the print statements to the console

VERSION = "1.3"     # added reset of counter chip and gate selection

serial_port = 23    # GPIO port for the Counter
reset_port = 22     # GPIO port for the Counter reset pin
gate_port = 25      # GPIO port for the gate time selection

bol = "G"   # for the Counter or $ for the NEO
eol = "\r"  # followed by \n
log_file = "counter"

gate = "1000"   # will be set at startup in main()

# instantiate an empty dict to hold the json data
display_data = {}

# create instance of pigpio class
pi = pigpio.pi()
# test to see if the daemon is already running
if not pi.connected:
    # if the daemon is not running, start it
    os.system("sudo pigpiod")
    sleep(1)
    pi = pigpio.pi()

# set the GPIO pin used for the bit-banging serial port
pi.set_mode(serial_port, pigpio.INPUT)

# data paths are on a RAM disk to protect the SD card.
# just before midnight, the log file will be emailed to me, activated
# by a cron job
# every new day, a new log file will be started and the log file from
# the previous day will be moved to the SD card by a cron job
# the logger currently keeps 31 days before it rotates
log_path = "/mnt/ramdisk/counter.log"
display_path = "/mnt/ramdisk/counter.json"

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
    global logger, handler

    if DEBUG:
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


def set_gate(mode=1):
    '''
    Setting the gate time of the counter
    I use a little input-output trick here to conform to the 3V3 voltage levels
    of the RPi, while the counter chip has 5V levels.
    '''
    global gate

    if mode== 10:
        # set gate to 10K
        print("Setting gate to 10Ks")
        # drive the port low
        pi.set_mode(gate_port, pigpio.OUTPUT)
        pi.write(gate_port, 0)
        gate = "10000s"
    else:
        # set gate to 1K
        print("Setting gate to 1Ks")
        # set the port to hi-Z, making it high
        pi.set_mode(gate_port, pigpio.INPUT)
        gate = "1000s"


def reset_counter():
    '''
    Reset the counter chip
    By doing that, we start a fresh counting cycle we know the starting time
    of, so we can correctly display the remaining number of minutes before we
    get an update. We can also already display the gate time.
    '''

    print("Resetting the counter")
    pi.set_mode(reset_port, pigpio.OUTPUT)
    pi.write(reset_port, 0) # actually reset it
    time.sleep(0.5)
    pi.set_mode(reset_port, pigpio.INPUT) # release the port back to hi-Z


def process_data(rcv_string, tstamp):
    '''
    process the string we received from the counter.
    This can be in the form of:
     - with a GPS connection:
     "Gate 1000s,S=12,10000000.000 Hz" or "Gate 10000s,S=12,10000000.0000 Hz"
     We're not using the number of satellites here, we do that differently
     - so without a GPS connection:
     "Gate 1000s,,10000000.000 Hz" or "Gate 10000s,,10000000.0000 Hz"
     Yannick had a version with leading zero's if number was less than 10MHz
     "Gate 1000s,,09999999.000 Hz" or "Gate 10000s,,09999999.0000 Hz"
     I asked him to remove them, but this code still handles it.
    '''

    # Check if we have three items in the string to avoid a ValueError
    # I saw this once when I switched from a 1K to a 10K gate time
    if (len(rcv_string.split(",")) == 3):
        # separate the tree segments
        gate_s, sat, counter_s = rcv_string.split(",")
        # take off the "Gate =" part, so we're left with "1000s" or "10000s"
        gate_t, gate = gate_s.split(" ")

        # take off the "Hz" part, we're not worried about the leading zero's
        try:  # it could still be wrong
            count, suff = counter_s.split(" ")
            if DEBUG : print(counter_s)
        except ValueError:
            print ("ValueError: {}".format(counter_s))
            return
        # save the data into a file so the display script can pick it up
        write_json_data(count, gate, tstamp)
    else:
        print("Error: no 3 segments to split {}".format(rcv_string))
    return



def write_json_data(gate, counter, tstamp):
    '''
    This script saves the data into a json-encoded file that the display
    driver can pick-up
    '''
    global display_data

    # this will be piped into the log file if DAEMON = True
    # or to the console if not
    print("gate\t{}\tcounter\t{}".format(gate,counter))

    display_data["counter"] = counter
    display_data["gate"] = gate
    display_data["tstamp"] = tstamp

    with open(display_path, 'w') as f:
        try:
            json.dump(display_data, f)
        except ValueError:
            print("ValueError from jason.dump")
            return
    return



# string slicing & dicing helpers
# https://stackoverflow.com/questions/22586286/python-is-there-an-equivalent-of-mid-right-and-left-from-basic
def right(s, amount):
    return s[amount:]

def left(s, amount):
    return s[:amount]

def mid(s, offset, amount):
    return s[offset-1:offset+amount-1]


def main():

    init()
    print("Bit Banging Serial Logger Counter - Version {}".format(VERSION))
    if DEBUG : print("opening serial port")
    # from joan:
    # https://raspberrypi.stackexchange.com/questions/27488/pigpio-library-example-for-bit-banging-a-uart
    # turn fatal exceptions off (so that closing an unopened gpio doesn't error)
    pigpio.exceptions = False
    pi.bb_serial_read_close(serial_port)
    # fatal exceptions back on
    pigpio.exceptions = True
    pi.bb_serial_read_open(serial_port, 9600)  # open the port, 8 bits is default

    # set the gate period to 1Ks
    set_gate(1)
    # reset the counter chip to start a fresh cycle
    # this means we can display the correct gate period, and we know the starting time
    reset_counter()

    str_s = ""  # holds the string building of segments
    str_r = ""  # holds the left-over from a previous string which may contain
                # the start of a new sentence

    # create an initial json file so the oled driver can display the initial data
    tstamp_s = int(time.time()/60)  # in minutes
    write_json_data(gate,0,tstamp_s)

    if DEBUG : print("start processing...")
    try:
        while True:
            # get some data. The bb_serial_read will read small segments of the string
            # so they need to be added together to form a complete sentence.
            (b_count, data) = pi.bb_serial_read(serial_port)  # b_count is byte count of data
            #if int(b_count) > 0: print("b_count: {} data: {}".format(int(b_count), data))
            # wait for the start of a new sentence, it starts with a begin-of-line(bol)
            if (int(b_count) == 0): # wait for real data
                continue
            # we have data
            # decode to ascii first so we can use string functions
            try:
                data_s = data.decode("utf-8", "ignore") # discard non-ascii data
                if DEBUG: print(data_s)
            except AttributeError as e:
                print('*** Decode error: {}'.format(e))
                continue
            # add the left-over from the previous string if there was one
            data_s = str_r + data_s
            if DEBUG: print(data_s)
            #  look for the bol in this segment
            if bol in data_s:
                if DEBUG: print("found bol")
                pos = data_s.find(bol)  # get the position of the bol
                # save the start of the sentence starting with bol
                str_s = right(data_s, pos)  # strip everything to the left
                # look to see if there are more bol's in this segment
                if str_s.count(bol) > 1 :   # there is another one!
                    # skip the first and get the position of the second bol
                    pos = str_s[1:].find(bol)
                    if DEBUG : print(pos)
                    # strip everything to the left of the second bol
                    str_s = right(str_s, pos+1)
                if DEBUG: print(str_s)

                # get more data segments to complete the sentence
                while (int(b_count) > 0):
                    #if DEBUG : print("building string")
                    (b_count, data) = pi.bb_serial_read(serial_port)
                    #if DEBUG : print("b_count: {} data: {}".format(int(b_count), data))
                    if int(b_count) == 0 : # only process real data
                        b_count = 1  # stay in this while loop
                        continue
                    # decode to ascii
                    try:
                        data_s = data.decode("utf-8", "ignore")
                    except ValueError.ParseError as e:
                        print('*** Decode error: {}'.format(e))
                        continue

                    # look for the eol "\r" of the sentence
                    if eol in data_s:
                        if DEBUG: print("found eol")
                        pos = data_s.find(eol)
                        if DEBUG: print("eol position ",pos)
                        str_r = left(data_s, pos)  # use everything to the left of the eol
                        str_s = str_s +  str_r     # finish the sentence
                        if DEBUG : print("received string = {}".format(str_s))
                        # create a starting timestamp so we can calculate the time
                        # left before we get the next sample
                        tstamp_s = int(time.time()/60)  # in minutes
                        # process the results and write them to a file
                        process_data(str_s, tstamp_s)
                        # save the left-over, which can be the start of a new sentence
                        str_r = right(data_s, pos+1)
                        # if we have a single "\n", discard it
                        if str_r == "\n" :
                            str_r = ""   # skip the \n part of the eol

                        if DEBUG: print("left over", str_r)
                        # start looking for a bol again
                        break
                    else:
                        # add the segments together
                        str_s = str_s +  data_s
                        if DEBUG: print(str_s)
                        # get more segments to complete the sentence

            else:
                # continue looking for the start of a segment
                str_s = ""
                data_s = ""
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

