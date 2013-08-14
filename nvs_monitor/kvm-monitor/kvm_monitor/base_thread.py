
import threading
import time

import helper


class BaseThread(object):
    RUN_TH = True

    def __init__(self):
        self.helper = helper.LibvirtQemuHelper()
        self.last_run_time = 0

    def start(self):
        thr = threading.Thread(target=self.serve)
        thr.start()
        return thr
