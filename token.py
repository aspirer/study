#! /usr/bin/python

import memcache
import sys


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: %s memcache_server token_list_file" % sys.argv[0]
        exit(1)
    memcache_server = [sys.argv[1]]
    token_file = sys.argv[2]
    try:
        mc = memcache.Client(memcache_server, debug=0)
        tokens = []
        with open(token_file) as f:
            tokens = f.readlines()
        for t in tokens:
            t = t.strip()
            if mc.get('token-' + t):
                print 'token %s is in memcached' % t
            else:
                print '\t\t\t\t\t\t\t WARN: token %s is not found!!!!' % t
    except Exception as e:
        print e
