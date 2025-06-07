# BabyPad

BabyPad is a small MicroPython application designed to log baby care activities using the [Baby Buddy](https://github.com/baby-buddy/babybuddy) API. It runs on microcontrollers such as the Raspberry Pi Pico W together with an LCD display, buttons and a rotary encoder.

The project allows you to start and stop feeding timers and records the data directly to a Baby Buddy server over Wi‑Fi. The UI is minimal and optimised for embedded devices with a two line display.

## Features

- Connects to a Wi‑Fi network and authenticates with a Baby Buddy instance
- Displays the active child and current time on a small I2C LCD
- Start and stop feeding timers with button presses
- Select feeding type and method using a rotary encoder
- Syncs the clock from `time.microsoft.com` on boot

## Hardware

The code assumes the following hardware configuration:

- **LCDDisplay** via I²C on pins `20` (SDA) and `21` (SCL)
- **ButtonArray** of up to eight buttons connected to pins `5`–`12`
- **RotaryEncoder** connected to pins `4`, `3` and `2`

These defaults can be changed by editing `hardware.py`.

## Setup

1. Install MicroPython on your board and copy the files from this repository (`main.py`, `api.py`, `hardware.py` and `secrets.json`).
2. Edit `secrets.json` with your Wi‑Fi credentials and Baby Buddy API token.
3. Ensure the libraries `urequests`, `machine_i2c_lcd` and `rotary_irq` are available on the device.
4. Reset or power up the board. After connecting to Wi‑Fi, the device synchronizes the clock using `time.microsoft.com` and then displays the current time ready for logging.

## Usage

- **Button 1** toggles the feeding timer. When stopping the timer, use the rotary encoder to choose the feed type and method before the data is sent to Baby Buddy.
- The display shows the active child's initials and a running timer while feeding is in progress.

## License

This project is released under the CC0 1.0 Universal license. See the `LICENSE` file for details.

