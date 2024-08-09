import asyncio
from easy_sync import sync_compatible

@sync_compatible
async def async_call():
    return "Hello, world"

def wrapped_call():
    return async_call().wait()

async def async_main():
    print(wrapped_call())

def sync_main():
    print(wrapped_call())

def test_so_question():
    ''' This MRE is from: https://stackoverflow.com/q/77274838/1608276 '''

    print("Calling in asyncio context")
    asyncio.get_event_loop().run_until_complete(async_main())
