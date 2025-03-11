#!/bin/bash
# robust_pair.sh

echo "Setting up robust Bluetooth pairing..."

# Stop all Bluetooth processes
sudo systemctl stop bluetooth
sudo killall bluetoothctl 2>/dev/null
sudo killall bt-agent 2>/dev/null
sleep 2

# Reset Bluetooth controller
sudo hciconfig hci0 down
sudo hciconfig hci0 up
sleep 1

# Start Bluetooth service
sudo systemctl start bluetooth
sleep 3

# Configure Bluetooth settings
sudo hciconfig hci0 name "GeekGoggles-Pi"
#sudo hciconfig hci0 class 0x100100  # Computer peripheral
sudo hciconfig hci0 piscan  # Make discoverable

# Set up bluetoothctl with proper agent
echo "Setting up Bluetooth agent..."
sudo bluetoothctl << EOF
power off
power on
agent DisplayYesNo
default-agent
discoverable on
pairable on
EOF

echo "Your Pi is now in pairing mode."
echo "When connecting from your laptop, KEEP THIS TERMINAL OPEN."
echo "PIN codes and pairing requests will appear below:"
echo "--------------------------------------------------------------"

# Monitor for pairing requests
sudo bluetoothctl

