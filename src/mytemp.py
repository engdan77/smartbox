try:
    from machine import Pin
except ImportError:
    from unittest.mock import Mock
    Pin = Mock()
    dht = Mock()
    dht_instance = Mock()
    dht_instance.temperature.return_value = 22
    dht.DHT22.return_value = dht_instance

    import asyncio
else:
    import dht
    import uasyncio as asyncio
from mylogger import Logger

logger = Logger.get_logger()

class MyTemp:
    def __init__(self, pin=4):
        self.d = dht.DHT22(Pin(pin))
        self.temp = 0
        self.humid = 0

    def refresh(self):
        self.d.measure()
        self.temp = self.d.temperature()
        self.humid = self.d.humidity()

    def read_temp(self):
        return self.temp

    def read_humid(self):
        return self.humid

    async def start(self, refresh_interval=15):
        count = 0
        while True:
            await asyncio.sleep(refresh_interval)
            try:
                self.refresh()
            except OSError as e:
                print('failed get temp due to {}'.format(e))
            count += 1
            logger.info('Updating temp {} current temp {}'.format(count, self.read_temp()))
