"""relay_control: project for controlling fan using an MCU"""

__license__ = "MIT"
__version__ = "0.0.3"
__email__ = "daniel@engvalls.eu"

import sys

from mymem import get_mem

try:
    import machine

except ImportError:
    import asyncio
    from unittest.mock import Mock
    WDT = Mock()
    machine = Mock()
    blocking_count_clicks = Mock(return_value=0)
    wifi_connect = Mock(return_value=True)
    stop_all_wifi = Mock()
    webrepl = Mock()
    from asyncio.exceptions import CancelledError
else:
    from mywifi import wifi_connect, start_ap, stop_all_wifi
    import uasyncio as asyncio
    from uasyncio import CancelledError
    from mybutton import blocking_count_clicks
    import webrepl

import gc
import time
import myconfig
from myweb import start_simple_web
from mywifi import get_ip

from mybutton import MyButton
from mypir import MyPir
from mysmoke import MySmoke
from mycontroller import MyController
from mytemp import MyTemp
from mydisplay import MyDisplay
from mywatchdog import WDT
from mywifi import start_ap

DEBUG = False

from mylogger import Logger
logger = Logger.get_logger()

app_objects = {}


WEBREPL_PASSWORD = 'relay'
CONFIG = {'essid': 'MYWIFI',
                  'password': 'MYPASSWORD',
                  'mqtt_enabled': 'false',
                  'mqtt_broker': '127.0.0.1',
                  'mqtt_topic': '/fan_control/temp',
                  'mqtt_username': 'username',
                  'mqtt_password': 'password',
                  'trigger_temp': '28',
                  'override_secs': '10'}

PIN_BUTTON = 10  # PULL_UP
PIN_OLED_SDA = 4
PIN_OLED_SCL = 14
PIN_RELAY = 5
PIN_PIR = 13
PIN_DHT22 = 16


def async_exception_handler(loop, context):
    logger.info(f'async exception handler: {context}')
    if 'esp' in sys.platform:
        print('async exception handler restarting, wait 5 sec')
        time.sleep(5)
        machine.reset()


def web_index(req, resp, **kwargs):
    yield from resp.awrite('foo')
    gc.collect()


async def wait_forever():
    while True:
        await asyncio.sleep(3)


async def start_controller(config):
    try:
        loop = asyncio.get_event_loop()
        wdt = WDT(timeout=30)
        temp_obj = MyTemp(pin=PIN_DHT22)
        smoke_obj = MySmoke()
        motion_obj = MyPir(PIN_PIR, event_loop=loop)
        button_obj = MyButton(PIN_BUTTON, event_loop=loop)
        display_obj = MyDisplay(sda_pin=PIN_OLED_SDA, scl_pin=PIN_OLED_SCL)
        gc.collect()
        loop.set_exception_handler(async_exception_handler)
        controller_object = MyController(button=button_obj, temp=temp_obj, motion=motion_obj, smoke=smoke_obj, display=display_obj, config=config, wdt=wdt, debug=DEBUG, event_loop=loop, sleep_interval=2000)
        global app_objects
        app_objects['controller'] = controller_object
        r = asyncio.create_task(controller_object.start())
        start_simple_web()
        try:
            await r
        except Exception as e:
            logger.info(f'{e.__class__}, {e.args}')
            await wait_forever()
    except CancelledError:
        print(f'Ending processes')


def start():
    logger.info('starting')
    logger.info(f'mem_free: {get_mem()}')
    logger.info(f'IP: {get_ip()}')
    gc.collect()
    # check initially how many click
    clicks = blocking_count_clicks(button_pin=PIN_BUTTON, timeout=5)
    if clicks == 1:
        print('enable AP wifi and webrepl')
        # TODO: Add AP WIFI and webrepl
    # stop_all_wifi()
    c = CONFIG
    if not c:
        logger.info('Create a config.json file')
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    if clicks == 2:
        print('starting webrepl using password {}'.format(WEBREPL_PASSWORD))
        webrepl.start_foreground()
    else:
        config = myconfig.get_config(input_default_config=c)
        del c
        gc.collect()
        asyncio.run(start_controller(config))
        del config
        gc.collect()



if __name__ == '__main__':
    start()
