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

def input_number(lcd, title, encoder, initial=0, step=1, min_val=0, max_val=100):
    """Simple numeric input using the rotary encoder."""
    val = initial
    encoder.reset(0)
    lcd.show(title, str(val))
    while True:
        diff = encoder.get()
        if diff != 0:
            val += diff * step
            if val < min_val:
                val = min_val
            if val > max_val:
                val = max_val
            lcd.show(title, str(val))
        if encoder.button_pressed():
            utime.sleep(0.2)
            return val
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
    sleep_active = False
    sleep_timer_id = None
    sleep_start_time = None
    tummy_active = False
    tummy_timer_id = None
    tummy_start_time = None
    pumping_active = False
    pumping_timer_id = None
    pumping_start_time = None

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
            lcd.show(f"{initials}   {timestr}", "Feed %02d:%02d" % (t_h, t_m))
        elif sleep_active:
            elapsed = utime.time() - sleep_start_time
            t_h = elapsed // 3600
            t_m = (elapsed % 3600) // 60
            lcd.show(f"{initials}   {timestr}", "Sleep %02d:%02d" % (t_h, t_m))
        elif tummy_active:
            elapsed = utime.time() - tummy_start_time
            t_h = elapsed // 3600
            t_m = (elapsed % 3600) // 60
            lcd.show(f"{initials}   {timestr}", "Tummy %02d:%02d" % (t_h, t_m))
        elif pumping_active:
            elapsed = utime.time() - pumping_start_time
            t_h = elapsed // 3600
            t_m = (elapsed % 3600) // 60
            lcd.show(f"{initials}   {timestr}", "Pump %02d:%02d" % (t_h, t_m))
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

        elif btn == 1:  # Button 2 - Sleep timer
            if not sleep_active:
                res = api.start_timer("sleep")
                if res and "id" in res:
                    sleep_active = True
                    sleep_timer_id = res["id"]
                    sleep_start_time = utime.time()
                else:
                    lcd.show("Error: Timer", "")
                    utime.sleep(2)
            else:
                res = api.stop_timer(sleep_timer_id)
                if res:
                    lcd.show("Sleep Logged", "")
                else:
                    lcd.show("API Error", "")
                utime.sleep(2)
                sleep_active = False
                sleep_timer_id = None
                sleep_start_time = None

        elif btn == 2:  # Button 3 - Diaper change
            option = select_from_list(lcd, "Diaper?", ["Wet", "Solid", "Both"], encoder)
            wet = option in ("Wet", "Both")
            solid = option in ("Solid", "Both")
            if api.log_diaper_change(wet=wet, solid=solid):
                lcd.show("Diaper Logged", option)
            else:
                lcd.show("API Error", "")
            utime.sleep(2)

        elif btn == 3:  # Button 4 - Tummy time timer
            if not tummy_active:
                res = api.start_timer("tummy time")
                if res and "id" in res:
                    tummy_active = True
                    tummy_timer_id = res["id"]
                    tummy_start_time = utime.time()
                else:
                    lcd.show("Error: Timer", "")
                    utime.sleep(2)
            else:
                res = api.stop_timer(tummy_timer_id)
                if res:
                    lcd.show("Tummy Logged", "")
                else:
                    lcd.show("API Error", "")
                utime.sleep(2)
                tummy_active = False
                tummy_timer_id = None
                tummy_start_time = None

        elif btn == 4:  # Button 5 - Weight entry
            weight = input_number(lcd, "Weight g?", encoder, initial=3500, step=10, min_val=0, max_val=20000)
            if api.log_weight(weight):
                lcd.show("Weight Logged", str(weight) + " g")
            else:
                lcd.show("API Error", "")
            utime.sleep(2)

        elif btn == 5:  # Button 6 - Temperature entry
            temp = input_number(lcd, "Temp C?", encoder, initial=37, step=1, min_val=30, max_val=45)
            if api.log_temperature(temp):
                lcd.show("Temp Logged", str(temp) + " C")
            else:
                lcd.show("API Error", "")
            utime.sleep(2)

        elif btn == 6:  # Button 7 - Pumping timer
            if not pumping_active:
                res = api.start_timer("pumping")
                if res and "id" in res:
                    pumping_active = True
                    pumping_timer_id = res["id"]
                    pumping_start_time = utime.time()
                else:
                    lcd.show("Error: Timer", "")
                    utime.sleep(2)
            else:
                res = api.stop_timer(pumping_timer_id)
                if res:
                    lcd.show("Pump Logged", "")
                else:
                    lcd.show("API Error", "")
                utime.sleep(2)
                pumping_active = False
                pumping_timer_id = None
                pumping_start_time = None

        elif btn == 7:  # Button 8 - Switch child
            api.next_child()
            lcd.show("Active Child", api.child_initials())
            utime.sleep(1)

        utime.sleep(0.1)

if __name__ == "__main__":
    main()
