# -*- coding: utf-8 -*-

# This file is part of tornado-stale-client.
# https://github.com/globocom/tornado-stale-client

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2016, Globo.com <backstage@corp.globo.com>

from io import BytesIO

import tornado.web
from tornado import gen
from tornado.httpclient import HTTPRequest, HTTPResponse, HTTPError
from tornado.httputil import HTTPHeaders
from tornado.testing import AsyncHTTPTestCase, gen_test
from smart_sentinel.tornado_client import TornadoStrictRedis

from tornado_stale_client import StaleHTTPClient


class FakeClient(object):

    def __init__(self, responses=None):
        self.responses = responses or []

    @gen.coroutine
    def fetch(self, request, **kwargs):
        raise gen.Return(self.responses.pop(0))

    def add_response(self, headers=None, code=200, body=b'fake'):
        request = HTTPRequest('/fake')
        headers = HTTPHeaders(headers or {})
        buffer = BytesIO(body)
        response = HTTPResponse(
            request=request,
            headers=headers,
            code=code,
            buffer=buffer,
        )
        self.responses.append(response)
        return response


class StaleHTTPClientTestCase(AsyncHTTPTestCase):
    @gen.coroutine
    def setUp(self):
        super(StaleHTTPClientTestCase, self).setUp()
        self.fake_client = FakeClient()
        self.cache = TornadoStrictRedis()
        yield self.cache.flushall()

    def get_app(self):
        return tornado.web.Application([])

    @gen_test
    def test_returns_response(self):
        fake_response = self.fake_client.add_response(
            code=200, body=b'fake response', headers={'fake': 'header'})

        client = StaleHTTPClient(cache=self.cache, client=self.fake_client)

        response = yield client.fetch('/url')

        self.assertResponseEqual(response, fake_response)

    @gen_test
    def test_accepts_request_object(self):
        fake_response = self.fake_client.add_response()

        client = StaleHTTPClient(cache=self.cache, client=self.fake_client)

        request = HTTPRequest('/url')
        response = yield client.fetch(request)

        self.assertIs(response, fake_response)

    @gen_test
    def test_returns_real_response(self):
        expected_response = self.fake_client.add_response()

        client = StaleHTTPClient(cache=self.cache, client=self.fake_client)
        response = yield client.fetch('/url')

        self.assertIs(response, expected_response)

    @gen_test
    def test_returns_response_from_primary_cache(self):
        response = self.fake_client.add_response()

        client = StaleHTTPClient(cache=self.cache, client=self.fake_client)
        response = yield client.fetch('/url')
        cached_response = yield client.fetch('/url')

        self.assertIsNot(cached_response, response)
        self.assertResponseEqual(cached_response, response)

    @gen_test
    def test_returns_stale_response_after_error(self):
        expected_response = self.fake_client.add_response(body=b'stale')
        error_response = self.fake_client.add_response(body=b'error', code=500)

        client = StaleHTTPClient(
            cache=self.cache, client=self.fake_client, ttl=0.001)

        yield client.fetch('/url')
        yield tornado.gen.sleep(0.002)
        stale_response = yield client.fetch('/url')

        self.assertIsNot(stale_response, error_response)
        self.assertResponseEqual(stale_response, expected_response)

    @gen_test
    def test_raises_error_after_error_with_empty_cache(self):
        self.fake_client.add_response(body=b'error', code=500)

        client = StaleHTTPClient(
            cache=self.cache, client=self.fake_client, ttl=None)

        with self.assertRaises(HTTPError):
            yield client.fetch('/url')

    @gen_test
    def test_returns_error_when_empty_cache_and_raise_error_flag_is_off(self):
        expected_response = self.fake_client.add_response(
            body=b'error', code=500)

        client = StaleHTTPClient(
            cache=self.cache, client=self.fake_client, ttl=None)

        response = yield client.fetch('/url', raise_error=False)

        self.assertIs(response, expected_response)

    @gen_test
    def test_caches_multiple_urls(self):
        first_expected = self.fake_client.add_response()
        second_expected = self.fake_client.add_response()

        client = StaleHTTPClient(
            cache=self.cache, client=self.fake_client, ttl=1)

        # Populate cache
        yield [client.fetch('/first'), client.fetch('/second')]

        # Read from cache
        first_response, second_response = yield [
            client.fetch('/first'), client.fetch('/second')]

        self.assertIsNot(first_response, first_expected)
        self.assertIsNot(second_response, second_expected)

        self.assertResponseEqual(first_response, first_expected)
        self.assertResponseEqual(second_response, second_expected)

    @gen_test
    def test_varies_cache_by_headers(self):
        json_response = self.fake_client.add_response(body=b'{}')
        xml_response = self.fake_client.add_response(body=b'<xml />')

        client = StaleHTTPClient(
            cache=self.cache, client=self.fake_client, ttl=1)

        # Populate and read from cache
        for i in range(2):
            first_response, second_response = yield [
                client.fetch('/url', headers={'Accept': 'application/json'}, vary=['Accept']),
                client.fetch('/url', headers={'Accept': 'text/xml'}, vary=['Accept'])
            ]

        self.assertIsNot(first_response, json_response)
        self.assertIsNot(second_response, xml_response)

        self.assertResponseEqual(first_response, json_response)
        self.assertResponseEqual(second_response, xml_response)

    def assertResponseEqual(self, response, expected_response):
        self.assertEqual(response.body, expected_response.body)
        self.assertEqual(response.code, expected_response.code)
        self.assertEqual(response.headers, expected_response.headers)

        self.assertIsInstance(response.headers, HTTPHeaders)

        self.assertIsInstance(response.request, HTTPRequest)
        self.assertIsInstance(response.request.headers, HTTPHeaders)
