import gc

try:
    from machine import Pin, I2C
    from ssd1306 import SSD1306_I2C
    import uasyncio as asyncio
except ModuleNotFoundError:
    from unittest.mock import Mock
    I2C = Mock()
    SSD1306_I2C = Mock()
    Pin = Mock()
    import asyncio

from mylogger import Logger

logger = Logger.get_logger()


class MyDisplay:
    def __init__(self, sda_pin=4, scl_pin=14, width=128, height=64, secs_between_screens=10):
        i2c = I2C(sda=Pin(sda_pin), scl=Pin(scl_pin))
        self.display = SSD1306_I2C(width, height, i2c)
        self.screens = {}
        self.current_screen = 0
        self.last_screen = self.current_screen
        self.secs_between_screens = secs_between_screens
        self.next_screen_timer = 0
        self.update_interval = 0.5
        self.count_between_screen_updates = self.secs_between_screens / self.update_interval
        self.current_update_count = 0

    def upsert_screen(self, title, content):
        self.screens[title] = content

    async def screen_expired(self):
        await asyncio.sleep(self.update_interval)
        self.current_update_count += 1
        if self.current_update_count > self.count_between_screen_updates:
            self.current_update_count = 0
            return True
        else:
            return False

    async def start(self):
        while True:
            if not self.screens:
                continue
            screen_expired = await self.screen_expired()
            if screen_expired:
                self.switch_to_next_screen()
            if self.current_screen != self.last_screen:
                self.current_update_count = 0
                logger.info(f'show screen {self.current_screen}')
                current_content = list(self.screens.values())[self.current_screen - 1]
                self.show_content(current_content)
                del current_content
            self.last_screen = self.current_screen
            del screen_expired
            gc.collect()

    def switch_to_next_screen(self):
        if not self.screens:
            return
        self.current_screen += 1
        if self.current_screen > len(self.screens):
            self.current_screen = 1
        logger.info(f'current screen switched to {self.current_screen}')

    def show_content(self, text=''):
        self.display.fill(0)
        self.display.show()
        px_between_lines = 12
        current_row_px = 0
        for line in text.split('\n'):
            self.display.text(line, 0, current_row_px, 1)
            current_row_px += px_between_lines
        self.display.show()


