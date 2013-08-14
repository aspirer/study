
import libvirt_qemu
from libvirt_qemu import libvirt
import threading

import log

LOG = log.getLogger(__name__)


try:
    LOG.info("Initing libvirt connection")
    _LIBVIRT_CONN = libvirt.open(None)
except libvirt.libvirtError as e:
    LOG.error("Init connection to libvirt failed, exception: %s" % e)
    raise e

CONN_LOCK = threading.RLock()


class LibvirtQemuHelper(object):
    def __init__(self):
        global _LIBVIRT_CONN
        if _LIBVIRT_CONN:
            self._conn = _LIBVIRT_CONN
        else:
            self._conn = None

    def _get_conn(self):
        LOG.info("Getting new libvirt connection")
        global _LIBVIRT_CONN
        _LIBVIRT_CONN = libvirt.open(None)
        self._conn = _LIBVIRT_CONN
        LOG.info("Got new libvirt connection")

    def _test_conn(self):
        # if conn disconnect, get a new one
        if not self._conn:
            return False
        try:
            self._conn.getLibVersion()
            return True
        except libvirt.libvirtError as e:
            if (e.get_error_code() in (libvirt.VIR_ERR_SYSTEM_ERROR,
                                       libvirt.VIR_ERR_INTERNAL_ERROR) and
                    e.get_error_domain() in (libvirt.VIR_FROM_REMOTE,
                                         libvirt.VIR_FROM_RPC)):
                LOG.warn("Connection to libvirt is broken")
                return False
            raise

    def list_all_domains(self):
        global CONN_LOCK
        with CONN_LOCK:
            try:
                if not self._test_conn():
                    self._get_conn()
            except libvirt.libvirtError as e:
                LOG.error("Connect to libvirt failed, exception: %s" % e)
                return []

            try:
                return self._conn.listAllDomains()
            except libvirt.libvirtError as e:
                LOG.warn("List all domains failed, exception: %s" % e)
                return []

    @staticmethod
    def exec_qga_command(domain, cmd, timeout=6, flags=0):
        LOG.debug("Going to execute qga cmd %s" % cmd)
        try:
            return libvirt_qemu.qemuAgentCommand(domain, cmd, timeout, flags)
        except libvirt.libvirtError as e:
            LOG.warn("Run qga cmd %s failed, uuid: %s, exception: %s" %
                        (cmd, domain.UUIDString(), e))
            return None
