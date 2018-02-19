# Basic python file that gets executed when the UE4 Game starts
# - place imports here to start our modules

import unreal_engine as ue

# load the GeneralProjjectSettings class
# (could be that classes are not loaded yet when ue_site (this script) is executed)
ue.load_class("/Script/EngineSettings.GeneralProjectSettings")

import marlene_server
