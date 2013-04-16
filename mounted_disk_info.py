#!/usr/bin/python
import os
def get_fs_info(path):
    """Get free/used/total space info for a filesystem

    :param path: Any dirent on the filesystem
    :returns: A dict containing:

             :free: How much space is free (in bytes)
             :used: How much space is used (in bytes)
             :total: How big the filesystem is (in bytes)
    """
    hddinfo = os.statvfs(path)
    total = hddinfo.f_frsize * hddinfo.f_blocks
    free = hddinfo.f_frsize * hddinfo.f_bavail
    used = hddinfo.f_frsize * (hddinfo.f_blocks - hddinfo.f_bfree)
    return {'total': int(float(total)/1024/1024),
            'free': int(float(free)/1024/1024),
            'used': int(float(used)/1024/1024)}

def get_mounted_disks():
    with open('/proc/mounts', 'r') as f:
        mounts = f.readlines()
    #print mounts
    for mount in mounts:
        if mount.startswith('/dev/'):
            mount = mount.split()
            dev = mount[0]
            target = mount[1]
            if target == '/':
                print 'root fs'
            else:
                print 'logical fs'
            print '%(dev)s mounts to %(target)s' % locals()
            print 'realpath:', os.path.realpath(dev)
            print 'space info(MB):', get_fs_info(target)

if __name__ == '__main__':
    get_mounted_disks()
