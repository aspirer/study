

import requests


"""
Data structure of instances cache:
{
	"uuid1": {
		"name1": "instance-name1",
		"domain1": "domain-in-libvirt",
		"last_heartbeat": "123457890",
		"last_monitor": "1235680",
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

}
"""

TOKEN = None
TENANT_ID = None

def _get_token():
    global TOKEN
    data = {"auth": {"tenantName": "demo",
                     "passwordCredentials":
                            {"username": "nbs",
                             "password": "nbs"}}}
    headers = {'content-type': 'application/json'}
    try:
        r = requests.post(auth_url, data=json.dumps(data), headers=headers)
        TOKEN = r.json()['access']['token']['id']
        TENANT_ID = r.json()['access']['token']['tenant']['id']
    except :
        TOKEN = None
        TENANT_ID = None


# get instances running on this host
def get_all_instances_on_host():
    headers = {"Accept": "application/json", "X-Auth-Token": TOKEN}
    params = {"host": "114-113-199-8"}
    r = requests.get(api_url, params=json.dumps(params), headers=headers)
    return r.json()["servers"]



# store/cache data of instance
class Instance(object):
    def __init__(self):
  		self.name =
		"domain1": "domain-in-libvirt",
		"last_heartbeat": "123457890",
		"last_monitor": "1235680",
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

    def update_last_heartbeat(self, last_heartbeat):
        self.last_heartbeat = last_heartbeat

    def update_last_monitor(self, last_monitor):
        self.last_monitor = last_monitor

    def save_temp(self, new_data):
        # store temp data of instance

    def read_temp(self):


class InstanceThread():
    def __init__(self, hb_lock, dc_lock, instances, delay):
        self.hb_lock = hb_lock
        self.dc_lock = dc_lock

        Timer(delay,)

    def update_instances(self, cached_instances):
        return_instancs = {}
        running_instances = get_all_instances_on_host()
        running_uuids = [inst['uuid'] for inst in running_instances]

        for inst in cached_instances.iteritems():
            if inst in running_uuids:
                return_instancs[inst] = cached_instances[]

        return self.
