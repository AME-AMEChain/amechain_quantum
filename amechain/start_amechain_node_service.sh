#! /bin/bash

BASEDIR=$(dirname $0)		# the DIR in which this script is located
cd $BASEDIR
SERVICE_NAME="amechain_node"

# Enable and start a systemd service
echo "Starting the Amechain node process as a systemd service"
cp $SERVICE_NAME.service /etc/systemd/system/$SERVICE_NAME.service
systemctl enable $SERVICE_NAME
systemctl stop $SERVICE_NAME       
systemctl daemon-reload
systemctl restart $SERVICE_NAME
systemctl status $SERVICE_NAME --no-pager
