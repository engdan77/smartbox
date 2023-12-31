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
    import gc

from mylogger import Logger

logger= Logger.get_logger()


class MyButton:
    def __init__(self, button_pin=14, event_loop=None):
        self.event_loop = event_loop
        self.single_pressed_queue = deque((), 10)
        self.button_pin = button_pin
        self.multi_press_interval_started = False
        self.button_clicks = deque((), 10)
        self.events = {}

    async def start(self):
        if self.event_loop:
            self.event_loop.create_task(self.check_presses())
        else:
            await self.check_presses()

    async def check_presses(self, sleep_time=0.2):
        while True:
            await asyncio.sleep(sleep_time)
            p = Pin(self.button_pin, Pin.IN, Pin.PULL_UP)
            if not p.value():
                logger.info('Initial button press')
                for i in range(20):
                    await asyncio.sleep(0.1)
                    if p.value():
                        self.single_pressed_queue.append(True)
                        if not self.multi_press_interval_started:
                            self.event_loop.create_task(self.start_multi_press_check())
                        gc.collect()
                        break
            del p
            gc.collect()

    async def start_multi_press_check(self):
        if self.multi_press_interval_started:
            while True:
                logger.info('Waiting for previous multi press to complete before check again')
                await asyncio.sleep(1)
                if not self.multi_press_interval_started:
                    logger.info('No multi-press in progress')
                    break
        self.multi_press_interval_started = True
        count_press = await self._count_presses()
        logger.info(f'count_press: {count_press}')
        if count_press:
            self.run_event(int(count_press))
        self.multi_press_interval_started = False
        gc.collect()

    async def _count_presses(self, total_interval_time=1.5):
        gc.collect()
        logger.info('Waiting for 2 secs for all presses')
        press_count = 0
        await asyncio.sleep(total_interval_time)
        for _ in range(10):
            try:
                logger.info(f'Increase press count by one, current: {press_count}')
                p = self.single_pressed_queue.popleft()
                press_count += 1
            except (ValueError, IndexError):
                logger.info(f'Queue empty, current: {press_count}')
                self.button_clicks.append(press_count)
                return press_count
            gc.collect()

    def run_event(self, number_of_presses):
        if number_of_presses in self.events.keys():
            func, args, kwargs = self.events[number_of_presses]
            logger.info(f'press {number_of_presses} triggers {func}')
            func(*args, **kwargs)
        else:
            logger.info(f'No function defined for {number_of_presses} clicks')

    def add_event(self, number_of_presses, func, args, kwargs):
        self.events[number_of_presses] = (func, args, kwargs)


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
