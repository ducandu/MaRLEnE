import asyncio
import unreal_engine as ue

loop = asyncio.new_event_loop()

asyncio.set_event_loop(loop)

def ticker_loop(delta_time):
    try:
        loop.stop()
        loop.run_forever()
    except Exception as e:
        ue.log_error(e)
    return True


ticker = ue.add_ticker(ticker_loop)