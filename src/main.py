import gc
gc.enable()

from machine import Pin
from src.data import Data
from src.setup import setup
from src.app import app

db = Data()

if Pin(2, Pin.IN).value() == 1:
    db.clear()
    
if db.state == "setup":
    setup(db)
else:
    try:
        app(db)
    except Exception as e:
        import urequests
        import machine
        import sys
        from io import StringIO
        from src.data import Log, RestartCounter
        from src.env import DEV, ERROR_WEBHOOK

        def get_exception_str(exception):
            f = StringIO()
            sys.print_exception(exception, f)
            return f.getvalue()
        
        print("error:", e)

        c = -1
        try:
            rc = RestartCounter()
            rc.increase()
            c = rc.get()
            urequests.post(ERROR_WEBHOOK, json={"content": f"crash counter: {c}"})
        except:
            pass

        try:
            log = Log()
            log.write(get_exception_str(e))
            urequests.post(ERROR_WEBHOOK, json={"content": f"{log.read(2000).strip()}"})
            log.clear()
        except:
            pass

        if not DEV:
            if c <= 1:
                machine.reset()
            elif c > 1 and c <= 6:
                machine.deepsleep(2 * 60 * 1000)
            elif c > 6 and c <= 11:
                machine.deepsleep(10 * 60 * 1000)
            elif c > 11:
                machine.deepsleep(60 * 60 * 1000)
