
import json
import time

from libvirt_qemu import libvirt
from base_thread import BaseThread
from oslo.config import cfg
import log
import sender
import utils


heartbeat_opts = [
    cfg.IntOpt('heartbeat_cmd_timeout',
               default=6,
               help='The timeout seconds of getting heartbeat by qga, '
                    'note that this value `must` larger than 5s, because '
                    'the timeout of libvirt checking qga status is 5s'),
    ]

CONF = cfg.CONF
CONF.register_opts(heartbeat_opts)

LOG = log.getLogger(__name__)


class HeartBeatThread(BaseThread):
    def __init__(self):
        super(HeartBeatThread, self).__init__()
        self.sender = sender.MemcacheClient()
        self.qga_cmd = {"execute": "guest-sync", "arguments": {"id": 0}}

    @staticmethod
    def stop():
        HeartBeatThread.RUN_TH = False
        LOG.debug("Set RUN_TH to False")

    def serve(self):
        LOG.info("Heartbeat thread start")
        domains = self.helper.list_all_domains()
        for dom in domains:
            if not self.RUN_TH:
                LOG.info("Break from hearbeat thread")
                break

            uuid = utils.get_domain_uuid(dom)
            if not uuid:
                LOG.warn("Get domain uuid failed")
                continue

            if not utils.is_active(dom):
                LOG.info("domain is not active, uuid %s" % uuid)
                continue

            heartbeat_cmd = json.dumps({"execute": "guest-ping"})
            response = self.helper.exec_qga_command(dom, heartbeat_cmd,
                                            timeout=CONF.heartbeat_cmd_timeout)
            LOG.debug("Ping command response from qga: %s" % response)
            if response:
                self.sender.report_heartbeat(uuid)
            else:
                LOG.warn("Ping command failed, uuid: %s" % uuid)

        LOG.info("Heartbeat thread end")
