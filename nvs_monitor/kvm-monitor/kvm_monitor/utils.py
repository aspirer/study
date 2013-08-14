
import json
import os
import socket
from xml.etree import ElementTree as ET

from libvirt_qemu import libvirt
from oslo.config import cfg

import log

util_opts = [
    cfg.StrOpt('instances_path',
               default='/var/lib/nova/instances/',
               help='Where instances are stored on disk'),
    cfg.StrOpt('config_path',
               default='/etc/nvs_monitor/',
               help='Where the conf files of nvs monitor are stored on disk'),
    cfg.StrOpt('monitor_setting_file_name',
               default='monitor-metrics.xml',
               help='The file name of monitor metrics setting'),
    cfg.StrOpt('info_file_name',
               default='info',
               help='The file name of instance info'),
    ]

CONF = cfg.CONF
CONF.register_opts(util_opts)

LOG = log.getLogger(__name__)


def get_host_name():
    try:
        return socket.gethostname()
    except socket.error as e:
        LOG.error("Get host name failed, exception: %s" % e)
        return None


def is_active(domain):
    try:
        return domain.isActive()
    except libvirt.libvirtError as e:
        LOG.error("Check domain is active failed, exception: %s" % e)
        return False


def get_domain_name(domain):
    try:
        return domain.name()
    except libvirt.libvirtError as e:
        LOG.error("Get domain name failed, exception: %s" % e)
        return None


def get_domain_uuid(domain):
    try:
        return domain.UUIDString()
    except libvirt.libvirtError as e:
        LOG.error("Get domain name failed, exception: %s" % e)
        return None


def get_instance_dir(domain):
    try:
        instance_dir = os.path.join(CONF.instances_path,
                                    get_domain_name(domain))
        if not os.path.exists(instance_dir):
            instance_dir = os.path.join(CONF.instances_path,
                                        get_domain_uuid(domain))

        if not os.path.exists(instance_dir):
            LOG.error("Get instance dir failed")
            return None
        else:
            return instance_dir
    except TypeError:
        LOG.error("Get instance dir failed, TypeError")
        return None


def get_info_file_dict(domain, project_id):
    try:
        info_file = os.path.join(get_instance_dir(domain), CONF.info_file_name)
        with open(info_file, 'r') as f:
            info_dict = json.loads(f.read())

        # check info file
        service = info_dict['service']
        ori_user = info_dict.get('ori_user')
        aggregation_items = info_dict.get('aggregation_items')
        resource_type = info_dict['resource_type']
        if not ori_user and service == 'openstack':
            info_dict['ori_user'] = project_id
        if not aggregation_items:
            info_dict['aggregation_items'] = {}
        if service == 'openstack' and resource_type != 'openstack':
            info_dict['resource_type'] = 'openstack'

        return info_dict
    except (IOError, TypeError, KeyError) as e:
        LOG.error("Load info file failed, exception: %s" % e)
        return None


def get_monitor_setting_root(domain):
    try:
        monitor_setting_file = os.path.join(CONF.config_path,
                                    CONF.monitor_setting_file_name)
        return ET.parse(monitor_setting_file)
    except (ET.ParseError, IOError, TypeError) as e:
        LOG.error("Parse monitor setting file failed, exception: %s" % e)
        return None


def get_identify_id(info_file_dict, uuid):
    if info_file_dict['service'] in ('openstack', 'NVS'):
        identify_id = uuid
    else:
        identify_id = info_file_dict['resource_id']

    return identify_id


def get_monitor_metrics(info_file_dict, monitor_setting_root):
    service = info_file_dict['service']
    resource_type = info_file_dict['resource_type']
    setting_services = monitor_setting_root.findall('service')
    metrics = []
    for s in setting_services:
        if (service == s.attrib.get('name') and
                resource_type == s.attrib.get('resource_type')):
            metrics = s.findall('metric')

    return metrics


def get_aggregation_dimensions(metric, ag_items):
    ags = metric.findall('aggregation')
    ag_dims = ''
    for ag in ags:
        ag_name = ag.attrib.get('name')
        if ag_name in ag_items:
            if ag_dims != '':
                ag_dims += ','
            ag_dims += (ag_name + '=' + ag_items[ag_name].encode('utf-8'))

    return ag_dims


