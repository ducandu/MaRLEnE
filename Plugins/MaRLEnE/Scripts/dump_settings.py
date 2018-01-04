import unreal_engine as ue
from unreal_engine.classes import GeneralProjectSettings

def get_project_name():
    return ue.get_mutable_default(GeneralProjectSettings).ProjectName

for prop in ue.get_mutable_default(GeneralProjectSettings).properties():
    print('{0} = {1}'.format(prop, ue.get_mutable_default(GeneralProjectSettings).get_property(prop)))