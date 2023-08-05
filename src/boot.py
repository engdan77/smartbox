import network
import time
sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    sta_if.connect('EDOWIFI', 'FEDCBAAAAA')
    while not sta_if.isconnected():
        time.sleep(1)
        print('Trying again...')
        pass
print('network config:', sta_if.ifconfig())
