from setuptools import find_packages, setup
import os
from glob import glob
package_name = 'humanoid_robot_description'
setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # This part ensures your folders are copied to the install directory
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'urdf'), glob(os.path.join('urdf', '*'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*'))),
        (os.path.join('share', package_name, 'meshes'), glob(os.path.join('meshes', '*'))),
        (os.path.join('share', package_name, 'scripts'), glob(os.path.join('scripts', '*.py'))),
        # NEW: texture image for the body screen (nested folder, so it needs
        # its own explicit entry — data_files doesn't recurse automatically)
        (os.path.join('share', package_name, 'materials', 'textures'), glob(os.path.join('materials', 'textures', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Asad',
    maintainer_email='asad@todo.todo',
    description='URDF and launch files for humanoid robot simulation',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gesture_starter=scripts.gesture_starter:main',
            'robot_gesture_node=scripts.robot_gesture_node:main',
        ],
    },
)
