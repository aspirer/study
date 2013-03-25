#! /usr/bin/python

import os
import json
from webob import Request,Response
from paste.deploy import loadapp
from wsgiref.simple_server import make_server

# Filter
class Auth(object):
    def __init__(self, app):
        print "enter init of auth, app=%s" % app
        self.app = app

    def __call__(self, env, start_response):
        print "enter call of filter auth, s_r=%s" % start_response
        return self.app(env, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "enter factory of filter auth: global_conf=%s, kwargs=%s" % (global_conf, kwargs)
        return Auth


def check_user(conf, given):
    expected_user = conf.get("user", None)
    given_user = given.get("user", None)
    expected_passwd = conf.get("passwd", None)
    given_passwd = given.get("passwd", None)
    if expected_user != given_user or expected_passwd != given_passwd:
        return False
    else:
        return True


# app
class Home(object):
    def __init__(self, conf):
        print "enter init of app Home"
        self.conf = conf

    def __call__(self, env, start_response):
        print "enter call of app Home, s_r=%s" % start_response
        req = Request(env)    
        res = Response()
        res.status = "200 OK"
        res.content_type = "text/json"
        if not check_user(self.conf, req.GET):
            res.status = "413 auth failed!"
            res.body = json.dumps({'user': req.GET.get('user', None),                  
                                   'passwd': req.GET.get('passwd', None)})
            return res(env, start_response)
        res.body = json.dumps(os.listdir('.'))
        return res(env, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "enter factory of app Home"
        return Home(global_conf)


class Ver(object):
    def __init__(self, conf):
        print "enter init of app Ver"
        self.conf = conf

    def __call__(self, env, start_response):
        print "enter call of app Ver, s_r=%s" % start_response
        req = Request(env)  
        res = Response()  
        res.status = "200 OK"  
        res.content_type = "text/json"
        if not check_user(self.conf, req.GET):
            res.status = "413 auth failed!"
            res.body = json.dumps({'user': req.GET.get('user', None), 
                                   'passwd': req.GET.get('passwd', None)})
            return res(env, start_response)
        res.body = json.dumps({"version": "1.0.1"})
        return res(env, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "enter factory of app Ver"
        return Ver(global_conf)


class Hello(object):
    def __init__(self, conf):
        print "enter init of app Hello"
        self.conf = conf

    def __call__(self, env, start_response):
        print "enter call of app Hello, s_r=%s" % start_response
        req = Request(env)    
        res = Response()
        res.status = "200 OK"
        res.content_type = "text/json"
        if not check_user(self.conf, req.GET):
            res.status = "413 auth failed!"
            res.body = json.dumps({'user': req.GET.get('user', None),                  
                                   'passwd': req.GET.get('passwd', None)})
            return res(env, start_response)
        res.body = json.dumps({"hello": "world"})
        return res(env, start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        print "enter factory of app hello"
        return Hello(global_conf)


if __name__ == "__main__":
    configfile = "test_pd.ini"
    appname = "test_pd"
    wsgi_app = loadapp("config:%s" % os.path.abspath(configfile), appname)
    server = make_server('localhost', 8080, wsgi_app)
    server.serve_forever()
