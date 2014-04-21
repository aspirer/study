#!/usr/bin/env python

import json
import Queue
import threading
import time

import libvirt
import libvirt_qemu


queue = Queue.Queue()

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

class ThreadUrl(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            #grabs domain from queue
            dom = self.queue.get()
            print guest_ping(dom)

            #signals to queue job is done
            self.queue.task_done()


if __name__ == '__main__':
    #spawn a pool of threads, and pass them queue instance
    for i in range(5):
        t = ThreadUrl(queue)
        t.setDaemon(True)
        t.start()

    conn = libvirt.open(None)
    while True:
        start = time.time()
        #populate queue with domain
        doms = conn.listAllDomains()
        for dom in doms:
            queue.put(dom)
        print "******Elapsed Time: %s" % (time.time() - start)
        time.sleep(5)

    #wait on the queue until everything has been processed
    queue.join()
