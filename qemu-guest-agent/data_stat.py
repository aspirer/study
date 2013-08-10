
import os
from libvirt_qemu import libvirt
import time
from base_thread import BaseThread
import instance
import sender

RUN_DC = True
enable_monitor = True
monitor_delay = 10

instances_path = "/var/lib/nova/instances/"

'''
Get system resources usage include disk, network, cpu, memory.
CPU: get cpu usage percent.
Memory: get total memory(KB), free memory and used memory datas.
Disk: get disk read/write data((KB)), requests and used delay(ms).
Network: get network I/O datas(bytes) and vm ip.
'''
class GetSystemUsage(object):
    def __init__(self, domain):
        self.dom = domain
        self.temp = {
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
        
        global instances_path
        info_file = instances_path + self.dom.name() + "info"
        if not os.path.exists(info_file):
            info_file = instances_path + self.dom.UUIDString() + "info"
        
        with open(info_file) as f:
            self.info = json.loads(f.read())

    def _get_cpu_usage_dict(self):
        '''
            Get CPU usage(percent) by vmstat command.
            @return: {'cpu_usage': 0.0}
        '''
        cpu_path = '/proc/stat'
        if os.path.exists(cpu_path):
            cpu_file_read = open(cpu_path, 'r')
            cpu_read_line = cpu_file_read.readline()
            cpu_file_read.close()
            cpu_infos = cpu_read_line.split()[1:-1]
            total_cpu_time = 0L
            for cpu_info in cpu_infos:
                total_cpu_time += long(cpu_info)
            last_cpu_time = TEMP_DATA['total_cpu_time']
            cpu_idle_time = long(cpu_infos[3])
            last_cpu_idle_time = TEMP_DATA['last_cpu_idle_time']
            total_cpu_period = float(total_cpu_time - last_cpu_time)
            idle_cpu_period = float(cpu_idle_time - last_cpu_idle_time)

            if total_cpu_period <= 0 or idle_cpu_period < 0:
                cpu_usage = 0.0
            else:
                idle_usage = idle_cpu_period / total_cpu_period * 100
                cpu_usage = round(100 - idle_usage, 2)

            TEMP_DATA['total_cpu_time'] = total_cpu_time
            TEMP_DATA['last_cpu_idle_time'] = cpu_idle_time
        else:
            cpu_usage = 0.0
        return {'cpu_usage': cpu_usage}

    def _get_loadavg_dict(self):
        '''
            Get loadavg info from /proc/loadavg.
            @return: {'loadavg_5': 4.32}
        '''
        with open('/proc/loadavg', 'r') as loadavg_file_read:
            loadavg_info_line = loadavg_file_read.readline()
        loadavg_5 = float(loadavg_info_line.split()[1])

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
        with open('/proc/meminfo', 'r') as mem_file_read:
            mem_info_lines = mem_file_read.readlines()

        total_memory = long(mem_info_lines[0].split()[1]) / 1024
        free_memory = (long(mem_info_lines[1].split()[1])
                       + long(mem_info_lines[2].split()[1])
                       + long(mem_info_lines[3].split()[1])) / 1024
        used_memory = total_memory - free_memory
        memory_usage_rate = (used_memory * 100) / total_memory

        return {
            'total_memory': total_memory,
            'free_memory': free_memory,
            'used_memory': used_memory,
            'memory_usage_rate': memory_usage_rate
        }

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
            with open('/proc/mounts', 'r') as f:
                mounts = f.readlines()
            mounted_disks = {}
            for mount in mounts:
                if mount.startswith('/dev/'):
                    mount = mount.split()
                    partition = os.path.realpath(mount[0]).rsplit('/')[-1]
                    target = mount[1]
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
            hddinfo = os.statvfs(path)
            total = hddinfo.f_frsize * hddinfo.f_blocks
            free = hddinfo.f_frsize * hddinfo.f_bavail
            used = hddinfo.f_frsize * (hddinfo.f_blocks - hddinfo.f_bfree)
            return {'total': float(total) / 1024 / 1024,
                    'free': float(free) / 1024 / 1024,
                    'used': float(used) / 1024 / 1024}

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
            with open('/proc/diskstats') as diskstats:
                disk_datas = diskstats.readlines()
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
        global TEMP_DATA
        now_disk_data = self._get_disk_data()
        write_request_period_time = now_disk_data['disk_write_request'] \
                                    - TEMP_DATA['disk_write_request']
        read_request_period_time = now_disk_data['disk_read_request'] \
                                    - TEMP_DATA['disk_read_request']
        if write_request_period_time == 0:
            write_request_period_time = 1
        if read_request_period_time == 0:
            read_request_period_time = 1

        disk_write_rate = float(now_disk_data['disk_write'] - \
                                TEMP_DATA['disk_write']) / PERIOD_TIME
        disk_read_rate = float(now_disk_data['disk_read'] - \
                               TEMP_DATA['disk_read']) / PERIOD_TIME
        disk_write_request = float(now_disk_data['disk_write_request'] - \
                TEMP_DATA['disk_write_request']) / PERIOD_TIME
        disk_read_request = float(now_disk_data['disk_read_request'] - \
                TEMP_DATA['disk_read_request']) / PERIOD_TIME
        disk_write_delay = float(now_disk_data['disk_write_delay'] - \
            TEMP_DATA['disk_write_delay']) / float(write_request_period_time)
        disk_read_delay = float(now_disk_data['disk_read_delay'] - \
            TEMP_DATA['disk_read_delay']) / float(read_request_period_time)
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
        last_partition_info = {}
        is_success = True
        if ENABLE_PARTITION_MONITOR and \
                now_disk_data.get('disk_partition_info') \
                != TEMP_DATA.get('disk_partition_info'):
            is_success = notify_platform_partition_change(
                            now_disk_data.get('disk_partition_info', []))
            if not is_success:
                last_partition_info = TEMP_DATA['disk_partition_info']

        for key in now_disk_data.keys():
            if key in TEMP_DATA:
                TEMP_DATA[key] = now_disk_data[key]

        # FIXME(hzyangtk): here add for don`t record partition info into temp.
        # To do this when partition monitor enable, partition change will occur
        if not ENABLE_PARTITION_MONITOR or not is_success:
            TEMP_DATA['disk_partition_info'] = last_partition_info

        return disk_usage_dict

    def _get_network_flow_data(self):
        '''
            Get network flow datas(Byte) from network card by
            command 'ifconfig'.
            Split the grep result and divide it into list.
            @return: ['10.120.0.1', '123', '123']
        '''
        receive_bytes = 0L
        transfer_bytes = 0L
        receive_packages = 0L
        transfer_packages = 0L
        # TODO(hzyangtk): When VM has multiple network card, it should monitor
        #                 all the cards but not only eth0.
        with open('/proc/net/dev', 'r') as net_dev:
            network_lines = net_dev.readlines()
        for network_line in network_lines:
            network_datas = network_line.replace(':', ' ').split()
            try:
                if network_datas[0] in NET_CARD_LIST:
                    receive_bytes += long(network_datas[1])
                    receive_packages += long(network_datas[2])
                    transfer_bytes += long(network_datas[9])
                    transfer_packages += long(network_datas[10])
            except Exception:
                continue
        return [receive_bytes, transfer_bytes]

    def _get_network_flow_rate_dict(self):
        '''
            Assemble dict datas collect from _get_network_flow_data()
            for network flow rate in 60s.
            Set network flow datas to TEMP_DATA.
            @return: {
                      'ip': '10.120.0.1',
                      'receive_rate': 0.0,
                      'transfer_rate': 0.0
                    }
        '''
        old_receive_bytes = TEMP_DATA['network_receive_bytes']
        old_transfer_bytes = TEMP_DATA['network_transfer_bytes']
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
        TEMP_DATA['network_receive_bytes'] = now_receive_bytes
        TEMP_DATA['network_transfer_bytes'] = now_transfer_bytes
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
        global enable_monitor
        if enable_monitor:
            return RUN_DC
        else:
            return False

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
            '''get_system_usage = GetSystemUsage(dom)
            all_usage_dict = get_system_usage.get_system_usage_datas()
            get_system_usage.save_temp()

            metadata_dict = read_info_file()
            metric_datas = DataFormater().format_data(all_usage_dict,
                                                      metadata_dict)
            metric_datas_json = json.dumps(metric_datas)
            send_request = sender.SendRequest(metadata_dict, metric_datas_json)
            send_request.send_request_to_server()'''
            print "monitor domain %s" % dom.UUIDString()
        print "--------end monitor", time.asctime()

        self.start()
