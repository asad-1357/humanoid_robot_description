#!/usr/bin/env python3
"""
Launch file for gesture demo: 
- Starts rviz
- Starts robot state publisher
- Performs hello1, hello2, hello3 gestures
- Then starts robot_gesture_node.py
"""
import os
import sys
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_name = 'humanoid_robot_description'
    package_dir = get_package_share_directory(package_name)
    
    urdf_file = os.path.join(package_dir, 'urdf', 'humanoid_robot.urdf')
    with open(urdf_file, 'r') as infp:
        robot_description = infp.read()

    # Path to scripts in source directory
    workspace_root = '/home/asad/ros2_ws'
    gesture_starter_script = os.path.join(workspace_root, 'src', package_name, 'scripts', 'gesture_starter.py')
    robot_gesture_node_script = os.path.join(workspace_root, 'src', package_name, 'scripts', 'robot_gesture_node.py')

    return LaunchDescription([
        # 1. Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),

        # 2. RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', os.path.join(package_dir, 'config', 'view_arm.rviz')] 
            if os.path.exists(os.path.join(package_dir, 'config', 'view_arm.rviz')) 
            else []
        ),

        # 3. Gesture Starter (performs hello1, hello2, hello3)
        ExecuteProcess(
            cmd=['python3', gesture_starter_script],
            output='screen',
            shell=False
        ),

        # 4. Robot Gesture Node (starts after initial gestures)
        ExecuteProcess(
            cmd=['python3', robot_gesture_node_script],
            output='screen',
            shell=False
        ),
    ])
