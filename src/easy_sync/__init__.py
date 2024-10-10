import asyncio
from functools import wraps
from collections.abc import Awaitable, Callable
from typing import TypeAlias, TypeVar, ParamSpec, overload
from easy_sync.transform import transform_function_to_sync


P = ParamSpec("P")
R = TypeVar("R")

Thunk : TypeAlias = Callable[[], R]

class Waitable(Awaitable[R]):
    ''' A class to represent the result of an async operation '''

    def __init__(self, async_thunk: Thunk[Awaitable[R]], sync_thunk : Thunk[R]):
        self._async_thunk = async_thunk
        self._sync_thunk = sync_thunk

    def __await__(self):
        return self._async_thunk().__await__()

    def wait(self) -> R:
        ''' sync wait for the result '''
        return self._sync_thunk()


@overload
def sync_compatible(fn: Callable[P, Awaitable[R]]) -> Callable[P, Waitable[R]]:
    ... # pragma: no cover

@overload
def sync_compatible(*, sync_fn: Callable[P, R]) -> Callable[ [Callable[P, Awaitable[R]]], Callable[P, Waitable[R]]]:
    ... # pragma: no cover

def sync_compatible( #type: ignore
        sync_fn: Callable[P, Awaitable[R]] | Callable[P, R]) -> Callable[P, Waitable[R]] | Callable[ [Callable[P, Awaitable[R]]], Callable[P, Waitable[R]]]:

    '''
    A decorator to make an async function sync compatible

    Usage 1 (generate sync version automatically):

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


    Usage 2 (reuse name only, specify the sync version yourself):

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

    if asyncio.iscoroutinefunction(sync_fn):
        # 装饰器的无参数用法，这里的 sync_fn 直接是被装饰的 async 函数而不是 sync_fn 参数
        fn = sync_fn # the function is async actually
        return sync_compatible_auto(fn)
    else:
        return sync_compatible_manual(sync_fn) #type: ignore


def sync_compatible_auto(fn: Callable[P, Awaitable[R]]) -> Callable[P, Waitable[R]]:
    real_sync_fn = transform_function_to_sync(fn)
    return _wrapper_maker_maker(real_sync_fn)(fn)


def sync_compatible_manual(sync_fn: Callable[P, R]) -> Callable[ [Callable[P, Awaitable[R]]], Callable[P, Waitable[R]]]:
    return _wrapper_maker_maker(sync_fn)


def _wrapper_maker_maker(sync_fn: Callable[P, R]) -> Callable[ [Callable[P, Awaitable[R]]], Callable[P, Waitable[R]]]:
    def wrapper_maker(fn: Callable[P, Awaitable[R]]) -> Callable[P, Waitable[R]]:

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Waitable[R]:

            def sync_thunk() -> R:
                return sync_fn(*args, **kwargs) #type: ignore

            def async_thunk() -> Awaitable[R]:
                return fn(*args, **kwargs)

            return Waitable(async_thunk=async_thunk, sync_thunk=sync_thunk)

        return wrapper
    return wrapper_maker
