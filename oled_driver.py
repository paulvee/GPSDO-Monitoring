#!/usr/bin/python3.7
#-------------------------------------------------------------------------------
# Name:         oled_driver.py
# Purpose:      Display GPSDO data on an 0.9" OLED display
#               The data is coming from the Yannick 10MHz counter and the
#               gps NEO which store the data on the ramdisk in a json format
#
#               the systemd script name is :  oled_driver.service
# Author:      paulv
#
# Created:     06-10-2020
# Copyright:   (c) paulv 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import time
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import locale
locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'
import json
import os

VERSION = "2.2"     # fixed bug to display sats when there is no json file
DEBUG = True


# data path is on a RAM disk to protect the SD card
neo_data_path = "/mnt/ramdisk/nmea.json"
counter_data_path = "/mnt/ramdisk/counter.json"

# instantiate an empty dict to pick-up the data stored by the devices
display_data = {}

# setup the OLED display
disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)
disp.begin()
disp.clear()
disp.display()
# print(disp.width, disp.height) # should be 128 x 32

image = Image.new('1', (disp.width, disp.height))   # create a blank image
draw = ImageDraw.Draw(image) # get drawing object to draw on image



def read_json_nmea():
    sat_nbr = 0
    # check if the file with the data is there
    if not os.path.isfile(neo_data_path):
        if DEBUG : print("no nmea data file")
        return(sat_nbr)

    with open(neo_data_path, 'r') as f:
        try:
            display_data = json.load(f)
        except ValueError:
            print("nmea: ValueError from jason.load")
            return(sat_nbr)

    # check for the presence of the NMEA data
    if "sat_nbr" in display_data.keys():
        sat_nbr = display_data["sat_nbr"]

    if sat_nbr != None :
        return(sat_nbr)
    else:
        print("read_json error")
        return("  ")


def read_json_counter():
    # check if the file with the data is there
    if not os.path.isfile(counter_data_path):
        print("no counter data file")
        return(0, 0, 0)

    with open(counter_data_path, 'r') as f:
        try:
            display_data = json.load(f)
        except ValueError:
            print("counter: ValueError from jason.load")
            return

    # check for the presence of the counter data
    # if counter is there, the rest will also be
    if "counter" in display_data.keys():
        counter = display_data["counter"]
        gate = display_data["gate"]
        tstamp = display_data["tstamp"]
    else:
        counter = 0
        gate = 0
        tstamp = 0

    return(counter, gate, tstamp)


def main():
    print("OLED display driver - Version {}".format(VERSION))

    # setup the display coordinates
    padding = 0 # first line
    shape_width = 20  # chars
    top = padding
    bottom = disp.height - padding
    x = padding
    my_font = ImageFont.load_default() # Load default font.

    try:
        while True:
            # get the data from the counter file
            counter, gate, tstamp = read_json_counter()
            # turn the counter string into a float
            counter_f = float(counter)
            # counter_p(recision) will be used in the display formatting
            counter_p = int(counter_f)
            if DEBUG : print(gate, counter_f,tstamp)

            # get the data from the neo file
            sat_nbr = read_json_nmea()

            # there has to be a valid digit in the string
            try:
                sat_nbr = int(sat_nbr)
                # ok, now right justify the number for the display position
                if sat_nbr < 9 :
                    sat_nbr_s = " "+str(sat_nbr)
                else:
                    sat_nbr_s = str(sat_nbr)
            except ValueError:
                print("received strange sat_nbr data : {}".format(sat_nbr))
                sat_nbr_s = "  "

            # setup the display formatting
            # set the number of decimals based on the selected gate time.
            # setup the remaining time counter when we can expect the next counter update
            gate_time_s = ""
            gate_time = 0
            if gate == "1000s" :
                # strip the leading zeroes if any
                counter_f = "{:,.3f}".format(counter_f).lstrip('0')
                gate_time_s = "1Ks"
                gate_time = int(1000/60)  # 16 minutes
            if gate =="10000s":
                #strip the leading zeroes if any
                counter_f = "{:,.4f}".format(counter_f).lstrip('0')
                gate_time_s = "10Ks"
                gate_time = int(10000/60)  # 166 minutes, 2.7 hrs

            # calculate the remaining time until the next counter update comes
            time_left = int(gate_time - (int(time.time()/60) - tstamp))

            # create right justified strings for the counter value
            if counter_p < 10000:      # 90,000.0000
                counter_s = "       {} Hz".format(counter_f) # 7 spaces padding
            elif counter_p < 100000:   # 900,000.0000
                counter_s = "      {} Hz".format(counter_f)  # 6 spaces padding
            elif counter_p < 1000000:  # 900,000.0000
                counter_s = "     {} Hz".format(counter_f)   # 5 spaces padding
            elif counter_p < 10000000: # 9,000,000.0000
                counter_s = "   {} Hz".format(counter_f)     # 3 spaces padding
            elif counter_p >= 10000000: # 10.000.000.0000
                counter_s = "  {} Hz".format(counter_f)      # 2 spaces padding
            else:
                counter_s = ""

            # draw a black filled box to clear the image
            draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

            # setup the 3 lines in memory
            draw.text((x, top +  1), str("{}".format(counter_s)), font=my_font, fill=255)
            draw.text((x, top + 12), 'sats: {}  gate: {}'.format(sat_nbr_s, gate_time_s), font=my_font, fill=255)
            draw.text((x, top + 23), 'min. left: {}'.format(time_left), font=my_font, fill=255)

            # display the image in memory on the screen
            disp.image(image)
            disp.display()

            time.sleep(1) # neo updates are coming every second, we don't need to be that quick


    except KeyboardInterrupt:
        print('\nTerminating')

    finally:
        disp.clear()
        disp.display()


if __name__ == '__main__':
    main()
