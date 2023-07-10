from machine import Pin, I2C
import ssd1306


class MyDisplay:
    def __init__(self, sda_pin=4, scl_pin=14, width=128, height=64):
        i2c = I2C(sda=Pin(4), scl=Pin(14))
        self.display = ssd1306.SSD1306_I2C(width, height, i2c)

    def show_text(self, text=''):
        self.display.fill(0)
        self.display.show()
        self.display.text(text, 0, 0, 1)
        self.display.show()
