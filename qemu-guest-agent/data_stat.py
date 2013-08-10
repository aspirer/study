
from libvirt_qemu import libvirt
import time
from base_thread import BaseThread
import instance
import sender

RUN_DC = True
enable_monitor = True
monitor_delay = 10


class GetSystemUsage(object):
    def __init__(self, domain):
        pass




class DataFormater(object):
    def __init__(self):
        pass



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
