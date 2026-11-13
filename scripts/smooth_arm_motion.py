import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class ArmSmoothMover(Node):
    def __init__(self):
        super().__init__('arm_smooth_mover')
        self.publisher_ = self.create_publisher(JointTrajectory, '/humanoid_controller/joint_trajectory', 10)
        
        # Joint names exactly as defined in your ros2_control setup
        self.joints = [
            'body_to_arm_joint_right', 'shoulder_yaw_joint_right', 'shoulder_pitch_joint_right', 
            'elbow_joint_right', 'palm_to_f1_right', 'palm_to_f2_right', 'palm_to_f3_right', 
            'body_to_arm_joint_left', 'shoulder_yaw_joint_left', 'shoulder_pitch_joint_left', 
            'elbow_joint_left', 'palm_to_f1_left', 'palm_to_f2_left', 'palm_to_f3_left'
        ]

        # Define your 4 Poses (14 values each to match the joint list)
        self.poses = [
            [0.0] * 14,                                      # Pose 1: Home (0s)
            [0.5, -0.2, 0.5, 1.0, 0.2, 0.2, 0.2] * 2,        # Pose 2: Action A (3s)
            [1.0, 0.0, 0.8, 0.5, 0.5, 0.5, 0.5] * 2,         # Pose 3: Action B (6s)
            [-0.5, 0.4, 0.2, 1.5, 0.0, 0.0, 0.0] * 2         # Pose 4: Action C (9s)
        ]

        self.timer_period = 12.0  # Full cycle is 12 seconds
        self.total_duration = 60.0 # Run for 1 minute
        self.start_time = self.get_clock().now()
        
        self.timer = self.create_timer(self.timer_period, self.send_trajectory)
        self.send_trajectory() # Send first cycle immediately

    def send_trajectory(self):
        now = self.get_clock().now()
        elapsed = (now - self.start_time).nanoseconds / 1e9
        
        if elapsed >= self.total_duration:
            self.get_logger().info('1 Minute reached. Stopping.')
            self.timer.cancel()
            return

        msg = JointTrajectory()
        msg.joint_names = self.joints

        for i, pose_angles in enumerate(self.poses):
            point = JointTrajectoryPoint()
            point.positions = pose_angles
            # Each pose is reached 3 seconds after the previous one
            point.time_from_start = Duration(sec=(i * 3))
            msg.points.append(point)

        self.get_logger().info(f'Publishing 12s cycle... (Elapsed: {elapsed:.1f}s)')
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ArmSmoothMover()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
