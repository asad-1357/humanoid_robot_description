# humanoid_robot_description

A ROS 2 package containing a humanoid robot description, URDF model, launch files, and helper scripts.

## Repository Contents

- `CMakeLists.txt` - ROS 2 package build configuration.
- `package.xml` - ROS 2 package metadata.
- `setup.py` - Python package setup for any Python-based nodes.
- `urdf/humanoid_robot.urdf` - Humanoid robot description.
- `launch/sim_launch.py` - ROS 2 launch file for simulation.
- `scripts/` - Python scripts for gestures, pose tuning, transcript sync, and robot control.
- `config/controllers.yaml` - Controller configuration.

## How to upload this package to GitHub

These are the exact steps used to upload the repository to GitHub:

1. Open a terminal in the repository root:
   ```bash
   cd /home/asad/ros2_ws/src/humanoid_robot_description
   ```
2. Check the git status and confirm the current branch and modified files:
   ```bash
   git status --short --branch
   ```
3. Add all files to the git index:
   ```bash
   git add .
   ```
4. Commit the changes with a meaningful message:
   ```bash
   git commit -m "Add README and upload humanoid_robot_description package"
   ```
5. Verify the GitHub remote is configured:
   ```bash
   git remote -v
   ```
6. Push the branch to GitHub:
   ```bash
   git push origin main
   ```

> Note: If your remote uses SSH, make sure your SSH key is configured on GitHub. If the remote uses HTTPS, you may need a GitHub personal access token.

## Installation

1. Source your ROS 2 workspace:
   ```bash
   source /opt/ros/<ros2-distro>/setup.bash
   source /home/asad/ros2_ws/install/setup.bash
   ```
2. Build the workspace if needed:
   ```bash
   cd /home/asad/ros2_ws
   colcon build
   ```

## Usage

Launch the humanoid robot simulation with:
```bash
ros2 launch humanoid_robot_description sim_launch.py
```

## Notes

- This repository is currently configured with the `origin` remote on GitHub.
- The package includes both URDF and ROS 2 launch/script support for humanoid robot description and motion.
