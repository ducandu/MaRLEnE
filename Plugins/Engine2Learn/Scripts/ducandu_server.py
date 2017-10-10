import unreal_engine as ue
import asyncio
import ue_asyncio
from unreal_engine.classes import DucanduSettings, GameplayStatics

# cleanup previous tasks
for task in asyncio.Task.all_tasks():
    task.cancel()

# this is called whenever a new client connects
async def new_client_connected(reader, writer):
    name = writer.get_extra_info('peername')
    ue.log('new client connection from {0}'.format(name))
    y = 2000
    while True:
        # wait for a line
        data = await reader.readline()
        if not data:
            break
        # first search for the currently running world
        playing_world = None
        for world in ue.all_worlds():
            if world.get_world_type() in (1, 3):
                playing_world = world
                break
        if playing_world:
            for actor in playing_world.all_actors():
                if actor.get_name() == 'Cube_2':
                    actor.set_actor_location(700, -300, 2022 * y)
            ue.log_warning('client {0} issued command "{1}" on world "{2}"'.format(name, data.decode().rstrip(), world.get_name()))
            GameplayStatics.SetGamePaused(playing_world, False)
            playing_world.world_tick(1.0/60.0)
            # here we tick the world
            GameplayStatics.SetGamePaused(playing_world, True)
        else:
            ue.log_error('client {0} issued command "{1}" but no game is running'.format(name, data.decode().rstrip()))
        y += 1
    ue.log('client {0} disconnected'.format(name))

# this spawns the server
# the try/finally trick allows for gentle shutdown of the server
# see below for more infos about exception management
async def spawn_server(host, port):
    try:
        coro = await asyncio.start_server(new_client_connected, host, port)
        ue.log('tcp server spawned on {0}:{1}'.format(host, port))
        await coro.wait_closed()
    finally:
        coro.close()
        ue.log('tcp server ended')
    
settings = ue.get_mutable_default(DucanduSettings)
if settings.Address and settings.Port:
    asyncio.ensure_future(spawn_server(settings.Address, settings.Port))