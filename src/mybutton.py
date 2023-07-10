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


class MyButton:
    def __init__(self, button_pin=14, event_loop=None):
        self.event_loop = event_loop
        self.pressed_queue = deque((), 10)
        self.button_pin = button_pin

    async def start(self):
        if self.event_loop:
            self.event_loop.create_task(self.check_presses())
        else:
            await self.check_presses()

    async def check_presses(self, sleep_time=0.3, bounce_secs=1):
        while True:
            await asyncio.sleep(sleep_time)
            p = Pin(self.button_pin, Pin.IN, Pin.PULL_UP)
            if bool(p.value()) is False:
                self.pressed_queue.append(True)
                logger.info('button pressed')
                await asyncio.sleep(bounce_secs)

    @property
    def pressed(self):
        try:
            return self.pressed_queue.popleft()
        except (ValueError, IndexError):
            return False


def blocking_count_clicks(button_pin=14, timeout=5, debounce_ms=5, sleep_ms=10):
    press_count = 0
    number_iterations = (timeout * 1000) / sleep_ms
    for _ in range(number_iterations):
        p = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        if bool(p.value()) is False:
            being_pressed = []
            for d in range(20):
                being_pressed.append(bool(p.value()))
                time.sleep_ms(debounce_ms)
            if not any(being_pressed):
                press_count += 1
                logger.info('button pressed')
        time.sleep_ms(sleep_ms)
    return press_count
