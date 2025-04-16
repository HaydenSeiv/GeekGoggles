#!/bin/bash

# Source the user profile to get the same environment as login
source /home/admin/.profile

# Setup pulseaudio if not running
pulseaudio --start --exit-idle-time=-1 || true

# Set environment variables
export DISPLAY=:0
export PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# Wait a moment for audio to initialize
sleep 2

# Change to the working directory
cd /home/admin/GeekGoggles/Pi_Code

# Activate the virtual environment
source /home/admin/GeekGoggles/Pi_Code/my_venv/bin/activate

# Run the actual program
cd /home/admin/GeekGoggles/Pi_Code
/home/admin/GeekGoggles/Pi_Code/my_venv/bin/python3 /home/admin/GeekGoggles/Pi_Code/main_Geek.py