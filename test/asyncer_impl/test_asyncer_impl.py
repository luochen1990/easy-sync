import asyncio
import asyncer
from typing import Callable, Coroutine, TypeVar
from typing_extensions import ParamSpec
import easy_async


X = TypeVar("X")
Y = TypeVar("Y")
P = ParamSpec("P")
R = TypeVar("R")


class Waitable(easy_async.Waitable[X, Y, R]):
    ''' A class to represent the result of an async operation '''

    def wait(self) -> R:
        return asyncer.syncify(lambda: self._coroutine)()


def sync_compatible(fn: Callable[P, Coroutine[X, Y, R]]) -> Callable[P, Waitable[X, Y, R]]:

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Waitable[X, Y, R]:
        awaitable = fn(*args, **kwargs)
        return Waitable(awaitable)

    return wrapper


def test_asyncer_impl():

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

        do_sync()

    asyncio.run(async_main())
