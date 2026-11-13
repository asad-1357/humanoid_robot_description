import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_name = 'humanoid_robot_description'
    
    # Path to your URDF/Xacro file
    urdf_file = os.path.join(get_package_share_directory(package_name), 'urdf', 'humanoid_robot.urdf')

    # IMPORTANT: Use xacro to process the file (this handles macros, legs, etc.)
    # This mimics what you did manually in the terminal
    robot_description_config = xacro.process_file(urdf_file)
    robot_description = robot_description_config.toxml()

    return LaunchDescription([
        # 1. Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}]
        ),

        # 2. Joint State Publisher GUI (Uncomment if needed for testing)
         Node(
             package='joint_state_publisher_gui',
             executable='joint_state_publisher_gui',
             name='joint_state_publisher_gui'
         ),

        # 3. RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', os.path.join(get_package_share_directory(package_name), 'config', 'view_arm.rviz')] 
            if os.path.exists(os.path.join(get_package_share_directory(package_name), 'config', 'view_arm.rviz')) else []
        ),
    ])
