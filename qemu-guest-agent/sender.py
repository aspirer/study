
import hashlib
import hmac
import httplib
import urllib

from xml.etree import ElementTree

class SendRequest(object):
    '''
        Send datas to monitor server by accesskey authorization.
    '''
    def __init__(self, metadata_dict, metric_datas_json=None,
                 request_uri='/rest/V1/MetricData',
                 headers={'Content-type': 'application/x-www-form-urlencoded'},
                 http_method='POST',
                 system_partitions=None,
                 logic_partitions=None,
                 parti_dimension=None):
        self.url = metadata_dict['monitorWebServerUrl']
        self.request_uri = request_uri
        self.headers = headers
        self.http_method = http_method
        self.project_id = metadata_dict['ori_user']
        self.name_space = metadata_dict['service']
        self.access_key = metadata_dict['accessKey']
        self.access_secret = metadata_dict['accessSecret']
        self.metric_datas_json = metric_datas_json
        self.system_partitions = system_partitions
        self.logic_partitions = logic_partitions
        self.parti_dimension = parti_dimension

    def send_request_to_server(self):
        '''
            Send monitor datas to collect server by POST request.
        '''
        params_dict = {
                'ProjectId': self.project_id,
                'Namespace': self.name_space,
                'AccessKey': self.access_key,
                'Signature': self.generate_signature()
        }
        if self.metric_datas_json != None:
            params_dict['MetricDatasJson'] = self.metric_datas_json
        if self.system_partitions != None:
            params_dict['SystemPartitions'] = self.system_partitions
        if self.logic_partitions != None:
            params_dict['LogicPartitions'] = self.logic_partitions
        if self.parti_dimension != None:
            params_dict['Dimension'] = self.parti_dimension
        params = urllib.urlencode(params_dict)

        if str(self.url).startswith('http://'):
            self.url = str(self.url).split("http://")[-1]
        conn = httplib.HTTPConnection(self.url)
        conn.request(self.http_method, self.request_uri, params, self.headers)
        response = conn.getresponse()
        conn.close()
        return response

    def generate_stringToSign(self):
        '''
            Generate stringToSign for signature.
        '''
        canonicalized_headers = ''
        if self.metric_datas_json != None:
            canonicalized_resources = ('AccessKey=%s&MetricDatasJson=%s&'
                                       'Namespace=%s&ProjectId=%s' %
                                    (self.access_key, self.metric_datas_json,
                                     self.name_space, self.project_id))
        elif self.system_partitions != None:
            canonicalized_resources = ('AccessKey=%s&Dimension=%s&'
                                       'LogicPartitions=%s&Namespace=%s&'
                                       'ProjectId=%s&SystemPartitions=%s' %
                                       (self.access_key, self.parti_dimension,
                                        self.logic_partitions, self.name_space,
                                        self.project_id,
                                        self.system_partitions))
        else:
            raise Exception()

        StringToSign = '%s\n%s\n%s\n%s\n' % \
                      (self.http_method, self.request_uri,
                       canonicalized_headers, canonicalized_resources)

        return StringToSign

    def generate_signature(self):
        '''
            Generate signature for authorization.
            Use hmac SHA-256 to calculate signature string and encode
            into base64.
            @return String
        '''
        stringToSign = self.generate_stringToSign()
        hashed = hmac.new(str(self.access_secret), stringToSign,
                          hashlib.sha256)
        s = hashed.digest()
        signature = s.encode('base64').rstrip()
        return signature




def notify_platform_partition_change(disk_partition_info, metadata_dict, xml_path, uuid):
    '''
        notify platform when partition changed only when service supports
        diskPartition metric.

        :param disk_partition_info: {'sys':['vda1'],
                                     'logic':['vda1', 'vdb1', 'dm-0']}
    '''
    # metadata_dict = read_info_file()
    service = metadata_dict.get('service')
    resource_type = metadata_dict.get('resource_type')
    setting_root = ElementTree.parse(xml_path)
    setting_services = setting_root.findall('service')
    metric_types = []
    for s in setting_services:
        if (service == s.attrib.get('name') and
                resource_type == s.attrib.get('resource_type')):
            metric_types = s.findall('metric')

    metrics = [m.attrib.get('name') for m in metric_types]
    if 'diskPartition' not in metrics:
        return False

    request_uri = '/rest/V1/nvs/updatePartitionInfo'
    system_partitions = ','.join(disk_partition_info['sys'])
    logic_partitions = ','.join(disk_partition_info['logic'])
    # partition dimension is like openstack=1.1.1.1 or RDS=123456
    parti_dimension = metadata_dict.get('service') + '=' + uuid
    send_request = SendRequest(metadata_dict=metadata_dict,
                               request_uri=request_uri,
                               system_partitions=system_partitions,
                               logic_partitions=logic_partitions,
                               parti_dimension=parti_dimension)
    try:
        response = send_request.send_request_to_server()
        if response.status == 200:
            return True
        else:
            return False
    except httplib.HTTPException as e:
        print "send request error, exception: %s" % e
        return False



class MemcacheClient(object):
    def __init__(self):
        print "MemcacheClient init"

    def report_heartbeat(self, uuid):
        print "+++++++++++++++instance %s is running" % uuid