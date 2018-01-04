import unreal_engine as ue
import asyncio
import ue_asyncio


async def hello_postponed():
    print('i am the coroutine at the next tick')

print('scheduling coroutine at the next tick')
asyncio.ensure_future(hello_postponed())
print('done')
