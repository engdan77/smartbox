try:
    from machine import Pin
except ImportError:
    from unittest.mock import Mock
    Pin = Mock()
    ADC = Mock()
    import asyncio
else:
    import dht
    import uasyncio as asyncio
    from machine import ADC

from mylogger import Logger

logger = Logger.get_logger()


class MySmoke:
    def __init__(self, pin=0):
        self.p = ADC(pin)
        self.smoke = 0

    def refresh(self):
        self.smoke = self.p.read()

    def read_smoke(self):
        return self.smoke

    async def start(self, refresh_interval=15):
        count = 0
        while True:
            await asyncio.sleep(refresh_interval)
            try:
                self.refresh()
            except OSError as e:
                print('failed get temp due to {}'.format(e))
            count += 1
            logger.info('Updating smoke {} current smoke {}'.format(count, self.read_smoke()))
