# -*- coding: utf-8 -*-

# This file is part of tornado-stale-client.
# https://github.com/globocom/tornado-stale-client

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2016, Globo.com <backstage@corp.globo.com>

import json
import logging
from io import BytesIO
from urllib.parse import urlencode

import tornado
from tornado import gen
from tornado.httpclient import HTTPRequest, HTTPResponse
from tornado.httputil import HTTPHeaders
from smart_sentinel.tornado_client import TornadoStrictRedis


logger = logging.getLogger(__name__)


class StaleHTTPClient(object):

    def __init__(self, cache=None, client=None,
                 primary_key_prefix='primary_http',
                 stale_key_prefix='stale_http',
                 ttl=5, stale_ttl=None):

        self.cache = cache or TornadoStrictRedis()
        self.client = client or tornado.httpclient.AsyncHTTPClient()
        self.primary_key_prefix = primary_key_prefix
        self.stale_key_prefix = stale_key_prefix
        self.ttl = ttl
        self.stale_ttl = stale_ttl

    @gen.coroutine
    def fetch(self, request, vary=None, **kwargs):
        should_raise_error = kwargs.pop('raise_error', True)

        # Convert to HTTPRequest if fetching a URL
        if not isinstance(request, HTTPRequest):
            request = HTTPRequest(url=request, **kwargs)

        # Try the primary cache
        cached_response = yield self.get_primary_cache(request, vary=vary)
        if cached_response is not None:
            raise gen.Return(cached_response)

        # Get the real response
        real_response = yield self.client.fetch(
            request, raise_error=False, **kwargs)

        # Set cache and return on success
        if real_response.error is None:
            yield self.set_cache(request, vary, real_response)
            raise gen.Return(real_response)

        # Response failed, try the stale cache
        stale_response = yield self.get_stale_cache(request, vary=vary)
        if stale_response is not None:
            raise gen.Return(stale_response)

        # No stale, return or throw error
        if should_raise_error:
            real_response.rethrow()

        raise gen.Return(real_response)

    def get_key(self, request, vary):
        vary = vary or []
        vary_headers = {
            k.lower(): v for k, v in request.headers.items() if k in vary}
        return request.url + "#" + urlencode(vary_headers)

    def get_primary_key(self, request, vary):
        return '%s:%s' % (self.primary_key_prefix, self.get_key(request, vary))

    def get_stale_key(self, request, vary):
        return '%s:%s' % (self.stale_key_prefix, self.get_key(request, vary))

    @gen.coroutine
    def get_cache(self, request, key):
        raw_data = yield self.cache.get(key)
        if raw_data is None:
            return None
        logger.debug('Loaded cache: %s', key)
        response = self.deserialize_response(request, raw_data)
        return response

    @gen.coroutine
    def get_primary_cache(self, request, vary):
        key = self.get_primary_key(request, vary)
        result = yield self.get_cache(request, key)
        return result

    @gen.coroutine
    def get_stale_cache(self, request, vary):
        key = self.get_stale_key(request, vary)
        result = yield self.get_cache(request, key)
        return result

    @gen.coroutine
    def set_cache(self, request, vary, response):
        primary_key = self.get_primary_key(request, vary)
        stale_key = self.get_stale_key(request, vary)

        logger.debug('Caching response: %s', request.url)

        serialized_response = self.serialize_response(request, response)

        pipe = yield self.cache.pipeline()
        with pipe:
            microseconds = int(self.ttl * 1000)
            pipe.set(primary_key, serialized_response, px=microseconds)
            microseconds = self.stale_ttl and int(self.stale_ttl * 1000)
            pipe.set(stale_key, serialized_response, px=microseconds)
            pipe.execute()

    def serialize_response(self, request, response):
        return json.dumps({
            'headers': dict(response.headers),
            'body': response.body.decode(),
            'code': response.code,
        })

    def deserialize_response(self, request, raw_data):
        data = json.loads(raw_data.decode())
        buffer = BytesIO(bytes(data['body'], 'utf-8'))
        request.headers = HTTPHeaders(request.headers)
        return HTTPResponse(
            request=request,
            headers=HTTPHeaders(data['headers']),
            code=data['code'],
            buffer=buffer,
        )
