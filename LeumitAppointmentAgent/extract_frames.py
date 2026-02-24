import cv2
import os

video_path = r'C:\Users\smogb\Videos\Captures\Main 2026-02-22 09-44-41.mp4'
output_dir = 'video_frames'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

cap = cv2.VideoCapture(video_path)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)

print(f'Video: {total_frames} frames, {fps:.0f} FPS, {total_frames/fps:.1f} seconds')
print()

# Extract every 2 seconds
frame_interval = int(fps * 2)
frame_count = 0
saved_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    if frame_count % frame_interval == 0:
        resized = cv2.resize(frame, (1280, 720))
        filename = os.path.join(output_dir, f'frame_{saved_count:03d}.png')
        cv2.imwrite(filename, resized)
        time_sec = frame_count / fps
        print(f'Frame {saved_count:02d} (t={time_sec:5.1f}s): {filename}')
        saved_count += 1
    
    frame_count += 1

cap.release()
print()
print(f'✓ Extracted {saved_count} frames to {output_dir}/')
