# This file is executed on every boot (including wake-boot from deepsleep)
import webrepl
import network
import time
import ntptime
import machine
import os
from Helpers.DateHelpers import UTCToET, TimeToString

# Configure Wifi
WIFI_SSID="YOUR_WIFI_SSID"
WIFI_WPA2_KEY="YOUR_WIFI_PASSWORD"

print("Setting radio mode to 'Station'")
wlan = network.WLAN(network.STA_IF)
print("Enabling radio")
wlan.active(True)
print("Waiting 1 second for interface to come up")
time.sleep(1) # Needed to give time for the radio to come up, otherwise the below line crashes the chip
print("Setting static IP on interface")
wlan.ifconfig(('YOUR_STATIC_IP','255.255.255.0','YOUR_GATEWAY_IP','YOUR_DNS_IP'))
print(f"Connecting to Wifi (SSID: '{WIFI_SSID})'...")
wlan.connect(WIFI_SSID, WIFI_WPA2_KEY)

# Wait maximum of 30 seconds
print("Waiting up to 30 seconds for wifi to connect before rebooting")
time_left = 30
while wlan.isconnected() == False and time_left > -1:
    time.sleep(1)
    time_left -= 1

if wlan.isconnected() == False:
    print("Unable to connect to WiFi, rebooting machine")
    machine.reset()
else:
    print("Wifi connected")
    
    # Install needed packages
    try:
        print("Attempting to import 'mcron' package")
        import mcron
    except ImportError:
        print("Unable to import 'mcron'. Attempting to pip install")
        import upip
        upip.install("micropython-mcron")

    # Start WebREPL
    
    # Check for config file
    try:
        print("Checking for WebREPL config file")
        os.stat('webrepl_cfg.py')
        print("WebREPL config file found")
    except OSError:
        print("WebREPL config file was not found, creating...")
        with open('webrepl_cfg.py', 'w') as config_file:
            config_file.write("PASS = 'YOUR_REPL_PASS'")     
    print("Starting WebREPL")
    webrepl.start()

    # Sync NTP Time
    print(f"Local time before synchronization: {TimeToString(time.localtime())}")
    ntptime.host='pool.ntp.org'
    ntptime.timeout=10
    ntptime.settime()
    print(f"GMT/UTC time after synchronization: {TimeToString(time.localtime())}")
    local_time = UTCToET()
    rtc = machine.RTC()
    # Conversion is needed between time formats from the 'utime' library vs 'machine.RTC'
    # Time.localtime format: (YYYY, MM, DD, HH, MM, SS, Day of week [Monday=0], Day of year)
    # RTC.datetime format:   (YYYY, MM, DD, Day of Week [Monday=0], HH, MM, SS, subseconds)
    rtc.datetime((local_time[0], local_time[1], local_time[2], local_time[6], local_time[3], local_time[4], local_time[5], 0))
    print(f"EST/EDT time after synchronization: {TimeToString(time.localtime())}")
    