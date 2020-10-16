#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:        mail_nmea_log.py
# Purpose:
#
# Author:      paulv
#
# Created:     13-03-2020
# Copyright:   (c) paulv 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
import re
import subprocess
import sys, traceback
import email
from time import time, sleep, gmtime, strftime, localtime
import zipfile

VERSION="1.1" #  added support for a RAM disk
DEBUG = False

# here is where we store the files
log_file = "/mnt/ramdisk/nmea.log"
zip_file = "/mnt/ramdisk/nmea.zip"
# target email account
mail_address = "pw.versteeg@gmail.com"


def mail_err_log():
    '''
    Just before mid-night has been found by cron, this function emails the daily
    logs.
    '''
    try:
        print("zip the file")
        os.chdir('/mnt/ramdisk')
        zipfile.ZipFile('nmea.zip', mode='w').write('nmea.log', compress_type=zipfile.ZIP_DEFLATED)
    except Exception as e:
        print("*** Exception {}".format(e))

    try:
        if os.path.isfile(log_file):
            # if the file is there...
            # send it out as an attachement
            cmd = 'mpack -s "Bliley NMEA log file" {} {}'.format(zip_file, mail_address)
            print("mail_nmea_log cmd : {}".format(cmd))
            subprocess.call([cmd], shell=True)

    except Exception as e:
        print("error", "Unexpected Exception in mail_counter_log() {0}".format(e))
        return



def main():
    print("Mail Bliley NMEA logs: log Version {}".format(VERSION))
    mail_err_log()

if __name__ == '__main__':
    main()
