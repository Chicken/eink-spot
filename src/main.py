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
    app(db)
