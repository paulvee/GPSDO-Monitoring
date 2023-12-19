# GPSDO-Monitoring
Monitoring, measuring and logging data from a high precision 10MHz GPS disciplined oscillator (GPSDO)

This project is no longer in use by me, but have a look for inspiration.

I am still using an RPi to monitor the output of a script that is used in the GPSDO. This script outputs a line of data every second. The TxD pin of the Nano that is used in the GPSDO is brought out and is monitored by an RPi. The RPi runs two scipts, one to capture the serial output, and a second script that runs at mid-night, compresses the log file and sends me an e-mail with the collected results. I then use Excel to plot the data in graphs that gives me an idea of the stability of the GPSDO. I use the same scripts on another RPi to collect the data from my Reciprocal Counter, that also uses an GPSDO inside as the master reference clock.
Here are the three scipts for the RPi:

  - ser_mon_gpsdo.py  : this collects the serial pin RxD data
  
  - ser_mon_gpsdo.service : this systemd script installs the Python script at boot time
  
  - mail_gpsdo_log.py : this is the e-mail script that is activated by cron at mid-night.
  

The files I uploaded are files that work, but may still undergo changes. During this process, I will overwrite the files with a newer version, and will NOT keep the old ones here.

Details are or will be in my Blog.  http://www.paulvdiyblogs.net/2020/10/monitoring-measuring-logging-gpsdo.html

Versions of the pdf diagrams I am now working from are called V2. Look at the Blog for more details.

Note that all these files are bound to change!
