import network
import time
import ubinascii
import machine
import micropython
import ujson
import gc
from umqtt.simple import MQTTClient


class hass_setup:
    msg_hass_config_switch = "{\"name\":\"%s\",\"stat_t\":\"tele/%s/STATE\",\"avty_t\":\"tele/%s/LWT\",\"pl_avail\":\"Online\",\"pl_not_avail\":\"Offline\",\"cmd_t\":\"cmnd/%s/POWER\",\"pl_off\":\"OFF\",\"pl_on\":\"ON\",\"val_tpl\":\"{{value_json.POWER}}\",\"uniq_id\":\"%s_RL_1\",\"dev\":{\"ids\":[\"%s\"]}}"
    msg_hass_config_sensor = "{\"name\":\"%s status\",\"stat_t\":\"tele/%s/HASS_STATE\",\"avty_t\":\"tele/%s/LWT\",\"pl_avail\":\"Online\",\"pl_not_avail\":\"Offline\",\"json_attr_t\":\"tele/%s/HASS_STATE\",\"unit_of_meas\":\"%%\",\"val_tpl\":\"{{value_json['RSSI']}}\",\"ic\":\"mdi:information-outline\",\"uniq_id\":\"%s_status\",\"dev\":{\"ids\":[\"%s\"],\"name\":\"%s\",\"mdl\":\"Sonoff Basic\",\"sw\":\"%s\",\"mf\":\"%s\"}}"

    tim1 = machine.Timer(-1)
    tim2 = machine.Timer(-1)
    tim3 = machine.Timer(-1)
    sta_if = network.WLAN(network.STA_IF)


    def __init__(self):
        self.debug_f = True
        config = {}
        mac = ubinascii.hexlify(self.sta_if.config('mac'))
        self.mqtt_mac = bytearray('00:00:00:00:00:00', 'ascii')
        j = 0
        for i in range(17):
            if self.mqtt_mac[i] == 58:
                continue
            self.mqtt_mac[i] = mac[j]
            if mac[j] > 96:
                self.mqtt_mac[i] = mac[j] - 32
            j += 1

        f = open('app_cfg.json', "r")
        config = ujson.load(f)
        self.log('loaded from app_cfg.json', 'Config')

        self.mqtt_client_id = config['mqtt_client_id'].encode()
        self.mqtt_name = config['mqtt_name'].encode()
        self.mqtt_topic = config['mqtt_topic'].encode()
        self.hass_id = config['hass_id'].encode()
        self.mqtt_user = config['mqtt_user']
        self.mqtt_pass = config['mqtt_pass']
        self.mqtt_server = config['mqtt_server']
        self.mqtt_port = config['mqtt_port']
        self.version = config['version']
        self.vendor = config['vendor']
        del config
        gc.collect()
        
        self.mqtt_essid = self.sta_if.config('essid').encode()
        self.deactivate_ap()
        self.wifi_conn_f = False
        self.mqtt_conn_f = False
        self.irh_1s_f = False
        self.irh_30s_f = False
        self.irh_5m_f = False
        self.hass_published = False
        self.network_fail_c = 0
        
        if self.sta_if.isconnected():
            self.log(self.sta_if.ifconfig(), 'Network config')
            self.wifi_conn_f = True
            
        
        self.mqtt_client = MQTTClient(self.mqtt_client_id, self.mqtt_server, self.mqtt_port, self.mqtt_user, self.mqtt_pass)
        self.led_hb = machine.Pin(5, machine.Pin.OUT)

        self.mqtt_client.set_callback(self.sub_cb)
        self.ci = 1
        self.rec_c = 0
        self.runable = True
        self.start = time.time()
        gc.collect()


    def log(self, data, desc = ''):
        if self.debug_f:
            print("PowerBoxPIR1: [%s] %s - %r" % (self.time(), desc, data))


    def irh_1s(self,t):
        self.irh_1s_f = True


    def irh_30s(self,t):
        self.irh_30s_f = True


    def irh_5m(self,t):
        self.irh_5m_f = True


    def deactivate_ap(self):
        ap_if = network.WLAN(network.AP_IF)
        self.log(ap_if.ifconfig(), 'Deactivating AP')
        ap_if.active(False)


    def sub_cb(self, topic, msg):
        msg = msg.decode()
        self.log(str(msg), 'MQTT cmnd')
        if msg == 'stop':
            self.runable = False
        if msg == 'debugon':
            self.debug_f = True
        if msg == 'debugoff':
            self.debug_f = False


    def fmt_num(self, n):
        if n < 10:
            return('0'+str(n))
        return(str(n))


    def time(self):
        t = time.localtime()
        return(str(t[0]) + "-" + self.fmt_num(t[1]) + "-" +self.fmt_num(t[2]) + "T" + self.fmt_num(t[3]) + ":" + self.fmt_num(t[4]) + ":" + self.fmt_num(t[5]))


    def publish_hass_config(self):
        self.mqtt_publish("homeassistant/switch/%s_RL_1/config".encode() % (self.hass_id), self.msg_hass_config_switch.encode() % (self.mqtt_name, self.mqtt_topic, self.mqtt_topic, self.mqtt_topic, self.hass_id, self.hass_id))
        time.sleep_ms(100)
        self.mqtt_publish("homeassistant/sensor/%s_status/config".encode() % (self.hass_id), self.msg_hass_config_sensor.encode() % (self.mqtt_name, self.mqtt_topic, self.mqtt_topic, self.mqtt_topic, self.hass_id, self.hass_id, self.mqtt_name, self.version, self.vendor))
        time.sleep_ms(100)
        self.log('Configuration published', 'HASS')
        self.hass_published = True
        self.runable = False

    def mqtt_publish(self, topic, msg):
        if self.wifi_chk_conn() and self.mqtt_conn_f:
            try:
                self.mqtt_client.publish(topic, msg)
            except OSError as e:
                self.log(e, 'MQTT Publish fail')
                self.mqtt_conn_f = False
        
        
    def mqtt_chk_msg(self):
        if self.wifi_chk_conn() and self.mqtt_conn_f:
            try:
                self.mqtt_client.check_msg()
            except OSError as e:
                self.log(e, 'MQTT Check Message fail')
                self.mqtt_conn_f = False
        
        
    def wifi_chk_conn(self):
        if self.wifi_conn_f:
            if self.sta_if.isconnected():
                return(True)
            else:
                self.wifi_conn_f = False
                self.network_fail_c += 1
                self.log('Wifi Disconnected')
                return(False)
        else:
            if self.sta_if.isconnected():
                self.wifi_conn_f = True
                self.rec_c += 1
                return(True)
            else:
                return(False)


    def mqtt_connect(self):
        try:
            self.mqtt_client.connect()
        except OSError as e:
            self.log(e, 'MQTT Connect fail')
            self.mqtt_conn_f = False
            self.network_fail_c += 1
        else:
            self.mqtt_conn_f = True
            self.network_fail_c = 0

        time.sleep_ms(100)
        if self.mqtt_conn_f:
            try:
                self.mqtt_client.subscribe(b"cmnd/" + self.mqtt_topic + b"/MP")
            except OSError as e:
                self.log(e, 'MQTT Subscribe fail')
                self.mqtt_conn_f = False
        time.sleep_ms(100)
        if self.mqtt_conn_f:
            try:
                self.mqtt_client.subscribe(b"cmnd/" + self.mqtt_topic + b"/POWER")
            except OSError as e:
                self.log(e, 'MQTT Subscribe fail')
                self.mqtt_conn_f = False


    def mqtt_chk_conn(self):
        if self.mqtt_conn_f:
            try:
                self.mqtt_client.ping()
            except OSError as e:
                self.log(e, 'MQTT Connection fail')
                self.mqtt_conn_f = False
                self.network_fail_c += 1
            else:
                self.mqtt_conn_f = True
                self.network_fail_c = 0

    def cron_1s(self):
        self.irh_1s_f = False
        self.led_hb.value(self.led_hb.value() ^ 1)


    def cron_30s(self):
        self.irh_30s_f = False
        self.mqtt_chk_conn()
        if not self.mqtt_conn_f:
            if self.wifi_chk_conn():
                self.mqtt_connect()
        if self.network_fail_c > 20:
            self.log('Machine Reset', 'Repeated network failure')
            machine.reset()
        self.publish_hass_config()    
        
 
    def cron_5m(self):
        gc.collect()

            
    def run(self):
        self.tim1.init(period=1000, mode=machine.Timer.PERIODIC, callback=self.irh_1s)
        self.tim2.init(period=30000, mode=machine.Timer.PERIODIC, callback=self.irh_30s)
        self.tim3.init(period=300000, mode=machine.Timer.PERIODIC, callback=self.irh_5m)
        if self.wifi_chk_conn():
            self.mqtt_connect()
        self.publish_hass_config()    
        while self.runable:
            self.mqtt_chk_msg()
            self.ci += 1
            if self.ci > 17280000:  #roll over approx every 2 days at 10 ms sleep
                self.ci = 1
            
            if self.irh_1s_f:
                self.cron_1s()
            if self.irh_30s_f:
                self.cron_30s()
            if self.irh_5m_f:
                self.cron_5m()

            time.sleep_ms(10)
            
        self.tim1.deinit()
        self.tim2.deinit()
        self.tim3.deinit()
        if self.wifi_chk_conn():
            self.mqtt_chk_msg()
        if self.wifi_chk_conn():
            try:
                self.mqtt_client.disconnect()
            except OSError as e:
                self.log(e, 'MQTT Disconnect fail')
                
        self.runable = True
        