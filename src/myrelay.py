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


class MyRelay:
    def __init__(self,
                 relay_pin=12,
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
        self.mqtt_topic = config.get('mqtt_topic').encode()
        self.mqtt_username = config.get('mqtt_username', None)
        self.mqtt_password = config.get('mqtt_password', None)
        self.trigger_temp = int(config.get('trigger_temp', 30))
        self.override_secs = int(config.get('override_secs', 60))
        self.last_override = 0
        self.temp = temp
        self.last_major_temp = 0
        self.minor_change = 0.5
        if self.display:
            display.show_text('Starting')

    async def start(self):
        if self.temp:
            asyncio.create_task(self.temp.start())
        if self.button:
            asyncio.create_task(self.button.start())
        if self.motion:
            asyncio.create_task(self.motion.start())
        if self.smoke:
            asyncio.create_task(self.smoke.start())
        if self.mqtt_enabled:
            # publish MQTT if enabled
            logger.info('Publishing MQTT start message')
            publish('relay_control_client',
                    self.mqtt_broker,
                    '/notification/message',
                    'relay_control_started',
                    self.mqtt_username,
                    self.mqtt_password)
            logger.info('Completed publishing start message')
        await asyncio.create_task(self.check_changes(sleep_time=self.sleep_interval))

    @property
    def on(self):
        return self.state

    @property
    def state_text(self):
        return 'on' if self.state is True else 'off'

    def switch_state(self, state=None):
        if state is None:
            self.state = not self.state
        else:
            self.state = state
        logger.info('changing state to {}'.format(self.state))
        self.relay(self.state)

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
            if self.temp:
                current_temp = self.temp.read()
                if abs(current_temp - self.last_major_temp) >= self.minor_change:
                    self.last_major_temp = current_temp
                    if self.mqtt_enabled:
                        # publish MQTT if enabled
                        logger.info('publishing {} to broker {} topic {}'.format(current_temp, self.mqtt_broker, self.mqtt_topic))
                        publish(b'relay_control_client',
                                self.mqtt_broker,
                                self.mqtt_topic,
                                current_temp,
                                self.mqtt_username,
                                self.mqtt_password)
            if self.wdt:
                if self.debug:
                    logger.info('Calm watchdog down, all okay')
                self.wdt.feed()
            gc.collect()
            logger.info(f'mem_free: {gc.mem_free()}')
