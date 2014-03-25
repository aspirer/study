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
            res.body = ah.do_action(res)

        return res(env, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "enter factory of app Home"
        return cls(global_conf)


LAST_ACTION = None
LAST_INSTANCE_UUID = None


class ActionHanlder(object):
    def __init__(self, action, params):
        self.action = action
        self.params = params

    def do_action(self, response):
        try:
            return self.__getattribute__('_action_' + self.action)(response)
        finally:
            if self.action in ['AttachVolume', 'DetachVolume']:
                global LAST_ACTION
                LAST_ACTION = self.action

    def _action_DescribeVolumes(self, response):
        global LAST_ACTION
        if LAST_ACTION == 'AttachVolume':
            return json.dumps({u'requestId': u'a6754e58-b3cc-11e3-926c-002590552f3c', u'volumes': [{u'attachDetachTime': 0, u'attachments': [{u'instanceId': self.params.get('InstanceId', LAST_INSTANCE_UUID), u'device': u'/dev/nbs/xdjo', u'status': u'attached', u'volumeId': u'fake-vol-id', u'attachTime': 0}], u'instanceId': self.params.get('InstanceId', LAST_INSTANCE_UUID), u'volumeName': u'fake-vol-name', u'maxWriteBandWidth': 40176640, u'snapshotId': u'0', u'referenceCount': 0, u'maxReadBandWidth': 39235, u'size': 10, u'projectId': u'eac8f915bfd6400fba5fbc5bf50c2a2e', u'waitNvsBeginTime': 1395717725480, u'waitNvsAction': 1, u'type': u'share', u'status': u'in-use', u'availabilityZone': u'none', u'maxWriteIOPS': 64, u'volumeId': u'fake-vol-id', u'copyCount': 2, u'device': u'/dev/nbs/xdjo', u'createTime': 1395717725408, u'lockStatus': u'unlock', u'machineId': 1, u'extendStatus': 0, u'diskType': u'normal', u'maxReadIOPS': 38}]})
        elif LAST_ACTION == 'DetachVolume':
            return json.dumps({u'requestId': u'6c0c8f4e-a5b0-11e3-965d-002590552f3c', u'volumes': [{u'attachDetachTime': 1394166286303, u'attachments': [], u'volumeName': u'fake-vol-name', u'maxWriteBandWidth': 40176640, u'snapshotId': u'0', u'referenceCount': 0, u'maxReadBandWidth': 39235, u'size': 20, u'projectId': u'eac8f915bfd6400fba5fbc5bf50c2a2e', u'waitNvsBeginTime': 0, u'waitNvsAction': 0, u'type': u'share', u'status': u'available', u'availabilityZone': u'none', u'maxWriteIOPS': 64, u'volumeId': u'fake-vol-id', u'copyCount': 2, u'createTime': 1394161409266, u'lockStatus': u'unlock', u'extendStatus': 0, u'diskType': u'normal', u'maxReadIOPS': 38}]})
        else:
            return json.dumps({u'requestId': u'6c0c8f4e-a5b0-11e3-965d-002590552f3c', u'volumes': [{u'attachDetachTime': 1394166286303, u'attachments': [], u'volumeName': u'fake-vol-name', u'maxWriteBandWidth': 40176640, u'snapshotId': u'0', u'referenceCount': 0, u'maxReadBandWidth': 39235, u'size': 20, u'projectId': u'eac8f915bfd6400fba5fbc5bf50c2a2e', u'waitNvsBeginTime': 0, u'waitNvsAction': 0, u'type': u'share', u'status': u'available', u'availabilityZone': u'none', u'maxWriteIOPS': 64, u'volumeId': u'fake-vol-id', u'copyCount': 2, u'createTime': 1394161409266, u'lockStatus': u'unlock', u'extendStatus': 0, u'diskType': u'normal', u'maxReadIOPS': 38}]})

    def _action_AttachVolume(self, response):
        global LAST_ACTION
        if LAST_ACTION == 'AttachVolume':
            response.status = "409 conflict action"
            return json.dumps({'error': 'duplicated action %s' % self.action})
        global LAST_INSTANCE_UUID
        LAST_INSTANCE_UUID = self.params.get('InstanceId')
        return json.dumps({u'attachment': {u'instanceId': self.params.get('InstanceId', LAST_INSTANCE_UUID), u'device': u'/dev/nbs/xdjo', u'status': u'attaching', u'volumeId': u'fake-vol-id', u'attachTime': 0}, u'requestId': u'c3e998cf-ac6a-43e1-92df-c08d24987956'})

    def _action_DetachVolume(self, response):
        global LAST_ACTION
        if LAST_ACTION == 'DetachVolume':
            response.status = "409 conflict action"
            return json.dumps({'error': 'duplicated action %s' % self.action})
        return json.dumps({u'detachment': {u'attachDetachTime': 1395717730133, u'attachments': [{u'instanceId': self.params.get('InstanceId', LAST_INSTANCE_UUID), u'device': u'/dev/nbs/xdjo', u'status': u'detaching', u'volumeId': u'fake-vol-id', u'attachTime': 1395717730133}], u'instanceId': self.params.get('InstanceId', LAST_INSTANCE_UUID), u'volumeName': u'fake-vol-name', u'maxWriteBandWidth': 40176640, u'snapshotId': u'0', u'referenceCount': 0, u'maxReadBandWidth': 39235, u'size': 10, u'projectId': u'eac8f915bfd6400fba5fbc5bf50c2a2e', u'waitNvsBeginTime': 1395718578369, u'waitNvsAction': 2, u'type': u'share', u'status': u'in-use', u'availabilityZone': u'none', u'maxWriteIOPS': 64, u'volumeId': u'fake-vol-id', u'copyCount': 2, u'device': u'/dev/nbs/xdjo', u'createTime': 1395717725408, u'lockStatus': u'unlock', u'machineId': 1, u'extendStatus': 0, u'diskType': u'normal', u'maxReadIOPS': 38}, u'requestId': u'52b258ac-3e50-4b47-b320-507162f653dc'})

    def _action_ExtendVolume(self, response):
        return json.dumps({u'requestId': u'c54157a6-2e6e-4743-b945-854abfddc3d4', u'size': 22})

    def _action_GetVolumeQos(self, response):
        return json.dumps({u'maxWriteIOPS': 64, u'volumeId': u'fake-vol-id', u'maxWriteBandWidth': 40176640, u'requestId': u'b1e1b051-62be-4a62-82c6-8b84f021cd9b', u'devicePath': u'/dev/nbd10', u'maxReadIOPS': 38, u'maxReadBandWidth': 39235})

    def _action_NotifyState(self, response):
        return json.dumps({u'return': True, u'requestId': u'9a572dae-2904-4c5a-b250-58d0586597b0'})

    def _action_UpdateVolumeQos(self, response):
        return json.dumps({u'return': True, u'requestId': u'061aa9cf-a38b-4068-b902-5bcc4f1b0008'})


if __name__ == "__main__":
    configfile = "nbs_server_fake.ini"
    appname = "nbs_server_fake"
    wsgi_app = loadapp("config:%s" % os.path.abspath(configfile), appname)
    server = make_server('localhost', 8081, wsgi_app)
    server.serve_forever()
