


class SendRequest(object):
    pass
    
    
class MemcacheClient(object):
    def __init__(self):
        print "MemcacheClient init"
        
    def report_heartbeat(self, uuid):
        print "instance %s is running" % uuid