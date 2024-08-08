Easy Sync
=========

Provide sync compatibility for your async functions

Motivation
----------

I don't want to always duplicate implementations for both synchronous and asynchronous versions of the same thing, and think out two name for each of them, as it is a waste of time.

So I hope there is some magic which can turn my asynchronous function implementations into synchronous versions.

I call this magic `@sync_compatible` here, with this decorator, your function `f` can be called via both `await f(x)` (in a asynchronous context) or `f(x).wait()` (in a synchronous context).


Features
--------

1. Use a single name of function for both async and sync version
2. Automatic provide a sync vertion from async version (WIP)
3. Lightweight, pure python, and no dependencies
4. Strict type annotation (validated by pylance the strict mode)
5. Unit test, and test coverage ratio is monitored

Usage
-----

### The Magic Style (WIP)

```python
from easy_sync import sync_compatible

@sync_compatible
async def async_add(a: int, b: int) -> int:
    await asyncio.sleep(1)
    ''' Add two numbers asynchronously '''
    return a + b

def do_sync():

    print(async_add(1, 2).wait())
    print(async_add(3, 4).wait())

do_sync()

async def async_main():
    result = await async_add(1, 2)
    print(result)

asyncio.run(async_main())
```

**NOTE: This usage is WIP and without a proper implementation yet.**

I would be extremely grateful if someone could contribute a proper implementation.

Any discussion about it's implementation is welcome [here](https://github.com/luochen1990/easy-sync/discussions).

There is also a discussion on [StackOverflow Question](https://stackoverflow.com/questions/77274838/how-do-i-wrap-asyncio-calls-in-general-purpose-non-async-functions).


### The Name Reusing Style

Use this helper to just reuse name only, you need to provide the sync version yourself.

This is not our final goal, but at least it solves the naming problem for now :)

```python
from easy_sync import sync_compatible

@sync_compatible(sync_fn = _sync_add)
async def async_add(a: int, b: int) -> int:
    await asyncio.sleep(1)
    return a + b

def _sync_add(a: int, b: int) -> int:
    sleep(1)
    return a + b

def main():
    print(async_add(1, 2).wait())
    print(async_add(3, 4).wait())

main()
```


Run tests and Contribute
------------------------

You can use `nix develop .` or `poetry shell` under the project root to enter the develop environment.

Currently, if you run `pytest` you will find that some cases is marked as `xfailed`, which are tests for WIP usage.

You can change the [alternative impl code](/test/asyncer_impl/test_asyncer_impl.py) to your own implementation and re-run `pytest`.
