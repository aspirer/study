
import json
from multiprocessing.dummy import Pool
import time

import libvirt
import libvirt_qemu


def guest_ping(dom):
    name = dom.name()
    print time.time(), name, 'start'
    if not dom.isActive():
        return None
    cmd = json.dumps({"execute": "guest-ping"})
    try:
        rsp = libvirt_qemu.qemuAgentCommand(dom, cmd, 1, 0)
    except libvirt.libvirtError as ex:
        print '%s, %s, libvirt error: %s' % (time.time(), name, ex)
        rsp = None
    except Exception as ex:
        print '%s, %s, unkown error: %s' % (time.time(), name, ex)
        rsp = None
    else:
        print time.time(), name, rsp, 'end'
    return rsp

conn = libvirt.open(None)

pn = 10
p = Pool(pn)
while True:
    doms = conn.listAllDomains()
    start = time.time()
    print '%s, %s pools start' % (start, pn)
    p.map(guest_ping, doms)
    end = time.time()
    print '%s, end' % end
    print '------%s--------' % (end - start)
    time.sleep(5)