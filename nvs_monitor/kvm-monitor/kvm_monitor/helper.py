
import libvirt_qemu
from libvirt_qemu import libvirt
import threading

import log

LOG = log.getLogger(__name__)


def _connect_auth_cb(creds, opaque):
    if len(creds) == 0:
        return 0
    LOG.warn("Can not handle auth request for %d credentials" % len(creds))

AUTH = [[libvirt.VIR_CRED_AUTHNAME,
         libvirt.VIR_CRED_ECHOPROMPT,
         libvirt.VIR_CRED_REALM,
         libvirt.VIR_CRED_PASSPHRASE,
         libvirt.VIR_CRED_NOECHOPROMPT,
         libvirt.VIR_CRED_EXTERNAL],
        _connect_auth_cb,
        None]

_LIBVIRT_CONN = None

CONN_LOCK = threading.RLock()


class LibvirtQemuHelper(object):
    def __init__(self):
        self._get_conn()

    def _get_conn(self):
        LOG.info("Getting new libvirt auth connection")
        global _LIBVIRT_CONN
        global AUTH
        _LIBVIRT_CONN = libvirt.openAuth('qemu:///system', AUTH, 0)
        self._conn = _LIBVIRT_CONN
        LOG.info("Got new libvirt auth connection, version: %s" %
                    self._conn.getLibVersion())

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
