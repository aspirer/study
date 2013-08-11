#! /usr/bin/python

import time
import threading
from threading import Timer

i = 1
r = {"a": "b", "c": "d"}
RUN = True
l1 = threading.RLock()
class th1(object):
    def __init__(self, delay):
        self.delay = delay
        #self.l = l
        #self.r = r

    def func1(self):
        global l1
        with l1:
            global i
            global r
            lr = len(r)
            if lr < 3:
                r[i] = i
            else:
                r = {}
            i += 1
            print "th1: r = ", r
            print "th1: i = ", i

            if i < 10:
                Timer(self.delay, self.func1).start()


    def func2(self):
        global l1
        with l1:
            global i
            global r
            if len(r):
                key = r.keys()[-1]
                print "\t\tth2 sleep 2s"
                time.sleep(2)
                print "\t\tth2 sleep end"
                r.pop(key)
            print "\t\tth2: r = ", r
            print "\t\tth2: i = ", i



            if i < 5:
                Timer(self.delay, self.func2).start()

    def start(self):
        print "start th1"
        Timer(self.delay, self.func1).start()
        print "start th2"
        Timer(self.delay, self.func2).start()





if __name__ == "__main__":

    #l2 = threading.RLock()
    d1 = 0
    d2 = 1

    # global R

    TH1 = th1(d1)


    TH1.start()



