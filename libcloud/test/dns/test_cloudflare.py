# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

from libcloud.test import unittest

from libcloud.dns.drivers.cloudflare import CloudFlareDNSDriver
from libcloud.dns.drivers.cloudflare import ZONE_EXTRA_ATTRIBUTES
from libcloud.dns.drivers.cloudflare import RECORD_EXTRA_ATTRIBUTES
from libcloud.dns.types import RecordType, ZoneDoesNotExistError
from libcloud.utils.py3 import httplib
from libcloud.test.secrets import DNS_PARAMS_CLOUDFLARE
from libcloud.test.file_fixtures import DNSFileFixtures
from libcloud.test import MockHttp


class CloudFlareDNSDriverTestCase(unittest.TestCase):

    def setUp(self):
        CloudFlareDNSDriver.connectionCls.conn_classes = (
            CloudFlareMockHttp, CloudFlareMockHttp)
        CloudFlareMockHttp.type = None
        CloudFlareMockHttp.use_param = 'a'
        self.driver = CloudFlareDNSDriver(*DNS_PARAMS_CLOUDFLARE)

    def test_list_record_types(self):
        record_types = self.driver.list_record_types()
        self.assertEqual(len(record_types), 9)
        self.assertTrue(RecordType.A in record_types)

    def test_list_zones(self):
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 1)

        zone = zones[0]
        self.assertEqual(zone.id, '1234')
        self.assertEqual(zone.domain, 'example.com')
        self.assertEqual(zone.type, 'master')

        for attribute_name in ZONE_EXTRA_ATTRIBUTES:
            self.assertTrue(attribute_name in zone.extra)

    def test_list_records(self):
        zone = self.driver.list_zones()[0]
        records = self.driver.list_records(zone=zone)
        self.assertEqual(len(records), 18)

        record = records[0]
        self.assertEqual(record.id, '364797364')
        self.assertEqual(record.name, None)
        self.assertEqual(record.type, 'A')
        self.assertEqual(record.data, '192.30.252.153')

        for attribute_name in RECORD_EXTRA_ATTRIBUTES:
            self.assertTrue(attribute_name in record.extra)

        record = records[4]
        self.assertEqual(record.id, '364982413')
        self.assertEqual(record.name, 'yesyes')
        self.assertEqual(record.type, 'CNAME')
        self.assertEqual(record.data, 'verify.bing.com')

        for attribute_name in RECORD_EXTRA_ATTRIBUTES:
            self.assertTrue(attribute_name in record.extra)

    def test_get_zone(self):
        zone = self.driver.get_zone(zone_id='1234')
        self.assertEqual(zone.id, '1234')
        self.assertEqual(zone.domain, 'example.com')
        self.assertEqual(zone.type, 'master')

    def test_get_zone_zone_doesnt_exist(self):
        self.assertRaises(ZoneDoesNotExistError, self.driver.get_zone,
                          zone_id='doenstexist')

    def test_create_record(self):
        zone = self.driver.list_zones()[0]
        record = self.driver.create_record(name='test5', zone=zone, type='A',
                                           data='127.0.0.3')
        self.assertEqual(record.id, '412561327')
        self.assertEqual(record.name, 'test5')
        self.assertEqual(record.type, 'A')
        self.assertEqual(record.data, '127.0.0.3')

    def test_update_records(self):
        zone = self.driver.list_zones()[0]
        record = zone.list_records()[0]
        updated_record = self.driver.update_record(record=record,
                                                   data='127.0.0.4')

        self.assertEqual(updated_record.name, 'test6')
        self.assertEqual(updated_record.type, 'A')
        self.assertEqual(updated_record.data, '127.0.0.4')
        self.assertEqual(updated_record.ttl, 120)

    def test_delete_record(self):
        zone = self.driver.list_zones()[0]
        record = zone.list_records()[0]
        result = self.driver.delete_record(record=record)
        self.assertTrue(result)

    def test_delete_zone(self):
        zone = self.driver.list_zones()[0]
        self.assertRaises(NotImplementedError, self.driver.delete_zone,
                          zone=zone)

    def test_ex_get_zone_stats(self):
        zone = self.driver.list_zones()[0]
        result = self.driver.ex_get_zone_stats(zone=zone)
        self.assertTrue('trafficBreakdown' in result)
        self.assertTrue('bandwidthServed' in result)
        self.assertTrue('requestsServed' in result)
        self.assertTrue('pro_zone' in result)
        self.assertTrue('userSecuritySetting' in result)

    def test_ex_zone_check(self):
        zone = self.driver.list_zones()[0]
        result = self.driver.ex_zone_check(zones=[zone])
        self.assertEqual(result, {'example.com': 4025956})

    def test_ex_get_ip_threat_score(self):
        result = self.driver.ex_get_ip_threat_score(ip='127.0.0.1')
        self.assertEqual(result, {'127.0.0.1': False})

    def test_get_ex_zone_settings(self):
        zone = self.driver.list_zones()[0]
        result = self.driver.ex_get_zone_settings(zone=zone)
        self.assertTrue('dnssec' in result)
        self.assertTrue('ddos' in result)
        self.assertTrue('email_filter' in result)
        self.assertTrue('secureheader_settings' in result)


class CloudFlareMockHttp(MockHttp):
    fixtures = DNSFileFixtures('cloudflare')

    def _api_json_html_zone_load_multi(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('zone_load_multi.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_rec_load_all(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('rec_load_all.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_rec_new(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('rec_new.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_rec_delete(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('rec_delete.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_rec_edit(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('rec_edit.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_stats(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('stats.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_zone_check(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('zone_check.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_ip_lkup(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('ip_lkup.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _api_json_html_zone_settings(
            self, method, url, body, headers):
        if method == 'GET':
            body = self.fixtures.load('zone_settings.json')
        else:
            raise AssertionError('Unsupported method')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())