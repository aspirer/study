
import libvirt_qemu
from libvirt_qemu import libvirt
import uuid

import threading

_LIBVIRT_CONN = libvirt.open(None)

LOCK = threading.RLock()

def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

    """
    try:
        return str(uuid.UUID(val)) == val
    except (TypeError, ValueError, AttributeError):
        return False


class LibvirtQemuHelper(object):
    def __init__(self):
        print "init libvirt conn"
        global _LIBVIRT_CONN
        if _LIBVIRT_CONN:
            self._conn = _LIBVIRT_CONN
        else:
            self._conn = None

    def _get_conn(self):
        print "get new libvirt conn"
        global _LIBVIRT_CONN
        try:
            _LIBVIRT_CONN = libvirt.open(None)
        except libvirt.libvirtError as e:
            print "get connection to libvirt failed, exception: %s" % e
        else:
            self._conn = _LIBVIRT_CONN

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
                print "test connection to libvirt failed"
                return False
            raise

    def list_all_domains(self):
        global LOCK
        with LOCK:
            if not self._test_conn():
                try:
                    self._get_conn()
                except libvirt.libvirtError as e:
                    print "get connection to libvirt failed, exception: %s" % e
                    return []
            try:
                return self._conn.listAllDomains()
            except libvirt.libvirtError as e:
                print "get all domain ids failed, exception: %s" % e
                return []

    def get_domain(self, id):
        if not id:
            return None

        if not self._test_conn():
            try:
                self._get_conn()
            except libvirt.libvirtError as e:
                print "get connection to libvirt failed"
                return None
        try:
            if is_uuid_like(id):
                domain = self._conn.lookupByUUIDString(id)
            else:
                domain = self._conn.lookupByID(id)
            return domain
        except libvirt.libvirtError as e:
            if e.get_error_code() in (libvirt.VIR_ERR_NO_DOMAIN,):
                # LOG.debug(_('instance not found in libvirt'))
                print "instance not found in libvirt"
            else:
                print "get domain error, exception: %s" % e
            return None

    @staticmethod
    def exec_qga_command(domain, cmd, timeout=1, flags=0):
        try:
            return libvirt_qemu.qemuAgentCommand(domain, cmd, timeout, flags)
        except libvirt.libvirtError as e:
            print "run qga cmd %s cmd error, uuid: %s, exception: %s" % (cmd, uuid, e)
            return None
