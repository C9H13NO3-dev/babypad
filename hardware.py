# hardware.py

from machine import Pin, I2C
from time import ticks_ms, ticks_diff, sleep_ms
from machine_i2c_lcd import I2cLcd
from rotary_irq import RotaryIRQ

class LCDDisplay:
    def __init__(self, i2c_addr=0x27, rows=2, cols=16, sda=20, scl=21, freq=100_000):
        self.i2c = I2C(0, sda=Pin(sda), scl=Pin(scl), freq=freq)
        self.lcd = I2cLcd(self.i2c, i2c_addr, rows, cols)
        self.rows = rows
        self.cols = cols
        self._lines = ["", ""]

    def clear(self):
        self.lcd.clear()
        self._lines = ["", ""]

    def show(self, line1, line2=""):
        lines = [line1[:self.cols], line2[:self.cols]]
        for row in range(min(self.rows, 2)):
            if self._lines[row] != lines[row]:
                self.show_line(row, lines[row])

    def show_line(self, row, text):
        self.lcd.move_to(0, row)
        self.lcd.putstr(" " * self.cols)
        self.lcd.move_to(0, row)
        self.lcd.putstr(text[:self.cols])
        if row < len(self._lines):
            self._lines[row] = text[:self.cols]


class ButtonArray:
    def __init__(self, pins=(5,6,7,8,9,10,11,12), debounce_ms=40):
        self.pins = [Pin(p, Pin.IN, Pin.PULL_UP) for p in pins]
        self.last_state = [1] * len(self.pins)
        self.debounce = debounce_ms
        self.last_press_time = [0] * len(self.pins)

    def read(self):
        # returns index (0-7) if a button is newly pressed, else None
        now = ticks_ms()
        for i, btn in enumerate(self.pins):
            val = btn.value()
            if self.last_state[i] == 1 and val == 0:
                if ticks_diff(now, self.last_press_time[i]) > self.debounce:
                    self.last_press_time[i] = now
                    self.last_state[i] = 0
                    return i
            elif val == 1:
                self.last_state[i] = 1
        return None

    def wait_for_press(self, idx=None):
        # waits for any button (or button idx) to be pressed, returns index
        while True:
            btn = self.read()
            if btn is not None and (idx is None or btn == idx):
                while self.pins[btn].value() == 0:
                    sleep_ms(10)
                sleep_ms(40)
                return btn
            sleep_ms(10)


class RotaryEncoder:
    def __init__(self, clk=4, dt=3, sw=2, min_val=-1000, max_val=1000):
        self.encoder = RotaryIRQ(
            pin_num_clk=clk,
            pin_num_dt=dt,
            min_val=min_val,
            max_val=max_val,
            incr=1,
            reverse=False,
            range_mode=RotaryIRQ.RANGE_UNBOUNDED,
            pull_up=True,
            half_step=False,
            invert=False
        )
        self.button = Pin(sw, Pin.IN, Pin.PULL_UP)
        self.last_button = 1
        self._last_val = self.encoder.value()

    def get(self):
        # Returns change since last check: +1/-1/0
        val = self.encoder.value()
        diff = val - self._last_val
        self._last_val = val
        if diff > 0:
            return 1
        elif diff < 0:
            return -1
        else:
            return 0

    def button_pressed(self):
        # Returns True once when button is pressed
        val = self.button.value()
        if self.last_button == 1 and val == 0:
            self.last_button = 0
            while self.button.value() == 0:
                sleep_ms(10)
            sleep_ms(30)
            self.last_button = 1
            return True
        self.last_button = val
        return False

    def wait_for_press(self):
        # Wait until encoder button is pressed and released
        while self.button.value() == 1:
            sleep_ms(10)
        while self.button.value() == 0:
            sleep_ms(10)
        sleep_ms(30)
        return True

    def reset(self, val=0):
        self.encoder.set(value=val)
        self._last_val = val

