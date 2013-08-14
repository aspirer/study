#! /usr/bin/python

import signal
import sys
import time

from oslo.config import cfg

import heartbeat
import data_stat
import log

global_opts = [
    cfg.BoolOpt('enable_monitor',
               default=True,
               help='Enable vm monitor'),
    cfg.BoolOpt('enable_heartbeat',
               default=True,
               help='Enable reporting vm heartbeat'),
    cfg.FloatOpt('check_interval',
                default=0.5,
                help='The interval time to check run thread or not'),
    ]

CONF = cfg.CONF
CONF.register_opts(global_opts)

LOG = log.getLogger(__name__)

RUN = True


def signal_handler(signum, frame):
    LOG.info("Receive signal: %s" % signum)
    global RUN
    RUN = False
    heartbeat.HeartBeatThread.stop()
    data_stat.MonitorThread.stop()


# main loop for monitor data collecting
def main():
    LOG.info("Enable heartbeat: %s" % CONF.enable_heartbeat)
    LOG.info("Enable monitor: %s" % CONF.enable_monitor)

    # create the heartbeat thread
    if CONF.enable_heartbeat:
        heartbeat_thr = heartbeat.HeartBeatThread()

    # create the monitor data collect thread
    if CONF.enable_monitor:
        data_stat_thr = data_stat.MonitorThread()

    while RUN:
        if CONF.enable_heartbeat and isinstance(heartbeat_thr,
                    heartbeat.HeartBeatThread):
            heartbeat_thr.start()

        if CONF.enable_monitor and isinstance(data_stat_thr,
                    data_stat.MonitorThread):
            data_stat_thr.start()

        time.sleep(CONF.check_interval)


# main entry
if __name__ == "__main__":
    LOG.info("Start monitor")
    # signal handle
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # daemonize()

    LOG.info("loading config files: %s" % sys.argv[2:])
    CONF(sys.argv[1:])
    #import ipdb;ipdb.set_trace()
    main()

    LOG.info("Nvs monitor is stopped")
