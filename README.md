# Market Scout v1.0.0
### A command-line tool for retrieving and representing market data

# Introduction 

This application, MARKET SCOUT, is designed to retrieve real-time and historical market data from a supported brokerage service API. The results are saved in the equity_name.csv file.

# Installation and Setup for Running Market Scout Locally
Here are the steps to run Market Scout from the command-line in your local environment. 
    
## Extraction: 
Clone the repo or download and extract all files to a location on your filesystem.
## CD to your project root and create a virtual environment: 
    # this command will create a Python 3.9 venv in your project root, which makes the project more self-contained
    # conda is used in this example but any package manager will work
    $ cd ../path/to/market_scout
    $ conda create --prefix ./envs python=3.9
## Activate your virtual environment
    # from the project root
    $ conda activate ./envs
## Install dependencies:
    # from project root, pip install dependencies defined in requirements.txt
    $ pip install -r requirements.txt
## Modify PYTHONPATH for the interpreter in your virtual environment (**This step is crucial. Without it, the program will raise an import error as it won't be able to find necessary modules**):
    # from project root, source the export_python_path helper script 
    # this tells the interpreter where to find custom modules so it can properly import them:
    $ source ./market_scout/helper_scripts/export_python_path.sh
## Run the tests
    # change to the test directory and run pytest. It will "discover" tests and run them
    $ cd test/
    $ pytest -vv

# Usage

## Print a description of the application and/or the help message
Here are two options for printing the help message for Market Scout

### First, customize Scout run command
    # If you have permission, symlink scout to /usr/local/bin/scout
    $ sudo ln -s /path/to/market_scout/src/scout

### Print application description
    # be sure your virtual environment is activated
    # change to project root and run scout
    $ cd /path/to/market_scout/
    $ scout

![the application description should be here](./img/app_description.png)

### Print help message
    # be sure your virtual environment is activated
    # change to project root and run the helper script
    $ cd/market_scout/
    $ scout --help

![scout help message should be here](./img/scout_help_msg.png)

## Run the Market Scout
Here is how to run scout

### Option 1: Run Market Scout
    # be sure your virtual environment is activated
    # change to project root and run pipeline.py
    $ cd /path/to/market_scout/
    $ scout <command> --option value

### Option 2: Run Gene Annotator using helper script
    # be sure your virtual environment is activated
    # change to project root and run the helper script
    $ cd /market_scout/
    $ python ./helper_scripts/not_here_yet.sh

Now you can observe the timestamped output directory in /path/to/output and check /path/to/output/output_<timestamp>/logs/scout.log for market data

## Spin up an instance of the Flask server
    # change to the api/ directory in project root and run the app
    $ cd ./market_scout/src/api
    $ ./app.py

## Use Curl to query annotation data
 $ curl "http://localhost:5000/genes?gene_stable_id=ENSG00000281775&pid_suffix=SF0"


# Running with Docker
Here are the steps to build the Market Scout container and run it

## Make sure docker is installed
    $ docker --version

## Build the docker image
    # cd to project root and run docker build
    $ cd ../market_scout/
    $ docker build -t Dockerfile -f ./containers/Dockerfile .

## Run the container
    # the Dockerfile has an ENTRYPOINT that points to market_scout/src/scout.py
    # running a container from this image will automatically execute the script
    $ docker run --name Dockerfile market-scout

## Run Interactively
    # to inspect output files in the container, run unit tests, or the api/app.py
    # run the container interactively and override the ENTRYPOINT
    # map port '5000' of the host to port '5000' of the container
    $ docker run -it -p 5000:5000 --entrypoint /bin/bash --name market_scout_container market-scout


Now, if ./api/app.py is run inside the container, you should be able to access the service from
your machine's browser or using a curl command from the terminal


# Functionality
    - Retrieves real-time and historical market data

