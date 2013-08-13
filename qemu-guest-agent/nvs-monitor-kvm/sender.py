
import hashlib
import hmac

import requests
import utils


class SendRequest(object):
    '''
        Send datas to monitor server by accesskey authorization.
    '''
    def __init__(self, info_file_dict, metric_datas_json=None,
                 request_uri='/rest/V1/MetricData',
                 headers={'Content-type': 'application/x-www-form-urlencoded'},
                 system_partitions=None,
                 logic_partitions=None,
                 parti_dimension=None):
        self.url = info_file_dict['monitorWebServerUrl']
        self.request_uri = request_uri
        self.headers = headers
        self.project_id = info_file_dict['ori_user']
        self.name_space = info_file_dict['service']
        self.access_key = info_file_dict['accessKey']
        self.access_secret = info_file_dict['accessSecret']
        self.metric_datas_json = metric_datas_json
        self.system_partitions = system_partitions
        self.logic_partitions = logic_partitions
        self.parti_dimension = parti_dimension

    def send_request_to_server(self):
        '''
            Send monitor datas to collect server by POST request.
        '''
        signature = self.generate_signature()
        if not signature:
            print "signature is null: %s" % signature
            return None

        params_dict = {
                'ProjectId': self.project_id,
                'Namespace': self.name_space,
                'AccessKey': self.access_key,
                'Signature': signature
        }
        if self.metric_datas_json != None:
            params_dict['MetricDatasJson'] = self.metric_datas_json
        if self.system_partitions != None:
            params_dict['SystemPartitions'] = self.system_partitions
        if self.logic_partitions != None:
            params_dict['LogicPartitions'] = self.logic_partitions
        if self.parti_dimension != None:
            params_dict['Dimension'] = self.parti_dimension

        try:
            r = requests.post(self.url + self.request_uri,
                        params=params_dict, headers=self.headers, timeout=3)
            return r
        except requests.exceptions.RequestException as e:
            print "send request to cloud monitor error, exception: %s" % e
            return None

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
            return None

        # http method is always POST currently
        StringToSign = 'POST\n%s\n%s\n%s\n' % (self.request_uri,
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
        if not stringToSign:
            return None
        hashed = hmac.new(str(self.access_secret), stringToSign,
                          hashlib.sha256)
        s = hashed.digest()
        signature = s.encode('base64').rstrip()
        return signature


def notify_platform_partition_change(disk_partition_info, info_file_dict,
                monitor_setting_root, identify_id):
    '''
        notify platform when partition changed only when service supports
        diskPartition metric.

        :param disk_partition_info: {'sys':['vda1'],
                                     'logic':['vda1', 'vdb1', 'dm-0']}
    '''
    request_uri = '/rest/V1/nvs/updatePartitionInfo'
    system_partitions = ','.join(disk_partition_info['sys'])
    logic_partitions = ','.join(disk_partition_info['logic'])
    # partition dimension is like openstack=1.1.1.1 or RDS=123456
    parti_dimension = info_file_dict.get('service') + '=' + identify_id
    send_request = SendRequest(info_file_dict=info_file_dict,
                               request_uri=request_uri,
                               system_partitions=system_partitions,
                               logic_partitions=logic_partitions,
                               parti_dimension=parti_dimension)
    response = send_request.send_request_to_server()
    if response and response.status_code == 200:
        return True
    else:
        return False


class MemcacheClient(object):
    def __init__(self):
        print "MemcacheClient init"

    def report_heartbeat(self, uuid):
        if uuid:
            print "+++++++++++++++instance %s is running" % uuid
