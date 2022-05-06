#! /bin/bash

echo "Running run-3.sh: Set up Amechain node and keys"
echo ""

# Color variables
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'
# Clear the color after that
clear='\033[0m'

GIT_DIR="/root/amechain_quantum"
BLOCKCHAIN_DIR="/root/blockchain"

mkdir -p $BLOCKCHAIN_DIR
mkdir -p $BLOCKCHAIN_DIR/{data,config,temp}
mkdir -p $BLOCKCHAIN_DIR/data/keys

echo -e "${green}Installing pre-requisites...${clear}"
apt update
apt install curl rsync -y
echo ""

# INSTALL wscat
apt install nodejs npm -y
npm install -g wscat

# INSTALL JAVA

JAVA_VER="16.0.2"
JAVA_URL="https://download.java.net/java/GA/jdk16.0.2/d4a915d82b4c4fbb9bde534da945d746/7/GPL/openjdk-16.0.2_linux-x64_bin.tar.gz"

# Step 1: Installing java
echo -e "${green}Installing java...${clear}"
if [[ `command -v java` ]]
    then
        echo "java is already installed"
    else
        cd $BLOCKCHAIN_DIR/temp
        echo "Downloading java package..."
        curl -O $JAVA_URL
        echo "Extracting java package..."
        tar -xf "openjdk-${JAVA_VER}_linux-x64_bin.tar.gz"
        echo "Copying java package to system path..."
        rsync "jdk-16.0.2" /opt/ -a  
fi

# Step 2: Adding java to $PATH
if [[ ! -f "/opt/jdk-$JAVA_VER/bin/java" ]]
    then 
        echo "Error: java not found in path. Exiting..."
        exit
fi
if [[ -f "/opt/jdk-$JAVA_VER/bin/java" ]] && [[ ! `grep '$JAVA_HOME' /etc/profile` ]]
    then
        echo "Adding the java path to /etc/profile"
        echo "" >> /etc/profile
        echo "JAVA_HOME=/opt/jdk-$JAVA_VER" >> /etc/profile
        echo 'PATH=$PATH:$JAVA_HOME/bin' >> /etc/profile  
fi
source /etc/profile
java -version
echo ""


# INSTALL BESU

# Step 1: Check if java is present. Exit if absent.
if [[ ! `command -v java` ]]  
    then
        echo "Error: java command not found. Exiting..."
        exit
fi

# Step 2: Installing besu
echo -e "${green}Installing Hyperledger besu...${clear}"
BESU_VER="22.1.2"       # Change this value to install a different version
if [[ `command -v besu` ]]
    then
        echo "Hyperledger besu is already installed"
    else
        echo "Installing Hyperledger Besu version $BESU_VER..."
        cd $BLOCKCHAIN_DIR/temp
        echo "Downloading besu package..."
        curl -O "https://hyperledger.jfrog.io/artifactory/besu-binaries/besu/$BESU_VER/besu-$BESU_VER.tar.gz"
        echo "Extracting besu package..."
        tar -xf besu-$BESU_VER.tar.gz
        echo "Copying besu package to system path..."
        cp besu-$BESU_VER /opt/ -r
fi

# Step 3: Adding besu to $PATH
if [[ ! -f "/opt/besu-$BESU_VER/bin/besu" ]]
    then 
        echo "Error: besu not found in path. Exiting..."
        exit
fi
if [[ -f "/opt/besu-$BESU_VER/bin/besu" ]] && [[ ! `grep '$BESU_HOME' /etc/profile` ]]
    then
        echo "Adding the besu path to /etc/profile"
        echo "" >> /etc/profile
        echo "BESU_HOME=/opt/besu-$BESU_VER" >> /etc/profile
        sed -i "/\$JAVA_HOME/d" /etc/profile    # remove the line containing $JAVA_HOME
        echo 'PATH=$PATH:$JAVA_HOME/bin:$BESU_HOME/bin' >> /etc/profile  
fi
source /etc/profile
besu --version

# Copy amechain related files to /root/blockchain
echo ""
echo -e "${green}Copying Amechain config files...${clear}"
rsync -a $GIT_DIR/amechain/config $BLOCKCHAIN_DIR/
if [[ -f "$BLOCKCHAIN_DIR/config/genesis.json" ]]
    then
        echo "Copied genesis and other files to /root/blockchain/"
fi

# Generating node keys and address
echo ""
echo -e "${green}PRIVATE KEY AND ADDRESS${clear}"
message()
{
    export node_address=`cat $BLOCKCHAIN_DIR/data/keys/node_address`
    echo -e "${yellow}IMPORTANT${clear}: Private key is stored at $BESU_HOME/key. ${yellow}DO NOT DELETE THIS FILE${clear}. Take a backup of this file and keep it safe."
    echo -e "The transaction fees for the validator node will be deposited to this address ${cyan}$node_address${clear}. This address is derived from the above private key. Thus, the fees can be accessed with the private key."
}

if [[ -f $BLOCKCHAIN_DIR/data/keys/nodekey.pub ]] && [[ -f $BLOCKCHAIN_DIR/data/keys/node_address ]]
    then
        echo "Private key and address have previously been generated for this validator node. The node shall use the same. No new key or address is generated now."
        message
    else
        echo -e "${green}Generating a new private key and address for this validator node...${clear}"
        besu public-key export --to=$BLOCKCHAIN_DIR/data/keys/nodekey.pub
        besu public-key export-address --to=$BLOCKCHAIN_DIR/data/keys/node_address
        if [[ -f $BLOCKCHAIN_DIR/data/keys/nodekey.pub ]] && [[ -f $BLOCKCHAIN_DIR/data/keys/node_address ]]
            then
                echo -e "Private key is successfully generated."
                cp -v $BESU_HOME/key $BLOCKCHAIN_DIR/data/keys/nodekey.pri  # nodekey.pri is used in config.toml
                message
            else
                echo "${red}Error:${clear} Unable to generate private key or address"
        fi
fi

# Creating a systemd service for amechain node
echo ""
echo -e "${green}Creating a systemd service for amechain node${clear}"
cd $GIT_DIR/amechain
source .env
if [ -z "$NODE_PUBLIC_IP" ]
    then
        echo -e "${red}Error:${clear} Public IP address of the node is not set in /root/amechain_quantum/amechain/.env"
        echo "Step 1: Define public IP address of the node in /root/amechain_quantum/amechain/.env in the below format."
        echo -e '\t\t NODE_PUBLIC_IP="aaa.bbb.ccc.ddd"'
        echo "Step 2: Run the script run-3.sh"
        exit
    else
        bash start_amechain_node_service.sh
fi
