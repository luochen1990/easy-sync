import asyncio
from types import TracebackType
from typing import Callable, Coroutine, TypeVar
from typing_extensions import ParamSpec


X = TypeVar("X")
Y = TypeVar("Y")
P = ParamSpec("P")
R = TypeVar("R")


class Waitable(Coroutine[X, Y, R]):
    ''' A class to represent the result of an async operation '''

    def __init__(self, coroutine: Coroutine[X, Y, R]):
        self._coroutine = coroutine

    def __await__(self):
        return self._coroutine.__await__()

    def send(self, value: Y):
        return self._coroutine.send(value)

    def throw(self, typ: type[BaseException], val: BaseException | object = None, tb: TracebackType | None = None, /) -> X: #type: ignore
        return self._coroutine.throw(typ, val, tb)

    def close(self):
        return self._coroutine.close()

    def wait(self) -> R:
        ''' sync wait for the result '''

        ...  #TODO: waiting for a better implementation
        return asyncio.run(self._coroutine)


def sync_compatible(fn: Callable[P, Coroutine[X, Y, R]]) -> Callable[P, Waitable[X, Y, R]]:
    '''
    A decorator to make an async function sync compatible

    Usage:

    @sync_compatible
    async def async_add(a: int, b: int) -> int:
        await asyncio.sleep(1)
        return a + b

    def main():
        print(async_add(1, 2).wait())
        print(async_add(3, 4).wait())

    main()
    '''

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Waitable[X, Y, R]:
        awaitable = fn(*args, **kwargs)
        return Waitable(awaitable)

    return wrapper
