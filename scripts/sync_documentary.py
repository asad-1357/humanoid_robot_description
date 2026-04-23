#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import subprocess  # Required to trigger audio playback

class DocumentaryPerformance(Node):
    def __init__(self):
        super().__init__('documentary_performance_node')
        self.publisher_ = self.create_publisher(
            JointTrajectory, 
            '/humanoid_controller/joint_trajectory', 
            10)
        
        self.count = 0
        self.max_repeats = 3
        self.media_file = "/home/asad/trimmed_small.mkv"
        
        # Initial delay to let RViz and controllers settle
        self.timer = self.create_timer(2.0, self.run_loop)
        self.get_logger().info(f"Performance Node Started. Repeating {self.max_repeats} times.")

    def run_loop(self):
        self.timer.cancel()

        if self.count < self.max_repeats:
            self.count += 1
            self.get_logger().info(f"--- Starting Motion & Audio Repeat {self.count} ---")
            
            # Start the Audio synced with motion
            subprocess.run(['killall', '-q', 'mpv']) 
            subprocess.Popen(['mpv', '--no-video', '--loop-file=no', self.media_file])
            
            self.send_performance()
            
            if self.count < self.max_repeats:
                # Wait 18 seconds before starting the next cycle
                self.timer = self.create_timer(18.0, self.run_loop)
            else:
                self.get_logger().info("Finished all repeats.")
        
    def send_performance(self):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = [
            "body_to_arm_joint_right", "shoulder_yaw_joint_right", "shoulder_pitch_joint_right", 
            "elbow_joint_right", "palm_to_f1_right", "palm_to_f2_right", "palm_to_f3_right",
            "body_to_arm_joint_left", "shoulder_yaw_joint_left", "shoulder_pitch_joint_left", 
            "elbow_joint_left", "palm_to_f1_left", "palm_to_f2_left", "palm_to_f3_left"
        ]

        def create_point(r_vals, l_vals, seconds):
            point = JointTrajectoryPoint()
            point.positions = r_vals + l_vals
            point.time_from_start = Duration(sec=int(seconds), nanosec=int((seconds % 1) * 1e9))
            return point

        # From your provided table
        init_r = [1.536, -0.999, 0.767, 0.0, 0.8, 0.0, 0.0]
        init_l = [1.536, 0.999, 0.942, 0.0, 0.8, 0.0, 0.0]
        
        dest_r = [1.536, -0.999, 0.767, 0.0, 0.8, 0.0, 0.0]
        dest_l = [-1.18, 1.063, -1.231, 0.0, 0.8, 0.0, 0.0]

        # 1. Start at Initial
        p0 = create_point(init_r, init_l, 0.1)
        # 2. Reach Desired Pose
        p1 = create_point(dest_r, dest_l, 4.0)
        # 3. Stay at Desired Pose for a moment
        p2 = create_point(dest_r, dest_l, 10.0)
        # 4. Return to Initial (Rest)
        p_reset = create_point(init_r, init_l, 14.0)

        msg.points = [p0, p1, p2, p_reset]
        self.publisher_.publish(msg)

def main():
    rclpy.init()
    node = DocumentaryPerformance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
