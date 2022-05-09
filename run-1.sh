#! /bin/bash

# A script that sets up QRN in the OS

# Color variables
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'
# Clear the color after that
clear='\033[0m'

echo -e "${green}Running run-1.sh script: Set up QRN in the OS${clear}"
echo ""

echo "Installing pre-requisites..."
apt update
apt install -y git pipenv rsync
echo ""

GIT_DIR="/root/amechain_quantum"
git config pull.rebase false

if [[ -d "$GIT_DIR/.git" ]]
    then
        cd $GIT_DIR
        git reset --hard    # discard your local changes completely
        git clean -fd   # discard untracked / new files in local
        git pull
fi

if [[ ! -d "$GIT_DIR" ]]
    then
        cd /root
        git clone https://github.com/AME-AMEChain/amechain_quantum.git
fi

echo ""
echo -e "${blue}TO DO:${clear}"
echo "If you are running a validator node, follow Steps 1,2,3. If you are running a non-validator node, follow Step 3 only."
echo "Step 1: Get the .env file by contacting amechain.io"
echo "Step 2: Copy it to /root/amechain_quantum/quantum/"
echo "Step 3: Run the script run-2.sh"

