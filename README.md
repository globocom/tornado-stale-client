# tornado-stale-client

An async http client for tornado with stale cache support.


# Using

```python
from redis import StrictRedis
from tornado_stale_client import StaleHTTPClient

@gen.coroutine
def main():
    cache = StrictRedis()
    client = StaleHTTPClient(cache=cache)

    response = yield client.fetch('http://...')
    print(response.code, 'GET', url, response.body)
```

Check `example.py` for a runnable demo.


# Options

The client accepts the following options:

| Option               | Description                                                        | Default                              |
| -------------------- | ------------------------------------------------------------------ | ------------------------------------ |
| cache                | `StrictRedis` instance or compatible                               | `redis.StrictRedis`                  |
| client               | Accepts any compatible tornado async http client                   | `tornado.httpclient.AsyncHTTPClient` |
| primary_key_prefix   | Prefix to use for the primary cache                                | "primary_http"                       |
| stale_key_prefix     | Prefix to use for the stale cache                                  | "stale_http"                         |
| ttl                  | `float`, time in seconds to keep the response in the primary cache | 5.0                                  |
| vary                 | list of headers in which the cache should vary                     | None                                 |


# Installing

```
pip install tornado-stale-client
```

# Testing / contributing

Clone, setup, test.

```
make setup
make test
```

# Releasing

* Bump to a `patch`, `minor` or `major` version.

```
# By default bumps to a patch version
make bump

# Or specific bump
make patch bump
make minor bump
make major bump
```

* Upload release to PyPI

The name of the server on `.pypirc` will be asked.

```
make release
```

