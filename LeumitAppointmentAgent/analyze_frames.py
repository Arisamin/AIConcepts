"""Analyze video frames to understand the booking flow."""
import os
from PIL import Image
import json

frames_dir = "video_frames"
output = []

# Analyze key frames
key_frames = [0, 5, 10, 15, 20, 30, 40, 50, 75, 100, 125, 150]

for idx in key_frames:
    frame_path = os.path.join(frames_dir, f"frame_{idx:03d}.png")
    if os.path.exists(frame_path):
        img = Image.open(frame_path)
        time_sec = idx * 2  # 2 seconds per frame
        info = {
            "frame": idx,
            "time": f"{time_sec}s",
            "file": f"frame_{idx:03d}.png",
            "size": img.size
        }
        output.append(info)
        print(f"Frame {idx:3d} (t={time_sec:3d}s): {frame_path}")

print(f"\nAnalyzed {len(output)} key frames")
print("\nTo view frames, open these files in the video_frames directory:")
for info in output:
    print(f"  {info['file']} at t={info['time']}")
