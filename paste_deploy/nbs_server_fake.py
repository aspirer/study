#! /usr/bin/python

import os
import json
from webob import Request,Response
from paste.deploy import loadapp
from wsgiref.simple_server import make_server


# app
class Home(object):
    def __init__(self, conf):
        print "enter init of app Home"
        self.conf = conf

    def __call__(self, env, start_response):
        print "enter call of app Home, s_r=%s" % start_response
        import ipdb;ipdb.set_trace()
        req = Request(env)
        res = Response()
        res.status = "200 OK"
        res.content_type = "text/json"

        res.body = json.dumps(os.listdir('.'))
        return res(env, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "enter factory of app Home"
        return Home(global_conf)


if __name__ == "__main__":
    configfile = "nbs_server_fake.ini"
    appname = "nbs_server_fake"
    wsgi_app = loadapp("config:%s" % os.path.abspath(configfile), appname)
    server = make_server('localhost', 8080, wsgi_app)
    server.serve_forever()
