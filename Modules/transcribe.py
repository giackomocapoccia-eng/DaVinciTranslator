from pathlib import Path
import whisper


def transcribe_audio(audio_path: Path, model_name: str = "base") -> dict:
    """
    Transcribes an audio file using OpenAI Whisper.

    Args:
        audio_path: Path to the WAV file.
        model_name: Whisper model to use.

    Returns:
        Whisper transcription result.
    """

    print(f"🧠 Loading Whisper model: {model_name}")

    model = whisper.load_model(model_name)

    print("🎤 Transcribing audio...")

    result = model.transcribe(str(audio_path))

    print("✅ Transcription completed.")

    return result