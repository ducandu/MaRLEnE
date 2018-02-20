# run this script in the python editor of the UE4 editor after selecting an asset in the asset browser
# in order to see that path for this class (useful for loading a class via ue.load_class).

import unreal_engine as ue

ue.log(ue.get_selected_assets()[0].get_path_name())
