try:
    import network
except ImportError:
    from unittest.mock import Mock
    network = Mock()
    import time
else:
    import time as time

import sys

from mylogger import Logger
logger = Logger.get_logger()


def stop_all_wifi():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)
    ap = network.WLAN(network.AP_IF)
    ap.active(False)


def start_ap(ssid='smartbox_control'):
    ap = network.WLAN(network.AP_IF)
    time.sleep(1)
    ap.active(True)
    ap.config(essid=ssid, authmode=network.AUTH_OPEN)
    logger.info('AP mode started')
    logger.info(ap.ifconfig())
    time.sleep(1)


def start_webrepl(password='smartbox'):
    logger.info('Staring webrepl')
    import webrepl
    webrepl.start(password='snabel')


def stop_wifi_start_webrepl():
    import entrymain
    o = entrymain.app_objects["controller"]
    o.display.stop()
    time.sleep(3)
    o.display.clear_screen()
    o.display.show_text('WEBREPL\nSTARTED')
    o.display.show()
    time.sleep(3)
    stop_all_wifi()
    start_ap()
    start_webrepl()


def get_ip():
    if 'esp' in sys.platform:
        network_type = network.STA_IF
        return network.WLAN(network_type).ifconfig()[0]
    else:
        import socket
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)


def wifi_connect(essid, password):
    connected = False
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.isconnected():
        logger.info('already connected to wifi, exiting')
        return True
    sta_if.active(False)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(essid, password)
        logger.info('connecting to network..., pause 3 sec')
        time.sleep(3)
        for i in range(1, 10):
            logger.info('attempt {}'.format(i))
            time.sleep(1)
            if sta_if.isconnected():
                connected = True
                break
        if not connected:
            sta_if.active(False)
    else:
        connected = True
    if connected:
        time.sleep(1)
        logger.info('network config:', sta_if.ifconfig())
    return connected
