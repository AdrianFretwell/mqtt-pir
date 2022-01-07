# The ESP8266 remembers the network details and automatically connects on boot.
# So you only need to call do_connect() once ever, or after erasing flash.
#import wifi_setup
#wifi_setup.do_connect()
import time

# Where a program runs on power up you need a delay (four seconds has been suggested) before doing anything.
# I guess the underlying RTOS of the ESP8266 takes a little time to start up.
time.sleep(4)


