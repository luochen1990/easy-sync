Easy Sync
=========

[![codecov](https://codecov.io/github/luochen1990/easy-sync/graph/badge.svg?token=OBG1BWIKC2)](https://codecov.io/github/luochen1990/easy-sync)

Easily provide synchronous compatibility for your Python asynchronous functions

Motivation
----------

Everytime I provide a Python package to my user, I'm expected to provide both sync version and async version API at the same time.

But I don't want to always duplicate implementations for both synchronous and asynchronous versions of the same thing, and think out two name for each of them, as it is a waste of time, and far from DRY.

I hope there is some magic which can turn my asynchronous function implementations into synchronous versions, so I can write once and get both of them.

I call this magic `@sync_compatible` here, your decorated function `f` can be called via both `await f(x)` (in a asynchronous context) or `f(x).wait()` (in a synchronous context).


Features
--------

1. Expose a single function name for both async and sync version
2. Automatic provide a sync version from your async function definition (via Metaprogramming)
3. Lightweight, pure python, and no dependencies
4. Complex cases such as list comprehensions, nested function definitions are also supported, feel free to write your pythonic code.
5. Strict type annotation are contained, and validated by pylance the strict mode. all type information is kept here
6. Unit tests contained, and test coverage ratio is monitored

Install
-------

```sh
pip install easy-sync
```
or

```sh
poetry add easy-sync
```

from ([pypi](https://pypi.org/project/easy-sync/))

Usage
-----


### The Automatic Usage

```python
from easy_sync import sync_compatible

@sync_compatible
async def async_add(a: int, b: int) -> int:
    await asyncio.sleep(1)
    return a + b

print(async_add(1, 2).wait())
```

This will generate a sync version code of your async function, the logic is:

1. Replaces all `await f(...)` statements into `f(...).wait()`
2. Replaces all `await asyncio.sleep(...)` statements into `time.sleep(...)`.

For other cases, you might need to define a wrapper for yourself, via [**The Manual Usage**](#the-manual-usage) of `@sync_compatible`

**Tips**

1. Extra decorators is ignored in the generated sync function, since they are written for async functions and probably not works on sync functions, keep them might cause unexpected error. If you really need them, please use [**The Manual Usage**](#the-manual-usage) and add decorators manually.
2. If you got `.wait() method not found` issues when use the `@sync_compatible` decorator with extra decorators, try lift this outer


### The Manual Usage

Instead of automatic generate the sync version, you are allowed to provide the sync function manually, and expose a single name to users.

This is useful to define your own wrapper, or cover some special cases the automatic usage cannot handle.

```python
from easy_sync import sync_compatible

@sync_compatible(sync_fn = _sync_fetch_url)
async def fetch_url(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

def _sync_fetch_url(url: str) -> str:
    return requests.get(url).text

@sync_compatible
async def get_data() -> str:
    return await fetch_url("https://site.name/path")

print(get_data().wait())
```


Run tests and Contribute
------------------------

You can use `nix develop .` or `poetry shell` under the project root to enter the develop environment.

Run unit tests via `pytest`, or run `pytest --cov=src` for coverage report.
