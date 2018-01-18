"""
 -------------------------------------------------------------------------
 MaRLEnE - Machine- and Reinforcement Learning ExtensioN for (game) Engines
 Plugins/MaRLEnE/Scripts/marlene_server.py

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
import server_utils as util
from unreal_engine.classes import MaRLEnESettings, GameplayStatics, InputSettings, GeneralProjectSettings
from unreal_engine.structs import Key
from unreal_engine.enums import EInputEvent

import msgpack
import msgpack_numpy as mnp

import re
#import pydevd
import sys


# make msgpack use the numpy-specific de/encoders
mnp.patch()

sys.path.append("c:/program files/pycharm 2017.2.2/debug-eggs/")  # always need to add this to the sys.path (location of PyCharm debug eggs)

# cleanup previous tasks
for task in asyncio.Task.all_tasks():
    task.cancel()


def seed(message):
    """
    Sets the random seed of the Game to some int value.
    """
    if "value" not in message:
        return {"status": "error", "message": "Field 'value' missing in 'seed' command message!"}
    elif not isinstance(message["value"], (int, float)):
        return {"status": "error", "message": "Field 'value' ({}) in 'seed' command is not of type int!".format(message["value"])}

    # set the random seed through the UnrealEnginePython interface
    value = int(message["value"])
    ue.set_random_seed(value)

    return {"status": "ok", "new_seed": value}


def reset(writer):
    """
    Resets the Game to its default start position and returns the resulting obs_dict.
    """
    playing_world = util.get_playing_world()
    if not playing_world:
        return {"status": "error", "message": "No playing world!"}

    # DEBUG
    #pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    ue.log("Resetting level.")
    # reset level
    playing_world.restart_level()

    # enqueue pausing the game for upcoming tick
    asyncio.ensure_future(util.pause_game())
    asyncio.ensure_future(get_and_send_obs_dict_async(writer, reward=0.0))

    return None


async def get_and_send_obs_dict_async(writer, reward=0.0):
    """
    Calls compile_obs_dict asynchronously and sends the message back via writer
    """
    message = util.compile_obs_dict(reward=reward)
    send_message(message, writer)
    return None


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

    playing_world = util.get_playing_world()
    if not playing_world:
        return {"status": "error", "message": "No playing world!"}

    if "setters" not in message:
        return {"status": "error", "message": "Field 'setters' missing in 'set' command message!"}

    actors = {}  # dict of uobjects: key=name (w/o number extension), value: list of actors that share this key (name)
    for a in playing_world.all_actors():
        name = re.sub(r'_\d+$', "", a.get_name(), 1)  # remove trailing _[digits]
        if name not in actors:
            actors[name] = [a]
        else:
            actors[name].append(a)

    # DEBUG
    #pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    # each set_cmd is a tuple
    for set_cmd in message["setters"]:
        if not isinstance(set_cmd, (list, tuple)) or len(set_cmd) < 2:
            return {"status": "error", "message": "Malformatted setter command {}. Needs to be ([actor:prop], [value][, is_relative]?).".format(set_cmd)}
        prop_spec, value, is_relative = set_cmd[0], set_cmd[1], False if len(set_cmd) < 3 else set_cmd[2]
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

    return util.compile_obs_dict()


def step(message):
    """
    Performs a single step in the game (could be several ticks) given some action/axis mappings.
    The number of ticks to perform can be specified through `num_ticks` (default=4).
    The fake amount of time (dt) that each tick will use can be specified through `delta_time` (default=1/60s).
    """
    playing_world = util.get_playing_world()
    if not playing_world:
        return {"status": "error", "message": "No playing world!"}

    delta_time = message.get("delta_time", 1.0/60.0)  # the force-set delta time (dt) for each tick
    num_ticks = message.get("num_ticks", 4)  # the number of ticks to work through (all with the given action/axis mappings valid)
    controller = playing_world.get_player_controller()

    ue.log("step command: delta_time={} num_ticks={}".format(delta_time, num_ticks))

    # DEBUG
    #pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    if "axes" in message:
        for axis in message["axes"]:
            # ue.log("-> axis {}={} (key={})".format(key_name, axis[1], Key(KeyName=key_name)))
            controller.input_axis(Key(KeyName=axis[0]), axis[1], delta_time)
    if "actions" in message:
        for action in message["actions"]:
            # ue.log("-> action {}={}".format(action_name, action[1]))
            controller.input_key(Key(KeyName=action[0]), EInputEvent.IE_Pressed if action[1] else EInputEvent.IE_Released)

    # unpause the game and then perform n ticks with the given inputs (actions and axes)
    for _ in range(num_ticks):
        was_unpaused = GameplayStatics.SetGamePaused(playing_world, False)
        if not was_unpaused:
            ue.log("WARNING: un-pausing game for next step was not successful!")

        # TODO: how do we collect rewards over the single ticks if we don't query the observers after each (have to always accumulate and compare to previous value)?
        playing_world.world_tick(delta_time, True)

        # after the first tick, reset all action mappings to False again (otherwise sending True in two succinct steps would not(!) repeat the action)
        if "actions" in message:
            for action in message["actions"]:
                controller.input_key(Key(KeyName=action[0]), EInputEvent.IE_Released)

        # pause again
        was_paused = GameplayStatics.SetGamePaused(playing_world, True)
        if not was_paused:
            ue.log("->WARNING: re-pausing game after step was not successful!")

    return util.compile_obs_dict()


def manage_message(message, writer):
    """
    Handles all incoming message by forwarding the message to one of our command-handling functions (e.g. reset, step, etc..)

    :param dict message: The incoming message dict.
    :param writer: The writer object to send async messages back to once done.
    :return: A response dict to be sent back to the client.
    :rtype: dict
    """
    print(message)

    if "cmd" not in message:
        return {"status": "error", "message": "Field 'cmd' missing in message!"}
    cmd = message["cmd"]
    if cmd == "step":
        return step(message)
    elif cmd == "reset":
        return reset(writer)
    elif cmd == "seed":
        return seed(message)
    elif cmd == "set":
        return set_props(message)
    elif cmd == "get_spec":
        return util.get_spec()

    return {"status": "error", "message": "Unknown method ({}) to call!".format(cmd)}


def send_message(message, writer):
    message = msgpack.packb(message)
    len_ = len(message)
    # ue.log("Got message cmd={} -> sending response of len={}".format(message["cmd"], len_))
    writer.write(bytes("{:08d}".format(len_), encoding="ascii") + message)  # prepend 8-byte len field to all our messages


# this is called whenever a new client connects
async def new_client_connected(reader, writer):
    name = writer.get_extra_info("peername")
    ue.log("new client connection from {0}".format(name))
    unpacker = msgpack.Unpacker()
    while True:
        # wait for a line
        # TODO: what if incoming command is longer than 8192? -> Add len field to beginning of messages (in both directions)
        data = await reader.read(8192)
        if not data:
            break
        unpacker.feed(data)
        for message in unpacker:
            response = manage_message(message, writer)
            # write back immediately
            if response:
                send_message(response, writer)
            # async calls -> do nothing here (async will handle it)

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

settings = ue.get_mutable_default(MaRLEnESettings)
if settings.Address and settings.Port:
    asyncio.ensure_future(spawn_server(settings.Address, settings.Port))
else:
    ue.log("No settings for either address ({}) or port ({})!".format(settings.Address, settings.Port))


