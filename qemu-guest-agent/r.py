
from threading import Timer
import timer
import time
i = timer.i
r = timer.r




class th2(object):
    def __init__(self, delay, l):
        self.delay = delay
        self.l = l
        #self.r = r

    def func(self):
        global i
        global r

        with self.l:
            if len(r):
                key = r.keys()[-1]
                print "\t\tth2 sleep 2s"
                time.sleep(2)
                print "\t\tth2 sleep end"
                r.pop(key)
            print "\t\tth2: r = ", r
            print "\t\tth2: i = ", i


        if i < 10:
            Timer(self.delay, self.func).start()

    def start(self):
        Timer(self.delay, self.func).start()
