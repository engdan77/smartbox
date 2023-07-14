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
    def __init__(self, sda_pin=4, scl_pin=14, width=128, height=64, secs_between_screens=3):
        i2c = I2C(sda=Pin(sda_pin), scl=Pin(scl_pin))
        self.display = SSD1306_I2C(width, height, i2c)
        self.screens = {'main': 'Daniels smarta..'}
        self.current_screen = 0
        self.secs_between_screens = secs_between_screens

    def upsert_screen(self, title, content):
        self.screens[title] = content

    async def start(self):
        while True:
            await asyncio.sleep(self.secs_between_screens)
            if not self.screens:
                continue
            self.switch_to_next_screen()
            logger.info(f'show screen {self.current_screen}')
            logger.info(f'all screens {self.screens}')
            current_content = list(self.screens.values())[self.current_screen - 1]
            self.show_content(current_content)
            del current_content
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
        self.display.text(text, 0, 0, 1)
        self.display.show()

