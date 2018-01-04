"""
 -------------------------------------------------------------------------
 engine2learn - server_utils.py
 
 Utility functions for the server-side environment script.
  
 created: 2017/12/17 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import unreal_engine as ue
from unreal_engine.classes import E2LObserver, GameplayStatics, CameraComponent, InputSettings, SceneCaptureComponent2D
import numpy as np
import re


# TODO: global observation_dict (init only once, then write to it in place) to save on garbage collection runs
_OBS_DICT = {}


# search for the currently running world
def get_playing_world():
    """
    UE4 world types:
    None=0, Game=1, Editor=2, PIE=3, EditorPreview=4, GamePreview=5, Inactive=6

    :return: Returns the currently playing UE4 world.Returns the currently playing UE4 world.
    Returns the first world within all worlds that is either a Game OR and PIE (play in editor) world.
    :rtype: UnrealEnginePython UWorld
    """
    # DEBUG
    #pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

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


async def pause_game():
    """
    Pauses the game.
    """
    playing_world = get_playing_world()
    if not playing_world:
        return {"status": "error", "message": "No playing world!"}

    # check whether game is already paused
    is_paused = GameplayStatics.IsGamePaused(playing_world)
    ue.log("pausing the game (is paused={})".format(is_paused))
    #if is_paused:
    #    GameplayStatics.SetGamePaused(playing_world, False)
    #    #playing_world.world_tick(1/600.0, True)  # mini tick?
    if not is_paused:
        success = GameplayStatics.SetGamePaused(playing_world, True)
        if not success:
            ue.log("->WARNING: Game could not be paused!")


def sanity_check_observer(observer, playing_world):
    obs_name = observer.get_name()
    # the observer could be destroyed
    if not observer.is_valid():
        # ue.log("Observer {} not valid".format(obs_name))
        return None, None
    if not observer.has_world():
        # ue.log("Observer {} has no world".format(obs_name))
        return None, None
    # observer lives in another world
    if playing_world is not None and observer.get_world() != playing_world:
        # ue.log("Observer {} lives in non-live world ({}) (playing-world={})".format(obs_name, observer.get_world(), playing_world))
        return None, None
    # get the observer's parent and name
    return observer.GetAttachParent(), obs_name


def get_scene_capture_and_texture(parent, obs_name, width=84, height=84):
    """
    Adds a SceneCapture2DComponent to some parent camera object so we can capture the pixels for this camera view.
    Then captures the image, renders it on the render target of the scene capture and returns the image as a numpy
    array.

    :param uobject parent: The parent camera/scene-capture actor/component to which the new SceneCapture2DComponent
        needs to be attached or for which the render target has to be created and/or returned.
    :param str obs_name: The name of the observer component.
    :param int width: The width (in px) to use for the render target.
    :param int height: The height (in px) to use for the render target.
    :return: numpy array containing the pixel values (0-255) of the captured image.
    :rtype: np.ndarray
    """

    texture = None  # the texture object to use for getting the image

    if parent.is_a(SceneCaptureComponent2D):
        scene_capture = parent
        texture = parent.TextureTarget
    elif parent.is_a(CameraComponent):
        scene_capture = get_child_component(parent, SceneCaptureComponent2D)
        if scene_capture:
            texture = scene_capture.TextureTarget
        else:
            scene_capture = parent.get_owner().add_actor_component(SceneCaptureComponent2D, "Engine2LearnScreenCapture", parent)
            scene_capture.bCaptureEveryFrame = False
            scene_capture.bCaptureOnMovement = False
    # error -> return nothing
    else:
        raise RuntimeError("Observer {} has bScreenCapture set to true, but is not a child of either a Camera or a SceneCapture2D!".format(obs_name))

    if not texture:
        # TODO: setup camera transform and options (greyscale, etc..)
        texture = scene_capture.TextureTarget = ue.create_transient_texture_render_target2d(width, height)
        ue.log("DEBUG: scene capture is created in get_scene_image texture={}".format(scene_capture.TextureTarget))

    return scene_capture, texture


def get_scene_capture_image(scene_capture, texture):
    """
    Takes a snapshot through a SceneCapture2DComponent and its Texture target and returns the image as a numpy array.

    :param uobject scene_capture: The SceneCapture2DComponent uobject.
    :param uobject texture: The TextureTarget uobject.
    :return: numpy array containing the pixel values (0-255) of the captured image
    :rtype: np.ndarray
    """
    # TODO: find out why image is not real-color (doesn't seem to be RGB encoded)
    # trigger the scene capture
    scene_capture.CaptureScene()
    # TODO: copy the bytes into the same memory location each time to avoid garbage collection
    byte_string = bytes(texture.render_target_get_data())  # use render_target_get_data_to_buffer(data,[mipmap]?) instead
    np_array = np.frombuffer(byte_string, dtype=np.uint8)  # convert to pixel values (0-255 uint8)
    img = np_array.reshape((texture.SizeX, texture.SizeY, 4))[:, :, :3]  # slice away alpha value

    return img


def compile_obs_dict(reward=None):
    """
    Compiles the current observations (based on all active E2LObservers) into a dictionary that is returned to the
    UE4Env object's reset/step/... methods.

    :param Union[float,None] reward: The absolute global accumulated reward value to set (mostly used to reset
    everything to 0 after a new episode is started).
    :returns: The obs_dict as a python dict (ready to be sent back to the client).
    :rtype: dict
    """
    global _REWARD

    playing_world = get_playing_world()
    r = 0.0
    is_terminal = False
    if reward is not None:
        _REWARD = reward

    # DEBUG
    #pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    for observer in E2LObserver.GetRegisteredObservers():
        parent, obs_name = sanity_check_observer(observer, playing_world)
        if not parent:
            continue
        # the reward observer
        elif obs_name == "_reward":
            if len(observer.ObservedProperties) != 1:
                return {"status": "error", "message": "Reward-observer {} has 0 or more than 1 property!".format(obs_name)}
            observed_prop = observer.ObservedProperties[0]
            prop_name = observed_prop.PropName
            if not parent.has_property(prop_name):
                return {"status": "error", "message": "Reward-property {} is not a property of parent ({})!".format(prop_name, parent)}
            r = parent.get_property(prop_name)[0]  # FOR NOW: use x-Location as reward (bad, but we need 20tab to add this functionality)
        # the is_terminal observer
        elif obs_name == "_is_terminal":
            if len(observer.ObservedProperties) != 1:
                return {"status": "error", "message": "IsTerminal-observer {} has 0 or more than 1 property!".format(obs_name)}
            observed_prop = observer.ObservedProperties[0]
            prop_name = observed_prop.PropName
            if not parent.has_property(prop_name):
                return {"status": "error", "message": "IsTerminal-property {} is not a property of parent ({})!".format(prop_name, parent)}
            is_terminal = (parent.get_property(prop_name)[0] > 0.0)  # FOR NOW: use Rotation: x > 0 as is_terminal signal
        # normal (non-reward/non-is_terminal) observer
        else:
            # this observer returns a camera image
            if observer.bScreenCapture:
                try:
                    scene_capture, texture = get_scene_capture_and_texture(parent, obs_name)
                except RuntimeError as e:
                    return {"status": "error", "message": "{}".format(e)}
                img = get_scene_capture_image(scene_capture, texture)
                _OBS_DICT[obs_name + "/camera"] = img

            for observed_prop in observer.ObservedProperties:
                if not observed_prop.bEnabled:
                    continue
                prop_name = observed_prop.PropName
                if not parent.has_property(prop_name):
                    continue

                prop = parent.get_property(prop_name)
                type_ = type(prop)
                if type_ == ue.FVector or type_ == ue.FRotator:
                    value = (prop[0], prop[1], prop[2])
                elif type_ == ue.UObject:
                    value = str(prop)
                elif type_ == bool or type_ == int or type_ == float:
                    value = prop
                else:
                    return {"status": "error", "message": "Observed property {} has an unsupported type ({})".format(prop_name, type_)}

                _OBS_DICT[obs_name+"/"+prop_name] = value

    # update global total reward counter
    prev_reward = _REWARD
    _REWARD = r
    message = {"status": "ok", "obs_dict": _OBS_DICT, "_reward": (r - prev_reward), "_is_terminal": is_terminal}
    return message


def get_spec():
    """
    Returns the observation_space (observers) and action_space (action- and axis-mappings) of the Game as a dict with
    keys: `observation_space` and `action_space`
    """
    playing_world = get_playing_world()

    # build the action_space descriptor
    action_space_desc = {}
    input_ = ue.get_mutable_default(InputSettings)
    # go through all action mappings
    # TODO: FOR NOW: ignore all non-keyboard mappings for simplicity.
    # TODO: Later, we will have to create a tick box to specify which actions should be sent to ML
    for action in input_.ActionMappings:
        if re.search(r'Gamepad|Mouse|Thumbstick', action.Key.KeyName):
            continue
        if action.ActionName not in action_space_desc:
            action_space_desc[action.ActionName] = {"type": "action", "keys": [action.Key.KeyName]}
        else:
            action_space_desc[action.ActionName]["keys"].append(action.Key.KeyName)
    for axis in input_.AxisMappings:
        if re.search(r'Gamepad|Mouse|Thumbstick', axis.Key.KeyName):
            continue
        if axis.AxisName not in action_space_desc:
            action_space_desc[axis.AxisName] = {"type": "axis", "keys": [(axis.Key.KeyName, axis.Scale)]}
        else:
            action_space_desc[axis.AxisName]["keys"].append((axis.Key.KeyName, axis.Scale))
    ue.log("action_space_desc: {}".format(action_space_desc))

    # DEBUG
    #pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    # build the observation_space descriptor
    observation_space_desc = {}
    for observer in E2LObserver.GetRegisteredObservers():
        parent, obs_name = sanity_check_observer(observer, playing_world)
        # ignore reward observer and is-terminal observer
        if not parent or obs_name == "_reward" or obs_name == "_is_terminal":
            continue

        # ue.log("DEBUG: get_spec observer {}".format(obs_name))

        # this observer returns a camera image
        if observer.bScreenCapture:
            try:
                _, texture = get_scene_capture_and_texture(parent, obs_name)
            except RuntimeError as e:
                return {"status": "error", "message": "{}".format(e)}
            observation_space_desc[obs_name+"/camera"] = {"type": "IntBox", "shape": (texture.SizeX, texture.SizeY, 3),
                                                          "min": 0, "max": 255}

        # go through non-camera/capture properties that need to be observed by this Observer
        for observed_prop in observer.ObservedProperties:
            if not observed_prop.bEnabled:
                continue
            prop_name = observed_prop.PropName
            if not parent.has_property(prop_name):
                continue

            type_ = type(parent.get_property(prop_name))
            if type_ == ue.FVector or type_ == ue.FRotator:
                desc = {"type": "Continuous", "shape": (3,)}  # no min/max -> will be derived from samples
            elif type_ == ue.UObject:
                desc = {"type": "str"}
            elif type_ == bool:
                desc = {"type": "Bool"}
            elif type_ == float:
                desc = {"type": "Continuous", "shape": (1,)}
            elif type_ == int:
                desc = {"type": "IntBox", "shape": (1,)}
            else:
                return {"status": "error", "message": "Observed property {} has an unsupported type ({})".
                    format(prop_name, type_)}

            observation_space_desc[obs_name+"/"+prop_name] = desc

    # ue.log("observation_space_desc: {}".format(observation_space_desc))

    return {"status": "ok", "game_name": get_project_name(), "action_space_desc": action_space_desc,
            "observation_space_desc": observation_space_desc}


# returns the UE project's name
def get_project_name():
    return ue.get_mutable_default(GeneralProjectSettings).ProjectName

