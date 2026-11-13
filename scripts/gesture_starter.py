#!/usr/bin/env python3
"""
Script to perform initial gestures (hello1, hello2, hello3) before starting gesture node
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import time
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gesture_mapper import JOINT_NAMES, get_joint_angles

PUBLISH_HZ = 60 

class GestureStarter(Node):
    def __init__(self):
        super().__init__("gesture_starter")
        self.publisher = self.create_publisher(JointState, "/joint_states", 10)
        
        # Initialize angles from neutral
        neutral_angles = get_joint_angles("neutral")
        self.current_pos = np.array(neutral_angles, dtype=float)
        self.target_pos  = np.array(neutral_angles, dtype=float)
        self.start_pos   = np.array(neutral_angles, dtype=float)
        
        self.start_time = time.time()
        self.duration = 1.0
        self.is_moving = False
        
        self.timer = self.create_timer(1.0 / PUBLISH_HZ, self.timer_callback)
        self.get_logger().info("Gesture Starter Node Online - Performing initial gestures")
        
        # Schedule gesture sequence
        self.gesture_sequence = ["hello1", "hello2", "hello3"]
        self.gesture_index = 0
        self.gesture_start_time = time.time()

    def lerp(self, start, end, t):
        t = np.clip(t, 0, 1)
        # Smootherstep easing
        t = t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
        return start + (end - start) * t

    def timer_callback(self):
        if self.is_moving:
            elapsed = time.time() - self.start_time
            progress = elapsed / self.duration
            
            self.current_pos = self.lerp(self.start_pos, self.target_pos, progress)
            
            if progress >= 1.0:
                self.is_moving = False
        
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = self.current_pos.tolist()
        self.publisher.publish(msg)
        
        # Check if it's time to perform next gesture (every 1.5 seconds)
        if time.time() - self.gesture_start_time > 1.5 and self.gesture_index < len(self.gesture_sequence):
            gesture = self.gesture_sequence[self.gesture_index]
            self.trigger_move(gesture, duration=1.0)
            self.get_logger().info(f"Performing gesture: {gesture}")
            self.gesture_index += 1
            self.gesture_start_time = time.time()
        
        # Exit after all gestures are done
        if self.gesture_index >= len(self.gesture_sequence) and not self.is_moving:
            self.get_logger().info("All initial gestures completed! Shutting down gesture starter...")
            time.sleep(0.5)  # Brief delay to ensure last position is published
            rclpy.shutdown()

    def trigger_move(self, gesture_name, duration=1.0):
        self.start_pos = np.array(self.current_pos)
        self.target_pos = np.array(get_joint_angles(gesture_name))
        self.duration = duration
        self.start_time = time.time()
        self.is_moving = True


def main(args=None):
    rclpy.init(args=args)
    node = GestureStarter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
