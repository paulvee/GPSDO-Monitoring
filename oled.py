#!/usr/bin/python3.7
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
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

sat_nbr = 12
dac = 12345
mhz = 10000000.1234


disp_mhz = "{:,.4f}".format(mhz)
print(disp_mhz)


disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)
disp.begin()
disp.clear()
disp.display()
print(disp.width, disp.height) # 128 x 32

image = Image.new('1', (disp.width, disp.height))
draw = ImageDraw.Draw(image)
print('[Press CTRL + C to end the script!]')

#draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=255)
#disp.image(image)
#disp.display()
#time.sleep(2)
#disp.clear()
#draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

try:
    while True:
        draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

        sat_nbr += 1
        dac += 10
        mhz += 1.001

        padding = 0 # first line
        shape_width = 20
        top = padding
        bottom = disp.height - padding
        x = padding

        '''
        print('Drawing a ellipse')
        x = padding

        draw.ellipse((x, top , x + shape_width, bottom),
        outline=255, fill=0)
        time.sleep(0.2)

        print('Drawing a rectangle')
        x += shape_width + padding
        draw.rectangle((x, top, x + shape_width, bottom),
        outline=255, fill=0)
        time.sleep(0.2)

        print('Drawing a triangle')
        x += shape_width + padding
        draw.polygon([(x, bottom), (x + shape_width / 2, top),
        (x + shape_width, bottom)], outline=255, fill=0)
        time.sleep(0.2)

        print('Drawing two lines')
        x += shape_width + padding
        draw.line((x, bottom, x + shape_width, top), fill=255)
        draw.line((x, top, x + shape_width, bottom), fill=255)
        time.sleep(0.2)
        '''

        print('Printing text')
        #x += shape_width + padding
        x = 0   # first position
        my_font = ImageFont.load_default() # Load default font.
        draw.text((x, top), str("{:,.4f}".format(mhz))+' MHz', font=my_font, fill=255)
        draw.text((x, top + 11), 'sats: '+str(sat_nbr), font=my_font, fill=255)
        draw.text((x, top + 22), 'DAC: '+str(dac), font=my_font, fill=255)
        time.sleep(0.5)

        disp.image(image)
        disp.display()
        time.sleep(1)

#        disp.clear()
#        disp.display()

except KeyboardInterrupt:
    print('\nScript end!')

finally:
    disp.clear()
    disp.display()



def main():
    pass

if __name__ == '__main__':
    main()
