import gc
import re

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


def get_digit_coords(part='upper'):
    if part == 'upper':
        return [0, 0, 20, 5]
    if part == 'middle':
        return [0, 20, 25, 5]
    if part == 'lower':
        return [0, 40, 25, 5]
    if part == 'right_all':
        return [20, 0, 5, 45]
    if part == 'left_all':
        return [0, 0, 5, 45]
    if part == 'left_upper':
        return [0, 0, 5, 25]
    if part == 'right_lower':
        return [20, 20, 5, 25]
    if part == 'right_upper':
        return [20, 0, 5, 25]
    if part == 'left_lower':
        return [0, 20, 5, 25]
    if part == 'dot':
        return [0, 40, 5, 5]


def get_digit_rects(char='0'):
    if char == '0':
        return 'upper lower left_all right_all'
    if char == '1':
        return 'right_all'
    if char == '2':
        return 'upper right_upper middle left_lower lower'
    if char == '3':
        return 'upper middle lower right_all'
    if char == '4':
        return 'left_upper middle right_all'
    if char == '5':
        return 'upper left_upper middle right_lower lower'
    if char == '6':
        return 'upper left_all middle right_lower lower'
    if char == '7':
        return 'upper right_all'
    if char == '8':
        return 'upper middle lower left_all right_all'
    if char == '9':
        return 'upper middle left_upper right_all'
    if char == '.':
        return 'dot'


def get_char_rectangles(char='0', x_offset=0, y_offset=0):
        pieces_with_offsets = []
        all_pieces = get_digit_rects(char).split()  # if a digit
        for piece in all_pieces:
            coords = get_digit_coords(piece)
            coords[0] += x_offset
            coords[1] += y_offset
            print(f'coord for {char}: {coords}')
            pieces_with_offsets.append(coords)
            del coords
            gc.collect()
        return pieces_with_offsets


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
        self.screen_save_count = 120
        self.remaining_count_before_screen_save = 120

    def upsert_screen(self, title, content):
        self.screens[title] = content

    async def screen_expired(self):
        self.current_update_count += 1
        if self.current_update_count > self.count_between_screen_updates:
            self.current_update_count = 0
            return True
        else:
            return False

    def screen_saver_count_update(self):
        if self.remaining_count_before_screen_save == 0:
            self.clear_screen()
        if self.remaining_count_before_screen_save > 0:
            self.remaining_count_before_screen_save -= 1

    def is_screen_saver_active(self):
        return bool(self.remaining_count_before_screen_save)

    def reset_screen_saver(self):
        self.remaining_count_before_screen_save = self.screen_save_count

    async def start(self):
        while True:
            await asyncio.sleep(self.update_interval)
            if not self.screens:
                continue
            if self.is_screen_saver_active():
                continue
            self.screen_saver_count_update()
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

    def switch_to_next_screen_reset_counter(self):
        self.reset_screen_saver()
        if not self.screens:
            return
        self.current_screen += 1
        if self.current_screen > len(self.screens):
            self.current_screen = 1
        logger.info(f'current screen switched to {self.current_screen}')

    def show(self):
        self.display.show()

    def show_text(self, text=''):
        px_between_lines = 12
        current_row_px = 0
        for line in text.split('\n'):
            self.display.text(line, 0, current_row_px, 1)
            current_row_px += px_between_lines
        del px_between_lines
        del current_row_px
        gc.collect()

    def clear_screen(self):
        self.display.fill(0)
        self.display.show()

    def show_content(self, content=''):
        self.clear_screen()
        digits = re.sub('[^0-9.]', '', content)
        text = re.sub('[0-9]', '', content)
        if digits and not len(digits) > 4:
            self.show_big_chars(digits)
            del digits
            gc.collect()
        if text:
            px_between_lines = 12
            current_row_px = 0
            for line in content.split('\n'):
                self.display.text(line, 0, current_row_px, 1)
                current_row_px += px_between_lines
            del px_between_lines
            del current_row_px
            gc.collect()
        self.display.show()

    def draw_rect(self, coords):
        self.clear_screen()
        start_x, start_y, end_x, end_y = coords
        self.display.fill_rect(start_x, start_y, end_x, end_y, 1)
        self.display.show()

    def show_big_chars(self, chars, pixels_between_x=32):
        self.clear_screen()
        x_offset = 0
        for char in str(chars):
            for rect in get_char_rectangles(char, x_offset, y_offset=15):
                start_x, start_y, end_x, end_y = rect
                self.display.fill_rect(start_x, start_y, end_x, end_y, 1)
                del start_x
                del start_y
                del end_x
                del end_y
                gc.collect()
            x_offset += pixels_between_x
        self.display.show()