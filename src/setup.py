import network
import asyncio
import gc
import socket
import time
import machine
import framebuf

from src.epd3in0g import EPD3in0g

def text(fb, text, x, y, mult, color):
    char_buf = bytearray(8)
    char_fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.MONO_HMSB)
    for char in text:
        char_fb.fill(0)
        char_fb.text(char, 0, 0, 1)
        for i in range(8):
            for j in range(8):
                if char_fb.pixel(i, j) == 1:
                    fb.fill_rect(x + mult * i, y + mult * j, mult, mult, color)
        x += 8 * mult

def setup(db):
    # start an access point
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    SELF_IP = "10.0.0.1"
    ap.ifconfig((SELF_IP, "255.255.255.0", SELF_IP, SELF_IP))
    ap.config(essid=db.ssid, password=db.passwd, authmode=4)
    print(f"AP started {db.ssid} | {db.passwd}")

    # scan for available networks
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    available_networks = list(map(lambda x: x[0].decode(), sta.scan()))
    sta.disconnect()
    print("available networks:", available_networks)

    # dns handler
    async def dns():
        # udp socket
        dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_socket.setblocking(False)
        dns_socket.bind(("0.0.0.0", 53))
        while True:
            gc.collect()
            # asyncio magic...?
            try:
                yield asyncio.core._io_queue.queue_read(dns_socket)
            except Exception:
                await asyncio.sleep_ms(100)
                continue
            data, addr = dns_socket.recvfrom(512)
            # is a standard query
            if (data[2] & 0x80 == 0 and data[2] & 0xf0 == 0):
                res = bytearray(data)
                res[2] |= 0x80 # turn query message into a response
                res[7] = 1 # one answer
                # pointer at domain name, A, IN, TTL 0, length 4
                res += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x00\x00\x04'
                # ip
                res += bytes(map(int, SELF_IP.split('.'))) 
                dns_socket.sendto(res, addr)
            await asyncio.sleep_ms(100)

    # http handler
    async def http(reader, writer):
        gc.collect()

        # read the main request line
        [method, path, _version] = (await reader.readline()).decode().strip().split(" ")
        print(f"requested {method} {path}")
        # consume headers
        content_length = 0
        while True:
            line = await reader.readline()
            if line.startswith(b"Content-Length:"):
                content_length = int(line.split(b":")[1])
            if line == b'\r\n':
                break
        gc.collect()

        if method == "GET":
            ssid_options = "".join(map(lambda x: f'<option value="{x}">{x}</option>', available_networks + ["__CUSTOM__"]))  
            # return the setup page on a GET request
            response = "\r\n".join(
            f"""
            HTTP/1.1 200 OK
            Content-Type: text/html
            Connection: close

            <!DOCTYPE html>
            <html>
            <head>
                <title>E-Ink Spot Price Display Setup</title>
            </head>
            <body>
                <h1>E-Ink Spot Price Display Setup</h1>
                <form method="POST" action="/">
                    <select id="choice" name="ssid_choice">
                        {ssid_options}
                    </select>
                    <input type="text" id="ssid" name="ssid" style="display: none;" placeholder="SSID"><br>
                    <input type="password" name="passwd" placeholder="Password" required><br>
                    <input type="text" name="margin" placeholder="Marginal price" required><br>
                    <input type="submit" value="Submit">
                    <script>
                        document.querySelector("#choice").addEventListener("change", function(e) {{
                          const ssid = document.querySelector("#ssid");
                          if (e.target.value === "__CUSTOM__") {{
                            ssid.style.display = "block";
                          }} else {{
                            ssid.style.display = "none";
                          }}
                        }});
                    </script>
                </form>
            </html>
            """.strip().split("\n"))
            await writer.awrite(response.encode())
            await writer.aclose()
        else:
            # parse data on a POST request
            body = (await reader.readexactly(content_length)).decode()
            data = dict(map(lambda x: x.split("="), body.strip().split("&")))
            print("setup", data["ssid_choice"], data["ssid"], data["margin"])

            ssid = data["ssid"] if data["ssid_choice"] == "__CUSTOM__" else data["ssid_choice"]

            # try to connect to given wifi
            print("trying to connect to wifi")
            sta = network.WLAN(network.STA_IF)
            sta.active(True)
            sta.connect(ssid, data["passwd"])
            now = time.time()
            failed = False
            while not sta.isconnected():
                await asyncio.sleep_ms(100)
                if time.time() - now > 5:
                    failed = True
                    break

            sta.disconnect()

            # check that the number is valid
            not_a_number = False
            try:
                float(data["margin"])
            except ValueError:
                not_a_number = True

            if failed or not_a_number:
                print("setup failed")
                # return an error page
                response = "\r\n".join(
                f"""
                HTTP/1.1 400 Bad Request
                Content-Type: text/html
                Connection: close

                <!DOCTYPE html>
                <html>
                <head>
                    <title>E-Ink Spot Price Display Setup</title>
                </head>
                <body>
                    <h1>E-Ink Spot Price Display Setup</h1>
                    <p>Failed to connect to wifi or invalid marginal price</p>
                </html>
                """.strip().split("\n"))
                await writer.awrite(response.encode())
                await writer.aclose()
                return
            
            db.state = "active"
            db.ssid = ssid
            db.passwd = data["passwd"]
            db.margin = float(data["margin"])
            db.save()
            print("setup success")
            
            # return a success page
            response = "\r\n".join(
            """
            HTTP/1.1 200 OK
            Content-Type: text/html
            Connection: close

            <!DOCTYPE html>
            <html>
            <head>
                <title>E-Ink Spot Price Display Setup</title>
            </head>
            <body>
                <h1>E-Ink Spot Price Display Setup</h1>
                <p>Settings saved. Restarting...</p>
            </html>
            """.strip().split("\n"))
            await writer.awrite(response.encode())
            await writer.aclose()

            time.sleep_ms(2000)

            print("restarting")
            # restart the device
            machine.reset()
    
    # start asyncio tasks and whatever
    loop = asyncio.get_event_loop()
    loop.create_task(dns())
    loop.create_task(asyncio.start_server(http, "0.0.0.0", 80))
    print("dns and http listening")

    print("displaying credentials")
    epd = EPD3in0g()
    (fb, buf, _w, _h) = epd.create_frame()

    text(fb, "SSID: " + db.ssid, 10, 20, 2, epd.RED)
    text(fb, "PASSWORD: " + db.passwd, 10, 40, 2, epd.RED)

    epd.init()
    epd.display(epd.get_buffer(buf))
    epd.sleep()

    loop.run_forever()
