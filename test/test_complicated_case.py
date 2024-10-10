import asyncio
import time
from easy_sync import sync_compatible

from functools import wraps
from collections.abc import Awaitable, Callable
from typing import TypeVar, ParamSpec


P = ParamSpec("P")
R = TypeVar("R")

def debug_async(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})")
        result = await func(*args, **kwargs)
        print(f"Returning {func.__name__}({signature}) = {result!r}")
        return result
    return wrapper

def _sync_add(a: int, b: int) -> int:
    ''' Add two numbers synchronously '''
    time.sleep(0.1)
    return a + b

@sync_compatible(sync_fn=_sync_add)
@debug_async
async def async_add(a: int, b: int) -> int:
    await asyncio.sleep(0.1)
    ''' Add two numbers asynchronously '''
    return a + b

@sync_compatible
@debug_async
async def async_double(x: int) -> int:
    r = await async_add(x, x)
    return r

@sync_compatible
async def async_list_comprehension(n: int) -> int:
    return sum([await async_add(i, i) for i in range(n)])

@sync_compatible
async def async_calc():

    @sync_compatible
    async def async_nested_func():
        r = await async_double(0)
        return r

    r = await async_double(15) + await async_list_comprehension(4) + await async_nested_func()
    print(r)
    return r


def test_complicated_case():

    def do_sync():
        r1 = async_add(1, 2).wait()
        assert r1 == 3
        print(r1)

        r2 = async_calc().wait()
        assert r2 == 42
        print(r2)

    do_sync()
    r3 = async_calc().wait()
    assert r3 == 42
    print(r3)

    async def async_main():
        r4 = await async_add(3, 4)
        assert r4 == 7
        print(r4)

        do_sync() #NOTE: the nested case

    asyncio.run(async_main())

    r5 = async_calc().wait()
    assert r5 == 42
    print(r5)
