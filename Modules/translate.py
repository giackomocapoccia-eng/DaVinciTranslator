from pathlib import Path
from deep_translator import GoogleTranslator


def translate_text(text: str, source="en", target="it") -> str:
    """
    Translate a single text string.
    """

    translator = GoogleTranslator(source=source, target=target)

    return translator.translate(text)


def translate_srt(input_file: Path, output_file: Path, source="en", target="it"):
    """
    Translate an SRT file preserving numbering and timestamps.
    """

    translator = GoogleTranslator(source=source, target=target)

    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    translated = []

    i = 0

    while i < len(lines):

        line = lines[i]

        if line.strip().isdigit():

            number = line
            timestamp = lines[i + 1]
            text = lines[i + 2].strip()

            text = lines[i + 2].strip()

            try:
                translated_text = translator.translate(text)

            except Exception:
                print(f"⚠ Errore nella traduzione: {text}")
                translated_text = text

            translated.append(number)

            translated.append(number)
            translated.append(timestamp)
            translated.append(translated_text + "\n\n")

            i += 4

        else:
            i += 1

    with open(output_file, "w", encoding="utf-8") as file:
        file.writelines(translated)

    print(f"✅ Traduzione completata: {output_file}")
