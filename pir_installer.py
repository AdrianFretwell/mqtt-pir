# This installer file attempts to set up the pir program on your ESP8266.
#
import time
import machine

def getinput(prompt, default):
    s = input(prompt + " (" + default + ") :")
    if len(s) < 1:
        s = default
    return(s)


def write_stage(stage):
    f = open('installer.stage', "w")
    f.write(str(stage))
    f.close()
    print('Installer stage %d saved.' % (stage))


def write_main():
    main_str = 'import time\n\ntime.sleep(4)\n'
    main_str = 'import time\n\ntime.sleep(4)\nimport pir\npir = pir.pir()\npir.run()\n'

    f = open('main.py', "w")
    f.write(main_str)
    f.close()
    print('New main.py written')
    time.sleep_ms(100)


def restart_msg():
    print('Please restart your device and run the installer again')
    print('If you are using Thonny CTRL-D should do it.')
    time.sleep_ms(200)

def main():
    print('PIR installer utility')
    ci = 'yes/no'
    while not ci == 'yes':
        ci = getinput('Ready to contine with installer?', ci)
        if ci == 'no':
            return
        
    stage = -1
    try:
        f = open('installer.stage', "r")
    except OSError:
        stage = 0

    if stage == -1:
        stage_s = f.read()
        f.close()
        try:
            stage = int(stage_s)
        except ValueError:
            stage = 0

    print('Installer Stage: %d' % (stage))
    if stage == 0:
        import wifi_setup
        write_stage(1)
        restart_msg()
        
    if stage == 1:
        import upip
        upip.install('umqtt.simple')
        write_stage(2)
        restart_msg()

    if stage == 2:
        import pir_cfg
        write_stage(3)
        restart_msg()

    if stage == 3:
        import pir_hass_setup
        pirsetup = pir_hass_setup.hass_setup()
        pirsetup.run()
        write_stage(4)
        write_main()
        print('Please restart your device the PIR program should now run automatically.')
        print('The program can be stopped by sending an MQTT message to cmnd/<your device topic name>/MP with the raw value \"stop\"')
        time.sleep_ms(200)

    
main()