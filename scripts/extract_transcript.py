#!/usr/bin/env python3
from faster_whisper import WhisperModel
import json
import os

VIDEO_PATH = os.path.expanduser("~/Downloads/English_Verbs_trimmed.mp4")
OUTPUT_PATH = os.path.expanduser("~/ros2_ws/src/humanoid_robot_description/scripts/transcript.json")

def extract_transcript():
    if not os.path.exists(VIDEO_PATH):
        print(f"File not found: {VIDEO_PATH}")
        return

    # Use CPU/Int8 for speed on standard computers
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print("Transcribing video content...")
    segments, _ = model.transcribe(VIDEO_PATH, beam_size=5)

    transcript = []
    for s in segments:
        entry = {
            "start": round(s.start, 2),
            "end": round(s.end, 2),
            "text": s.text.strip()
        }
        transcript.append(entry)
        print(f"[{entry['start']}s]: {entry['text']}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(transcript, f, indent=2)
    print(f"Done! Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    extract_transcript()