try:
    from machine import Pin, I2C
    from ssd1306 import SSD1306_I2C
except ModuleNotFoundError:
    from unittest.mock import Mock
    I2C = Mock()
    SSD1306_I2C = Mock()
    Pin = Mock()



class MyDisplay:
    def __init__(self, sda_pin=4, scl_pin=14, width=128, height=64):
        i2c = I2C(sda=Pin(sda_pin), scl=Pin(scl_pin))
        self.display = SSD1306_I2C(width, height, i2c)

    def show_text(self, text=''):
        self.display.fill(0)
        self.display.show()
        self.display.text(text, 0, 0, 1)
        self.display.show()
