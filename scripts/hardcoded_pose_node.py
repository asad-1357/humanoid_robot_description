#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import time
import threading
import os
import sys
import subprocess
import numpy as np

# Automatically find and patch your script folder path to import gesture_mapper safely
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    from gesture_mapper import JOINT_NAMES, get_joint_angles
except ImportError:
    JOINT_NAMES = [
        "body_to_arm_joint_right", "shoulder_yaw_joint_right", "shoulder_pitch_joint_right", 
        "elbow_joint_right", "palm_to_f1_right", "palm_to_f2_right", "palm_to_f3_right",
        "body_to_arm_joint_left", "shoulder_yaw_joint_left", "shoulder_pitch_joint_left", 
        "elbow_joint_left", "palm_to_f1_left", "palm_to_f2_left", "palm_to_f3_left",
        "face_yaw_joint",
    ]
    
    GESTURES = {
        "hello1": [[-0.059, -0.287, -1.570, 0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0], [0.1]],
        "hello2": [[-0.059, -0.287, -0.999, 0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0], [-0.1]],
        "hello3": [[-0.059, -0.287, -1.570, 0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0], [0.0]],
        "neutral": [[1.434, -0.829, 0.910, 0.0, 0.0, 0.0, 0.0], [1.434, 0.819, 0.738, 0.0, 0.0, 0.0, 0.0], [0.0]],
        "explaining_idea": [[-0.823, -1.052, -0.500, 0.0, 0.0, 0.0, 0.0], [-0.806, 1.203, -0.569, 0.0, 0.0, 0.0, 0.0], [0.0]],
        "small_detail": [[1.2, -0.4, 0.5, 0.0, 0.0, 0.0, 0.0], [1.3, 0.6, 0.18, 0.0, 0.0, 0.0, 0.0], [0.0]],
        "compare_this": [[0.0, -1.5, 0.0, 0.0, 0.0, 0.0, 0.0], [1.3391, 0.6088, 0.1847, 0.0, 0.0, 0.0, 0.0], [0.0]],
        "compare_that": [[1.4776, -0.5547, 0.1285, 0.0, 0.0, 0.0, 0.0], [0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0]]
    }
    def get_joint_angles(gesture_name):
        raw = GESTURES.get(gesture_name, GESTURES["neutral"])
        return raw[0] + raw[1] + raw[2]

PUBLISH_HZ = 60 
VIDEO_PATH = os.path.expanduser("~/Downloads/English_Verbs_trimmed.mp4")

class HardcodedPoseNode(Node):
    def __init__(self):
        super().__init__("hardcoded_pose_player")
        self.publisher = self.create_publisher(JointState, "/joint_states", 10)
        
        neutral_angles = get_joint_angles("neutral")
        self.current_pos = np.array(neutral_angles, dtype=float)
        self.target_pos  = np.array(neutral_angles, dtype=float)
        self.start_pos   = np.array(neutral_angles, dtype=float)
        
        self.start_time = time.time()
        self.duration = 1.0
        self.is_moving = False
        
        self.video_process = None
        
        self.timer = self.create_timer(1.0 / PUBLISH_HZ, self.timer_callback)
        self.get_logger().info("Hardcoded Pose Node Online - Continuous Loop Mode Active")

    def lerp(self, start, end, t):
        t = np.clip(t, 0, 1)
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

    def trigger_move(self, gesture_name, duration=1.0):
        try:
            angles = get_joint_angles(gesture_name)
        except Exception:
            angles = get_joint_angles("neutral")
            
        self.start_pos = np.array(self.current_pos) 
        self.target_pos = np.array(angles)
        self.duration = duration
        self.start_time = time.time()
        self.is_moving = True

    def launch_background_video(self):
        """Launches mpv player in a separate background window"""
        if os.path.exists(VIDEO_PATH):
            self.get_logger().info(f"Launching video in background: {VIDEO_PATH}")
            try:
                self.video_process = subprocess.Popen(
                    ["mpv", VIDEO_PATH],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            except Exception as e:
                self.get_logger().error(f"Could not launch mpv player: {e}")
        else:
            self.get_logger().warn(f"Video file not found at: {VIDEO_PATH}.")

    def wait_while_checking_video(self, duration):
        """Blocks execution to hold a pose, but terminates instantly if the video closes"""
        start_wait = time.time()
        while time.time() - start_wait < duration:
            # Check if video window was shut down or ended naturally
            if self.video_process and self.video_process.poll() is not None:
                return False
            time.sleep(0.05)
        return True

    def execute_pose_routine(self):
        self.launch_background_video()
        time.sleep(0.5)  # Let video window instantiate

        # --- 1. INTRO HELLO SEQUENCE (Plays exactly once at the beginning) ---
        self.get_logger().info("--- Phase 1: Playing Intro Greetings ---")
        intro_sequence = [
            ("hello1", 1.2),  
            ("hello2", 0.8),
            ("hello3", 0.8),
            ("neutral", 1.0)  
        ]

        for pose, duration in intro_sequence:
            # Drop tracking instantly if user exits the video during greeting sequence
            if self.video_process and self.video_process.poll() is not None:
                self.get_logger().info("Video closed early during Intro. Exiting.")
                return

            self.get_logger().info(f"Moving to: {pose}")
            self.trigger_move(pose, duration)
            if not self.wait_while_checking_video(duration + 0.3):
                return

        # --- 2. REPEATING POSE LOOP (Runs continuously until video ends) ---
        self.get_logger().info("--- Phase 2: Starting Continuous Loop of 4 Teacher Poses ---")
        custom_poses = [
            ("explaining_idea", 1.5, 2.0), 
            ("small_detail",     1.2, 2.5),
            ("compare_this",     1.0, 2.0),
            ("compare_that",     1.0, 3.0)
        ]

        loop_count = 1
        while True:
            # Check if video process is dead before starting a new iteration cycle
            if self.video_process and self.video_process.poll() is not None:
                self.get_logger().info("Video ended. Breaking out of custom pose loop.")
                break

            self.get_logger().info(f"Executing Teacher Pose Loop Cycle #{loop_count}")
            
            for pose_name, transition_time, hold_time in custom_poses:
                self.get_logger().info(f"Moving to target pose [{pose_name}]")
                self.trigger_move(pose_name, transition_time)
                
                # Wait out the movement transition and stable hold safely
                video_is_alive = self.wait_while_checking_video(transition_time + hold_time)
                
                # If video stops during a pose step, abort instantly
                if not video_is_alive:
                    self.get_logger().info("Video window terminated mid-pose sequence.")
                    break
            
            if self.video_process and self.video_process.poll() is not None:
                break
                
            loop_count += 1

        # --- 3. FINAL RESET ---
        self.get_logger().info("Routine lifecycle wrapping up. Returning system to neutral.")
        self.trigger_move("neutral", 2.0)
        time.sleep(2.0)

def main():
    rclpy.init()
    node = HardcodedPoseNode()

    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()
    
    time.sleep(1.0) 
    
    try:
        node.execute_pose_routine()
    except KeyboardInterrupt:
        node.get_logger().warn("Routine lifecycle halted via user interrupt request.")
    finally:
        # Guarantee background player termination if node script is killed prematurely
        try:
            if node.video_process and node.video_process.poll() is None:
                node.get_logger().info("Terminating active background video process...")
                node.video_process.terminate()
                node.video_process.wait(timeout=2)
        except Exception:
            pass

        try:
            node.trigger_move("neutral", 1.0)
            time.sleep(1.0)
        except Exception:
            pass
        
        rclpy.shutdown()

if __name__ == "__main__":
    main()