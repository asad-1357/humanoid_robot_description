#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import subprocess

class WavingPerformance(Node):
    def __init__(self):
        super().__init__('waving_performance_node')
        self.publisher_ = self.create_publisher(
            JointTrajectory, 
            '/humanoid_controller/joint_trajectory', 
            10)
        
        self.count = 0
        self.max_repeats = 3
        self.media_file = "/home/asad/trimmed_small.mkv"
        
        self.timer = self.create_timer(2.0, self.run_loop)
        self.get_logger().info(f"Waving Node Started. Folder: sync_documentary2")

    def run_loop(self):
        self.timer.cancel()

        if self.count < self.max_repeats:
            self.count += 1
            self.get_logger().info(f"--- Starting Wave Repeat {self.count} ---")
            
            subprocess.run(['killall', '-q', 'mpv'])
            subprocess.Popen(['mpv', '--no-video', '--loop-file=no', self.media_file])
            
            self.send_wave()
            
            # Setting timer for 15s to allow for the waving duration
            if self.count < self.max_repeats:
                self.timer = self.create_timer(15.0, self.run_loop)
            else:
                self.get_logger().info("Finished waving.")
        
    def send_wave(self):
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

        # Constant Right Arm (Initial Position)
        r_fix = [1.536, -0.999, 0.767, 0.0, 0.8, 0.0, 0.0]

        # Wave Positions (Left Arm)
        rest_l = [1.536, 0.999, 0.942, 0.0, 0.8, 0.0, 0.0]      # Down
        pos_a  = [-1.18, 1.063, -1.231, 0.0, 0.8, 0.0, 0.0]     # Salute/Wave Left
        pos_b  = [-0.50, 1.500, -1.231, 0.0, 0.8, 0.0, 0.0]     # Wave Right (Adjusted Yaw)

        # --- WAVE TIMELINE ---
        p0 = create_point(r_fix, rest_l, 0.1)  # Start at rest
        p1 = create_point(r_fix, pos_a, 1.5)   # Up to salute position
        
        # The Oscillations (Waving back and forth)
        p2 = create_point(r_fix, pos_b, 2.5)   
        p3 = create_point(r_fix, pos_a, 3.5)   
        p4 = create_point(r_fix, pos_b, 4.5)   
        p5 = create_point(r_fix, pos_a, 5.5)   
        
        p6 = create_point(r_fix, rest_l, 7.5)  # Back to rest

        msg.points = [p0, p1, p2, p3, p4, p5, p6]
        self.publisher_.publish(msg)

def main():
    rclpy.init()
    node = WavingPerformance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
