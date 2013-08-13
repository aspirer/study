
import helper
from threading import Timer

class BaseThread(object):
    RUN_TH = True

    def __init__(self):
        self.helper = helper.LibvirtQemuHelper()

    def _run(self):
        return self.RUN_TH

    def serve(self):
        print "not implement"

    def start(self):
        if self._run():
            Timer(self.delay, self.serve).start()