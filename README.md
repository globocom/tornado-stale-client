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

