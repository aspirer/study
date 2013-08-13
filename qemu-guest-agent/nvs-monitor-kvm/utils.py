
import json
import os
import socket
from xml.etree import ElementTree as ET

from libvirt_qemu import libvirt
from oslo.config import cfg

util_opts = [
    cfg.StrOpt('instances_path',
               default='/var/lib/nova/instances/',
               help='Where instances are stored on disk'),
    ]

CONF = cfg.CONF
CONF.register_opts(util_opts)


def get_host_name():
    try:
        return socket.gethostname()
    except socket.error:
        return None


def is_active(domain):
    try:
        return domain.isActive()
    except libvirt.libvirtError:
        return False


def get_domain_name(domain):
    try:
        return domain.name()
    except libvirt.libvirtError:
        return None


def get_domain_uuid(domain):
    try:
        return domain.UUIDString()
    except libvirt.libvirtError:
        return None


def get_instance_dir(domain):
    try:
        instance_dir = CONF.instances_path + get_domain_name(domain)
        if not os.path.exists(instance_dir):
            instance_dir = CONF.instances_path + get_domain_uuid(domain)

        if not os.path.exists(instance_dir):
            return None
        else:
            return instance_dir
    except TypeError:
        return None


def get_info_file_dict(domain, project_id):
    try:
        info_file = get_instance_dir(domain) + "/info"
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
    except (IOError, TypeError, KeyError):
        return None


def get_monitor_setting_root(domain):
    try:
        monitor_setting_file = get_instance_dir(domain) + "/monitor_setting.xml"
        return ET.parse(monitor_setting_file)
    except (ET.ParseError, IOError, TypeError):
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


