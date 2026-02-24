"""Extract and transcribe audio from video using moviepy and Google Speech Recognition."""
import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import sys

video_path = r'C:\Users\smogb\Videos\Captures\Main 2026-02-22 09-44-41.mp4'

print("="*70)
print("VIDEO TRANSCRIPTION TOOL")
print("="*70)
print(f"Video: {video_path}")
print()

# Load video
print("Loading video...")
try:
    clip = VideoFileClip(video_path)
    print(f"✓ Video loaded: {clip.duration:.1f} seconds")
except Exception as e:
    print(f"✗ Error loading video: {e}")
    sys.exit(1)

# Extract audio
print("Extracting audio...")
try:
    audio = clip.audio
    if audio is None:
        print("✗ No audio track found in video")
        sys.exit(1)
    
    audio_path = "temp_audio.wav"
    print(f"  Writing to {audio_path}...")
    audio.write_audiofile(audio_path)
    print(f"✓ Audio extracted")
except Exception as e:
    print(f"✗ Error extracting audio: {e}")
    sys.exit(1)
finally:
    clip.close()

# Transcribe
print()
print("Transcribing audio...")
print("  (Sending to Google Speech Recognition - may take 1-2 minutes)")
recognizer = sr.Recognizer()

try:
    with sr.AudioFile(audio_path) as source:
        print("  Reading audio file...")
        audio_data = recognizer.record(source)
    
    print("  Recognizing speech...")
    text = recognizer.recognize_google(audio_data)
    
    print()
    print("="*70)
    print("TRANSCRIPTION RESULT:")
    print("="*70)
    print(text)
    print("="*70)
    
    # Save transcription
    with open("video_narration.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    print()
    print(f"✓ Transcription saved to video_narration.txt")
    
except sr.UnknownValueError:
    print("✗ Could not understand the audio")
    sys.exit(1)
except sr.RequestError as e:
    print(f"✗ Speech recognition error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
finally:
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print(f"✓ Cleaned up temp files")
