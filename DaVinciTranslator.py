from pathlib import Path

from Modules.audio import extract_audio
from Modules.transcribe import transcribe_audio

VIDEO_FOLDER = Path("Video")
OUTPUT_FOLDER = Path("Output")

SUPPORTED_FORMATS = [
    "*.mp4",
    "*.mov",
    "*.mkv",
    "*.avi"
]

print("=" * 50)
print(" DaVinciTranslator v1.0")
print("=" * 50)

video_files = []

for pattern in SUPPORTED_FORMATS:
    video_files.extend(VIDEO_FOLDER.glob(pattern))

if not video_files:
    print("❌ Nessun video trovato.")
    exit()

video = video_files[0]

print(f"🎬 Video trovato: {video.name}")

audio = extract_audio(video, OUTPUT_FOLDER)

# Trascrizione con Whisper
result = transcribe_audio(audio)

print("\n==============================")
print("TESTO TRASCRITTO")
print("==============================\n")

print(result["text"])