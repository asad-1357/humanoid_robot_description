import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_name = 'humanoid_robot_description'
    urdf_file = os.path.join(get_package_share_directory(package_name), 'urdf', 'humanoid_robot.urdf')
    with open(urdf_file, 'r') as infp:
        robot_description = infp.read()

    return LaunchDescription([
        # 1. Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),

        # 2. Joint State Publisher GUI
        # Node(
        #     package='joint_state_publisher_gui',
        #     executable='joint_state_publisher_gui',
        #     name='joint_state_publisher_gui'
        # ),

        # 3. RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', os.path.join(get_package_share_directory(package_name), 'config', 'view_arm.rviz')] if os.path.exists(os.path.join(get_package_share_directory(package_name), 'config', 'view_arm.rviz')) else []
        ),
    ])