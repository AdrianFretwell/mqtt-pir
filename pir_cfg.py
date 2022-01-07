import network
import ubinascii
import machine
import gc

def getinput(prompt, default):
    s = input(prompt + " (" + default + ") :")
    if len(s) < 1:
        s = default
    return(s)

def main():
    print('SwitchPIR configuration utility')
    mac = ubinascii.hexlify(network.WLAN(network.STA_IF).config('mac'))
    hass_id = bytearray('000000', 'ascii')
    for i in range(6):
        hass_id[i] = mac[i+6]
        if mac[i+6] > 96:
            hass_id[i] = mac[i+6] - 32

    config_exists = True
    try:
        f = open('app_cfg.py', "r")
    except OSError:
        config_exists = False
    else:
        f.close()

    overwrite = 'no'
    if config_exists:
        overwrite = getinput('Config exists, overwrite (yes/no)?', overwrite)
        if not overwrite == 'yes':
            gc.collect()
            return()

    mqtt_client_id = getinput('MQTT Client Id', ubinascii.hexlify(machine.unique_id()).decode())
    mqtt_name = getinput('MQTT Name', 'SwitchPIR1')
    mqtt_topic = getinput('MQTT Topic', 'switch-motion-sensor-1')
    hass_id = getinput('HASS Id', hass_id.decode())
    mqtt_user = getinput('MQTT User', 'mymqtt')
    mqtt_pass = getinput('MQTT Password', 'mypassword')
    mqtt_server = getinput('MQTT Server', '192.168.6.52')
    mqtt_port = getinput('MQTT Port', '1883')
    version = getinput('Software version', '1.0.0.2(pir switch)')
    vendor = getinput('Vendor', 'A2 Engineering Services')

    f = open('app_cfg.py', "w")
    f.write("mqtt_client_id=\"%s\"\n" % (mqtt_client_id))
    f.write("mqtt_name=\"%s\"\n" % (mqtt_name))
    f.write("mqtt_topic=\"%s\"\n" % (mqtt_topic))
    f.write("hass_id=\"%s\"\n" % (hass_id))
    f.write("mqtt_user=\"%s\"\n" % (mqtt_user))
    f.write("mqtt_pass=\"%s\"\n" % (mqtt_pass))
    f.write("mqtt_server=\"%s\"\n" % (mqtt_server))
    f.write("mqtt_port=%s\n" % (mqtt_port))
    f.write("version=\"%s\"\n" % (version))
    f.write("vendor=\"%s\"\n" % (vendor))
    f.close()
    print('Config written to app_cfg.py')
    gc.collect()
    

main()
