
import time
from threading import Timer

i = 1

def hello():
    print "hello, world"
    if i < 10:
        Timer(3.0, hello).start()

Timer(3.0, hello).start()



while i < 13:
    print "%d" % i
    time.sleep(1)
    i += 1