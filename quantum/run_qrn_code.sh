#! /bin/bash

BASEDIR=$(dirname $0)		# the DIR in which this script is located
cd $BASEDIR
source .env

# Run the python code
pipenv install
cd $BASEDIR/qrn_code
if [[ $ENV = "production" ]]
    then
        pipenv run python3 main.py 1>/dev/null
    else
        pipenv run python3 main.py
fi

