
from threading import Timer
import time

import helper


class BaseThread(object):
    RUN_TH = True

    def __init__(self):
        self.helper = helper.LibvirtQemuHelper()
        self.last_run_time = 0

    def _run(self):
        if self.RUN_TH:
            return ((long(time.time()) - self.last_run_time) >= self.delay)

    def start(self):
        if self._run():
            Timer(0, self.serve).start()
            self.last_run_time = long(time.time())