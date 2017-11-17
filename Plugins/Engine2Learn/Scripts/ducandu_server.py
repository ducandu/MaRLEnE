"""
 -------------------------------------------------------------------------
 engine2learn - Plugins/Engine2Learn/Scripts/ducandu_server.py

 The server running inside UE4 (UnrealEnginePython) and listening on a
 port for incoming ML connections.
 Handles incoming commands from the ML environment such as stepping
 through the game, setting properties, resetting the game, etc..

 created: 2017/10/26 in PyCharm
 (c) 2017-2018 Roberto DeLoris (20tab) & Sven Mika (ducandu)
 -------------------------------------------------------------------------
"""

import unreal_engine as ue
import asyncio
import ue_asyncio
from unreal_engine.classes import DucanduSettings, GameplayStatics, E2LObserver, CameraComponent, SceneCaptureComponent2D, InputSettings
from unreal_engine.structs import Key
from unreal_engine.enums import EInputEvent
import msgpack
import re
from time import sleep
import pydevd


# TODO: global observation_dict (init only once, then write to it in place) to save on garbage collection runs
_OBS_DICT = {}

# cleanup previous tasks
for task in asyncio.Task.all_tasks():
    task.cancel()


# search for the currently running world
def get_playing_world():
    """
    UE4 world types:
    None=0, Game=1, Editor=2, PIE=3, EditorPreview=4, GamePreview=5, Inactive=6

    :return: Returns the currently playing UE4 world.Returns the currently playing UE4 world.
    Returns the first world within all worlds that is either a Game OR and PIE (play in editor) world.
    :rtype: UnrealEnginePython UWorld
    """
    playing_world = None
    for world in ue.all_worlds():
        if world.get_world_type() in (1, 3):  # game or pie
            playing_world = world
            break
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


def set_props(message):
    """
    Interface that allows us to set properties of different Actors/Components in the playing world.
    Arguments are passed in as a list (kwargs parameter: 'setters') of tuples:
    (/?actor:[component(s):]?prop-name, value, is_relative)
    - actor/component/prop string could be a pattern. The syntax corresponds to perl regular expressions if the
    string starts with a '/'
    - value: the new value for the property to be set to
    - is_relative: if True, the old value of the property will be incremented by the given value (negative values decrement the property value)

    :param dict message: The incoming message from the client.
    :return: A response dict to be sent back to the client.
    :rtype: dict
    """

    playing_world = get_playing_world()
    if not playing_world:
        return {"status": "error", "message": "No playing world!"}

    if b"setters" not in message:
        return {"status" : "error", "message": "Field 'setters' missing in 'set' command message!"}

    actors = {}  # dict of uobjects: key=name (w/o number extension), value: list of actors that share this key (name)
    for a in playing_world.all_actors():
        name = re.sub(r'_\d+$', "", a.get_name(), 1)  # remove trailing _[digits]
        if name not in actors:
            actors[name] = [a]
        else:
            actors[name].append(a)

    # DEBUG
    import pydevd
    import sys
    sys.path.append("c:/program files/pycharm 2017.2.2/debug-eggs/")  # always need to add this to the sys.path (location of PyCharm debug eggs)
    pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    # each set_cmd is a tuple
    for set_cmd in message[b"setters"]:
        if not isinstance(set_cmd, (list, tuple)) or len(set_cmd) < 2:
            return {"status": "error", "message": "Malformatted setter command {}. Needs to be ([actor:prop], [value][, is_relative]?).".format(set_cmd)}
        prop_spec, value, is_relative = set_cmd[0].decode(), set_cmd[1], False if len(set_cmd) < 3 else set_cmd[2]
        uobjects = None  # the final uobject (could be an actor or a component or a component of a component, etc..)
        while True:
            mo = re.match(r':?(\w+)((:\w+)*)', prop_spec)
            if not mo:
                return {"status" : "error",
                        "message": "Malformatted actor[:comp]?:property specifier ({}). "+
                                   "Needs to be [actor-pattern[:comp-pattern(s)]*:property-pattern].".format(prop_spec)}
            next_, prop_spec, _ = mo.groups()
            # next_ is a pattern for actor names
            if uobjects is None:
                uobjects = []
                # go through list of actors to collect the matching ones
                for a, l in actors.items():
                    if re.match(next_, a):
                        uobjects.extend(l)  # playing_world.find_object(next_)
            # next_ is a pattern for some sub-component of an Actor/other Component (still something left of the prop_spec)
            elif prop_spec:
                # go through list of uobjects to see whether they have components with the given name (next_)
                uobjects_next = []
                for uobj in uobjects:
                    comps = uobj.get_actor_components()
                    for comp in comps:
                        if re.match(next_, comp.get_name()):
                            uobjects_next.append(comp)  # playing_world.find_object(next_)
                # update our list of matching components
                uobjects = uobjects_next
            # next_ is the name of the property
            else:
                # go through all collected uobjects and change the property
                for uobj in uobjects:
                    print("trying to change uobj->{}".format(next_))
                    if uobj.has_property(next_):
                        if is_relative:
                            old_val = uobj.get_property(next_)
                            uobj.set_property(next_, old_val + value)
                        else:
                            uobj.set_property(next_, value)
                break

    return {"status": "ok", "obs_dict": compile_obs_dict()}


