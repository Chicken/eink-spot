import machine
from os import mkdir
from random import getrandbits

class Data:
    def __init__(self):
        try:
            f = open("/data/state", "r")
            [state, ssid, passwd, margin] = f.readlines()
            self.state = state.strip()
            self.ssid = ssid.strip()
            self.passwd = passwd.strip()
            self.margin = float(margin.strip())
        except:
            try:
                mkdir("/data")
            except:
                pass
            self.clear()

    def save(self):
        with open("/data/state", "w") as f:
            f.write(self.state + "\n")
            f.write(self.ssid + "\n")
            f.write(self.passwd + "\n")
            f.write(str(self.margin) + "\n")

    def clear(self):
        self.state = "setup"
        self.ssid = "eink-spot-" + machine.unique_id().hex()[:8]
        self.passwd = hex(getrandbits(32))[2:]
        self.margin = float(0)
        self.save()

class Log:
    def __init__(self):
        try:
            open("/data/log", "a").close()
        except:
            try:
                mkdir("/data")
            except:
                pass
            open("/data/log", "a").close()

    def write(self, msg):
        with open("/data/log", "a") as f:
            f.write(msg + "\n")
            f.flush()

    def read(self, size):
        with open("/data/log", "r") as f:
            return f.read(size)

    def clear(self):
        open("/data/log", "w").close()

class RestartCounter:
    def __init__(self):
        try:
            f = open("/data/restart_counter", "r")
            self.count = int(f.readline())
        except:
            try:
                mkdir("/data")
            except:
                pass
            self.reset()

    def save(self):
        with open("/data/restart_counter", "w") as f:
            f.write(str(self.count) + "\n")

    def reset(self):
        self.count = 0
        self.save()

    def increase(self):
        self.count += 1
        self.save()

    def get(self):
        return self.count
