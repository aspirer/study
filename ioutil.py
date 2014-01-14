#! /usr/bin/python

import os
import random
import sys
import time

HZ = 100

def calc_ioutil(old, new, intv):
    return ((new - old) / intv * HZ)/10

def read_disk_stat(dev):
    disk_stat = os.path.join('/sys/block/', dev, 'stat')
    with open(disk_stat, 'r') as df:
        ds = df.readline()
    return float(ds.split()[9])

def get_uptime():
    with open('/proc/uptime', 'r') as uf:
        ut = uf.readline()
    return (float(ut.split()[0])*HZ + float(ut.split()[1])*HZ/100)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        interval = 1.0 * 1000
        dev = 'vda'
    else:
        interval = float(sys.argv[1]) * 1000
        dev = sys.argv[2]

    old_tot_ticks = 0
    new_tot_ticks = 0
    old_uptime = 0
    new_uptime = 0
    first_time = True
    while True:
        if first_time:
            print 'first time, ignore output'
            first_time = False
            new_tot_ticks = read_disk_stat(dev)
            new_uptime = get_uptime()
        else:
            old_tot_ticks = new_tot_ticks
            new_tot_ticks = read_disk_stat(dev)
            old_uptime = new_uptime
            new_uptime = get_uptime()
            intv = new_uptime - old_uptime
            print '%util: '+str(calc_ioutil(old_tot_ticks, new_tot_ticks, 100))+'%'

        time.sleep(interval/1000)
