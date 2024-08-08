import asyncio

import pytest
from easy_async import sync_compatible

@sync_compatible
async def async_add(a: int, b: int) -> int:
    await asyncio.sleep(1)
    ''' Add two numbers asynchronously '''
    return a + b

@pytest.mark.xfail("nested case is not supported yet and waiting for a better implementation")
def test_nested_case():

    def do_sync():

        print(async_add(1, 2).wait())
        print(async_add(3, 4).wait())

    do_sync()

    async def async_main():
        result = await async_add(1, 2)
        print(result)

        do_sync() #NOTE: the nested case

    asyncio.run(async_main())
