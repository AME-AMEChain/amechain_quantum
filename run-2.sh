#! /bin/bash

# Color variables
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'
# Clear the color after that
clear='\033[0m'

echo -e "${green}Running run-2.sh script: Set up Quantum Security in the OS${clear}"
echo ""

GIT_DIR="/root/amechain_quantum"

if [[ ! -d "$GIT_DIR" ]]
    then
        echo -e "${red}Aborting...${clear}"
        echo "Directory $GIT_DIR does not exist on your filesystem."
        echo "Execute run-1.sh first"
        exit
fi

if [[ ! -f "$GIT_DIR/quantum/.env" ]]
    then
        echo -e "${red}Aborting...${clear}"
        echo "File $GIT_DIR/quantum/.env does not exist on your filesystem."
        echo "Step 1: If you are running a validator node, get the .env file by contacting amechain.io"
        echo "Step 2: Copy it to /root/amechain_quantum/quantum/"
        echo "Step 3: If you are running either a validator or non-validator node, run the script https://github.com/amechainq/amechain_quantum/blob/main/run-2.sh"
        exit
fi

cd $GIT_DIR/quantum
bash start_quantum_service.sh
echo -e "${cyan}Quantum setup is over.${clear}"

# Steps to initialize amechain node
cd $GIT_DIR/amechain
NODE_ENV="$GIT_DIR/amechain/.env"
if [[ ! -f $NODE_ENV ]]
    then
        touch $NODE_ENV
        echo "# The node server's public ip" > $NODE_ENV
        echo 'NODE_PUBLIC_IP=""' >> $NODE_ENV
fi

echo ""
echo -e "${blue}TO SETUP AMECHAIN NODE:${clear}"
echo "Step 1: Define public IP address of the node in /root/amechain_quantum/amechain/.env in the below format."
echo -e '\t\t NODE_PUBLIC_IP="aaa.bbb.ccc.ddd"'
echo "Step 2: Run the script run-3.sh"
