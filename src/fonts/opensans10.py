# Licensed under the Open Font License https://openfontlicense.org/
# https://fonts.google.com/specimen/Open+Sans
# Code generated by font_to_py.py.
# Font: OpenSans-Regular.ttf Char set: 0123456789
# Cmd: ./font_to_py.py -c 0123456789 OpenSans-Regular.ttf 10 opensans10.py
version = '0.42'

def height():
    return 10

def baseline():
    return 10

def max_width():
    return 8

def hmap():
    return True

def reverse():
    return False

def monospaced():
    return False

def min_ch():
    return 48

def max_ch():
    return 63

_font =\
b'\x06\x00\x78\x0c\x04\x08\x10\x20\x20\x00\x20\x20\x08\x00\x3c\x66'\
b'\x42\x42\x42\x42\x42\x42\x66\x3c\x08\x00\x18\x38\x48\x08\x08\x08'\
b'\x08\x08\x08\x08\x08\x00\x3c\x46\x02\x02\x04\x0c\x18\x30\x60\x7e'\
b'\x08\x00\x3c\x46\x02\x04\x38\x06\x02\x02\x06\x7c\x08\x00\x04\x0c'\
b'\x14\x14\x24\x44\x44\xff\x04\x04\x08\x00\x7e\x40\x40\x40\x7c\x06'\
b'\x02\x02\x06\x7c\x08\x00\x1e\x20\x60\x40\x5c\x62\x42\x42\x62\x3c'\
b'\x08\x00\x7e\x02\x06\x04\x0c\x08\x08\x10\x10\x20\x08\x00\x3c\x42'\
b'\x42\x66\x38\x2c\x42\x42\x42\x3c\x08\x00\x3c\x46\x42\x42\x46\x3a'\
b'\x02\x02\x04\x78'

_index =\
b'\x00\x00\x0c\x00\x18\x00\x24\x00\x30\x00\x3c\x00\x48\x00\x54\x00'\
b'\x60\x00\x6c\x00\x78\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
b'\x00\x00\x84\x00'

_mvfont = memoryview(_font)
_mvi = memoryview(_index)
ifb = lambda l : l[0] | (l[1] << 8)

def get_ch(ch):
    oc = ord(ch)
    ioff = 2 * (oc - 48 + 1) if oc >= 48 and oc <= 63 else 0
    doff = ifb(_mvi[ioff : ])
    width = ifb(_mvfont[doff : ])

    next_offs = doff + 2 + ((width - 1)//8 + 1) * 10
    return _mvfont[doff + 2:next_offs], 10, width

