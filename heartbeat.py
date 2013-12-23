#! /usr/bin/python

import datetime
import memcache
import sys


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: heartbeat memcache_server uuid"
        exit(1)
    memcache_server = [sys.argv[1]]
    uuid = sys.argv[2]
    key = '%s_heart' % uuid
    value = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    try:
        mc = memcache.Client(memcache_server, debug=0)
        mc.set(key, value)
        print "Heartbeat reports successfully, Latest heartbeat timestamp: %s" % mc.get(key)
    except Exception as e:
        print e
