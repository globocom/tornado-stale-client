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

1. Bump to a `patch`, `minor` or `major` version.

```
# By default bumps to a patch version
make bump

# Or specific bump
make patch bump
make minor bump
make major bump
```

2. Upload release to PyPI

The name of the server on `.pypirc` will be asked.

```
make release
```

