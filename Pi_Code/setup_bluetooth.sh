#!/bin/bash
# setup_bluetooth.sh

echo "Setting up Bluetooth..."

# Stop bluetooth service
sudo systemctl stop bluetooth
sleep 2

# Make sure bluetooth is unblocked
sudo rfkill unblock bluetooth

# Start bluetooth service
sudo systemctl start bluetooth
sleep 2

# Set class to be more discoverable (0x000100 - computer peripheral)
sudo hciconfig hci0 class 0x000100

# Configure bluetooth
sudo bluetoothctl << EOF
remove B8:27:EB:5F:7D:15
power off
power on
discoverable yes
discoverable-timeout 0
pairable on
name GeekGoggles-Pi
class 0x000100
EOF

# Set discoverable mode directly
sudo hciconfig hci0 piscan

echo "Current Bluetooth status:"
sudo hciconfig -a

echo "Bluetooth setup complete. Device should be visible as 'GeekGoggles-Pi'"
