try:
    import machine
except ImportError:
    from unittest.mock import Mock
    Pin = Mock()
    from collections import deque
    import asyncio
    import time
else:
    from machine import Pin
    from ucollections import deque
    import uasyncio as asyncio
    import time as time

from mylogger import Logger

logger= Logger.get_logger()


class MyPir:
    def __init__(self, button_pin=14, event_loop=None):
        self.event_loop = event_loop
        self.motion_queue = deque((), 10)
        self.pir_pin = button_pin

    async def start(self):
        if self.event_loop:
            self.event_loop.create_task(self.check_motion())
        else:
            await self.check_motion()

    async def check_motion(self, sleep_time=0.3, wait_secs=10):
        while True:
            await asyncio.sleep(sleep_time)
            p = Pin(self.pir_pin, Pin.IN)
            if bool(p.value()) is True:
                self.motion_queue.append(1)
                logger.info(f'motion detected, waiting {wait_secs} secs before non motion')
                await asyncio.sleep(wait_secs)
                self.motion_queue.append(0)

    def read_motion(self):
        try:
            return self.motion_queue.popleft()
        except (ValueError, IndexError):
            return 0

