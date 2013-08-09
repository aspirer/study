
import libvirt_qemu
from libvirt_qemu import libvirt

class LibvirtQemuHelper():
    def __init__(self):
        self._conn = libvirt.open(None)

    def _get_conn(self):
        self._conn = libvirt.open(None)

    def _test_conn(self):
        # if conn disconnect, get a new one
        try:
            self._conn.getLibVersion()
            return True
        except libvirt.libvirtError as e:
            if (e.get_error_code() in (libvirt.VIR_ERR_SYSTEM_ERROR,
                                       libvirt.VIR_ERR_INTERNAL_ERROR) and
                e.get_error_domain() in (libvirt.VIR_FROM_REMOTE,
                                         libvirt.VIR_FROM_RPC)):
                # LOG.debug(_('Connection to libvirt broke'))
                return False
            raise

    def get_domain_by_uuid(self, instance_uuid):
        if not self._test_conn():
            try:
                self._get_conn()
            except libvirt.libvirtError as e:
                # LOG.debug(_('get connection to libvirt failed'))
                return None
        try:
            domain = self._conn.lookUpByUUIDString(instance_uuid)
            return domain
        except libvirt.libvirtError as e:
            if e.get_error_code() in (libvirt.VIR_ERR_NO_DOMAIN,):
                # LOG.debug(_('instance not found in libvirt'))
            return None

    @staticmethod
    def exec_qga_command(domain, cmd, timeout=3, flags=0):
        try:
            return libvirt_qemu.qemuAgentCommmand(domain, cmd, timeout, flags)
        except libvirt.libvirtError as e:
            # LOG.error()
            return None
