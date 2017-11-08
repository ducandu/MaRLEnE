import unreal_engine as ue
import asyncio
import ue_asyncio
from unreal_engine.classes import DucanduSettings, GameplayStatics, E2LObserver, CameraComponent, SceneCaptureComponent2D, InputSettings
from unreal_engine.structs import Key
from unreal_engine.enums import EInputEvent
import msgpack


# TODO: global observation_dict (populated only once, then written to in place) to save on garbage collection runs
_OBS_DICT = {}

# cleanup previous tasks
for task in asyncio.Task.all_tasks():
    task.cancel()


# search for the currently running world
def get_playing_world():
    playing_world = None
    ue.log("inside get_playing_world()")
    for world in ue.all_worlds():
        if world.get_world_type() in (1, 3):
            playing_world = world
            break
    ue.log("returning from get_playing_world()")
    return playing_world


def get_child_component(component, component_class):
    for child in component.AttachChildren:
        if child.is_a(component_class):
            return child
    return None


def reset(message):
    """
    Resets the Game to its default start position and returns the resulting obs_dict.
    """
    playing_world = get_playing_world()
    if not playing_world:
        return {"status": "error", "message": "No playing world!"}

    ue.log("Resetting level and pausing.")
    # reset level
    playing_world.restart_level()

    # pause the game
    GameplayStatics.SetGamePaused(playing_world, True)

    o = compile_obs_dict()
    ue.log("-> sending back status ok and obs_dict {}.".format(o))
    return {"status": "ok", "obs_dict": o}


def step(message):
    """
    Performs a single step in the game (could be several ticks) given some action/axis mappings and maybe some set commands.
    """
    playing_world = get_playing_world()
    if not playing_world:
        return {"status": "error", "message": "No playing world!"}

    delta_time = message.get(b"delta_time", 1.0/60.0)  # the force-set delta time (dt) for each tick
    num_ticks = message.get(b"num_ticks", 4)  # the number of ticks to work through (all with the given action/axis mappings valid)
    controller = playing_world.get_player_controller()

    ue.log("step command delta={} ticks={}".format(delta_time, num_ticks))

    # unpause the game and then perform n ticks with the given inputs (actions and axes)
    GameplayStatics.SetGamePaused(playing_world, False)
    for _ in range(num_ticks):
        #controller.input_axis(Key(KeyName="Right"), -1.0, delta_time)
        if b"axes" in message:
            for axis in message[b"axes"]:
                key_name = axis[0].decode()
                ue.log("-> axis {}={} (key={})".format(key_name, axis[1], Key(KeyName=key_name)))
                controller.input_axis(Key(KeyName=key_name), axis[1], delta_time)
        if b"actions" in message:
            for action in message[b"actions"]:
                action_name = action[0].decode()
                ue.log("-> action {}={}".format(action_name, action[1]))
                controller.input_key(Key(KeyName=action_name), EInputEvent.IE_Pressed if action[1] else EInputEvent.IE_Released)
        playing_world.world_tick(delta_time)
    # pause again
    GameplayStatics.SetGamePaused(playing_world, True)

    return {"status": "ok", "obs_dict": compile_obs_dict()}


def compile_obs_dict():
    """
    Compiles the current observations (based on all active E2LObservers) into a dictionary that is returned to the UE4Env object's reset/step/... methods.
    """
    playing_world = get_playing_world()

    for observer in E2LObserver.GetRegisteredObservers():
        if not observer.has_world():
            continue
        # observer lives in another world
        if observer.get_world() != playing_world:
            continue
        # make sure this observer is attached so some parent Actor/Component
        parent = observer.GetAttachParent()
        if not parent:
            continue

        obs_name = observer.get_name()

        # this observer returns a camera image
        if observer.bScreenCapture:
            if parent.is_a(SceneCaptureComponent2D):
                texture = parent.TextureTarget
                if not texture:
                    return {"status": "error", "message": "SceneCapture2DComponent (parent of Observer {}) does not have a TextureTarget "+
                                                          "(call `get_spec` first on the UE4Env)!".format(obs_name)
                            }
                parent.CaptureScene()  # trigger scene capture
                # TODO: copy the bytes into the same memory location each time to avoid garbage collection
                _OBS_DICT[obs_name+":camera"] = bytes(texture.render_target_get_data())
            elif parent.is_a(CameraComponent):
                scene_capture = get_child_component(parent, SceneCaptureComponent2D)
                if scene_capture:
                    texture = scene_capture.TextureTarget
                    scene_capture.CaptureScene()
                    # TODO: copy the bytes into the same memory location each time to avoid garbage collection
                    _OBS_DICT[obs_name+":camera"] = bytes(texture.render_target_get_data())
                else:
                    return {"status": "error", "message": "CameraComponent (parent of Observer {}) does not have a SceneCapture2DComponent "+
                                                          "(call `get_spec` first on the UE4Env)!".format(obs_name)
                            }
            else:
                return {"status": "error",
                        "message": "Observer {} has bScreenCapture set to true, but is not a child of either a Camera or a SceneCapture2D!".format(obs_name)}

        for observed_prop in observer.ObservedProperties:
            if not observed_prop.bEnabled:
                continue
            if not parent.has_property(observed_prop.PropName):
                continue
            _OBS_DICT[obs_name+":"+observed_prop.PropName] = str(parent.get_property(observed_prop.PropName))
    return _OBS_DICT


