#! /usr/bin/python


import sys

from oslo.config import cfg

import heartbeat
import data_stat


global_opts = [
    cfg.BoolOpt('enable_monitor',
               default=True,
               help='Enable vm monitor'),
    cfg.BoolOpt('enable_heartbeat',
               default=True,
               help='Enable reporting vm heartbeat'),
    ]

CONF = cfg.CONF
CONF.register_opts(global_opts)


# main loop for monitor data collecting
def main():
    print "loading config files: %s" % sys.argv[1:]
    CONF(sys.argv[1:])

    # create the heartbeat thread
    if CONF.enable_heartbeat:
        heartbeat_thr = heartbeat.HeartBeatThread()
        heartbeat_thr.start()

    # create the monitor data collect thread
    if CONF.enable_monitor:
        data_stat_thr = data_stat.MonitorThread()
        data_stat_thr.start()


# main entry
if __name__ == "__main__":
    # signal handle

    # LOG.info("start monitor")
    # daemonize()
    #heartbeat.HeartBeatThread.stop()
    #data_stat.MonitorThread.stop()
    #print heartbeat.HeartBeatThread.RUN_TH
    #print data_stat.MonitorThread.RUN_TH

    main()
    # LOG.info("stop monitor")



