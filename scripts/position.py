#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import json
import time
import threading
import numpy as np
import os

# --- 1. CONFIGURATION & MAPPING ---
# Ensure these match your URDF exactly
JOINT_NAMES = [
    'body_to_arm_joint_right', 'shoulder_yaw_joint_right', 'shoulder_pitch_joint_right', 'elbow_joint_right', 'finger_center_joint_right',
    'body_to_arm_joint_left', 'shoulder_yaw_joint_left', 'shoulder_pitch_joint_left', 'elbow_joint_left', 'finger_center_joint_left'
]

# Preset poses for fallback or specific triggers
POSES = {
    "neutral":   [0.0, 0.0, 0.0, 0.0, 0.0,  0.0, 0.0, 0.0, 0.0, 0.0],
    "welcome":   [0.0, 0.0, -0.5, 0.5, 0.0,  0.0, 0.0, -0.5, 0.5, 0.0],
    "wave_1":    [0.0, 0.6, -1.5, 1.2, 0.0,  0.0, -0.6, -1.5, 1.2, 0.0],
    "wave_2":    [0.0, -0.4, -1.5, 1.2, 0.0,  0.0, 0.4, -1.5, 1.2, 0.0],
    "salute":    [0.0, 0.0, -1.57, 0.0, 0.0,  0.0, 0.0, -1.57, 0.0, 0.0],
    "think":     [0.0, 0.2, -1.2, 1.5, 0.0,  0.0, -0.2, -0.4, 0.2, 0.0]
}

# --- 2. EASING FUNCTIONS ---
def smootherstep(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

def ease_out_cubic(t):
    return 1.0 - (1.0 - t) ** 3

class RobotGestureEngine(Node):
    def __init__(self):
        super().__init__('robot_gesture_engine')
        self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        
        self.current_angles = np.array(POSES["neutral"])
        self.publish_rate = 100  # Hz
        self.dt = 1.0 / self.publish_rate
        
        self.get_logger().info("Gesture Engine Initialized at 100Hz")

    def publish_current(self, positions):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = positions.tolist()
        self.publisher.publish(msg)

    def move_to(self, target_list, duration=1.0, style="smooth"):
        """Interpolates from current position to target."""
        target_pose = np.array(target_list)
        start_pose = np.array(self.current_angles)
        steps = max(int(duration * self.publish_rate), 1)
        
        for i in range(1, steps + 1):
            t_raw = i / steps
            
            # Select Easing
            if style == "smooth":
                t = smootherstep(t_raw)
            elif style == "settle":
                t = ease_out_cubic(t_raw)
            else:
                t = t_raw # Linear
            
            interp_pose = start_pose + (target_pose - start_pose) * t
            self.publish_current(interp_pose)
            self.current_angles = interp_pose
            time.sleep(self.dt)

    def hold(self, duration):
        """Maintains current pose for a set time."""
        steps = max(int(duration * self.publish_rate), 1)
        for _ in range(steps):
            self.publish_current(self.current_angles)
            time.sleep(self.dt)

    def process_transcript(self, transcript_data):
        """Syncs movements to the transcript timestamps."""
        self.get_logger().info("Starting Transcript Playback...")
        start_time = time.time()

        for segment in transcript_data:
            text = segment['text'].lower()
            target_start = segment['start']
            target_end = segment['end']
            duration = target_end - target_start

            # Logic to map text keywords to Poses
            # This replaces the external gesture_mapper for simplicity
            pose_key = "neutral"
            if "hello" in text or "welcome" in text: pose_key = "welcome"
            elif "wave" in text: pose_key = "wave_1"
            elif "think" in text or "know" in text: pose_key = "think"
            elif "important" in text: pose_key = "salute"

            target_pose = POSES.get(pose_key, POSES["neutral"])

            # Sync Timing: Wait until it's time to start the move
            elapsed = time.time() - start_time
            wait_time = target_start - elapsed
            if wait_time > 0:
                self.hold(wait_time)

            # Execution
            self.get_logger().info(f"Executing: {pose_key} for '{text}'")
            move_time = min(duration * 0.5, 1.2) # Spend half the time moving
            self.move_to(target_pose, duration=move_time, style="smooth")
            
            # Hold the pose for the remainder of the speech segment
            remaining = (target_end - target_start) - move_time
            if remaining > 0:
                self.hold(remaining)

        # Final return to neutral
        self.move_to(POSES["neutral"], duration=2.0)

def main():
    rclpy.init()
    node = RobotGestureEngine()

    # Load Transcript (Change path as needed)
    path = os.path.expanduser("~/ros2_ws/src/humanoid_robot_description/scripts/transcript.json")
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Run playback in a separate thread so node stays responsive
        playback_thread = threading.Thread(target=node.process_transcript, args=(data,))
        playback_thread.start()
        
        rclpy.spin(node)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()