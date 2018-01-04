import unreal_engine as ue
from unreal_engine.classes import DumbActor_C
from unreal_engine.classes import GameplayStatics
from unreal_engine import FVector
from .server_utils import get_playing_world


world = get_playing_world()
if not world:
    raise Exception("no playing world found")

dumb_actor = None
for actor in world.all_actors():
    if actor.is_a(DumbActor_C):
        dumb_actor = actor
        break

if not dumb_actor:
    raise Exception('no DumbActor found')

print(dumb_actor)


for i in range(4):
    GameplayStatics.SetGamePaused(world, False)
    # the second argument, when set to True, increases the frame counter value
    world.world_tick(1.0, True)
    GameplayStatics.SetGamePaused(world, True)
    print(dumb_actor.get_actor_location())

# just for safety
GameplayStatics.SetGamePaused(world, True)