"""    processing_dict = {"_playing_world": {"uobj": [playing_world], "is_final": False}}
    only_final_entries = False
    is_first = True


    while not only_final_entries:
        # copy dict
        processing_dict_cpy = processing_dict.copy()
        only_final_entries = True
        for key, entry in processing_dict.items():
            if entry["is_final"]:
                continue
            entry["is_final"] = True
            print("Processing item: "+key)
            list_ = entry["uobj"]  # type: list
            no_comps = True
            # get all sub-comps of all actors under this name (usually just one) and add them to dict, then repeat
            # - the very first time this is run, uobj is the playing world (get actors, not comps)
            for uobj in list_:
                print("\tuobj: {}".format(uobj))
                comps = uobj.all_actors() if is_first else uobj.get_actor_components()
                if len(comps) > 0:
                    no_comps = False
                for comp in comps:
                    print("\t\tsub-comp: {}".format(comp.get_name()))
                    comp_name = ("" if is_first else key+":")+re.sub(r'_\d+$', "", comp.get_name(), 1)  # remove trailing _[digits]
                    if comp_name not in processing_dict_cpy:
                        processing_dict_cpy[comp_name] = {"uobj": [comp], "is_final": False}
                    else:
                        processing_dict_cpy[comp_name]["uobj"].append(comp)
            if no_comps is False:
                only_final_entries = False

        is_first = False

        processing_dict = processing_dict_cpy
        processing_dict.pop("_playing_world", None)  # remove playing world (seed item) after first round

        print("Now keys in dict before next round: {}".format(processing_dict.keys()))

        if only_final_entries:
            print("No next round")
            break
"""
"""
    # temporary solution: collect all actors+[components]* in a list, then go through the list regex'ing for the incoming expression
    # - collect matching actors/components in new list and set properties of these actors to the given value
    processing_list = playing_world.all_actors()
    #final_list = processing_list[:]
    ongoing = True
    while ongoing:
        for uobj in processing_list:
            comps = uobj.get_actor_components()
            #if len(comps) == 0:
            #    ongoing = False
            # add the components to this actor and add the new combination to the final_list


    if b"setters" in message:
        # each set_cmd is a tuple
        for set_cmd in message[b"setters"]:
            prop_spec = set_cmd[0].decode()
            uobject = None  # the final uobject (could be an actor or a component or a component of a component, etc..)
            prop_name = None  # the final property to set to a new value
            while True:
                mo = re.match(r'(\w+):(\w+)(:\w+)*', prop_spec)
                assert mo
                next_ = mo.group(1)
                # next_ is an Actor within the world
                if uobject is None:
                    # TODO: handle names+underscore+number
                    uobject = playing_world.find_object(next_)
                # next_ is a Component of an Actor/other Component
                else:
                    # TODO: handle names+underscore+number
                    uobject = uobject.get_actor_component(next_)

    def print_props(uobject, num_tabs):
        for prop in uobject.properties():
            print(("\t" * num_tabs)+"->"+prop)

    # DEBUG: print out all actors' names for fun
    actors = playing_world.all_actors()
    print("All actor's names")
    for uobj in actors:
        print("\t"+uobj.get_name())
        print_props(uobj, 2)
        comps = uobj.get_actor_components()
        for c in comps:
            print("\t\t:"+c.get_name())
            print_props(c, 3)
"""


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
                    return {"status": "error", "message": "SceneCapture2DComponent (parent of Observer {}) does not have a TextureTarget " +
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
    """
    Handles all incoming message by forwarding the message to one of our command-handling functions (e.g. reset, step, etc..)

    :param dict message: The incoming message dict.
    :return: A response dict to be sent back to the client.
    :rtype: dict
    """
    print(message)

    if b"cmd" not in message:
        return {"status": "error", "message": "Field 'cmd' missing in message!"}
    cmd = message[b"cmd"]
    if cmd == b"step":
        return step(message)
    elif cmd == b"reset":
        return reset(message)
    elif cmd == b"set":
        return set_props(message)
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