def get_spec():
    """
    Returns the observation_space (observers) and action_space (action- and axis-mappings) of the Game as a dict with keys:
    `observation_space` and `action_space`
    """
    auto_texture_size = (84, 84)  # the default size of SceneCapture2D components automatically added to a camera

    playing_world = get_playing_world()

    # build the action_space descriptor
    action_space_desc = {}
    input_ = ue.get_mutable_default(InputSettings)
    # go through all action mappings
    for action in input_.ActionMappings:
        if action.ActionName not in action_space_desc:
            action_space_desc[action.ActionName] = {"type": "action", "keys": [action.Key.KeyName]}
        else:
            action_space_desc[action.ActionName]["keys"].append(action.Key.KeyName)
    for axis in input_.AxisMappings:
        if axis.AxisName not in action_space_desc:
            action_space_desc[axis.AxisName] = {"type": "axis", "keys": [(axis.Key.KeyName, axis.Scale)]}
        else:
            action_space_desc[axis.AxisName]["keys"].append((axis.Key.KeyName, axis.Scale))
    ue.log("action_space_desc: {}".format(action_space_desc))

    # build the observation_space descriptor
    observation_space_desc = {}
    for observer in E2LObserver.GetRegisteredObservers():
        if not observer.has_world():
            continue
        # observer lives in another world
        if playing_world is not None and observer.get_world() != playing_world:
            continue
        # make sure this observer is attached so some parent Actor/Component
        parent = observer.GetAttachParent()
        if not parent:
           continue

        obs_name = observer.get_name()

        # this observer returns a camera image
        if observer.bScreenCapture:
            if parent.is_a(SceneCaptureComponent2D):
                texture = parent.TextureTarget
                if not texture:
                    # todo pass texture size and format
                    texture = ue.create_transient_texture_render_target2d(auto_texture_size[0], auto_texture_size[1])
                    parent.TextureTarget = texture
            elif parent.is_a(CameraComponent):
                scene_capture = get_child_component(parent, SceneCaptureComponent2D)
                if scene_capture:
                    texture = scene_capture.TextureTarget
                # if it is a CameraComponent without SceneCaptureComponent2D -> generate one dynamically
                else:
                    scene_capture = parent.get_owner().add_actor_component(SceneCaptureComponent2D, "Engine2LearnScreenCapture", parent)
                    scene_capture.bCaptureEveryFrame = False
                    scene_capture.bCaptureOnMovement = False
                    texture = scene_capture.TextureTarget = ue.create_transient_texture_render_target2d(auto_texture_size[0], auto_texture_size[1])
                    # TODO: setup camera transform and options
            else:
                return {"status": "error", "message":
                    "Observer {} has bScreenCapture set to true, but is not a child of either a Camera or a SceneCapture!".format(obs_name)}

            #OBSOLETE? TRY w/o min/max: observation_space_desc[name+":camera"] = {"type": "image_rgb", "mins": 0, "maxs": 255, "shape": (texture.SizeX, texture.SizeY, 3)}
            observation_space_desc[obs_name+":camera"] = {"type": "cam", "shape": (texture.SizeX, texture.SizeY, 3)}  # 1=int

        # go through non-capture properties that need to be observed by this Observer
        for observed_prop in observer.ObservedProperties:
            if not observed_prop.bEnabled:
                continue
            if not parent.has_property(observed_prop.PropName):
                continue

            #OBSOLETE? TRY w/o min/max: observation_space_desc[name+":"+observed_prop.PropName] = {"type": 0, "min": observed_prop.RangeMin, "max": observed_prop.RangeMax}

            #PUT THIS BACK->observation_space_desc[obs_name+":"+observed_prop.PropName] = {"type": observed_prop.DataType, "shape": (observed_prop.Count,)}  # TODO: store type and shape somewhere in C++ code
            #JUST A TEST
            observation_space_desc[obs_name+":"+observed_prop.PropName] = {"type": "bool"}  # for now -> just allow booleans
    ue.log("observation_space_desc: {}".format(observation_space_desc))

    return {"status": "ok", "action_space_desc": action_space_desc, "observation_space_desc": observation_space_desc}
    

def manage_message(message):
    print(message)

    if b"cmd" not in message:
        return {"status": "error", "message": "Field 'cmd' missing in message!"}
    cmd = message[b"cmd"]
    if cmd == b"step":
        return step(message)
    elif cmd == b"reset":
        return reset(message)
    elif cmd == b"get_spec":
        return get_spec()

    return {"status": "error", "message": "Unknown method ({}) to call!".format(cmd)}


# this is called whenever a new client connects
async def new_client_connected(reader, writer):
    name = writer.get_extra_info('peername')
    ue.log('new client connection from {0}'.format(name))
    #unpacker = msgpack.Unpacker(encoding="ascii")
    unpacker = msgpack.Unpacker()
    #y = 2000
    while True:
        # wait for a line
        # TODO: what if incoming command is longer than 8192? -> Add len field to beginning of messages (in both directions)
        data = await reader.read(8192)
        if not data:
            break
        unpacker.feed(data)
        for message in unpacker:
            response = msgpack.packb(manage_message(message))
            len_ = len(response)
            ue.log("Got message cmd={} -> sending response of len={}".format(message[b"cmd"], len_))
            writer.write(bytes("{:08d}".format(len_), encoding="ascii")+response)  # prepend 8-byte len field to all our messages

    ue.log('client {0} disconnected'.format(name))


# this spawns the server
# the try/finally trick allows for gentle shutdown of the server
async def spawn_server(host, port):
    try:
        coro = await asyncio.start_server(new_client_connected, host, port)
        ue.log('tcp server spawned on {0}:{1}'.format(host, port))
        await coro.wait_closed()
    finally:
        coro.close()
        ue.log('tcp server ended')

    
"""
Main Program: Get UE4 settings and start listening on port for incoming connections.
"""

settings = ue.get_mutable_default(DucanduSettings)
if settings.Address and settings.Port:
    asyncio.ensure_future(spawn_server(settings.Address, settings.Port))
else:
    ue.log("No settings for either address ({}) or port ({})!".format(settings.Address, settings.Port))


