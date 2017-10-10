import unreal_engine as ue
from unreal_engine.classes import DucanduSettings

settings = ue.get_mutable_default(DucanduSettings)
for prop in settings.properties():
    print('{0}={1}'.format(prop, settings.get_property(prop)))
