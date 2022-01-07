import os
import network
import time
import ntptime
import ubinascii
import machine
import micropython
import gc
from umqtt.simple import MQTTClient


class pir:
    state_msg = "{\"Time\":\"%s\",\"Uptime\":\"%s\",\"UptimeSec\":%s,\"MemFree\":%s,\"MemAlloc\":%s,\"Stack\":%s,\"Sleep\":%s,\"MqttCount\":%s,\"POWER\":\"%s\",\"Wifi\":{\"AP\":1,\"SSId\":\"%s\",\"MAC\":\"%s\",\"RSSI\":%s,\"Signal\":%s,\"LinkCount\":%s,\"Downtime\":\"%s\"}}"
    hass_state_msg = "{\"Version\":\"%s\",\"BuildDateTime\":\"%s\",\"Module or Template\":\"Sonoff Basic\",\"RestartReason\":\"%s\",\"Uptime\":\"%s\",\"Hostname\":\"%s-%s\",\"IPAddress\":\"%s\",\"RSSI\":\"%s\",\"Signal (dBm)\":\"%s\",\"WiFi LinkCount\":%s,\"WiFi Downtime\":\"%s\",\"MqttCount\":%s}"
    import app_cfg as cf
    tim1 = machine.Timer(-1)
    tim2 = machine.Timer(-1)
    tim3 = machine.Timer(-1)
    sta_if = network.WLAN(network.STA_IF)


    def __init__(self):
        self.debug_f = True
        rstc = {0:'Power ON', 1:'Watchdog Reset', 2:'Hard Reset', 4:'Soft Reset', 5:'Deep Sleep Reset', 6:'Hard Reset'}
        self.reset_cause = rstc[machine.reset_cause()]
        del rstc
        mac = ubinascii.hexlify(self.sta_if.config('mac'))
        mqtt_mac = bytearray('00:00:00:00:00:00', 'ascii')
        j = 0
        for i in range(17):
            if mqtt_mac[i] == 58:
                continue
            mqtt_mac[i] = mac[j]
            if mac[j] > 96:
                mqtt_mac[i] = mac[j] - 32
            j += 1

        self.mqtt_mac = mqtt_mac.decode()
        
        self.mqtt_essid = self.sta_if.config('essid').encode()
        self.ipaddr = self.sta_if.ifconfig()[0].encode()
        self.deactivate_ap()
        self.wifi_conn_f = False
        self.mqtt_conn_f = False
        self.irh_1s_f = False
        self.irh_30s_f = False
        self.irh_5m_f = False
        self.reboot = False
        self.network_fail_c = 0
        self.wifi_link_c = 0
        self.mqtt_link_c = 0
        self.wifi_dwnt = 0
        self.wifi_dwnt_start = 0
        
        if self.sta_if.isconnected():
            self.log(self.sta_if.ifconfig(), 'Network config')
            self.wifi_conn_f = True
            self.wifi_link_c = 1
            try:
                ntptime.settime()
            except OSError as e:
                self.log(e, 'NTP Timeout')
                self.network_fail_c += 1
                
        
        self.mqtt_client = MQTTClient(self.cf.mqtt_client_id, self.cf.mqtt_server, self.cf.mqtt_port, self.cf.mqtt_user, self.cf.mqtt_pass)
        self.led_heartbeat = machine.Pin(12, machine.Pin.OUT)
        self.led_motion = machine.Pin(13, machine.Pin.OUT)
        self.led_motion.value(0)

        self.pir = machine.Pin(14, machine.Pin.IN)
        self.pir.irq(trigger=machine.Pin.IRQ_RISING, handler=self.handle_interrupt)

        self.mqtt_client.set_callback(self.sub_cb)
        self.ci = 1
        self.mt = 0
        self.pir_flag = False
        self.runable = True
        self.start = time.time()
        gc.collect()
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())


    def log(self, data, desc = ''):
        if self.debug_f:
            print("%s: [%s] %s - %r" % (self.cf.mqtt_name, self.time(), desc, data))


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
        if msg == 'ON':
            self.pir_flag = True
            self.mt = 0
        if msg == 'OFF':
            self.pir_flag = False
        if msg == 'debugon':
            self.debug_f = True
        if msg == 'debugoff':
            self.debug_f = False
        if msg == 'reboot':
            self.reboot = True


    def handle_interrupt(self, pin):
        self.pir_flag = True
        self.mt = 0


    def fmt_num(self, n):
        if n < 10:
            return('0'+str(n))
        return(str(n))


    def uptime(self, delta):
        d = delta // 86400
        h = (delta % 86400) // 3600
        m = ((delta % 86400) // 60) % 60
        s = (delta % 86400) % 60
        return(str(d)+"T"+self.fmt_num(h)+":"+self.fmt_num(m)+":"+self.fmt_num(s))


    def uptimesec(self):
        return(str(time.time() - self.start))


    def time(self, v = 0):
        if v == 0:
            t = time.localtime()
        else:
            t = time.localtime(v)
        return(str(t[0]) + "-" + self.fmt_num(t[1]) + "-" +self.fmt_num(t[2]) + "T" + self.fmt_num(t[3]) + ":" + self.fmt_num(t[4]) + ":" + self.fmt_num(t[5]))


    def publish_state(self, lp_sleep):
        pwr = 'OFF'
        if self.pir_flag:
            pwr = 'ON'
        self.mqtt_publish("tele/%s/STATE".encode() % (self.cf.mqtt_topic), self.state_msg.encode() % (self.time(), self.uptime(time.time() - self.start), self.uptimesec(), str(gc.mem_free()), str(gc.mem_alloc()), str(micropython.stack_use()), lp_sleep, str(self.mqtt_link_c), pwr, self.mqtt_essid, self.mqtt_mac, (self.sta_if.status('rssi') + 100) * 2, str(self.sta_if.status('rssi')), str(self.wifi_link_c), self.uptime(self.wifi_dwnt)))


    def publish_hass_state(self):
        st = os.stat('pir.py')
        self.mqtt_publish("tele/%s/HASS_STATE".encode() % (self.cf.mqtt_topic), self.hass_state_msg.encode() % (self.cf.version, self.time(st[7]), self.reset_cause, self.uptime(time.time() - self.start), self.cf.mqtt_name, self.cf.hass_id, self.ipaddr, str((self.sta_if.status('rssi') + 100) * 2), str(self.sta_if.status('rssi')), str(self.wifi_link_c), self.uptime(self.wifi_dwnt), str(self.mqtt_link_c)))


    def publish_lwt(self, status):
        self.mqtt_publish("tele/%s/LWT".encode() % (self.cf.mqtt_topic), status.encode())


    def publish_motion(self, status):
        self.mqtt_publish("stat/%s/POWER".encode() % (self.cf.mqtt_topic), status.encode())
        time.sleep_ms(100)
        self.mqtt_publish("stat/%s/RESULT".encode() % (self.cf.mqtt_topic), "{\"POWER\":\"%s\"}".encode() % (status))
        time.sleep_ms(100)
        self.mqtt_publish("stat/%s/SWITCH1T".encode() % (self.cf.mqtt_topic), b"{\"TRIG\":\"SINGLE\"}")


    def mqtt_publish(self, topic, msg):
        if self.wifi_chk_conn() and self.mqtt_conn_f:
            try:
                self.mqtt_client.publish(topic, msg)
            except OSError as e:
                self.log(e, 'MQTT Pub fail')
                self.mqtt_conn_f = False
        
        
    def mqtt_chk_msg(self):
        if self.wifi_chk_conn() and self.mqtt_conn_f:
            try:
                self.mqtt_client.check_msg()
            except OSError as e:
                self.log(e, 'MQTT Chk Msg fail')
                self.mqtt_conn_f = False
        
        
    def wifi_chk_conn(self):
        if self.wifi_conn_f:
            if self.sta_if.isconnected():
                return(True)
            else:
                self.wifi_conn_f = False
                self.network_fail_c += 1
                self.log('Wifi Disconnected')
                self.wifi_dwnt_start = time.time()
                return(False)
        else:
            if self.sta_if.isconnected():
                self.wifi_conn_f = True
                self.wifi_link_c += 1
                self.wifi_dwnt += (time.time() - self.wifi_dwnt_start)                
                return(True)
            else:
                return(False)


    def mqtt_connect(self):
        try:
            self.mqtt_client.connect()
        except OSError as e:
            self.log(e, 'MQTT Conn fail')
            self.mqtt_conn_f = False
            self.network_fail_c += 1
        else:
            self.mqtt_conn_f = True
            self.mqtt_link_c += 1
            self.network_fail_c = 0

        time.sleep_ms(100)
        if self.mqtt_conn_f:
            try:
                self.mqtt_client.subscribe(b"cmnd/" + self.cf.mqtt_topic + b"/MP")
            except OSError as e:
                self.log(e, 'MQTT Sub. fail')
                self.mqtt_conn_f = False
        time.sleep_ms(100)
        if self.mqtt_conn_f:
            try:
                self.mqtt_client.subscribe(b"cmnd/" + self.cf.mqtt_topic + b"/POWER")
            except OSError as e:
                self.log(e, 'MQTT Sub fail')
                self.mqtt_conn_f = False


    def mqtt_chk_conn(self):
        if self.mqtt_conn_f:
            try:
                self.mqtt_client.ping()
            except OSError as e:
                self.log(e, 'MQTT Conn fail')
                self.mqtt_conn_f = False
                self.network_fail_c += 1
            else:
                self.mqtt_conn_f = True
                self.network_fail_c = 0


    def cron_1s(self):
        self.irh_1s_f = False
        self.led_heartbeat.value(self.led_heartbeat.value() ^ 1)


    def cron_30s(self):
        self.irh_30s_f = False
        self.mqtt_chk_conn()
        if not self.mqtt_conn_f:
            if self.wifi_chk_conn():
                self.mqtt_connect()
        if self.network_fail_c > 20:
            self.log('Machine Reset', '>20 net. failures')
            machine.reset()
        
                
    def cron_5m(self):
        self.irh_5m_f = False
        self.publish_state('10')
        time.sleep_ms(100)
        self.publish_hass_state()
        time.sleep_ms(100)
        gc.collect()
        
        
    def run(self):
        self.tim1.init(period=1000, mode=machine.Timer.PERIODIC, callback=self.irh_1s)
        self.tim2.init(period=30000, mode=machine.Timer.PERIODIC, callback=self.irh_30s)
        self.tim3.init(period=300000, mode=machine.Timer.PERIODIC, callback=self.irh_5m)
        if self.wifi_chk_conn():
            self.mqtt_connect()
        self.publish_lwt('Online')
        time.sleep_ms(100)
        self.publish_state('10')
        time.sleep_ms(100)
        self.publish_hass_state()
        time.sleep_ms(100)
        while self.runable:
            self.mqtt_chk_msg()
            self.ci += 1
            if self.ci > 17280000:  #roll over approx every 2 days at 10 ms sleep
                self.ci = 1
                if self.wifi_chk_conn():
                    try:
                        ntptime.settime()
                    except OSError as e:
                        self.log(e, 'NTP Timeout')
            
            if self.pir_flag:
                if self.mt == 0:
                    self.led_motion.value(1)
                    self.publish_state('10')
                    time.sleep_ms(100)
                    self.publish_motion('ON')
                self.mt += 1
                if self.mt == 2000:
                    self.pir_flag = False
                    self.led_motion.value(0)
                    self.publish_state('10')
                    time.sleep_ms(100)
                    self.publish_motion('OFF')

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
        self.publish_lwt('Offline')
        time.sleep_ms(100)
        self.runable = True
        if self.reboot:
            machine.reset()

