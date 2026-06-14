#!/bin/bash
# Quick setup script for ros_llm workspace

set -e

echo "Setting up ROS LLM workspace..."

# Check if ROS 2 is sourced
if [ -z "$ROS_DISTRO" ]; then
    echo "Error: ROS 2 not sourced. Please run:"
    echo "  source /opt/ros/jazzy/setup.bash"
    exit 1
fi

echo "ROS 2 $ROS_DISTRO detected"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install ROS dependencies
echo "Installing ROS dependencies..."
sudo apt update
sudo apt install -y \
    ros-$ROS_DISTRO-cv-bridge \
    ros-$ROS_DISTRO-vision-msgs \
    ros-$ROS_DISTRO-geometry-msgs \
    ros-$ROS_DISTRO-nav-msgs \
    python3-opencv

# Build workspace
echo "Building workspace..."
colcon build --packages-select llm_nav_commander

# Source workspace
echo "Sourcing workspace..."
source install/setup.bash

# Test installation
echo "Testing installation..."
python3 src/llm_nav_commander/scripts/test_installation.py

echo ""
echo "Setup complete! To use:"
echo "  source install/setup.bash"
echo "  ros2 launch llm_nav_commander scene_analyzer.launch.py"
