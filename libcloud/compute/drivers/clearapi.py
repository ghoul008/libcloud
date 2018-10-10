import json
import httplib

from io import BytesIO

from libcloud.compute.base import Node, NodeDriver
from libcloud.common.clearapi import ClearAPIConnection
from libcloud.compute.types import Provider, NodeState



__all__ = [
    "ClearAPINodeDriver"
]

class ClearAPINodeDriver(NodeDriver):
    """
    Base ClearAPI node driver.
    A `node` can be either a host or a guest
    """

    connectionCls = ClearAPIConnection
    type = Provider.CLEARAPI
    name = 'ClearAPI'

    # TODO: map describing available states of nodes
    NODE_STATE_MAP = {'Active': NodeState.RUNNING,
                      'off': NodeState.OFF}

    def __init__(self, key=None, url=None,verify=True):
        """
        :param key: apikey
        :param uri: api endpoint
        """

        if not key:
            raise Exception("Api Key not specified")

        host = url

       # strip the prefix
        prefixes = ['http://', 'https://']
        for prefix in prefixes:
            if host.startswith(prefix):
                host = host.replace(prefix, '')

        self.connectionCls.host = host
        super(ClearAPINodeDriver, self).__init__(key=key, uri=url)
        self.connection.host = host

    def list_nodes(self):
        """
        List clearAPI nodes

        :rtype: ``list`` of :class:`ClearAPINode`
        """
        response = self.connection.request('/clearos/clearapi/v2/rest/host/get_all_host')
        nodes = [self._to_node(host)
                 for host in response.object['data']]
        return nodes

    def _to_node(self, data):
        extra = {}
        private_ips = []
        private_ips.append(data['ipv4'])

        if data['status'] == 'Active':
            state = NodeState.RUNNING
        else:
            state = NodeState.STOPPED

        for key in data:
            extra[key] = data[key]

        json_data = {"uuid": data['uuid']}

        node = Node(id=data['id'], name=data['model_name'], state=state,
                    private_ips=private_ips, public_ips=[], created_at=data['add_date'],
                    driver=self, extra=extra)
        return node


    def ex_power_reset(self, node, reset_type):
        data = {
            "uuid": node.extra['uuid'],
            "reset_type": reset_type
        }
        res = self.connection.request('/clearos/clearapi/v2/rest/host/power_reset',
                                      data=json.dumps(data), method='POST')
        return res.status in [httplib.OK, httplib.CREATED, httplib.ACCEPTED]

    def ex_get_host(self, node):
        data = {"uuid": node.extra['uuid']}
        response = self.connection.request('/clearos/clearapi/v2/rest/host/get_host',
                                      data=json.dumps(data), method='POST')
        if 'data' in response.object:
            ret = {}
            ret['id'] = response.object['data']['id']
            ret['uuid'] = response.object['data']['uuid']
            ret['power_control_info'] = response.object['data']['power_control_info']
            ret['power_supply_info'] = response.object['data']['power_supply_info']

        return ret

    def ex_upload_firmware(self, node, zip_file):
        files={'zip_file': zip_file}
        data = {
            "uuid": node.extra['uuid']
        }
        res = self.connection.request('/clearos/clearapi/v2/rest/host/upload_firmware',
                                      files=files, data=data, method='POST')
        return res.status in [httplib.OK, httplib.CREATED, httplib.ACCEPTED]

    def ex_put_firmware(self, node, firmware_id):
        data = {
            "uuid": node.extra['uuid'],
            "firmware_id": firmware_id
        }
        res = self.connection.request('/clearos/clearapi/v2/rest/host/put_firmware',
                                      data=json.dumps(data), method='POST')
        return res.status in [httplib.OK, httplib.CREATED, httplib.ACCEPTED]

    def ex_delete_firmware(self, node, firmware_id):
        data = {
            "uuid": node.extra['uuid'],
            "firmware_id": firmware_id
        }
        res = self.connection.request('/clearos/clearapi/v2/rest/host/delete_firmware',
                                      data=json.dumps(data), method='POST')
        return res.status in [httplib.OK, httplib.CREATED, httplib.ACCEPTED]

    def ex_backup_firmware(self, node):
        data = {
            "uuid": node.extra['uuid']
        }
        res = self.connection.request('/clearos/clearapi/v2/rest/host/take_backup_firmware',
                                      data=json.dumps(data), method='POST')
        return res.status in [httplib.OK, httplib.CREATED, httplib.ACCEPTED]
