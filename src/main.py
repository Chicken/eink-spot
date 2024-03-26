import network
import machine
import time
import ntptime
import urequests

from src.env import WLAN_SSID, WLAN_PASS, API_KEY, DEV
from src.epd3in0g import EPD3in0g
from src.fonts import opensans48, opensans32, opensans10
from src.fonts.writer import CWriter

def connect_to_wlan():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WLAN_SSID, WLAN_PASS)
        while not wlan.isconnected():
            pass
        print("network:", wlan.ifconfig())

# connect to wifi and sync time
connect_to_wlan()
ntptime.settime()

reset_cause = machine.reset_cause()
wake_reason = machine.wake_reason()
print("reset:", reset_cause, ", wake:", wake_reason)

# only do anything when powered on or scheduled to wake up from deep sleep
if (not (
    reset_cause == machine.PWRON_RESET
    or (
        reset_cause == machine.DEEPSLEEP_RESET 
        and wake_reason == machine.DEEPSLEEP
        )
    )):
    # sleep till the next full hour
    current_time = time.localtime()
    seconds_until_next_hour = 3600 - (current_time[4] * 60 + current_time[5])
    print("woke up at the wrong time, sleeping")
    if not DEV: machine.deepsleep(seconds_until_next_hour * 1000)

# get the electricity price data
response = urequests.get(f'http://homeapi.antti.codes/electricity_prices?key={API_KEY}')
price_data = response.json()
response.close()

print("data acquired")

epd = EPD3in0g()
(fb, buf, w, h) = epd.create_frame()

# draw the actual frame content
text_writer48 = CWriter(fb, opensans48, fgcolor=epd.WHITE, bgcolor=epd.BLACK)
CWriter.set_textpos(fb, 0, 0)
text_writer48.printstring(str(round(price_data["today"]["now"]["price"],1)))

next_three_hours = list(filter(lambda entry: entry["time"] > price_data["today"]["now"]["time"], list(reversed(price_data["today"]["prices"])) + list(reversed(price_data["tomorrow"]["prices"] or []))))[:3]
over100 = len(list(filter(lambda x: x, map(lambda x: x["price"] > 100, next_three_hours)))) + (price_data["today"]["now"]["price"] > 100)
under10 = len(list(filter(lambda x: x, map(lambda x: x["price"] < 10, next_three_hours)))) + (price_data["today"]["now"]["price"] < 10)

if over100 >= 1: next_three_hours = next_three_hours[:2]

text_writer32 = CWriter(fb, opensans32, fgcolor=epd.WHITE, bgcolor=epd.BLACK)
for i, entry in enumerate(next_three_hours):
    text_writer32.printstring(" " if over100 >= 1 or under10 <= 1 else ("   " if under10 >= 3 else "  "))
    text_writer32.printstring(str(round(entry["price"], 1)))

fb.hline(0, 50, w, epd.BLACK)
fb.hline(0, h - 15, w, epd.BLACK)

prices = list(reversed(price_data["today"]["prices"]))
tomorrow_shown = False
if price_data["tomorrow"]["prices"] is not None:
    tomorrow_shown = True
    prices = prices[12:]
    prices += list(reversed(price_data["tomorrow"]["prices"]))[:12]
max_price = max(map(lambda x: x["price"], prices))

labels = (
    "12 13 14 15 16 17 18 19 20 21 22 23 0   1   2    3   4    5   6   7   8   9  10 11"
    if tomorrow_shown else
    " 0   1   2   3   4    5   6   7    8   9 10 11 12 13 14 15 16 17 18 19 20 21 22 23"
)
text_writer10 = CWriter(fb, opensans10, fgcolor=epd.WHITE, bgcolor=epd.BLACK)
CWriter.set_textpos(fb, h - 11, 0)
text_writer10.printstring(labels)

x = 0
for (i, entry) in enumerate(prices):
    height = int(entry["price"] / max_price * 100)
    fb.rect(x, 52 + (100 - height), 15 - (i % 3 == 0), height, epd.RED if entry["time"] == price_data["today"]["now"]["time"] else epd.YELLOW, True)
    x += 15 + (1 if i % 3 == 0 else 2)

# display the updated frame and go back to sleep
print("displaying")
epd.init()
epd.display(epd.get_buffer(buf))
epd.sleep()

# sleep till the next full hour
current_time = time.localtime()
seconds_until_next_hour = 3600 - (current_time[4] * 60 + current_time[5])
print("sleeping")
if not DEV: machine.deepsleep(seconds_until_next_hour * 1000)
