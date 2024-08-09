Easy Sync
=========

[![codecov](https://codecov.io/github/luochen1990/easy-sync/graph/badge.svg?token=OBG1BWIKC2)](https://codecov.io/github/luochen1990/easy-sync)

Provide sync compatibility for your async functions

Motivation
----------

I don't want to always duplicate implementations for both synchronous and asynchronous versions of the same thing, and think out two name for each of them, as it is a waste of time.

So I hope there is some magic which can turn my asynchronous function implementations into synchronous versions.

I call this magic `@sync_compatible` here, with this decorator, your function `f` can be called via both `await f(x)` (in a asynchronous context) or `f(x).wait()` (in a synchronous context).


Features
--------

1. Use a single name of function for both async and sync version
2. Automatic provide a sync vertion from async version (code generation underground)
3. Lightweight, pure python, and no dependencies
4. Strict type annotation (validated by pylance the strict mode)
5. Unit test, and test coverage ratio is monitored

Usage
-----

Install via `pip install easy-sync` or `poetry add easy-sync` from ([pypi](https://pypi.org/project/easy-sync/))

### The Magic Style

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

**NOTE: There are some requirements**

This will generate a sync version code of your async function, which replaces all `await f(...)` into `f(...).wait()` and `await asyncio.sleep(...)` into `time.sleep(...)`.

So you need to make sure all `await` statement is **sync compatible**.

A statement is **sync compatible** here if it is one of the following cases:

1. The called function `f` is decorated with `@sync_compatible` decorator, and called like `await f(...)`
2. The called function is exactly `asyncio.sleep`, and the statement is literally `await asyncio.sleep(...)`

For other case, you might need to define a wrapper for yourself, via **The Name Reusing Style** of `@sync_compatible`


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
