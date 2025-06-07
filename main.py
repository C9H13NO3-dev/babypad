# main.py

import network
import utime
from hardware import LCDDisplay, ButtonArray, RotaryEncoder
from api import BabyBuddyAPI

# --- Connect to WiFi ---
def connect_wifi(ssid, password, lcd):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    lcd.show("Connecting WiFi", ssid)
    wlan.connect(ssid, password)
    for _ in range(30):
        if wlan.isconnected():
            lcd.show("WiFi Connected", wlan.ifconfig()[0])
            utime.sleep(1)
            lcd.clear()
            return True
        utime.sleep(1)
    lcd.show("WiFi Error", "")
    utime.sleep(2)
    return False

# --- Feeding types/methods for selection ---
FEED_TYPES = [
    "breast milk", "formula", "fortified milk", "other"
]
FEED_METHODS = [
    "both breasts", "left breast", "right breast", "bottle", "other"
]

def select_from_list(lcd, title, options, encoder):
    idx = 0
    encoder.reset(0)
    lcd.show(title, options[idx])
    while True:
        diff = encoder.get()
        if diff != 0:
            idx = (idx + diff) % len(options)
            lcd.show(title, options[idx])
        if encoder.button_pressed():
            utime.sleep(0.2)
            return options[idx]
        utime.sleep(0.05)

def main():
    # --- Init hardware ---
    lcd = LCDDisplay()
    buttons = ButtonArray()
    encoder = RotaryEncoder()

    # --- Load API (and WiFi secrets) ---
    try:
        api = BabyBuddyAPI("secrets.json")
    except Exception as e:
        lcd.show("Error: Secrets", str(e))
        while True:
            utime.sleep(1)

    # --- WiFi connect ---
    wifi = api.secrets["wifi"]
    if not connect_wifi(wifi["ssid"], wifi["password"], lcd):
        while True:
            utime.sleep(1)

    # --- Baby Buddy API connect ---
    lcd.show("Connecting...", "")
    if not api.is_connected():
        lcd.show("API Conn Error", "")
        while True:
            utime.sleep(2)

    # --- App state ---
    feeding_active = False
    feeding_timer_id = None
    feeding_start_time = None

    # --- Main loop ---
    while True:
        # --- Time + initials display ---
        initials = api.child_initials()
        now = utime.localtime()
        timestr = "%02d:%02d" % (now[3], now[4])
        if feeding_active:
            elapsed = utime.time() - feeding_start_time
            t_h = elapsed // 3600
            t_m = (elapsed % 3600) // 60
            lcd.show(f"{initials}   {timestr}", "Timer: %02d:%02d" % (t_h, t_m))
        else:
            lcd.show(f"{initials}   {timestr}", "Ready")

        # --- Button 1: Feeding ---
        btn = buttons.read()
        if btn == 0:  # Button 1
            # Start or stop feeding
            if not feeding_active:
                # Start feeding timer
                res = api.start_timer("feeding", data={"type": "breast milk", "method": "both breasts"})
                if res and "id" in res:
                    feeding_active = True
                    feeding_timer_id = res["id"]
                    feeding_start_time = utime.time()
                else:
                    lcd.show("Error: Timer", "")
                    utime.sleep(2)
            else:
                # Stop feeding timer and log details
                # Select type
                feed_type = select_from_list(lcd, "Feed Type?", FEED_TYPES, encoder)
                feed_method = select_from_list(lcd, "Feed Method?", FEED_METHODS, encoder)
                res = api.stop_timer(feeding_timer_id, data={"type": feed_type, "method": feed_method})
                if res:
                    lcd.show("Logged!", feed_type + "/" + feed_method)
                else:
                    lcd.show("API Error", "")
                utime.sleep(2)
                feeding_active = False
                feeding_timer_id = None
                feeding_start_time = None

        utime.sleep(0.1)

if __name__ == "__main__":
    main()
