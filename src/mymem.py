import gc
import sys


def get_mem():
    if 'esp' in sys.platform:
        return gc.mem_free()
    else:
        return 0

