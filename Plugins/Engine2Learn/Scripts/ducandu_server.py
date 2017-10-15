import unreal_engine as ue
import asyncio
import ue_asyncio
from unreal_engine.classes import DucanduSettings, GameplayStatics, E2LObserver, CameraComponent, SceneCaptureComponent2D
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



def get_child_component(component, component_class):
    for child in component.AttachChildren:
        if child.is_a(component_class):
            return child
    return None

def manage_message(message):
    snapshot = []
    playing_world = get_playing_world()
    if not playing_world:
        return {'status': 'error', 'message': 'no playing world'}
    print(message)
    # do what is required and then pause
    GameplayStatics.SetGamePaused(playing_world, False)
    playing_world.world_tick(1.0/60.0)
    GameplayStatics.SetGamePaused(playing_world, True)
    snapshot = []
    for observer in E2LObserver.GetRegisteredObservers():
        if not observer.has_world():
            continue
        if observer.get_world() != playing_world:
            continue
        parent = observer.GetAttachParent()
        if not parent:
           continue
        item = {}
        item['observer'] = observer.get_name()
        if observer.bScreenCapture:
            if parent.is_a(SceneCaptureComponent2D):
                texture = parent.TextureTarget
                if not texture:
                    # todo pass texture size and format
                    texture = ue.create_transient_texture_render_target2d(1024, 1024)
                    parent.TextureTarget = texture
                # trigger scene capture
                parent.CaptureScene()
                item['screen'] = bytes(texture.render_target_get_data())
            elif parent.is_a(CameraComponent):
                scene_capture = get_child_component(parent, SceneCaptureComponent2D)
                if scene_capture:
                    texture = scene_capture.TextureTarget
                    scene_capture.CaptureScene()
                    item['screen'] = bytes(texture.render_target_get_data())
                else:
                    # if it is a CameraComponent, dynamically generate a new SceneCaptureComponent2D
                    scene_capture = parent.get_owner().add_actor_component(SceneCaptureComponent2D, 'Engine2LearnScreenCapture', parent)
                    scene_capture.bCaptureEveryFrame = False
                    scene_capture.bCaptureOnMovement = False
                    scene_capture.Texture = ue.create_transient_texture_render_target2d(1024, 1024)
                    # TODO: setup camera transform and options
                    scene_capture.CaptureScene()
                    print(scene_capture)
                    item['screen'] = bytes(texture.render_target_get_data())
        item['props'] = []
        for observed_prop in  observer.ObservedProperties:
            if not observed_prop.bEnabled:
                continue
            if not parent.has_property(observed_prop.PropName):
                continue
            prop = {}
            prop['name'] = observed_prop.PropName
            # for now, store it as a string
            prop['value'] = str(parent.get_property(observed_prop.PropName))
            item['props'].append(prop)
        snapshot.append(item)
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