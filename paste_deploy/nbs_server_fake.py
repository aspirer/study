#! /usr/bin/python

import os
import json
from webob import Request,Response
from paste.deploy import loadapp
from wsgiref.simple_server import make_server


NBS_ACTION_LIST = ['DescribeVolumes', 'AttachVolume', 'DetachVolume',
                   'ExtendVolume', 'GetVolumeQos', 'NotifyState',
                   'UpdateVolumeQos']


# app
class NbsManager(object):
    def __init__(self, conf):
        print "enter init of app Home"
        self.conf = conf

    def __call__(self, env, start_response):
        req = Request(env)
        params = {}
        for k,v in req.params.iteritems():
            params[k] = v

        res = Response()

        res.content_type = "text/json"
        action = params.pop('Action', None)
        if action is None:
            res.status = "400 bad request"
            res.body = json.dumps({'error': 'action is needed'})
        elif action not in NBS_ACTION_LIST:
            res.status = "404 action %s not found" % action
            res.body = json.dumps({'error': 'action %s is invalid' % action})
        else:
            res.status = "200 OK"
            ah = ActionHanlder(action, params)
            res.body = ah.do_action()

        return res(env, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "enter factory of app Home"
        return cls(global_conf)


LAST_ACTION = None


class ActionHanlder(object):
    def __init__(self, action, params):
        global LAST_ACTION
        self.last_action = LAST_ACTION
        print '__init__: last action is %s' % LAST_ACTION
        self.action = action
        self.params = params

    def do_action(self):
        try:
            return self.__getattribute__('_action_' + self.action)()
        finally:
            if action in ['AttachVolume', 'DetachVolume']:
                global LAST_ACTION
                LAST_ACTION = self.action
                print 'do_action: current done action is %s' % LAST_ACTION

    def _action_DescribeVolumes(self):
        return json.dumps({u'requestId': u'a6754e58-b3cc-11e3-926c-002590552f3c', u'volumes': [{u'attachDetachTime': 0, u'attachments': [{u'instanceId': u'4ec28a40-737a-47ba-b437-7dbf1ab3a8d9', u'device': u'/dev/nbs/xdjo', u'status': u'attaching', u'volumeId': u'6a034334-dcd', u'attachTime': 0}], u'instanceId': u'4ec28a40-737a-47ba-b437-7dbf1ab3a8d9', u'volumeName': u'RDS4ec28a40_737a_47ba_b437_7dbf1ab3a8d9', u'maxWriteBandWidth': 39235, u'snapshotId': u'0', u'referenceCount': 0, u'maxReadBandWidth': 39235, u'size': 10, u'projectId': u'eac8f915bfd6400fba5fbc5bf50c2a2e', u'waitNvsBeginTime': 1395717725480, u'waitNvsAction': 1, u'type': u'share', u'status': u'in-use', u'availabilityZone': u'none', u'maxWriteIOPS': 64, u'volumeId': u'6a034334-dcd', u'copyCount': 2, u'device': u'/dev/nbs/xdjo', u'createTime': 1395717725408, u'lockStatus': u'unlock', u'machineId': 1, u'extendStatus': 0, u'diskType': u'normal', u'maxReadIOPS': 38}]})

    def _action_AttachVolume(self):
        return json.dumps({u'attachment': {u'instanceId': u'1110e548-2c20-4e30-8093-5268dca3acd9', u'device': u'/dev/nbs/xdjo', u'status': u'attaching', u'volumeId': u'6a034334-dcd', u'attachTime': 0}, u'requestId': u'c3e998cf-ac6a-43e1-92df-c08d24987956'})

    def _action_DetachVolume(self):
        return json.dumps({u'detachment': {u'attachDetachTime': 1395717730133, u'attachments': [{u'instanceId': u'4ec28a40-737a-47ba-b437-7dbf1ab3a8d9', u'device': u'/dev/nbs/xdjo', u'status': u'detaching', u'volumeId': u'6a034334-dcd', u'attachTime': 1395717730133}], u'instanceId': u'4ec28a40-737a-47ba-b437-7dbf1ab3a8d9', u'volumeName': u'RDS4ec28a40_737a_47ba_b437_7dbf1ab3a8d9', u'maxWriteBandWidth': 39235, u'snapshotId': u'0', u'referenceCount': 0, u'maxReadBandWidth': 39235, u'size': 10, u'projectId': u'eac8f915bfd6400fba5fbc5bf50c2a2e', u'waitNvsBeginTime': 1395718578369, u'waitNvsAction': 2, u'type': u'share', u'status': u'in-use', u'availabilityZone': u'none', u'maxWriteIOPS': 64, u'volumeId': u'6a034334-dcd', u'copyCount': 2, u'device': u'/dev/nbs/xdjo', u'createTime': 1395717725408, u'lockStatus': u'unlock', u'machineId': 1, u'extendStatus': 0, u'diskType': u'normal', u'maxReadIOPS': 38}, u'requestId': u'52b258ac-3e50-4b47-b320-507162f653dc'})

    def _action_ExtendVolume(self):
        return json.dumps({u'requestId': u'c54157a6-2e6e-4743-b945-854abfddc3d4', u'size': 22})

    def _action_GetVolumeQos(self):
        return json.dumps({u'maxWriteIOPS': 64, u'volumeId': u'6a034334-dcd', u'maxWriteBandWidth': 40176640, u'requestId': u'b1e1b051-62be-4a62-82c6-8b84f021cd9b', u'devicePath': u'/dev/nbd10', u'maxReadIOPS': 38, u'maxReadBandWidth': 40176640})

    def _action_NotifyState(self):
        return json.dumps({u'return': True, u'requestId': u'9a572dae-2904-4c5a-b250-58d0586597b0'})

    def _action_UpdateVolumeQos(self):
        return json.dumps({u'return': True, u'requestId': u'061aa9cf-a38b-4068-b902-5bcc4f1b0008'})


if __name__ == "__main__":
    configfile = "nbs_server_fake.ini"
    appname = "nbs_server_fake"
    wsgi_app = loadapp("config:%s" % os.path.abspath(configfile), appname)
    server = make_server('localhost', 8080, wsgi_app)
    server.serve_forever()
