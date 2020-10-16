#!/usr/bin/python3
#-------------------------------------------------------------------------------
# Name:        serial_counter_monbb.py
# Purpose:     Serial port monitoring on a RaspberryPi Zero-W with pigpio
#              bit-banging software to use more serial ports
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
import time
import pigpio

VERSION = "2.1"     # add support for a RAM disk

DEBUG = True

serial_port = 23 # GPIO port

#create instance of pigpio class
pi = pigpio.pi()
if not pi.connected:
    os.system("sudo pigpiod")
    time.sleep(1)
    pi = pigpio.pi()

pi.set_mode(serial_port, pigpio.INPUT)

data_rb = "" # used to build fractional bits of the received data
prev_data_rb = ""
rb_count_int = 0 # used to reconstruct the bits
prev_rb_count_int = 0

# data path is on a RAM disk to protect the SD card
# every new day, the log file will be moved to the SD card by a cron job
data_path = "/mnt/ramdisk/"

# -- Logger definitions
LOG_FILENAME = data_path+"counterbb.log"
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



def main():
    global prev_data_rb, data_rb, rb_count_int, prev_rb_count_int

    if DEBUG: print("Bit Banging Serial counter logger Version {}".format(VERSION))

    init()

    if DEBUG: print("opening serial port")

    # from joan:
    # https://raspberrypi.stackexchange.com/questions/27488/pigpio-library-example-for-bit-banging-a-uart
    # turn fatal exceptions off (so that closing an unopened gpio doesn't error)
    pigpio.exceptions = False
    pi.bb_serial_read_close(serial_port)
    # turn fatal exceptions back on
    pigpio.exceptions = True
    pi.bb_serial_read_open(serial_port, 9600)

    if DEBUG:
        if (status is not 0 ):
            print("bb port {} open status : {}".format(serial_port, status))

    try:
        while True:

            (b_count, data) = pi.bb_serial_read(serial_port)
            b_count_int = int(b_count)

            #  if the string is broken into pieces, rebuild it
            if (b_count_int > 0 and b_count_int < 26):
                #print("*** format error {} - {}".format(b_count_int, data))
                try:
                    data_rb = data.decode('utf-8').rstrip()
                except Exception as e:
                    print("*** Exception: {}".format(e))
                    print(data)
                    continue
                data_rb = prev_data_rb + data_rb
                prev_data_rb = data_rb
                rb_count_int = prev_rb_count_int + b_count_int
                prev_rb_count_int = rb_count_int
                #print("*building: {} - {}".format(rb_count_int, data_rb))
                if rb_count_int == 26 :
                    #print("*success : {}".format(data_rb))
                    try:
                        (gate, counter) = data_rb.split(',')
                        counter_f = float(counter.rstrip('Hz'))
                    except Exception as e:
                        print("*** Exception: {}".format(e))
                        print(counter)
                        continue

                    #print("*gate : {} counter : {}".format(gate, counter))
                    if counter_f < 100000 :
                        counter_s = " {:,.4f}".format(counter_f)  # add a leading space
                    else:
                        counter_s = "{:,.4f}".format(counter_f)
                    d_gate = gate
                    if gate == "Gate 1000s" :
                        d_gate = "Gate 1K"
                    if gate == "Gate 10000s" :
                        d_gate = "Gate 10K"
                    print("{}s  Counter = {} Hz *".format(d_gate, counter_s))
                else:
                    continue

            # if we have a valid length, process normally
            if (b_count_int == 26) :

                prev_data_rb = ""
                prev_rb_count_int = 0

                try:
                    data_s = data.decode('utf-8').rstrip()
                    (gate, counter) = data_s.split(',')
                except Exception as e:
                    print("*** Exception: {}".format(e))
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

                    print("{}s  Counter = {} Hz".format(d_gate, counter_s))

                except Exception as e:
                    print("*** Exception: {}".format(e))
                    continue

            time.sleep(.1)  # keep this well < 1s to avoid currupted data
            tstamp_s = time.time()

    except KeyboardInterrupt: # Ctrl-C
        print("\nCtrl-C - Terminated")
        status = pi.bb_serial_read_close(serial_port)
        if DEBUG:
            if (status is not 0 ):
                print("bb port {} close status : {}".format(serial_port, status))
        pi.stop()
        os._exit(1)

    except Exception as e:
        sys.stderr.write("Got exception: {}".format(e))
        print(traceback.format_exc())
        status = pi.bb_serial_read_close(serial_port)
        if DEBUG:
            if (status is not 0 ):
                print("bb port {} close status : {}".format(serial_port, status))
        pi.stop()
        os._exit(1)


if __name__ == '__main__':
    main()
