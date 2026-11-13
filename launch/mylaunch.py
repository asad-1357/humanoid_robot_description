import os
import xacro
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_name = 'humanoid_robot_description'
    urdf_file = os.path.join(get_package_share_directory(package_name), 'urdf', 'metal_cabinet_classroom.urdf.xacro')
    robot_description_config = xacro.process_file(urdf_file)
    robot_description = robot_description_config.toxml()

    pose_script_path ='/home/asad/ros2_ws/src/humanoid_robot_description/scripts/hardcoded_pose_node.py'
    rviz_config_path = os.path.join(get_package_share_directory(package_name), 'config', 'view_arm.rviz')

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_path] if os.path.exists(rviz_config_path) else []
        ),
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=['python3', pose_script_path],
                    output='screen'
                )
            ]
        ),
    ])
