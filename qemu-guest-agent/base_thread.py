
import helper
from threading import Timer

class BaseThread(object):
    def __init__(self):
        self.helper = helper.LibvirtQemuHelper()

    def _run(self):
        print "not implement"

    def serve(self):
        print "not implement"

    def start(self):
        if self._run():
            Timer(self.delay, self.serve).start()