import unreal_engine as ue
import asyncio
import ue_asyncio
from unreal_engine.classes import DucanduSettings, GameplayStatics, E2LObserver
import msgpack

# cleanup previous tasks
for task in asyncio.Task.all_tasks():
    task.cancel()

# search for the currently running world
def get_playing_world():
    playing_world = None
    for world in ue.all_worlds():
        if world.get_world_type() in (1, 3):
            playing_world = world
            break
    return playing_world

def manage_message(message):
    snapshot = []
    playing_world = get_playing_world()
    if not playing_world:
        return {'status': 'error', 'message': 'no playing world'}
    print(message)
    # do what is required and then pause
    playing_world.world_tick(1.0/60.0)
    GameplayStatics.SetGamePaused(playing_world, False)
    snapshot = []
    for observer in E2LObserver.GetRegisteredObservers():
        if not observer.has_world():
            continue
        if observer.get_world() != playing_world:
            continue
        item = {}
        item['observer'] = observer.get_name()
        item['props'] = []
        for observed_prop in  observer.ObservedProperties:
            prop = {}
            prop['name'] = observed_prop.PropName
            prop['enabled'] = observed_prop.bEnabled
            item['props'].append(prop)
        snapshot.append(item)
    GameplayStatics.SetGamePaused(playing_world, False)
    return snapshot

# this is called whenever a new client connects
async def new_client_connected(reader, writer):
    name = writer.get_extra_info('peername')
    ue.log('new client connection from {0}'.format(name))
    unpacker = msgpack.Unpacker()
    y = 2000
    while True:
        # wait for a line
        data = await reader.read(8192)
        if not data:
            break
        unpacker.feed(data)
        for message in unpacker:
            response = manage_message(message)
            print(response)
            writer.write(msgpack.packb(response))

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