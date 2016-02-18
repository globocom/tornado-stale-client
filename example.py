# -*- coding: utf-8 -*-

import logging
import sys

import tornado
from tornado import gen

from tornado_stale_client import StaleHTTPClient


@gen.coroutine
def main():
    from redis import StrictRedis

    cache = StrictRedis()
    client = StaleHTTPClient(cache=cache)

    response = yield client.fetch('http://www.globo.com')
    print(
        response.code, 'GET',
        response.effective_url, response.body[:50], '...')

    tornado.ioloop.IOLoop.instance().stop()


if __name__ == '__main__':
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    root.addHandler(stream)

    main()

    tornado.ioloop.IOLoop.instance().start()
