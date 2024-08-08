import asyncio
from functools import wraps
from typing import Awaitable, Callable, TypeAlias, TypeVar, ParamSpec, overload


P = ParamSpec("P")
R = TypeVar("R")

Thunk : TypeAlias = Callable[[], R]

class Waitable(Awaitable[R]):
    ''' A class to represent the result of an async operation '''

    def __init__(self, async_thunk: Thunk[Awaitable[R]], sync_thunk : Thunk[R] | None):
        self._async_thunk = async_thunk
        self._sync_thunk = sync_thunk or self._wait_async_thunk

    def __await__(self):
        return self._async_thunk().__await__()

    def wait(self) -> R:
        ''' sync wait for the result '''
        return self._sync_thunk()

    def _wait_async_thunk(self) -> R:
        ''' sync wait for the result '''
        r : R = asyncio.run(self._async_thunk()) #type: ignore
        return r #type: ignore


@overload
def sync_compatible(fn: Callable[P, Awaitable[R]]) -> Callable[P, Waitable[R]]:
    ...

@overload
def sync_compatible(*, sync_fn: Callable[P, R]) -> Callable[ [Callable[P, Awaitable[R]]], Callable[P, Waitable[R]]]:
    ...

def sync_compatible( #type: ignore
        sync_fn: Callable[P, Awaitable[R]] | Callable[P, R]) -> Callable[P, Waitable[R]] | Callable[ [Callable[P, Awaitable[R]]], Callable[P, Waitable[R]]]:

    '''
    A decorator to make an async function sync compatible

    Usage 1 (use the default sync version, not recommended since it uses asyncio.run() and not works in nested async functions for now):

        ```
        @sync_compatible
        async def async_add(a: int, b: int) -> int:
            await asyncio.sleep(1)
            return a + b

        def main():
            print(async_add(1, 2).wait())
            print(async_add(3, 4).wait())

        main()
        ```


    Usage 2 (reuse name only, you need to provide the sync version yourself):

        ```
        def _sync_add(a: int, b: int) -> int:
            sleep(1)
            return a + b

        @sync_compatible(sync_fn = _sync_add)
        async def async_add(a: int, b: int) -> int:
            await asyncio.sleep(1)
            return a + b

        def main():
            print(async_add(1, 2).wait())
            print(async_add(3, 4).wait())

        main()
        ```
    '''

    def wrapper_maker_maker(sync_fn: Callable[P, R] | None) -> Callable[ [Callable[P, Awaitable[R]]], Callable[P, Waitable[R]]]:
        def wrapper_maker(fn: Callable[P, Awaitable[R]]) -> Callable[P, Waitable[R]]:

            @wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> Waitable[R]:

                def sync_thunk() -> R:
                    return sync_fn(*args, **kwargs) #type: ignore

                def async_thunk() -> Awaitable[R]:
                    return fn(*args, **kwargs)

                return Waitable(async_thunk=async_thunk, sync_thunk=sync_thunk if sync_fn else None)

            return wrapper
        return wrapper_maker

    if asyncio.iscoroutinefunction(sync_fn):
        return wrapper_maker_maker(None)(sync_fn)
    else:
        return wrapper_maker_maker(sync_fn)
