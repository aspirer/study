
import base64
import json
import os

from libvirt_qemu import libvirt
import time
from base_thread import BaseThread
import instance
import sender

RUN_DC = True
monitor_delay = 3
read_file_time_out = 1
temp_file_timeout = 30
READ_BUF_LEN = 1024
PERIOD_TIME = 60
NET_CARD_LIST = ['eth0', ]

instances_path = "/var/lib/nova/instances/"


'''
Get system resources usage include disk, network, cpu, memory.
CPU: get cpu usage percent.
Memory: get total memory(KB), free memory and used memory datas.
Disk: get disk read/write data((KB)), requests and used delay(ms).
Network: get network I/O datas(bytes) and vm ip.
'''
class GetSystemUsage(object):
    def __init__(self, domain, helper):
        self.domain = domain
        self.helper = helper
        global instances_path
        self.instance_dir = instances_path + self.domain.name()
        if not os.path.exists(self.instance_dir):
            self.instance_dir = instances_path + self.domain.UUIDString()

        info_file = self.instance_dir + "/info"
        with open(info_file, 'r') as f:
            self.info = json.loads(f.read())

        print "init temp file"
        self.temp = {
                    'total_cpu_time': 0L,
                    'last_cpu_idle_time': 0L,
                    'disk_read_request': 0L,
                    'disk_write_request': 0L,
                    'disk_read': 0L,
                    'disk_write': 0L,
                    'disk_read_delay': 0,
                    'disk_write_delay': 0,
                    'network_receive_bytes': 0L,
                    'network_transfer_bytes': 0L,
                    'disk_partition_info': {},
                    'timestamp': 0L
                }

    def load_temp(self):
        global temp_file_timeout
        temp_file = self.instance_dir + "/temp"
        if os.path.exists(temp_file):
            try:
                print "loading temp file"
                with open(temp_file, 'r') as f:
                    temp_data = json.loads(f.read())
                elapse = long(time.time()) - temp_data['timestamp']
                if elapse >= 0 and elapse <= PERIOD_TIME + temp_file_timeout:
                    for k,v in temp_data.iteritems():
                        if k in self.temp:
                            self.temp[k] = v
                    print "loaded temp file: %s" % self.temp
                    return True
                else:
                    print "temp file time out"
                    return False
            except (KeyError, TypeError, AttributeError, ValueError) as e:
                print "temp file %s read failed, exception: %s" % (temp_file, e)
                return False
        else:
            print "temp file not found at %s" % temp_file
            return False

    def save_temp(self):
        temp_file = self.instance_dir + "/temp"
        print "save temp data of instance %s: %s" % (self.domain.UUIDString(), self.temp)
        with open(temp_file, 'w') as f:
            print "saving temp file to %s" % temp_file
            self.temp['timestamp'] = long(time.time())
            f.write(json.dumps(self.temp))
            print "saved temp file"


    """
	"return": {
		"count": 755,
		"buf-b64": "Y3B1ICA0OTYxIDAgNTQwNiA1MzQ4MT...",
		"eof": true
	}
    """
    def _read_file_from_guest(self, file, mode='r', read_eof=False):
        global read_file_time_out
        cmd_open = json.dumps({"execute": "guest-file-open",
                                 "arguments": {"path": file, "mode": mode}})

        response = self.helper.exec_qga_command(self.domain, cmd_open,
                                                timeout=read_file_time_out)
        if response:
            print "open file response: %s" % response
            try:
                handle = json.loads(response)['return']
            except (ValueError, KeyError, TypeError):
                print "get file handle failed"
                handle = None
        else:
            print "open guest file %s by qga failed, exception: %s" % (file, e)
            handle = None

        if not handle:
            return None

        global READ_BUF_LEN
        cmd_read = json.dumps({"execute": "guest-file-read",
                               "arguments": {"handle": handle,
                                             "count": READ_BUF_LEN}})
        read_file_b64 = None
        eof = False
        while not eof:
            response = self.helper.exec_qga_command(self.domain, cmd_read,
                                                    timeout=read_file_time_out)
            if response:
                print "read file response: %s" % response
                try:
                    if not read_eof:
                        # don't need to read all file contents
                        eof = True
                    else:
                        eof = json.loads(response)['return']['eof']
                    read_file_b64 = json.loads(response)['return']['buf-b64']
                except (ValueError, KeyError, TypeError):
                    print "get file handle failed"
                    read_file_b64 = None
                    break
            else:
                print "open guest file %s by qga failed, exception: %s" % (file, e)
                read_file_b64 = None
                break

        cmd_close = json.dumps({"execute": "guest-file-close",
                                "arguments": {"handle": handle}})
        self.helper.exec_qga_command(self.domain, cmd_close,
                                    timeout=read_file_time_out)

        if not read_file_b64:
            return None

        try:
            return base64.decodestring(read_file_b64)
        except binascii.Error as e:
            print "base64 decode failed, exception: %s" % e
            return None

    def _get_cpu_usage_dict(self):
        '''
            Get CPU usage(percent) by vmstat command.
            @return: {'cpu_usage': 0.0}
        '''
        cpu_stat = self._read_file_from_guest('/proc/stat')
        if cpu_stat:
            cpu_read_line = cpu_stat.splitlines()[0]
            cpu_infos = cpu_read_line.split()[1:-1]
            total_cpu_time = 0L
            for cpu_info in cpu_infos:
                total_cpu_time += long(cpu_info)
            last_cpu_time = self.temp['total_cpu_time']
            cpu_idle_time = long(cpu_infos[3])
            last_cpu_idle_time = self.temp['last_cpu_idle_time']
            total_cpu_period = float(total_cpu_time - last_cpu_time)
            idle_cpu_period = float(cpu_idle_time - last_cpu_idle_time)

            if total_cpu_period <= 0 or idle_cpu_period < 0:
                cpu_usage = 0.0
            else:
                idle_usage = idle_cpu_period / total_cpu_period * 100
                cpu_usage = round(100 - idle_usage, 2)

            self.temp['total_cpu_time'] = total_cpu_time
            self.temp['last_cpu_idle_time'] = cpu_idle_time
        else:
            print "cpu_usage get failed, uuid: %s" % self.domain.UUIDString()
            cpu_usage = 0.0
        return {'cpu_usage': cpu_usage}

    def _get_loadavg_dict(self):
        '''
            Get loadavg info from /proc/loadavg.
            @return: {'loadavg_5': 4.32}
        '''
        loadavg_file_read = self._read_file_from_guest('/proc/loadavg')
        if loadavg_file_read:
            loadavg_info_line = loadavg_file_read.splitlines()[0]
            loadavg_5 = float(loadavg_info_line.split()[1])
        else:
            print "loadavg_5 get failed, uuid: %s" % self.domain.UUIDString()
            loadavg_5 = 0.0
        return {'loadavg_5': loadavg_5}

    def _get_memory_usage_dict(self):
        '''
            Get memory info(MB) from /proc/meminfo.
            @return: {'total_memory': 1, 'free_memory': 1,
                      'used_memory': 1, 'memory_usage_rate': 45}
            free_memory = MemFree + Buffers + Cached
            used_memory = MemTotal - free_memory
            memory_usage_rate = used_memory * 100 / MemTotal
        '''
        mem_usage = {
            'total_memory': 0,
            'free_memory': 0,
            'used_memory': 0,
            'memory_usage_rate': 0
        }
        mem_file_read = self._read_file_from_guest('/proc/meminfo')
        if mem_file_read:
            mem_info_lines = mem_file_read.splitlines()
        else:
            print "mem_usage get failed, uuid: %s" % self.domain.UUIDString()
            return mem_usage

        mem_usage['total_memory'] = long(mem_info_lines[0].split()[1]) / 1024
        mem_usage['free_memory'] = (long(mem_info_lines[1].split()[1])
                       + long(mem_info_lines[2].split()[1])
                       + long(mem_info_lines[3].split()[1])) / 1024
        mem_usage['used_memory'] = (mem_usage['total_memory'] -
                                    mem_usage['free_memory'])
        mem_usage['memory_usage_rate'] = ((mem_usage['used_memory'] * 100) /
                                            mem_usage['total_memory'])

        return mem_usage

    def _get_disk_data(self):
        '''
            Use command df to get all partitions` used/available disk
            datas(MB).
            Find string start with '/dev/' and split it with '/' to get
            disks` name into dict disks. Like '/dev/vda1' to get 'vda'.
            Call _get_disk_data_by_proc() to get datas from /proc/diskstats.
            @return: {
                      'disk_read_request': 0, 'disk_write_request': 0,
                      'disk_read': 0, 'disk_write': 0, 'disk_read_delay': 1,
                      'disk_write_delay': 1, 'used_disk': 0,
                      'avail_disk': 0,
                      'disk_partition_info': {'sys': ['vda1'],
                                              'logic': ['vdb1', 'dm-0']}
                      'disk_partition_data': {'vda': {'avail_capacity': 500,
                                                      'partition_usage': 15}}
                    }
        '''
        def _get_mounted_disks():
            '''
                Get mounted disks/partitions from /proc/mounts.
                @return: partition:target dict: {'vda1': '/', 'dm-0': '/mnt'}
            '''
            mounted_disks = {}
            mounts_file = self._read_file_from_guest('/proc/mounts')
            if mounts_file:
                mounts = mounts_file.splitlines()
            else:
                print "mounted disks get failed, uuid: %s" % self.domain.UUIDString()
                return mounted_disks
            for mount in mounts:
                if mount.startswith('/dev/'):
                    mount = mount.split()
                    partition = os.path.realpath(mount[0]).rsplit('/')[-1]
                    target = mount[1]
                    if (partition not in mounted_disks and
                                    target not in mounted_disks.values()
                                    or (target == '/' and
                                        '/' not in mounted_disks.values())):
                        mounted_disks[partition] = target

            return mounted_disks

        def _get_fs_info(path):
            """Get free/used/total space info for a filesystem

            :param path: Any dirent on the filesystem
            :returns: A dict containing:
                     :free: How much space is free (in bytes)
                     :used: How much space is used (in bytes)
                     :total: How big the filesystem is (in bytes)
            """
            fs_info = {'total': 0.0,
                       'free': 0.0,
                       'used': 0.0}
            cmd_statvfs = json.dumps({"execute": "guest-get-statvfs",
                                      "arguments": {"path": path}})
            response = self.helper.exec_qga_command(self.domain, cmd_statvfs,
                                                    timeout=read_file_time_out)
            if response:
                print "open file response: %s" % response
                try:
                    hddinfo = json.loads(response)['return']
                except (ValueError, KeyError, TypeError):
                    print "get statvfs failed, uuid: %s" % self.domain.UUIDString()
                    hddinfo = None
            else:
                print "get statvfs failed, uuid: %s" % self.domain.UUIDString()
                return fs_info

            fs_info['total'] = (hddinfo['f_frsize'] * hddinfo['f_blocks'] /
                                1024 / 1024)
            fs_info['free'] = (hddinfo['f_frsize'] * hddinfo['f_bavail'] /
                                1024 / 1024)
            fs_info['used'] = (hddinfo['f_frsize'] * (hddinfo['f_blocks'] -
                                    hddinfo['f_bfree']) / 1024 / 1024)
            return fs_info

        def _get_patition_info(disks, total_disk_info):
            partitions = {'sys': [], 'logic': []}
            for partition, target in disks.iteritems():
                fs_info = _get_fs_info(target)
                free = fs_info['free']
                used = fs_info['used']
                total = fs_info['total']
                usage = round(used / total * 100, 2)
                total_disk_info['disk_partition_data'][partition] = {
                                        'avail_capacity': free,
                                        'partition_usage': usage
                                    }
                total_disk_info['used_disk'] += used
                total_disk_info['avail_disk'] += free
                if target == '/':
                    partitions['sys'].append(partition)
                else:
                    partitions['logic'].append(partition)

            # NOTE(hzyangtk): here to store all the partition names
            total_disk_info['disk_partition_info'] = partitions

        def _get_disk_data_by_proc(disks, total_disk_info):
            '''
                Get disks infos from /proc/diskstats, like:
                    read/write datas(KB),
                    request times(count time),
                    read/write paid time(ms) and so on.
                And set the datas into total_disk_info dict.
            '''
            partitions = disks.keys()
            diskstats = self._read_file_from_guest('/proc/diskstats')
            if diskstats:
                disk_datas = diskstats.splitlines()
            else:
                print "get diskstats failed, uuid: %s" % self.domain.UUIDString()
                return

            for disk_data in disk_datas:
                datas = disk_data.split()
                if datas[2] in partitions:
                    total_disk_info['disk_read_request'] += long(datas[3])
                    total_disk_info['disk_write_request'] += long(datas[7])
                    total_disk_info['disk_read'] += long(datas[5]) / 2
                    total_disk_info['disk_write'] += long(datas[9]) / 2
                    total_disk_info['disk_read_delay'] += long(datas[6])
                    total_disk_info['disk_write_delay'] += long(datas[10])

        disks = _get_mounted_disks()
        total_disk_info = {
            'disk_read_request': 0,
            'disk_write_request': 0,
            'disk_read': 0,
            'disk_write': 0,
            'disk_read_delay': 0,
            'disk_write_delay': 0,
            'used_disk': 0,
            'avail_disk': 0,
            'disk_partition_info': {},
            'disk_partition_data': {}
        }

        if disks:
            _get_patition_info(disks, total_disk_info)
            _get_disk_data_by_proc(disks, total_disk_info)

        return total_disk_info

    def _get_disk_usage_rate_dict(self):
        '''
            Assemble all the datas collected from _get_disk_data().
            @return: {
                      'disk_read_request': 0.0, 'disk_write_rate': 0.0,
                      'disk_write_delay': 0.0, 'disk_read_delay': 0.0,
                      'disk_read_rate': 0.0, 'used_disk': 0,
                      'disk_write_request': 0, 'disk_partition_info': ['vda1'],
                      'disk_partition_data': {'vda': {'avail_capacity': 500,
                                                      'partition_usage': 15}}
                     }
        '''
        global PERIOD_TIME
        now_disk_data = self._get_disk_data()
        write_request_period_time = now_disk_data['disk_write_request'] \
                                    - self.temp['disk_write_request']
        read_request_period_time = now_disk_data['disk_read_request'] \
                                    - self.temp['disk_read_request']
        if write_request_period_time == 0:
            write_request_period_time = 1
        if read_request_period_time == 0:
            read_request_period_time = 1

        disk_write_rate = float(now_disk_data['disk_write'] - \
                                self.temp['disk_write']) / PERIOD_TIME
        disk_read_rate = float(now_disk_data['disk_read'] - \
                               self.temp['disk_read']) / PERIOD_TIME
        disk_write_request = float(now_disk_data['disk_write_request'] - \
                self.temp['disk_write_request']) / PERIOD_TIME
        disk_read_request = float(now_disk_data['disk_read_request'] - \
                self.temp['disk_read_request']) / PERIOD_TIME
        disk_write_delay = float(now_disk_data['disk_write_delay'] - \
            self.temp['disk_write_delay']) / float(write_request_period_time)
        disk_read_delay = float(now_disk_data['disk_read_delay'] - \
            self.temp['disk_read_delay']) / float(read_request_period_time)
        if disk_write_rate < 0 or disk_read_rate < 0 \
                        or disk_write_request < 0 or disk_read_request < 0 \
                        or disk_write_delay < 0 or disk_read_delay < 0:
            disk_write_rate = 0.0
            disk_read_rate = 0.0
            disk_write_request = 0.0
            disk_read_request = 0.0
            disk_write_delay = 0.0
            disk_read_delay = 0.0

        disk_usage_dict = {
                'used_disk': now_disk_data['used_disk'],
                'disk_write_rate': disk_write_rate,
                'disk_read_rate': disk_read_rate,
                'disk_write_request': disk_write_request,
                'disk_read_request': disk_read_request,
                'disk_write_delay': disk_write_delay,
                'disk_read_delay': disk_read_delay,
                'disk_partition_info': now_disk_data['disk_partition_info'],
                'disk_partition_data': now_disk_data['disk_partition_data']
        }

        # when partition info changed, notify platform with new partition info
        #last_partition_info = {}
        #is_success = True
        #if now_disk_data.get('disk_partition_info') \
        #        != self.temp.get('disk_partition_info'):
            #is_success = notify_platform_partition_change(
            #                now_disk_data.get('disk_partition_info', []))
            #if not is_success:
            #   last_partition_info = self.temp['disk_partition_info']

        for key in now_disk_data.keys():
            if key in self.temp:
                self.temp[key] = now_disk_data[key]

        # FIXME(hzyangtk): here add for don`t record partition info into temp.
        # To do this when partition monitor enable, partition change will occur
        #if not ENABLE_PARTITION_MONITOR or not is_success:
        #    self.temp['disk_partition_info'] = last_partition_info

        return disk_usage_dict

    def _get_network_flow_data(self):
        '''
            Get network flow datas(Byte) from network card by
            command 'ifconfig'.
            Split the grep result and divide it into list.
            @return: ['10.120.0.1', '123', '123']
        '''
        global NET_CARD_LIST
        receive_bytes = 0L
        transfer_bytes = 0L
        receive_packages = 0L
        transfer_packages = 0L
        # TODO(hzyangtk): When VM has multiple network card, it should monitor
        #                 all the cards but not only eth0.
        net_devs = self._read_file_from_guest('/proc/net/dev')
        if net_devs:
            network_lines = net_devs.splitlines()
        else:
            print "get network data failed, uuid: %s" % self.domain.UUIDString()
            return [receive_bytes, transfer_bytes]
        for network_line in network_lines:
            network_datas = network_line.replace(':', ' ').split()
            try:
                if network_datas[0] in NET_CARD_LIST:
                    receive_bytes += long(network_datas[1])
                    receive_packages += long(network_datas[2])
                    transfer_bytes += long(network_datas[9])
                    transfer_packages += long(network_datas[10])
            except (KeyError, ValueError, IndexError, TypeError):
                continue
        return [receive_bytes, transfer_bytes]

    def _get_network_flow_rate_dict(self):
        '''
            Assemble dict datas collect from _get_network_flow_data()
            for network flow rate in 60s.
            Set network flow datas to self.temp.
            @return: {
                      'ip': '10.120.0.1',
                      'receive_rate': 0.0,
                      'transfer_rate': 0.0
                    }
        '''
        global PERIOD_TIME
        old_receive_bytes = self.temp['network_receive_bytes']
        old_transfer_bytes = self.temp['network_transfer_bytes']
        now_receive_bytes, now_transfer_bytes = \
                                    self._get_network_flow_data()
        receive_rate = float(now_receive_bytes - old_receive_bytes) \
                                            / 1024 / PERIOD_TIME
        transfer_rate = float(now_transfer_bytes - old_transfer_bytes) \
                                            / 1024 / PERIOD_TIME
        if receive_rate < 0 or transfer_rate < 0:
            receive_rate = 0
            transfer_rate = 0

        network_info_dict = {
                'receive_rate': receive_rate,
                'transfer_rate': transfer_rate
        }
        self.temp['network_receive_bytes'] = now_receive_bytes
        self.temp['network_transfer_bytes'] = now_transfer_bytes
        return network_info_dict

    def get_system_usage_datas(self):
        '''
            Get all system datas and assemble them into all_system_usage_dict.
            The key names of all_system_usage_dict are the same as XML setting.
        '''
        cpu_usage = self._get_cpu_usage_dict()
        loadavg = self._get_loadavg_dict()
        memory_usage = self._get_memory_usage_dict()
        network_usage = self._get_network_flow_rate_dict()
        disk_usage = self._get_disk_usage_rate_dict()
        all_system_usage_dict = {
            'cpuUsage': cpu_usage['cpu_usage'],
            'memUsage': memory_usage['used_memory'],
            'networkReceive': network_usage['receive_rate'],
            'networkTransfer': network_usage['transfer_rate'],
            'diskUsage': disk_usage['used_disk'],
            'diskWriteRate': disk_usage['disk_write_rate'],
            'diskReadRate': disk_usage['disk_read_rate'],
            'diskWriteRequest': disk_usage['disk_write_request'],
            'diskReadRequest': disk_usage['disk_read_request'],
            'diskWriteDelay': disk_usage['disk_write_delay'],
            'diskReadDelay': disk_usage['disk_read_delay'],
            'diskPartition': [disk_usage['disk_partition_info'],
                              disk_usage['disk_partition_data']],
            'loadavg_5': loadavg['loadavg_5'],
            'memUsageRate': memory_usage['memory_usage_rate']
        }

        return all_system_usage_dict


