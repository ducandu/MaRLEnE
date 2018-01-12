"""
TensorForce client for executing parallelized RL-jobs in the cloud
using an ecosystem (e.g. Spark) and a cloud computing provider (e.g. AWS)
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import warnings
import awscli as aws
import sys
import os
import shutil


parser = argparse.ArgumentParser(prog="tensorforce", usage="%(prog)s [command] [options]?")

parser.add_argument('command', nargs=1, help="The client command to execute.")

args, remaining_args = parser.parse_known_args()

# logging.basicConfig(filename="logfile.txt", level=logging.INFO)
#logging.basicConfig(stream=sys.stderr)
#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

if args.command == "help":
    parser.print_help()
# create a new project (in the current folder)
elif args.command == "init":
    parser.add_argument('-n', '--name', required=True, help="The name of the project.")
    args = parser.parse_args(remaining_args)

    # error if no name

    # check if there is already a .tensorforce file in this folder
    if os.path.isdir(".tensorforce"):
        warnings.warn("WARNING: this directory already contains a tensorforce project. Would you like to overwrite it?",
                      category=UserWarning)
        response = input(">")
        if response.upper() != "Y":
            quit()

        # erase the existing project and create a new one
        shutil.rmtree(".tensorforce")

    # create a new .tensorforce dir
    os.mkdir(".tensorforce")
# create a new experiment
elif args.command == "experiment":


