import subprocess
from pathlib import Path


def extract_audio(video_path: Path, output_folder: Path) -> Path:
    """
    Estrae l'audio da un video utilizzando FFmpeg.

    Args:
        video_path: percorso del file video.
        output_folder: cartella in cui salvare l'audio.

    Returns:
        Path del file audio WAV creato.
    """

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

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
        str(audio_path),
    ]

    print("🎵 Estrazione audio...")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as error:
        print(f"❌ Errore durante l'estrazione dell'audio: {error}")
        raise

    print(f"✅ Audio creato: {audio_path}")

    return audio_path
