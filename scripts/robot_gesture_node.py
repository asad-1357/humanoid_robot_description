#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import json
import time
import threading
import subprocess
import os
import sys
import socket
import tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gesture_mapper import JOINT_NAMES, get_gesture_for_text, get_joint_angles

TRANSCRIPT_PATH = os.path.expanduser("~/ros2_ws/src/humanoid_robot_description/scripts/transcript.json")

PUBLISH_HZ = 60 

class GesturePlayerNode(Node):
    def __init__(self):
        super().__init__("gesture_player")
        self.publisher = self.create_publisher(JointState, "/joint_states", 10)
        
        # Initialize angles from neutral
        neutral_angles = get_joint_angles("neutral")
        self.current_pos = np.array(neutral_angles, dtype=float)
        self.target_pos  = np.array(neutral_angles, dtype=float)
        self.start_pos   = np.array(neutral_angles, dtype=float)
        
        self.start_time = time.time()
        self.duration = 1.0
        self.is_moving = False
        
        # Video synchronization
        self.video_process = None
        self.video_stopped = False
        self.mpv_socket = None
        self.video_paused = False
        self.pause_time = 0  # Track how long video has been paused
        self.total_pause_duration = 0  # Total pause time accumulated
        self.last_position = 0
        self.position_timeout = 0
        
        self.timer = self.create_timer(1.0 / PUBLISH_HZ, self.timer_callback)
        self.get_logger().info("Gesture Player Node Online - 60Hz Interpolation")

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

    def trigger_move(self, gesture_name, duration=1.0):
        self.start_pos = np.array(self.current_pos) # Start from current position
        self.target_pos = np.array(get_joint_angles(gesture_name))
        self.duration = duration
        self.start_time = time.time()
        self.is_moving = True

    def check_video_status(self):
        """Check if video is running, paused, or stopped"""
        # Check if video process ended
        if self.video_process and self.video_process.poll() is not None:
            self.video_stopped = True
            return 'stopped'
        
        # Check pause state via socket
        if self.mpv_socket:
            try:
                self.mpv_socket.sendall(b'{"command": ["get_property", "pause"]}\n')
                response = self.mpv_socket.recv(1024).decode('utf-8').strip()
                data = json.loads(response)
                is_paused = data.get('data', False)
                
                if is_paused and not self.video_paused:
                    # Video just paused
                    self.video_paused = True
                    self.pause_time = time.time()
                    self.get_logger().info("Video paused - robot paused")
                    return 'paused'
                    
                elif not is_paused and self.video_paused:
                    # Video just resumed
                    self.video_paused = False
                    pause_duration = time.time() - self.pause_time
                    self.total_pause_duration += pause_duration
                    # Adjust active move start_time so interpolation freezes during pause
                    if getattr(self, 'is_moving', False):
                        try:
                            self.start_time += pause_duration
                        except Exception:
                            pass
                    self.get_logger().info(f"Video resumed - robot resumed (paused for {pause_duration:.1f}s)")
                    return 'resumed'
                    
                elif is_paused:
                    return 'paused'
                else:
                    return 'playing'
                    
            except (socket.error, json.JSONDecodeError, KeyError, BlockingIOError):
                return 'playing'  # Assume playing if can't query
        
        return 'playing'

    def play_transcript(self, segments):
        # --- 1. STARTUP INTRO SEQUENCE ---
        self.get_logger().info("Playing Intro Sequence: Hello 1, 2, 3")
        
        # Define your intro sequence here
        intro_sequence = [
            ("hello1", 1.2), # (Pose Name, Duration to reach it)
            ("hello2", 0.8),
            ("hello3", 0.8),
            ("neutral", 1.0) # Reset to neutral before starting the lesson
        ]

        for pose, duration in intro_sequence:
            self.get_logger().info(f"Intro Pose: {pose}")
            self.trigger_move(pose, duration)
            # Wait for the movement to finish + a tiny pause to "hold" the pose
            time.sleep(duration + 0.3) 

        # --- 2. START VIDEO TRANSCRIPT ---
        self.get_logger().info("Intro complete. Starting transcript sync...")
        lesson_start = time.time()
        
        for seg in segments:
            # Check video status
            status = self.check_video_status()
            
            if status == 'stopped':
                self.get_logger().info("Video stopped - ending playback")
                return
                
            elif status == 'paused':
                # Wait while video is paused; when resumed continue the same segment
                self.get_logger().info("Video paused - robot waiting...")
                while True:
                    s2 = self.check_video_status()
                    if s2 == 'stopped':
                        return
                    if s2 != 'paused':
                        break
                    time.sleep(0.1)
                # Video resumed, continue processing this segment
                self.get_logger().info("Video resumed - continuing segment")
            
            # Calculate elapsed time (accounting for pauses)
            elapsed = time.time() - lesson_start - self.total_pause_duration
            wait_time = seg["start"] - elapsed - 0.2  # 200ms lead time
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Double-check video status before executing
            status = self.check_video_status()
            if status == 'stopped':
                return
            elif status == 'paused':
                continue  # Skip this segment if paused, will be picked up next loop

            gesture = get_gesture_for_text(seg["text"])
            seg_duration = seg["end"] - seg["start"]
            move_duration = max(0.5, seg_duration * 0.6)
            
            self.get_logger().info(f"Moving to {gesture} for: {seg['text']}")
            self.trigger_move(gesture, move_duration)
            
            # Wait for segment duration, but check for pause during wait
            remaining = seg_duration
            while remaining > 0:
                status = self.check_video_status()
                if status == 'stopped':
                    return
                elif status != 'paused':
                    sleep_time = min(0.05, remaining)  # Check pause status frequently
                    time.sleep(sleep_time)
                    remaining -= sleep_time
                else:
                    # Video paused: wait here until resume or stop, then continue waiting for remaining
                    while True:
                        s2 = self.check_video_status()
                        if s2 == 'stopped':
                            return
                        if s2 != 'paused':
                            break
                        time.sleep(0.1)
                    continue

        # Final return to neutral at the very end of the video
        self.trigger_move("neutral", 2.0)
