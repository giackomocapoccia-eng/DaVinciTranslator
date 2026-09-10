from pathlib import Path

from Modules.audio import extract_audio
from Modules.transcribe import transcribe_audio
from Modules.subtitles import build_subtitles, save_srt
from Modules.translate import translate_srt

VIDEO_FOLDER = Path("Video")
OUTPUT_FOLDER = Path("Output")

SUPPORTED_FORMATS = (
    "*.mp4",
    "*.mov",
    "*.mkv",
    "*.avi",
)


def find_videos() -> list[Path]:
    """
    Cerca tutti i video supportati nella cartella Video.
    """
    video_files = []

    for pattern in SUPPORTED_FORMATS:
        video_files.extend(VIDEO_FOLDER.glob(pattern))

    video_files.sort()

    return video_files


def select_video(video_files: list[Path]) -> Path:
    """
    Mostra la lista dei video e restituisce quello scelto.
    """
    print(f"✅ Trovati {len(video_files)} video:")

    for i, video in enumerate(video_files, start=1):
        print(f"{i}. {video.name}")

    while True:
        try:
            choice = int(input("\nSeleziona il video: ")) - 1

            if 0 <= choice < len(video_files):
                return video_files[choice]

            print("❌ Numero non valido.")

        except ValueError:
            print("❌ Inserisci un numero.")


def main():
    """
    Punto di ingresso del programma.
    """
    print("=" * 50)
    print(" DaVinciTranslator - Development Version")
    print("=" * 50)

    VIDEO_FOLDER.mkdir(exist_ok=True)
    OUTPUT_FOLDER.mkdir(exist_ok=True)

    video_files = find_videos()

    if not video_files:
        print("❌ Nessun video trovato nella cartella Video")
        input("Premi INVIO per chiudere...")
        return

    video_path = select_video(video_files)

    print("\n🎬 Video selezionato:")
    print(video_path.name)

    audio = extract_audio(video_path, OUTPUT_FOLDER)

    result = transcribe_audio(audio)

    subtitles = build_subtitles(result)

    video_name = video_path.stem

    output_srt = OUTPUT_FOLDER / f"{video_name}_EN.srt"

    save_srt(subtitles, output_srt)

    output_it = OUTPUT_FOLDER / f"{video_name}_IT.srt"

    translate_srt(output_srt, output_it)

    print("\n✅ Processo completato!")


if __name__ == "__main__":
    main()
