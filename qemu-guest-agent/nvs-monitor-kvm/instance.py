
import helper
import json
import os
import requests
import utils
from oslo.config import cfg
import log

instance_opts = [
    cfg.StrOpt('auth_url',
               default='http://127.0.0.1:5000/v2.0/tokens',
               help='The interval seconds of collecting vm monitor data'),
    cfg.StrOpt('api_url_prefix',
               default='http://127.0.0.1:8774/v2/',
               help='The interval seconds of collecting vm monitor data'),
    cfg.StrOpt('api_url_suffix',
               default='/servers/detail',
               help='The interval seconds of collecting vm monitor data'),
    cfg.StrOpt('admin_tenant_name',
               default='admin',
               help='The interval seconds of collecting vm monitor data'),
    cfg.StrOpt('admin_user_name',
               default='admin',
               help='The interval seconds of collecting vm monitor data'),
    cfg.StrOpt('admin_password',
               default='admin',
               help='The timeout seconds of getting instances by nova api'),
    cfg.StrOpt('instances_host',
               default=utils.get_host_name(),
               help='The timeout seconds of getting instances by nova api'),
    cfg.IntOpt('nova_request_timeout',
               default=5,
               help='The timeout seconds of getting instances by nova api'),
    cfg.IntOpt('token_retry_times',
               default=1,
               help='The timeout seconds of getting instances by nova api'),

    ]

CONF = cfg.CONF
CONF.register_opts(instance_opts)

LOG = log.getLogger(__name__)

TOKEN = None
TENANT_ID = None


def _get_token():
    LOG.info("Going to get token")
    global TOKEN
    global TENANT_ID
    data = {"auth": {"tenantName": CONF.admin_tenant_name,
                     "passwordCredentials":
                            {"username": CONF.admin_user_name,
                             "password": CONF.admin_password}}}
    headers = {'content-type': 'application/json'}
    try:
        r = requests.post(CONF.auth_url, data=json.dumps(data),
                          headers=headers, timeout=CONF.nova_request_timeout)
        TOKEN = r.json()['access']['token']['id']
        TENANT_ID = r.json()['access']['token']['tenant']['id']
        LOG.info("get token: %s, belong to tenant: %s" % (TOKEN, TENANT_ID))
    except (TypeError, KeyError, ValueError) as e:
        LOG.error("Get token failed, exception: %s" % e)
        TOKEN = None
        TENANT_ID = None


# get instances running on this host
def get_all_instances_on_host():
    global TOKEN
    global TENANT_ID
    if TOKEN is None or TENANT_ID is None:
        _get_token()

    if TOKEN is None or TENANT_ID is None:
        return []

    if not CONF.instances_host:
        LOG.error("Host name is invalid")
        return []

    headers = {"Accept": "application/json", "X-Auth-Token": TOKEN}
    params = {"all_tenants": 1, "host": CONF.instances_host}
    api_url = CONF.api_url_prefix + TENANT_ID + CONF.api_url_suffix

    retry = 0
    while retry <= CONF.token_retry_times:
        try:
            r = requests.get(api_url, params=params, headers=headers,
                             timeout=CONF.nova_request_timeout)
            if r.status_code == 401:
                retry += 1
                _get_token()
            elif r.status_code == 200:
                servers = r.json()["servers"]
                return servers
            else:
                LOG.error("Get instances error, code: %s" % r.status_code)
                return []
        except requests.exceptions.RequestException as e:
            LOG.error("Get instances error, exception: %s" % e)
            return []