def play_video(path):
    """Play video using mpv with JSON IPC for pause/play detection"""
    # Create a temporary socket file for JSON IPC
    socket_path = tempfile.mktemp(suffix='.sock', prefix='mpv_')
    
    try:
        # Start mpv with JSON IPC socket
        process = subprocess.Popen([
            "mpv", 
            path,
            f"--input-ipc-server={socket_path}"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        
        # Wait for mpv to create the socket
        time.sleep(2)
        
        # Try to connect to the socket
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(socket_path)
            sock.settimeout(0.5)  # Short timeout for non-blocking queries
            return process, sock
        except (socket.error, FileNotFoundError):
            # Socket connection failed, return process without socket
            return process, None
            
    except Exception as e:
        print(f"Error starting mpv: {e}", flush=True)
        return None, None

def main():
    with open(TRANSCRIPT_PATH) as f:
        data = json.load(f)
    
    # Extract video path and segments from transcript
    video_path = os.path.expanduser(data.get("video", "~/Downloads/English_Verbs_trimmed.mp4"))
    segments = data.get("segments", data) if isinstance(data, dict) else data

    rclpy.init()
    node = GesturePlayerNode()

    # Spin in background
    thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()

    # Start video and track the process (play_video returns (process, socket))
    proc, sock = play_video(video_path)
    node.video_process = proc
    node.mpv_socket = sock
    
    time.sleep(1.0) # Buffer for video player to open
    
    try:
        node.play_transcript(segments)
    except KeyboardInterrupt:
        pass
    finally:
        # Move to neutral, then clean up video process/socket
        try:
            node.trigger_move("neutral", 2.0)
            time.sleep(2.0)
        except Exception:
            pass

        # Close mpv socket and terminate process if present
        try:
            if node.mpv_socket:
                try:
                    node.mpv_socket.close()
                except Exception:
                    pass
            if node.video_process:
                try:
                    node.video_process.terminate()
                    node.video_process.wait(timeout=2)
                except Exception:
                    pass
        except Exception:
            pass

        rclpy.shutdown()

if __name__ == "__main__":
    main()