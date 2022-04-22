#! /bin/bash

BASEDIR=$(dirname $0)		# the DIR in which this script is located
cd $BASEDIR
source .env
source /etc/profile     # To load env var $BESU_HOME

# Run the besu command
echo "Starting the Amechain node using besu command..."
$BESU_HOME/bin/besu --config-file="/root/blockchain/config/config.toml" --p2p-host=$NODE_PUBLIC_IP
