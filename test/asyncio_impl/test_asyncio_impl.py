import asyncio
from functools import wraps
from typing import Awaitable, Callable, TypeVar, ParamSpec
import pytest
import easy_sync


P = ParamSpec("P")
R = TypeVar("R")


class Waitable(easy_sync.Waitable[R]):
    ''' A class to represent the result of an async operation '''

    #@override
    def _wait_async_thunk(self) -> R:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        r = loop.run_until_complete(self._async_thunk())
        return r


def sync_compatible(fn: Callable[P, Awaitable[R]]) -> Callable[P, Waitable[R]]:

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Waitable[R]:

        def async_thunk() -> Awaitable[R]:
            return fn(*args, **kwargs)

        return Waitable(async_thunk=async_thunk, sync_thunk=None)

    return wrapper


@pytest.mark.xfail(reason="Not Possible")
def test_asyncer_impl_nested_case():

    @sync_compatible
    async def async_add(a: int, b: int) -> int:
        await asyncio.sleep(0.1)
        ''' Add two numbers asynchronously '''
        return a + b

    def do_sync():

        print(async_add(1, 2).wait())
        print(async_add(3, 4).wait())

    do_sync()

    async def async_main():
        result = await async_add(1, 2)
        print(result)

        do_sync() #NOTE: the nested case

    asyncio.run(async_main())
