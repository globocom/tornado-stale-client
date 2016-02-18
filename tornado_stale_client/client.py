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


class StaleHTTPClient(object):

    def __init__(self, cache, client=None,
                 primary_key_prefix='primary_http',
                 stale_key_prefix='stale_http',
                 ttl=5, vary=None):

        self.cache = cache
        self.client = client or tornado.httpclient.AsyncHTTPClient()
        self.primary_key_prefix = primary_key_prefix
        self.stale_key_prefix = stale_key_prefix
        self.ttl = ttl
        self.vary = vary or ()

    @gen.coroutine
    def fetch(self, request, **kwargs):
        should_raise_error = kwargs.pop('raise_error', True)

        # Convert to HTTPRequest if fetching a URL
        if not isinstance(request, HTTPRequest):
            request = HTTPRequest(url=request, **kwargs)

        # Try the primary cache
        cached_response = self.get_primary_cache(request)
        if cached_response is not None:
            raise gen.Return(cached_response)

        # Get the real response
        real_response = yield self.client.fetch(
            request, raise_error=False, **kwargs)

        # Set cache and return on success
        if real_response.error is None:
            self.set_cache(request, real_response)
            raise gen.Return(real_response)

        # Response failed, try the stale cache
        stale_response = self.get_stale_cache(request)
        if stale_response is not None:
            raise gen.Return(stale_response)

        # No stale, return or throw error
        if should_raise_error:
            real_response.rethrow()

        raise gen.Return(real_response)

    def get_key(self, request):
        vary_headers = {
            k.lower(): v for k, v in request.headers.items() if k in self.vary}
        return request.url + "#" + urlencode(vary_headers)

    def get_primary_key(self, request):
        return '%s:%s' % (self.primary_key_prefix, self.get_key(request))

    def get_stale_key(self, request):
        return '%s:%s' % (self.stale_key_prefix, self.get_key(request))

    def get_cache(self, request, key):
        raw_data = self.cache.get(key)
        if raw_data is None:
            return None
        logging.debug('Loaded cache: %s', key)
        response = self.deserialize_response(request, raw_data)
        return response

    def get_primary_cache(self, request):
        key = self.get_primary_key(request)
        return self.get_cache(request, key)

    def get_stale_cache(self, request):
        key = self.get_stale_key(request)
        return self.get_cache(request, key)

    def set_cache(self, request, response):
        primary_key = self.get_primary_key(request)
        stale_key = self.get_stale_key(request)

        logging.debug('Caching response: %s', request.url)

        serialized_response = self.serialize_response(request, response)

        with self.cache.pipeline() as pipe:
            microseconds = int(self.ttl * 1000)
            pipe.psetex(primary_key, microseconds, serialized_response)
            pipe.set(stale_key, serialized_response)
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
        return HTTPResponse(
            request=request,
            headers=data['headers'],
            code=data['code'],
            buffer=buffer,
        )


