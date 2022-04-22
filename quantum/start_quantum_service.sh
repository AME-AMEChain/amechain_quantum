#! /bin/bash

BASEDIR=$(dirname $0)		# the DIR in which this script is located
cd $BASEDIR
source .env
SERVICE_NAME="quantum"

# Enable and start a systemd service
if [[ $ENV = "production" ]]
    then
        echo "Starting the QRN processing as a systemd service"
        cp $SERVICE_NAME.service /etc/systemd/system/$SERVICE_NAME.service
        systemctl enable $SERVICE_NAME
        systemctl stop $SERVICE_NAME        
        systemctl daemon-reload
        systemctl restart $SERVICE_NAME
        
    else
        echo "This is not a production server"
fi
