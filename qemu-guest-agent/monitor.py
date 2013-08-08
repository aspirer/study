#! env


import base64
import ConfigParser


import libvirt_qemu
import requests


# store/cache data of instances
"""
Data structure of instances:
[
    {
        "uuid1": "instance-uuid1",
        "name1": "instance-name1",
        "domain1": "domain-in-libvirt",
        "temp": {
            'total_cpu_time': 0,
            'last_cpu_idle_time': 0,
            'disk_read_request': 0,
            'disk_write_request': 0,
            'disk_read': 0,
            'disk_write': 0,
            'disk_read_delay': 0,
            'disk_write_delay': 0,
            'network_receive_bytes': 0,
            'network_transfer_bytes': 0,
            'disk_partition_info': {

            },
            'timestamp': 0
        }
    },
]
"""
class Instances(object):
    def __init__():
        self.instances = []

    def update(instances):
        # update cache of instances

    def store_temp(instance_uuid):
        # store temp data of instance

    def read_temp(instance_uuid):


class LibvirtQemuHelper():
    def __init__():
        self.conn = xxx

    def _get_conn():
        self.conn = yyyy

    def _test_conn():
        # if conn disconnect, get a new one
        try:
            self.conn.getLibVersion():
        except Exception:
            self._get_conn()

    def get_domain_by_uuid(instance_uuid):




# get instances running on this host
class NovaClient(object):
    def __init__():



class GetSystemUsage(object):




class SendRequest(object):




class DataFormater(object):




# main loop for monitor data collecting
def main():

    while True:
        # get all instances on this host

        for instance in instances:

            # store/cache instances

            # collect monitor data from instance

            # format data

            # send data to cloud monitor

        time.sleep(delay)




# main entry
if __name__ == "__main__":




