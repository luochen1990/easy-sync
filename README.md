Easy Async
==========

**NOTE: This is a WIP project without a proper implementation yet.**

But tests are added, and things are strictly type checked here.

I would be extremely grateful if someone could contribute a proper implementation.

Any discussion about it's implementation is welcome [here](https://github.com/luochen1990/easy-async/discussions).

There is also a discussion on [StackOverflow Question](https://stackoverflow.com/questions/77274838/how-do-i-wrap-asyncio-calls-in-general-purpose-non-async-functions).

Motivation
----------

I don't want to always duplicate implementations for both synchronous and asynchronous versions of the same thing, as it is a waste of time.

So I hope there is some magic which can turn my asynchronous function implementations into synchronous versions.

I call this magic `@sync_compatible` here, with this decorator, your function `f` can be called via both `await f(x)` (in a asynchronous context) or `f(x).wait()` (in a synchronous context).


Usage
-----

```python
from easy_async import sync_compatible

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

Run tests
---------

You can use `nix develop .` or `poetry shell` under the project root to enter the develop environment.

Currently, if you run `pytest` you will got:

```text
========================================== short test summary info ===========================================
FAILED test/asyncer_impl/test_asyncer_impl.py::test_asyncer_impl - RuntimeError: This function can only be run from an AnyIO worker thread
FAILED test/test_nested_case.py::test_nested_case - RuntimeError: asyncio.run() cannot be called from a running event loop
======================================== 2 failed, 1 passed in 6.06s =========================================
```
