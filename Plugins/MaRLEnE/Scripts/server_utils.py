"""
 -------------------------------------------------------------------------
 MaRLEnE - server_utils.py
 
 Utility functions for the server-side environment script.
  
 created: 2017/12/17 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

import unreal_engine as ue
from unreal_engine.classes import MLObserver, GameplayStatics, GeneralProjectSettings, CameraComponent, InputSettings, SceneCaptureComponent2D
import unreal_engine.classes
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
    # DEBUG: I want to know whether the world changes after reset, etc...
    #ue.log("DEBUG: playing world: {}".format(playing_world))
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
    return observer.get_owner(), obs_name  # observer.GetAttachParent(), obs_name


def get_scene_capture_and_texture(owner, observer):
    """
    Adds a SceneCapture2DComponent to some parent camera object so we can capture the pixels for this camera view.
    Then captures the image, renders it on the render target of the scene capture and returns the image as a numpy
    array.

    :param uobject owner: The owner camera/scene-capture actor to which the new SceneCapture2DComponent
        needs to be attached or for which the render target has to be created and/or returned.
    :param uobject observer: The MLObserver uobject.
    :return: numpy array containing the pixel values (0-255) of the captured image.
    :rtype: np.ndarray
    """

    texture = None  # the texture object to use for getting the image

    # look for first SceneCapture2DComponent
    scene_captures = owner.get_actor_components_by_type(SceneCaptureComponent2D)
    if len(scene_captures) > 0:
        scene_capture = scene_captures[0]
        texture = scene_capture.TextureTarget
        #ue.log("DEBUG: get_scene_capture_and_texture -> found a scene_capture; texture={}".format(texture))
    # then CameraComponent
    else:
        cameras = owner.get_actor_components_by_type(CameraComponent)
        if len(cameras) > 0:
            camera = cameras[0]
            scene_capture = get_child_component(camera, SceneCaptureComponent2D)
            if scene_capture:
                texture = scene_capture.TextureTarget
                #ue.log("DEBUG: get_scene_capture_and_texture -> found a camera with scene_capture comp; texture={}".format(texture))
            else:
                scene_capture = owner.add_actor_component(SceneCaptureComponent2D, "MaRLEnE_SceneCapture", camera)
                scene_capture.bCaptureEveryFrame = False
                scene_capture.bCaptureOnMovement = False
                #ue.log("DEBUG: get_scene_capture_and_texture -> found a camera w/o scene_capture comp -> added it; texture={}".format(
                #    texture))
        # error -> return nothing
        else:
            raise RuntimeError("Observer {} has bScreenCapture set to true, but its owner does not possess either a "
                               "Camera or a SceneCapture2D!".format(observer.get_name()))

    if not texture:
        # use MLObserver's width/height settings
        texture = scene_capture.TextureTarget =\
            ue.create_transient_texture_render_target2d(observer.Width or 84, observer.Height or 84)
        #ue.log("DEBUG: scene capture is created in get_scene_image texture={} will return texture {}".format(scene_capture.TextureTarget, texture))

    return scene_capture, texture


def get_scene_capture_image(playing_world, scene_capture, texture, gray_scale=False):
    """
    Takes a snapshot through a SceneCapture2DComponent and its Texture target and returns the image as a numpy array.

    Args:
        playing_world (uworld): The UWorld object of the running Game.
        scene_capture (uobject): The SceneCapture2DComponent uobject.
        texture (uobjects): The TextureTarget uobject.
        gray_scale (bool): Whether to transform the image into gray-scale before returning.

    Returns: Numpy array containing the pixel values (0-255) of the captured image.
    """
    #ue.log("DEBUG: In get_scene_capture_image(scene_capture={} texture={} gray_scale={})".
    #       format(scene_capture, texture, gray_scale))

    # TODO: find out why image is not real-color (doesn't seem to be RGB encoded)
    # trigger the scene capture (enable rendering only for this moment)
    viewport = playing_world.get_game_viewport()
    viewport.game_viewport_client_set_rendering_flag(True)
    scene_capture.CaptureScene()
    # TODO: copy the bytes into the same memory location each time to avoid garbage collection
    byte_string = bytes(texture.render_target_get_data())  # use render_target_get_data_to_buffer(data,[mipmap]?) instead
    viewport.game_viewport_client_set_rendering_flag(False)
    # convert to pixel values (0-255 uint8)
    np_array = np.frombuffer(byte_string, dtype=np.uint8)

    # DEBUG
    #pydevd.settrace("192.168.2.107", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    # do a simple dot product to get the gray-scaled image
    if gray_scale:
        img = np.dot(np_array.reshape((texture.SizeX * texture.SizeY, 4))[:, :3],
                     np.matrix([0.299, 0.587, 0.114]).T).astype(np.uint8)  # needs to be cast back to uint8!
        img = img.reshape((texture.SizeX, texture.SizeY))
    # no gray-scale: only slice away alpha value
    else:
        img = np_array.reshape((texture.SizeX, texture.SizeY, 4))[:, :, :3]

    return img


def compile_obs_dict(reward=None):
    """
    Compiles the current observations (based on all active MLObservers) into a dictionary that is returned to the
    UE4Env object's reset/step/... methods.

    Args:
        reward (Union[float,None]): The absolute global accumulated reward value to set (mostly used to reset
            everything to 0 after a new episode is started).

    Returns: The obs_dict as a python dict (ready to be sent back to the client).
    """
    global _REWARD

    playing_world = get_playing_world()
    r = 0.0  # accumulated reward
    is_terminal = False
    if reward is not None:
        _REWARD = reward

    # DEBUG
    #pydevd.settrace("localhost", port=20023, stdoutToServer=True, stderrToServer=True)  # DEBUG
    # END: DEBUG

    for observer in MLObserver.GetRegisteredObservers():
        owner, obs_name = sanity_check_observer(observer, playing_world)
        if not owner:
            continue
        # the reward observer
        elif observer.ObserverType == 1:
            if len(observer.ObservedProperties) != 1:
                return {"status": "error", "message": "Reward-observer {} has 0 or more than 1 property!".format(obs_name)}
            observed_prop = observer.ObservedProperties[0]
            prop_name = observed_prop.PropName
            if not owner.has_property(prop_name):
                return {"status": "error", "message": "Reward-property {} is not a property of owner ({})!".format(prop_name, owner)}
            r = owner.get_property(prop_name)
        # the is_terminal observer
        elif observer.ObserverType == 2:
            if len(observer.ObservedProperties) != 1:
                return {"status": "error", "message": "IsTerminal-observer {} has 0 or more than 1 property!".format(obs_name)}
            observed_prop = observer.ObservedProperties[0]
            prop_name = observed_prop.PropName
            if not owner.has_property(prop_name):
                return {"status": "error", "message": "IsTerminal-property {} is not a property of owner ({})!".format(prop_name, owner)}
            is_terminal = owner.get_property(prop_name)
        # normal (non-reward/non-is_terminal) observer
        else:
            # this observer returns a camera image
            if observer.bScreenCapture:
                try:
                    scene_capture, texture = get_scene_capture_and_texture(owner, observer)
                except RuntimeError as e:
                    return {"status": "error", "message": "{}".format(e)}
                img = get_scene_capture_image(playing_world, scene_capture, texture, observer.bGrayscale)
                _OBS_DICT[obs_name + "/camera"] = img

            for observed_prop in observer.ObservedProperties:
                if not observed_prop.bEnabled:
                    continue
                prop_name = observed_prop.PropName
                if not owner.has_property(prop_name):
                    continue

                prop = owner.get_property(prop_name)
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
    _REWARD = r  # update global _REWARD counter
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
    for observer in MLObserver.GetRegisteredObservers():
        owner, obs_name = sanity_check_observer(observer, playing_world)
        #ue.log("obs={} name={} owner={} enabled={} gray={} type={}".
        #       format(observer, obs_name, owner, observer.bEnabled, observer.bGrayscale, observer.ObserverType))
        # ignore reward observer (ObserverType=1) and is-terminal observer (ObserverType=2)
        if not owner or observer.ObserverType > 0:
            continue

        # ue.log("DEBUG: get_spec observer {}".format(obs_name))

        # this observer returns a camera image
        if observer.bScreenCapture:
            try:
                _, texture = get_scene_capture_and_texture(owner, observer)
            except RuntimeError as e:
                return {"status": "error", "message": "{}".format(e)}
            observation_space_desc[obs_name+"/camera"] = {
                "type": "IntBox",
                "shape": (texture.SizeX, texture.SizeY) if observer.bGrayscale else (texture.SizeX, texture.SizeY, 3),
                "min": 0, "max": 255}

        # go through non-camera/capture properties that need to be observed by this Observer
        for observed_prop in observer.ObservedProperties:
            if not observed_prop.bEnabled:
                continue
            prop_name = observed_prop.PropName
            if not owner.has_property(prop_name):
                continue

            type_ = type(owner.get_property(prop_name))
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

    ue.log("observation_space_desc: {}".format(observation_space_desc))

    return {"status": "ok", "game_name": get_project_name(), "action_space_desc": action_space_desc,
            "observation_space_desc": observation_space_desc}


# returns the UE project's name
def get_project_name():
    return ue.get_mutable_default(GeneralProjectSettings).ProjectName


def print_delta_time(dt):
    ue.log_warning("dt={}".format(dt))
    return True

