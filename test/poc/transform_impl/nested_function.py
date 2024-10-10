import inspect

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeAlias, TypeVar, ParamSpec


P = ParamSpec("P")
R = TypeVar("R")

Thunk : TypeAlias = Callable[[], R]

def show_source_code(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    source_code = inspect.getsource(fn)
    print("SOURCE CODE (from decorator):")
    print(source_code)
    return fn

@show_source_code
async def async_calc():

    @show_source_code
    async def async_nested_func():
        return 1

    source_code = inspect.getsource(async_nested_func)
    print("SOURCE CODE (direct):")
    print(source_code)

    r = 1 + await async_nested_func()
    print(r)
    return r

if __name__ == "__main__":
    import asyncio

    async def main():
        r = await async_calc()
        print(r)

    asyncio.run(main())
