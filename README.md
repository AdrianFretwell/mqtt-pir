Home Automation Motion Sensor
=============================
<p align="center">
  <img src="https://raw.githubusercontent.com/AdrianFretwell/mqtt-pir/master/readmeimages/pir_bb.jpg" alt="Fritzing Circuit Image"/>
</p>

This implements a motion sensor as a simple SONOFF device, it implements robust
MQTT, behaves like a Tasmota switch and is compatible with Home Assistant.
The code is written in Micro Python.
You can find out more about these systems at the following websites:
[micropython.org](http://www.micropython.org).
[mqtt.org](https://mqtt.org).
[home-assistant.io](https://www.home-assistant.io).
[tasmota.github.io](https://tasmota.github.io/docs).
[espressif.com](https://www.espressif.com/en/products/socs/esp8266).

The program is broken up into several components because, collectively, they
are too big to fit into the memory on an esp8266 chip.  Each component can be
run individually and in the case of files like `wifi_setup.py` could be useful
in other projects.

The components are as follows:
- pir_installer.py -- Runs a step by step setup actually on the microcontroller,
  it requires restarts between the stages to free memory before finally writing
  a main.py that will run th eapplication automatically on boot.
- wifi_setup.py -- Configure WiFi settings - only required once.
- pir_cfg.py -- Generates a configuration file for the application
- pir_hass_setup.py -- Sends out MQTT discovery messages, that configure the
  device in the Home ssistant (HASS).
- pir.py -- The application.

The image above shows an esp8266 on a development board.  These boards make
prototyping easy.  The GPIO pins used for this application are:
- GPIO 12 - Heartbeat LED.
- GPIO 13 - Motion Detected LED.
- GPIO 14 - Input from motion sensor board, (RCWL-0516 microwave radar motion sensor).

GPIO 13 could also be used to drive a relay etc. and although set high when motion
is detected, it can also be set high with an MQTT message.

Once configured the application can be run at the REPL prompt.  Below is an example
showing also a typical debugging log output:
```
>>> import pir
>>> pir = pir.pir()
    PowerboxPIR1: [2022-01-07T03:43:52] Deactivating AP - ('0.0.0.0', '0.0.0.0', '0.0.0.0', '192.168.22.1')
    PowerboxPIR1: [2022-01-07T03:43:52] Network config - ('192.168.22.188', '255.255.255.0', '192.168.22.1', '192.168.22.1')
>>> pir.run()
    PowerboxPIR1: [2022-01-07T07:54:19] MQTT Chk Msg fail - OSError(103,)
    PowerboxPIR1: [2022-01-07T07:54:20]  - 'Wifi Disconnected'
    PowerboxPIR1: [2022-01-07T15:11:18] MQTT cmnd - 'debugoff'

```

MQTT oubound topics are:
- tele/<device name>/STATE
- tele/<device name>/HASS_STATE
- stat/<device name>/POWER
- stat/<device name>/RESULT
- stat/<device name>/SWITCH1T
- homeassistant/switch/<device name>_RL_1/config
- homeassistant/sensor/<device name>_status/config

MQTT inbound topics are:
- cmnd/<device name>/MP [`stop`, `debugon`, `debugoff`, `reboot`]
- cmnd/<device name>/POWER [`ON`, `OFF`]

Typical MQTT messages look like this:
```
STATE = {"Time":"2022-01-07T12:30:46","Uptime":"0T04:52:12","UptimeSec":17532,"MemFree":21056,"MemAlloc":16928,"Stack":2912,"Sleep":10,"MqttCount":2,"POWER":"OFF","Wifi":{"AP":1,"SSId":"mynet","MAC":"44:17:93:0F:F9:83","RSSI":48,"Signal":-76,"LinkCount":2,"Downtime":"0T00:00:14"}}
HASS_STATE = {"Version":"1.0.0.2(pir switch)","BuildDateTime":"2022-01-06T20:27:06","Module or Template":"Sonoff Basic","RestartReason":"Hard Reset","Uptime":"0T07:07:14","Hostname":"PowerboxPIR1-0FF983","IPAddress":"192.168.22.188","RSSI":"50","Signal (dBm)":"-75","WiFi LinkCount":2,"WiFi Downtime":"0T00:00:14","MqttCount":2}
MP = debugon
POWER = ON
RESULT = {"POWER":"ON"}
POWER = ON
SWITCH1T = {"TRIG":"SINGLE"}

```

Other useful software used in the development of this project are:
- MQTT Explorer - [mqtt-explorer.com](https://mqtt-explorer.com).
- Thonny - [thonny.org](https://thonny.org)
- esptool -[github.com/espressif/esptool](https://github.com/espressif/esptool)
- fritzing - [fritzing.org](https://fritzing.org/)
