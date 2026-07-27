from pathlib import Path

from Modules.audio import extract_audio
from Modules.transcribe import transcribe_audio
from Modules.subtitles import build_subtitles, save_srt

VIDEO_FOLDER = Path("Video")
OUTPUT_FOLDER = Path("Output")

SUPPORTED_FORMATS = ["*.mp4", "*.mov", "*.mkv", "*.avi"]


print("=" * 50)
print(" DaVinciTranslator v1.0")
print("=" * 50)


VIDEO_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)


video_files = []

for pattern in SUPPORTED_FORMATS:
    video_files.extend(VIDEO_FOLDER.glob(pattern))


if not video_files:
    print("❌ Nessun video trovato nella cartella Video")
    input("Premi INVIO per chiudere...")
    exit()


print(f"✅ Trovati {len(video_files)} video:")

for i, video in enumerate(video_files, start=1):
    print(f"{i}. {video.name}")


choice = int(input("\nSeleziona il video: ")) - 1

video_path = video_files[choice]


print("\n🎬 Video selezionato:")
print(video_path.name)


audio = extract_audio(video_path, OUTPUT_FOLDER)

result = transcribe_audio(audio)

subtitles = build_subtitles(result)

output_srt = OUTPUT_FOLDER / "DaVinciResolve_EN.srt"

save_srt(subtitles, output_srt)

print("\n✅ Processo completato!")
