import random

try:
    from machine import Pin
except ImportError:
    from unittest.mock import Mock
    Pin = Mock()
    import asyncio
else:
    import time
    import uasyncio as asyncio
from mymqtt import publish
from mylogger import Logger
import gc
import mywifi

logger = Logger.get_logger()


def randrange(start, stop=None):
    if stop is None:
        stop = start
        start = 0
    upper = stop - start
    bits = 0
    pwr2 = 1
    while upper > pwr2:
        pwr2 <<= 1
        bits += 1
    while True:
        r = random.getrandbits(bits)
        if r < upper:
            break
    return r + start


def randint(start, stop):
    return randrange(start, stop + 1)


class MyController:
    def __init__(self,
                 relay_pin=5,
                 button=None,
                 temp=None,
                 motion=None,
                 smoke=None,
                 display=None,
                 event_loop=None,
                 config=None,
                 wdt=None,
                 sleep_interval=0.5,
                 debug=False):
        logger.info('Starting MyRelay')
        logger.info(f'current config {config}')
        self.event_loop = event_loop
        self.debug = debug
        self.sleep_interval = sleep_interval
        self.wdt = wdt
        self.relay = Pin(relay_pin, Pin.OUT)
        self.button = button
        self.motion = motion
        self.smoke = smoke
        self.display = display
        self.state = False
        self.mqtt_enabled = config.get('mqtt_enabled', False)
        self.mqtt_broker = config.get('mqtt_broker', None)
        self.mqtt_topic = config.get('mqtt_topic')
        self.mqtt_username = config.get('mqtt_username', None)
        self.mqtt_password = config.get('mqtt_password', None)
        self.trigger_temp = int(config.get('trigger_temp', 30))
        self.override_secs = int(config.get('override_secs', 60))
        self.last_override = 0
        self.temp = temp
        self.humid = temp
        self.last_major_reading = {'temp': 0, 'humid': 0, 'smoke': 0, 'motion': 0}
        self.sensor_thresholds = {'temp': 0.5, 'humid': 1, 'smoke': 1, 'motion': 0.1}
        if self.display:
            display.upsert_screen('info', f'Daniels\nSmartBox\nIP: {mywifi.get_ip()}')

    async def start(self):
        for item in ('temp', 'button', 'motion', 'smoke', 'display'):
            instance = getattr(self, item, None)
            if instance:
                asyncio.create_task(instance.start())
        if self.mqtt_enabled:
            logger.info('Publishing MQTT start message')
            print(f'mem_free: {gc.mem_free()}')
            self.publish_mqtt('status', 'on')
        if self.button and self.display:
            self.button.add_event(1, self.display.switch_to_next_screen, [], {})
            self.button.add_event(2, self.switch_state, [], {})
        if self.motion.read_motion():
            self.display.reset_screen_saver()
        await asyncio.create_task(self.check_changes(sleep_time=self.sleep_interval))

    def switch_state(self, state=None):
        if state is None:
            self.state = not self.state
        else:
            self.state = state
        logger.info(f'changing state to {self.state}')
        self.relay.value(self.state)

    def pause_temp_check(self):
        logger.info('update last override')
        self.last_override = time.time()

    @property
    def in_pause_mode(self):
        return self.last_override > 0 and time.time() <= self.last_override + self.override_secs

    async def check_changes(self, sleep_time=0.5, button_time_secs=1):
        while True:
            if self.debug:
                logger.info('Polling..')
                if randint(0, 20) >= 19:
                    raise RuntimeError('provoked error')
            await asyncio.sleep(1)
            for item in ('temp', 'humid', 'smoke', 'motion'):
                if getattr(self, item):
                    await self.mqtt_sensor_update(item)
            if self.wdt:
                if self.debug:
                    logger.info('Calm watchdog down, all okay')
                self.wdt.feed()
            gc.collect()
            print(f'mem_free: {gc.mem_free()}')
            gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

    def publish_mqtt(self, item, data):
        if self.mqtt_enabled:
            # publish MQTT if enabled
            logger.info(f'publishing {item}: {data}')
            publish('smart_box_client',
                    self.mqtt_broker,
                    f'{self.mqtt_topic}/{item}',
                    data,
                    self.mqtt_username,
                    self.mqtt_password)

    async def mqtt_sensor_update(self, item):
        current_value = getattr(getattr(self, item), f'read_{item}')()
        logger.info(f'{item}: {current_value}')
        if abs(current_value - self.last_major_reading[item]) >= self.sensor_thresholds[item]:
            self.last_major_reading[item] = current_value
            self.publish_mqtt(item, current_value)
            if self.display:
                self.display.upsert_screen(item, f'{item}: {current_value}')
        del current_value
        gc.collect()
