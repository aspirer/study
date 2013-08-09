#!/usr/bin/python


import base64
import ConfigParser

RUN = True

# main loop for monitor data collecting
def main():
    instances = {}
    # create three threads

    # two locks is needed(one for heartbeat, another for monitor)

    # get all instances on this host in a thread(lock the two locks)
    instance.get_instance_on_host(instances)

    # handle heartbeat in another thread(lock heartbeat)
    heartbeat.report(instances)

    # then collect the monitor data in the last thread(lock monitor)
    data_stat.report(instances)



# main entry
if __name__ == "__main__":
    # signal handle

    # LOG.info("start monitor")
    # daemonize()
    main()
    # LOG.info("stop monitor")



