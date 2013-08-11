#! /usr/bin/python



# import ConfigParser


import time

import heartbeat
import data_stat


enable_heartbeat = True
enable_monitor = True


# main loop for monitor data collecting
def main():

    # create the heartbeat thread
    if enable_heartbeat:
        heartbeat_thr = heartbeat.HeartBeatThread()
        heartbeat_thr.start()

    # create the monitor data collect thread
    if enable_monitor:
        data_stat_thr = data_stat.MonitorThread()
        data_stat_thr.start()


# main entry
if __name__ == "__main__":
    # signal handle

    # LOG.info("start monitor")
    # daemonize()
    main()
    # LOG.info("stop monitor")