class DataFormater(object):

    def _setting_params(self, metricName, dimensions,
                        aggregationDimensions, sum_value, unit):
        '''
            Setting the metric element parameters and datas.
            @return: dict
        '''
        metric_datas = {
            'metricName': metricName,
            'dimensions': dimensions,
            'aggregationDimensions': aggregationDimensions,
            'sum': sum_value,
            'maxinum': sum_value,
            'mininum': sum_value,
            'sampleCount': 1,
            'createTime': long(time.time() * 1000),
            'unit': unit
        }

        return metric_datas

    def format_data(self, all_usage_dict, metadata_dict):
        '''
            Format the collected datas into result and defined format:
            {"metricDatas": [
                        {"metricName": "cpuUsage",
                         "dimensions": "ip=1.1.1.1",
                         "aggregationDimensions": "cluster=c1,env=prod",
                         "sum": 101,
                         "maxinum": 101,
                         "mininum": 101,
                         "sampleCount": 1,
                         "createTime": 1344329292557,
                         "unit": null
                         }
                      ]
            }
        '''
        metric_datas = dict()
        metric_datas['metricDatas'] = list()

        if metadata_dict['service'] == 'openstack' or \
                        metadata_dict['service'] == 'NVS':
            # for openstack resource_id is store VM ip (eth0)
            identify_id = get_uuid()
        else:
            identify_id = metadata_dict['resource_id']

        aggregation_items = metadata_dict['aggregation_items']

        # Read XML settings and set aggregation dimension
        # infos and store metric datas
        root = ElementTree.parse(XML_PATH)
        services = root.getiterator("service")
        for service in services:
            if service.attrib['name'] == metadata_dict['service'] and \
            service.attrib['resource_type'] == metadata_dict['resource_type']:
                metrics = service.getiterator('metric')
                for metric in metrics:
                    metric_type = metric.attrib['name']
                    metric_unit = metric.attrib['unit']
                    aggregations = metric.getiterator('aggregation')
                    aggregationDimensions = ''
                    for aggregation in aggregations:
                        ag_name = aggregation.attrib['name']
                        if ag_name in aggregation_items:
                            if aggregationDimensions != '':
                                aggregationDimensions += ','
                            aggregationDimensions += ag_name + '=' + \
                                    aggregation_items[ag_name].encode('utf-8')
                    if metric_type == 'diskPartition' and \
                                    ENABLE_PARTITION_MONITOR:
                        partition_info = all_usage_dict[metric_type][0]
                        partition_datas = all_usage_dict[metric_type][1]
                        partition_setting = {
                            'avail_capacity': ['availCapacity', 'Megabytes'],
                            'partition_usage': ['partitionUsage', 'Percent']
                        }
                        for partition_name in partition_datas:
                            if partition_name in partition_info['sys']:
                                partition_identity = 'system'
                            elif partition_name in partition_info['logic']:
                                partition_identity = 'logic'
                            else:
                                continue
                            # for partition data dimensions is like
                            # partition=1.1.1.1#::#system#::#vda1
                            dimensions = 'partition=' + identify_id + \
                                    '#::#' + partition_identity + \
                                    '#::#' + partition_name
                            for parti_data_name in \
                                            partition_datas[partition_name]:
                                parti_metric_name = \
                                        partition_setting[parti_data_name][0]
                                parti_unit = \
                                        partition_setting[parti_data_name][1]
                                parti_metric_data = \
                            partition_datas[partition_name][parti_data_name]
                                metric_data = self._setting_params(
                                    parti_metric_name, dimensions,
                                    aggregationDimensions, parti_metric_data,
                                    parti_unit)
                                metric_datas['metricDatas'].append(metric_data)
                    elif metric_type != 'diskPartition':
                        # for normal data dimensions is like
                        # openstack=1.1.1.1  or  RDS=1234567890
                        dimensions = metadata_dict['resource_type'] + '=' + \
                                                                    identify_id
                        metric_data = self._setting_params(metric_type,
                                    dimensions, aggregationDimensions,
                                    all_usage_dict[metric_type], metric_unit)
                        metric_datas['metricDatas'].append(metric_data)

        return metric_datas



