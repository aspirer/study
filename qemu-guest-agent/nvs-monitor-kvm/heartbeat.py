
import json
import time

from libvirt_qemu import libvirt
from base_thread import BaseThread
from oslo.config import cfg
import sender
import utils

RUN_HB = True

heartbeat_opts = [
    cfg.IntOpt('heartbeat_delay',
               default=5,
               help='The interval seconds of collecting vm monitor data'),
    cfg.IntOpt('heartbeat_cmd_timeout',
               default=6,
               help='The timeout seconds of getting heartbeat by qga, '
                    'note that this value `must` larger than 5s, because '
                    'the timeout of libvirt checking qga status is 5s'),
    ]

CONF = cfg.CONF
CONF.register_opts(heartbeat_opts)


class HeartBeatThread(BaseThread):
    def __init__(self):
        super(HeartBeatThread, self).__init__()
        self.delay = CONF.heartbeat_delay
        self.sender = sender.MemcacheClient()
        self.qga_cmd = {"execute": "guest-sync", "arguments": {"id": 0}}

    @staticmethod
    def stop():
        HeartBeatThread.RUN_TH = False

    def serve(self):
        print "-----heartbeat start: ", time.asctime()
        domains = self.helper.list_all_domains()
        for dom in domains:
            if not utils.is_active(dom):
                print "domain is not active %s" % dom.UUIDString()
                continue
            heartbeat_cmd = json.dumps({"execute": "guest-sync",
                                    "arguments": {"id": long(time.time())}})
            response = self.helper.exec_qga_command(dom, heartbeat_cmd,
                                            timeout=CONF.heartbeat_cmd_timeout)
            print "qga response: %s" % response
            if response:
                self.sender.report_heartbeat(utils.get_domain_uuid(dom))
            else:
                print "heartbeat command failed"
        print "-----heartbeat end: ", time.asctime()

        self.start()