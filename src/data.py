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
        f = open("/data/state", "w")
        f.write(self.state + "\n")
        f.write(self.ssid + "\n")
        f.write(self.passwd + "\n")
        f.write(str(self.margin) + "\n")
        f.close()

    def clear(self):
        self.state = "setup"
        self.ssid = "eink-spot-" + machine.unique_id().hex()[:8]
        self.passwd = hex(getrandbits(32))[2:]
        self.margin = float(0)
        self.save()
