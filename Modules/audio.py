import subprocess
from pathlib import Path


def extract_audio(video_path, output_folder):
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)

    audio_path = output_folder / "audio.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(audio_path)
    ]

    print("🎵 Estrazione audio...")

    subprocess.run(command, check=True)

    print("✅ Audio creato:")
    print(audio_path)

    return audio_path