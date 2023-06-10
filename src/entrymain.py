"""relay_control: project for controlling fan using an MCU"""

__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "daniel@engvalls.eu"

try:
    import machine

except ImportError:
    import asyncio
    from unittest.mock import Mock
    WDT = Mock()
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
import myconfig
from myweb import naw

from mybutton import MyButton
from myrelay import MyRelay
from mytemp import MyTemp
from mywatchdog import WDT
from mywifi import stop_all_wifi, start_ap
from mylogger import Logger

logger = Logger.get_logger()

# import mypicoweb
# from microdot_asyncio import Microdot

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

# app = Microdot()


# @app.route('/')
# async def hello(request):
#     return 'Hello, world!'

async def wait_forever():
    while True:
        await asyncio.sleep(3)


async def start_relay_control(config):
    wdt = WDT(timeout=30)
    temp_obj = MyTemp(pin=PIN_DHT22)
    button_obj = MyButton()
    # relay_task = MyRelay(button=button_obj, temp=temp_obj, config=config, wdt=wdt, debug=True, sleep_interval=2000).start()
    # web_task = asyncio.create_task(app.start_server(port=5050))

    # app = mypicoweb.MyPicoWeb(__name__, temp_obj=temp_obj, button_obj=button_obj, relay_obj=relay_obj)
    # app.add_url_rule('/save', web_save)
    # app.add_url_rule('/status', web_status)
    # app.add_url_rule('/getconfig', web_getconfig)
    # app.add_url_rule('/jquery.min.js', web_jquery)
    # app.add_url_rule('/', web_index)

    # async def main(_eth):
    #     logger_task = asyncio.create_task(log_temperature())
    #     server_task = asyncio.create_task(server.start_server(_eth.ifconfig()[0],port=80))
    #     await asyncio.gather(logger_task, server_task)

    gc.collect()
    # async_temp_updates = asyncio.create_task(update_temp(temp_obj))
    # app.run(port=5050)
    try:
        # requires more memory
        # results = await asyncio.gather(web_task, relay_task, return_exceptions=True)
        relay_task = MyRelay(button=button_obj, temp=temp_obj, config=config, wdt=wdt, debug=True,
                             sleep_interval=2000)
        asyncio.create_task(relay_task.start())
        asyncio.create_task(naw.run())
        await wait_forever()
    except CancelledError:
        print(f'Ending processes')


def start():
    logger.info('starting')
    # check initially how many click
    clicks = blocking_count_clicks(button_pin=PIN_BUTTON, timeout=5)
    if clicks == 1:
        print('enable AP wifi and webrepl')
        # TODO: Add AP WIFI and webrepl
    stop_all_wifi()
    c = CONFIG
    wifi_connected = wifi_connect(c['essid'], c['password'])
    if not wifi_connected:
        start_ap()
    if clicks == 2:
        print('starting webrepl using password {}'.format(WEBREPL_PASSWORD))
        webrepl.start_foreground()
    else:
        config = myconfig.get_config()
        asyncio.run(start_relay_control(config))
        del c
        gc.collect()


if __name__ == '__main__':
    start()