class MonitorThread(BaseThread):
    def __init__(self):
        super(MonitorThread, self).__init__()
        global monitor_delay
        self.delay = monitor_delay

    def _run(self):
        global RUN_DC
        return RUN_DC

    def _update_instances(self):
        print "ith: 2, ", time.asctime()
        db_instances = instance.get_all_instances_on_host()
        db_uuids = [inst['id'] for inst in db_instances]

        hyper_domains = self.helper.list_all_domains()
        hyper_uuids = [dom.UUIDString() for dom in hyper_domains]
        monitor_domains = [dom for dom in hyper_domains
                                if dom.UUIDString() in db_uuids]
        hyper_lost_domains = [uuid for uuid in db_uuids
                                if uuid not in hyper_uuids]
        hyper_residual_domains = [dom.UUIDString() for dom in hyper_domains
                                    if dom.UUIDString() not in db_uuids]
        print "lost instances on the hypervisor: %s" % hyper_lost_domains
        print "residual domains on the hypervisor: %s" % hyper_residual_domains
        print "monitor domains: %s" % [dom.UUIDString() for dom in monitor_domains]
        return monitor_domains

    def serve(self):
        monitor_domains = self._update_instances()
        print "------start monitor ", time.asctime()
        for dom in monitor_domains:

            try:
                get_system_usage = GetSystemUsage(dom, self.helper)
            except (IOError, AttributeError, ValueError):
                print "init sys usage failed, info file not found, uuid: %s" % dom.UUIDString()
                continue
            temp_ok = get_system_usage.load_temp()
            all_usage_dict = get_system_usage.get_system_usage_datas()
            get_system_usage.save_temp()

            if temp_ok:
                print "monitor data of instance %s: %s" % (dom.UUIDString(), all_usage_dict)
            else:
                print "first start or temp file is expired"

            #metadata_dict = read_info_file()
            #metadata_ok = handle_metadata(metadata_dict)
            #if temp_ok and metadata_ok:
                #metric_datas = DataFormater().format_data(all_usage_dict,
                #                                          metadata_dict)
                #metric_datas_json = json.dumps(metric_datas)
                #send_request = sender.SendRequest(metadata_dict, metric_datas_json)
                #send_request.send_request_to_server()
            print "monitor domain %s" % dom.UUIDString()
        print "--------end monitor", time.asctime()

        self.start()
