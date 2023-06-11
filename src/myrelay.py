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

logger = Logger.get_logger()


class MyRelay:
    def __init__(self,
                 relay_pin=12,
                 button=None,
                 temp=None,
                 event_loop=None,
                 config=None,
                 wdt=None,
                 sleep_interval=0.5,
                 debug=False):
        logger.info('Staring MyRelay')
        self.event_loop = event_loop
        self.debug = debug
        self.sleep_interval = sleep_interval
        self.wdt = wdt
        self.relay = Pin(relay_pin, Pin.OUT)
        self.button = button
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

    async def start(self):
        asyncio.create_task(self.temp.start())
        asyncio.create_task(self.button.start())
        # self.event_loop.create_task(self.check_changes(sleep_ms=self.sleep_interval))
        if self.mqtt_enabled:
            # publish MQTT if enabled
            publish('relay_control_client',
                    self.mqtt_broker,
                    '/notification/message',
                    'relay_control_started',
                    self.mqtt_username,
                    self.mqtt_password)
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
        print('changing state to {}'.format(self.state))
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
                if random.randint(0, 20) >= 19:
                    raise RuntimeError('provoked error')
            await asyncio.sleep(1)
            # if self.button.pressed is True:
            #     self.pause_temp_check()
            #     print('switching state to {} due to button pressed, '
            #           'waiting {} secs for further press'.format(not self.state, button_time_secs))
            #     self.switch_state()
            #     await asyncio.sleep(button_time_secs)
            current_temp = self.temp.read()
            if abs(current_temp - self.last_major_temp) >= self.minor_change:
                self.last_major_temp = current_temp
                if self.mqtt_enabled:
                    # publish MQTT if enabled
                    print('publishing {} to broker {} topic {}'.format(current_temp, self.mqtt_broker, self.mqtt_topic))
                    publish(b'relay_control_client',
                            self.mqtt_broker,
                            self.mqtt_topic,
                            current_temp,
                            self.mqtt_username,
                            self.mqtt_password)

            if self.temp and not self.in_pause_mode:
                if current_temp >= self.trigger_temp and self.on is False:
                    print('turning on relay due to temp above {}'.format(self.trigger_temp))
                    self.switch_state(True)
                    self.pause_temp_check()
                elif current_temp < self.trigger_temp and self.on is True:
                    print('turning off relay due to temp below {}'.format(self.trigger_temp))
                    self.switch_state(False)
            if self.wdt:
                self.wdt.feed()
