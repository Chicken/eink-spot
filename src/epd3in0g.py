from time import sleep_ms
from machine import Pin, SPI
from micropython import const
import framebuf

EPD_WIDTH = const(168)
EPD_HEIGHT = const(400)

BLACK = const(0b00)
WHITE = const(0b01)
YELLOW = const(0b10)
RED = const(0b11)

# TODO: should there be a power pin?
RST_PIN = const(19) # reset, low active
DC_PIN = const(0) # high = data, low = data
CS_PIN = const(5) # spi chip select, low active 
BUSY_PIN = const(4) # busy, low active

POWER_OFF = const(0x02)
POWER_ON = const(0x04)
DEEP_SLEEP = const(0x07)
DATA_START_TRANSMISSION = const(0x10)
DATA_REFRESH = const(0x12)

class Palette(framebuf.FrameBuffer):
    def __init__(self):
        self.buf = bytearray(1)
        super().__init__(self.buf, 4, 1, framebuf.GS2_HMSB)
    def bg(self, color):
        self.pixel(1, 0, color)
    def fg(self, color):
        self.pixel(0, 0, color)

class FB(framebuf.FrameBuffer):
    def __init__(self, *argv, **kwargs):
        self.width = 0;
        self.height = 0;
        self.palette = Palette()
        super().__init__(*argv, **kwargs)

class EPD3in0g:
    def __init__(self):
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.BLACK = BLACK
        self.WHITE = WHITE
        self.YELLOW = YELLOW
        self.RED = RED

    def software_reset(self):
        self.RST.value(1) # ensure reset is not active
        sleep_ms(20)
        self.RST.value(0) # reset
        sleep_ms(2)
        self.RST.value(1) # release reset
        sleep_ms(20)

    def send_command(self, command, data=None):
        self.DC.value(0) # select command
        self.CS.value(0) # active spi
        self.SPI.write(bytearray([command]))
        self.CS.value(1) # deactive spi
        if data is not None:
            self.send_data(data)

    def send_data(self, data):
        self.DC.value(1) # select data
        self.CS.value(0) # active spi
        self.SPI.write(bytearray([data]) if isinstance(data, int) else bytearray(data))
        self.CS.value(1) # deactive spi
        
    def wait_for_idle(self):
        while(self.BUSY.value() == 0): # low = busy, high = idle
            sleep_ms(20)

    def refresh_display(self):
        self.send_command(DATA_REFRESH, 0x00) # magic numbers
        self.wait_for_idle()

        self.send_command(POWER_OFF, 0x00) # magic numbers
        self.wait_for_idle()
        
    def init(self):
        # init all io
        self.RST = Pin(RST_PIN, Pin.OUT)
        self.DC = Pin(DC_PIN, Pin.OUT)
        self.CS = Pin(CS_PIN, Pin.OUT)
        self.BUSY = Pin(BUSY_PIN, Pin.IN)

        self.SPI = SPI(1, baudrate=4000000, polarity=0, phase=0)

        # reset or wake up the display from sleep
        self.software_reset()

        # seriously just a bunch of magic setup commands and data that I can't find the documentation for
        self.send_command(0x66, b'\x49\x55\x13\x5d\x05\x10')
        self.send_command(0xb0, 0x00)
        self.send_command(0x01, b'\x0f\x00')
        self.send_command(0x00, b'\x4f\x6b')
        self.send_command(0x06, b'\xd7\xde\x12')
        self.send_command(0x61, b'\x00\xa8\x01\x90')
        self.send_command(0x50, 0x37)
        self.send_command(0x60, b'\x0c\x05')
        self.send_command(0xe3, 0xff)
        self.send_command(0x84, 0x00)
        return 0

    # input image is a bytearray where each byte is four pixels
    def display(self, image):
        width = self.width // 4
        height = self.height

        self.send_command(POWER_ON)
        self.wait_for_idle()

        # tell the display to await for data and write data byte by byte
        self.send_command(DATA_START_TRANSMISSION)
        for j in range(0, height):
            for i in range(0, width):
                self.send_data(image[i + j * width])

        # actually do the drawing
        self.refresh_display()
        
    def clear(self, color=WHITE):
        # create a byte with four instances of chosen color
        color_byte = color << 6 | color << 4 | color << 2 | color

        self.send_command(POWER_ON)
        self.wait_for_idle()

        # tell the display to await for data and write data byte by byte
        self.send_command(DATA_START_TRANSMISSION)
        for _ in range(0, EPD_HEIGHT):
            for _ in range(0, EPD_WIDTH // 4):
                self.send_data(color_byte)

        # actually do the drawing
        self.refresh_display()

    def sleep(self):
        self.send_command(POWER_OFF, 0x00) # magic numbers
        self.send_command(DEEP_SLEEP, 0xa5) # magic numbers
 
        sleep_ms(200)
        self.SPI.deinit()

    # create a rotated framebuf for drawing
    def create_frame(self):
        buf = bytearray(EPD_WIDTH * EPD_HEIGHT // 4)
        # EPD_WIDTH and EPD_HEIGHT are reversed because the framebuf is rotated
        fb = FB(buf, EPD_HEIGHT, EPD_WIDTH, framebuf.GS2_HMSB)
        fb.width = EPD_HEIGHT
        fb.height = EPD_WIDTH
        fb.fill(WHITE)
        return (
            fb,
            buf,
            EPD_HEIGHT, # frame width
            EPD_WIDTH, # frame height
        )

    # image needs to be rotate 90 degrees
    # epd wants the largest to be first
    # HMSB has the lowest bit first
    # could be optimized but not necessary
    def get_buffer(self, buf):
        rotated_buf = bytearray(EPD_WIDTH * EPD_HEIGHT // 4)

        # EPD_WIDTH and EPD_HEIGHT are reversed because the framebuf is rotated
        for row in range(EPD_WIDTH):
            for col in range(EPD_HEIGHT // 4):
                # the byte we are currently on
                byte = buf[row * EPD_HEIGHT // 4 + col]
                # calculate the index in a rotated byte for this row
                row_shift = (3 - row % 4) * 2
                # calculate the bytes in which the pixels are in the rotated buffer
                _a = ((EPD_HEIGHT - col * 4 - 1) * EPD_WIDTH + row) // 4
                _b = ((EPD_HEIGHT - col * 4 - 2) * EPD_WIDTH + row) // 4
                _c = ((EPD_HEIGHT - col * 4 - 3) * EPD_WIDTH + row) // 4
                _d = ((EPD_HEIGHT - col * 4 - 4) * EPD_WIDTH + row) // 4
                # set the bits in those bytes
                rotated_buf[_a] = rotated_buf[_a] | ((byte >> 0 & 0b11) << row_shift)
                rotated_buf[_b] = rotated_buf[_b] | ((byte >> 2 & 0b11) << row_shift)
                rotated_buf[_c] = rotated_buf[_c] | ((byte >> 4 & 0b11) << row_shift)
                rotated_buf[_d] = rotated_buf[_d] | ((byte >> 6 & 0b11) << row_shift)

        return rotated_buf
