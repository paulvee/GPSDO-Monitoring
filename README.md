# GPSDO-Monitoring
Monitoring, measuring and logging data from a high precision 10MHz GPS disciplined oscillator (GPSDO)

This section is currently under development.

The files I uploaded are test files that work, but are not completely done yet. 
Details are or will be in my Blog, also under development.  http://www.paulvdiyblogs.net/2020/10/monitoring-measuring-logging-gpsdo.html


Serial_gpsdo_mon.py 
is my standard logging script for the Lars report. It currently runs on my Model 2B (the classic) that uses the standard Serial UART. I need to modify this script to use the bit-banging library so I can use an additional serial UART on the RPi Zero-W.

mail_ocxo_log.py 
is the script that emails the log file just before mid-night to my local PC.

Serial_counter_mon3.py 
is the monitoring script for Yannick's counter. It runs already on the Pi Zero-W, but uses the switched back UART.

Serial_counter_monbb.py 
is the bit-banging version that uses one of the GPIO ports to receive the serial data from the counter.

mail_counter_log.py 
is the scipt that emails the counter log file to my email account.

gps.py 
is a test script for monitoring the NEO that uses the standard (switched back) serial UART.

Serial_gps_bb.py 
is the NEO NMEA sentence monitoring using the bit-banging library. It uses a GPIO pin to listen to the device.

mail_nmea_log.py 
is the mail program that sends me the logs to my account.
