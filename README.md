###tx_clients
[![Anaconda-Server Badge](https://anaconda.org/getpantheon/tx_clients/badges/installer/conda.svg)](https://conda.anaconda.org/getpantheon)
[![CircleCI](https://circleci.com/gh/pantheon-systems/tx_clients.svg?style=svg)](https://circleci.com/gh/pantheon-systems/tx_clients)
[![Coverage Status](https://coveralls.io/repos/github/pantheon-systems/tx_clients/badge.svg)](https://coveralls.io/github/pantheon-systems/tx_clients)

This is a library of twisted helpers.

##Developing & running
### Install Conda
**NEVER install conda with pip, this will pollute your system level python installation and possibly upgrade your python version.**

Download and run the miniconda script for python 2.7 [Miniconda installer] (http://conda.pydata.org/miniconda.html)

Command line **linux** installation:

    # Download the latest version of the miniconda setup script
    wget http://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -O ~/miniconda.sh
    # Run the setup script
    ~/miniconda.sh
    # Let it install to the default directory ($HOME/miniconda2) and accept the terms.

Command line **Mac OSX** installation:

    # Download the latest version of the miniconda setup script
    wget http://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh -O ~/miniconda.sh
    # Run the setup script
    ~/miniconda.sh
    # Let it install to the default directory ($HOME/miniconda2) and accept the terms.

### Update conda and download basic dependencies

    # Update conda
    conda update -y conda
    # Install conda build, a wrapper for building conda packages
    conda install -y conda-build

### Add our channel to your conda configuration

    # For access to just public repositories:
    conda config --add channels pantheon

    # For access to both public and private repositories you need an anaconda.org account
    # and must contact magellan to be added to the developers group for our organization
    # For convenience you can embed a personal access token in the channel URL. A token
    # can be generated using the anaconda cloud api or a command line utility.
    conda install -y anaconda-client
    anaconda login
    PRIVATE_REPO_TOKEN=`anaconda auth --create -n private_repo --scopes 'conda:download'`
    conda config --add channels https://conda.anaconda.org/t/$PRIVATE_REPO_TOKEN/pantheon

### Clone Repostiroy

    git clone git@github.com:pantheon-systems/tx_clients.git $HOME/tx_clients

### Create and activate the conda environment
Make sure you have added the pantheon channels as directed above:

    conda env create
    source activate tx_clients

##Debugging
TODO tips and tricks for debugging this app

##Known Issues/Limitation
TODO Any system-wide implementation details or design tradeoffs

##Configuring
TODO how to configure the application's parameters.

##Testing
TODO how to run and debug the tests locally before committing.

    # Run tests and collect code coverage
    make test
    # See the coverage report
    make coverage
    # Run linter
    make lint
    # Run flake8
    make flake8

##Deployment
TODO See Similar Piepline Example: https://getpantheon.atlassian.net/wiki/display/VULCAN/Cookbook+Testing
how to deploy the application on live, any dependencies that need
to be deployed too.

# FAQ
TODO Unanswered questions or clarifications related to this repository or document

# Troubleshoot
TODO Ways of resolving problems with setting up local development
