#!/bin/bash

# run this script to set PYTHONPATH of the python interpreter in your virtual environment

# Get the helper script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# cd from the 'helper_scripts' dir one level up to get the project root
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Construct PYTHONPATH dynamically based on the project root
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src:$PROJECT_ROOT/src/utils:$PROJECT_ROOT/src/utils/cli:$PROJECT_ROOT/test:$PROJECT_ROOT/test/utils:$PROJECT_ROOT/test/utils/cli:/tmp/ibapi-9.81.1.post1/src"

echo "PYTHONPATH set to: $PYTHONPATH"