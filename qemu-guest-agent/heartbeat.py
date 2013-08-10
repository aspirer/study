﻿
import json
import time

from libvirt_qemu import libvirt
from base_thread import BaseThread

import sender

RUN_HB = True
enable_heartbeat = True
heartbeat_delay = 5
heartbeat_cmd_timeout = 1

class HeartBeatThread(BaseThread):
    def __init__(self):
        super(HeartBeatThread, self).__init__()
        global heartbeat_delay
        self.delay = heartbeat_delay
        self.sender = sender.MemcacheClient()
        self.qga_cmd = {"execute": "guest-sync", "arguments": {"id": 0}}

    def _run(self):
        global RUN_HB
        global enable_heartbeat
        if enable_heartbeat:
            return RUN_HB
        else:
            return False

    def serve(self):
        print "-----heartbeat start: ", time.asctime()
        domains = self.helper.list_all_domains()
        for dom in domains:
            self.qga_cmd["arguments"]["id"] = int(time.time())
            try:
                uuid = dom.UUIDString()
                global heartbeat_cmd_timeout
                result = self.helper.exec_qga_command(dom,
                                        json.dumps(self.qga_cmd),
                                        timeout=heartbeat_cmd_timeout)
                print "qga response: %s" % result
            except libvirt.libvirtError as e:
                print "run qga cmd error, uuid: %s, exception: %s" % (uuid, e)
            else:
                self.sender.report_heartbeat(uuid)
        print "-----heartbeat end: ", time.asctime()

        self.start()