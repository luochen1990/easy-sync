import asyncio
import time
from easy_async import sync_compatible

def _sync_add(a: int, b: int) -> int:
    ''' Add two numbers synchronously '''
    time.sleep(1)
    return a + b

@sync_compatible(sync_fn=_sync_add)
async def async_add(a: int, b: int) -> int:
    await asyncio.sleep(1)
    ''' Add two numbers asynchronously '''
    return a + b

def test_name_resue_style():

    def do_sync():

        print(async_add(1, 2).wait())
        print(async_add(3, 4).wait())

    do_sync()

    async def async_main():
        result = await async_add(1, 2)
        print(result)

        do_sync() #NOTE: the nested case

    asyncio.run(async_main())
