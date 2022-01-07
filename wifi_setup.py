# The ESP8266 remembers the network details and automatically connects on boot.
# So you only need to call do_connect() once ever, or after erasing flash.
#
import network
import time
import gc


def getinput(prompt, default):
    s = input(prompt + " (" + default + ") :")
    if len(s) < 1:
        s = default
    return(s)


def do_connect():
    import wifi_cfg as cf
    
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        if not cf.if_ip == '0.0.0.0':
            sta_if.ifconfig((cf.if_ip, cf.if_subnet_mask, cf.if_dateway, cf.if_dns))

        sta_if.connect(cf.wifi_user, cf.wifi_pass)
        while not sta_if.isconnected():
            time.sleep_ms(50)
        print('network config: ', sta_if.ifconfig())
        print('deactivating AP: ', ap_if.ifconfig())
        ap_if.active(False)

    del sta_if
    del ap_if


def do_new_config():
    wifi_user = getinput('WiFi Username', 'mywifi')
    wifi_pass = getinput('WiFi Password', 'mypassword')
    if_ip = getinput('IP Address (0.0.0.0) for DHCP', '0.0.0.0')
    if_subnet_mask = getinput('Subnet Mask', '255.255.255.0')
    if_dateway = getinput('Gateway (0.0.0.0) for DHCP', '0.0.0.0')
    if_dns = getinput('DNS Server (0.0.0.0) for DHCP', '0.0.0.0')

    f = open('wifi_cfg.py', "w")
    f.write("wifi_user=\"%s\"\n" % (wifi_user))
    f.write("wifi_pass=\"%s\"\n" % (wifi_pass))
    f.write("if_ip=\"%s\"\n" % (if_ip))
    f.write("if_subnet_mask=\"%s\"\n" % (if_subnet_mask))
    f.write("if_dateway=\"%s\"\n" % (if_dateway))
    f.write("if_dns=\"%s\"\n" % (if_dns))
    f.close()
    print('Config written to wifi_cfg.py')


def main():
    print('Wifi configuration utility')
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.isconnected():
        close_conn = getinput('Wifi is already connected, disconnect (yes/no)?', 'no')
        if close_conn == 'yes':
            sta_if.active(False)

    no_config = False
    try:
        f = open('wifi_cfg.py', "r")
    except OSError:
        no_config = True
    else:
        f.close()

    if no_config:
        do_new_config()
    else:
        overwrite = getinput('Config exists, overwrite (yes/no)?', 'no')
        if overwrite == 'yes':
            do_new_config()

    wifisetup = getinput('Configure WiFi on chip now (yes/no)?', 'no')
    if not wifisetup == 'yes':
        gc.collect()
        return()

    do_connect()
    gc.collect()
    

main()