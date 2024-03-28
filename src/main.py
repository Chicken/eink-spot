import network
import machine
import time
import ntptime
import urequests

from src.env import WLAN_SSID, WLAN_PASS, API_KEY, DEV
from src.epd3in0g import EPD3in0g
from src.fonts import opensans48bold, opensans28, opensans10
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
print("time before sync:", time.localtime())
ntptime.host = "fi.pool.ntp.org"
ntptime.settime()
print("time after sync:", time.localtime())

print("dev:", DEV)

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

current_time = time.localtime()
seconds_until_next_hour = 3600 - (current_time[4] * 60 + current_time[5])
if seconds_until_next_hour < 60:
    if not DEV: time.sleep(seconds_until_next_hour)
    
if not DEV: time.sleep(10)

# get the electricity price data
response = urequests.get(f'http://homeapi.antti.codes/electricity_prices?key={API_KEY}')
price_data = response.json()
response.close()

print("data acquired")

# calculate some stufff from data
price_now = round(price_data["today"]["now"]["price"],1)
price_now_str = str(price_now)

next_hours = list(map(lambda entry: round(entry["price"], 1), filter(
    lambda entry: entry["time"] > price_data["today"]["now"]["time"],
    list(reversed(price_data["today"]["prices"]))
    + list(reversed(price_data["tomorrow"]["prices"] or []))
)))[:3]

now_large = price_now >= 100 or price_now <= -10
next_large_count = len(list(filter(lambda x: x >= 100 or x <= -10, next_hours)))

now_cell_width = 160 if now_large else 125

# too many big numbers just wont fit in the screen :(
if (not now_large and next_large_count >= 2) or (now_large and next_large_count > 0):
    next_hours = next_hours[:2]

epd = EPD3in0g()
(fb, buf, w, h) = epd.create_frame()

# draw the actual frame content
text_writer48 = CWriter(fb, opensans48bold, fgcolor=epd.WHITE, bgcolor=epd.BLACK)
CWriter.set_textpos(fb, 0, (now_cell_width // 2) - (text_writer48.stringlen(price_now_str) // 2))
text_writer48.printstring(price_now_str)
fb.vline(now_cell_width, 0, 50, epd.BLACK)

text_writer28 = CWriter(fb, opensans28, fgcolor=epd.WHITE, bgcolor=epd.BLACK)
CWriter.set_textpos(fb, row=20)
remaining_width = w - now_cell_width
for i, price in enumerate(next_hours):
    CWriter.set_textpos(fb, col=(
        now_cell_width
        + remaining_width // len(next_hours) * i
        + remaining_width // (2 * len(next_hours))
        - text_writer28.stringlen(str(price)) // 2
        + 2 * (i == 0 and not now_large and next_large_count == 1)
    ))
    text_writer28.printstring(str(price))

fb.hline(0, 50, w, epd.BLACK)
fb.hline(0, h - 15, w, epd.BLACK)

prices = list(reversed(price_data["today"]["prices"]))
tomorrow_shown = False
if price_data["tomorrow"]["prices"] is not None:
    tomorrow_shown = True
    prices = prices[12:]
    prices += list(reversed(price_data["tomorrow"]["prices"]))[:12]
max_price = max(map(lambda x: x["price"], prices))
min_price = min(map(lambda x: x["price"], prices))
if min_price > 0: min_price = 0

labels = (
    "12 13 14 15 16 17 18 19 20 21 22 23 0 1 2 3 4 5 6 7 8 9 10 11".split(" ")
    if tomorrow_shown else
    "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23".split(" ")
)
text_writer10 = CWriter(fb, opensans10, fgcolor=epd.WHITE, bgcolor=epd.BLACK)
CWriter.set_textpos(fb, row=h - 11)

x = 0
for (i, entry) in enumerate(prices):
    if entry["price"] >= 0:
        height = int(entry["price"] / max_price * (100 * (max_price / (max_price - min_price))))
        fb.rect(
            x,
            52 + int(100 * (max_price / (max_price - min_price)) - height),
            15 - (i % 3 == 0),
            height,
            epd.RED if entry["time"] == price_data["today"]["now"]["time"] else epd.YELLOW,
            True
        )
    else:
        height = int(entry["price"] / min_price * (100 * (-min_price / (max_price - min_price))))
        fb.rect(
            x,
            52 + int(100 * (max_price / (max_price - min_price))),
            15 - (i % 3 == 0),
            height,
            epd.RED if entry["time"] == price_data["today"]["now"]["time"] else epd.YELLOW,
            True
        )
    CWriter.set_textpos(fb, col=x + 6 - text_writer10.stringlen(labels[i]) // 2)
    text_writer10.printstring(labels[i])
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
