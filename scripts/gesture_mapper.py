#!/usr/bin/env python3
import math

JOINT_NAMES = [
    "body_to_arm_joint_right", "shoulder_yaw_joint_right", "shoulder_pitch_joint_right", 
    "elbow_joint_right", "palm_to_f1_right", "palm_to_f2_right", "palm_to_f3_right",
    "body_to_arm_joint_left", "shoulder_yaw_joint_left", "shoulder_pitch_joint_left", 
    "elbow_joint_left", "palm_to_f1_left", "palm_to_f2_left", "palm_to_f3_left",
    "face_yaw_joint",
]

GESTURES = {
    "hello1": [[-0.059, -0.287, -1.570, 0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0], [0.1]],
    "hello2": [[-0.059, -0.287, -0.999, 0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0], [0.-1]],
    "hello3": [[-0.059, -0.287, -1.570, 0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "neutral": [[1.434, -0.829, 0.910, 0.0, 0.0, 0.0, 0.0], [1.434, 0.819, 0.738, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "point_right": [[0.008, -0.605, -0.482, 0.0, 0.0, 0.0, 0.0], [1.3391, 0.6088, 1.078, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "point_left": [[1.4776, -0.5547, 0.910, 0.0, 0.0, 0.0, 0.0], [0.008, -0.718, -0.482, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "both_up": [[0.008, -0.605, -0.482, 0.0, 0.0, 0.0, 0.0], [0.008, -0.597, -0.482, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "emphasize": [[-1.570, -1.591, -0.678, 0.0, 0.0, 0.0, 0.0], [-1.570, 1.870, -1.214, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "open_arms": [[-0.908, -1.461, -0.701, 0.0, 0.0, 0.0, 0.0], [-0.636, 1.546, -1.044, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "think": [[-1.57, -1.87, -1.1818, 0.0, 0.0, 0.0, 0.0], [-1.57, 1.57, -1.57, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "count": [[-0.6465, -1.87, -1.1818, 0.0, 0.0, 0.0, 0.0], [1.57, 0.71, 0.4618, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "wave_right": [[-1.57, -1.87, -0.1141, 0.0, 0.0, 0.0, 0.0], [-1.1082, 0.5582, -0.6465, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "running": [[0.721, 1.012, 0.785, 0.0, 0.0, 0.0, 0.0], [-1.315, -0.172, 0.229, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "playing": [[-1.1082, -1.87, -0.1141, 0.0, 0.0, 0.0, 0.0], [-1.502, 0.5582, -0.6465, 0.0, 0.0, 0.0, 0.0], [0.0]],
    # Added teacher poses directly into GESTURES
    "explaining_idea": [[-0.823, -1.052, -0.500, 0.0, 0.0, 0.0, 0.0], [-0.806, 1.203, -0.569, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "small_detail": [[1.2, -0.4, 0.5, 0.0, 0.0, 0.0, 0.0], [1.3, 0.6, 0.18, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "compare_this": [[0.0, -1.5, 0.0, 0.0, 0.0, 0.0, 0.0], [1.3391, 0.6088, 0.1847, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "compare_that": [[1.4776, -0.5547, 0.1285, 0.0, 0.0, 0.0, 0.0], [0.0, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "settle_down": [[1.383, 1.012, 0.178, 0.0, 0.0, 0.0, 0.0], [1.383, -1.021, 0.161, 0.0, 0.0, 0.0, 0.0], [0.0]],
    "reading": [[-0.059, -0.287, -1.570, 0.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.8, 0.0, 0.0, 0.0, 0.0], [0.1]],
    "jumping": [[-1.383, 0.194, -0.197, 0.0, 0.0, 0.0, 0.0], [-1.383, -0.111, -0.212, 0.0, 0.0, 0.0, 0.0], [0.0]]
}

KEYWORD_GESTURES = {
    "this": "point_right", "that": "point_left", "look": "point_right",
    "important": "emphasize", "remember": "emphasize", "first": "count",
    "example": "open_arms", "think": "think", "understand": "think",
    "verb": "explaining_idea", "past": "point_left", "future": "point_right",
    "hello": "wave_right", "run": "running" , "today": "open_arms", "lesson": "explaining_idea","sits": "settle_down","read":"reading","jump":"jumping"
}

def get_gesture_for_text(text):
    text_lower = text.lower()
    for word in text_lower.split():
        clean = word.strip(".,!?;:'\"")
        if clean in KEYWORD_GESTURES:
            return KEYWORD_GESTURES[clean]
    return "neutral"

def get_joint_angles(gesture_name):
    raw = GESTURES.get(gesture_name, GESTURES["neutral"])
    return raw[0] + raw[1] + raw[2]
