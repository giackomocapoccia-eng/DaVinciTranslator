from pathlib import Path
from dataclasses import dataclass

MAX_LINE_LENGTH = 38
MAX_LINES = 2
MIN_DURATION = 1.0
MAX_DURATION = 6.0


@dataclass
class Subtitle:
    index: int
    start: float
    end: float
    text: str


def format_timestamp(seconds):
    milliseconds = int(seconds * 1000)

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    seconds = milliseconds // 1000
    milliseconds %= 1000

    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def wrap_text(text, max_chars=42):

    words = text.split()

    lines = []
    current = ""

    for word in words:

        if len(current) + len(word) + 1 <= max_chars:
            current += " " + word

        else:
            lines.append(current.strip())
            current = word

    if current:
        lines.append(current.strip())

    return "\n".join(lines)


def build_subtitles(result: dict) -> list[Subtitle]:
    """
    Build a list of Subtitle objects from Whisper word timestamps.
    """

    subtitles = []
    subtitle_index = 1

    for segment in result["segments"]:

        if "words" not in segment:
            continue

        words = segment["words"]

        current_words = []
        start_time = None
        last_end = None

        for word_data in words:

            word = word_data["word"].strip().replace("\n", " ")

            if not word:
                continue

            if start_time is None:
                start_time = word_data["start"]

            current_words.append(word)
            last_end = word_data["end"]

            text = " ".join(current_words)

            duration = last_end - start_time

            should_close = (
                len(text) >= MAX_LINE_LENGTH
                or duration >= MAX_DURATION
                or word.endswith((".", "!", "?"))
            )

            if should_close:

                if duration < MIN_DURATION:
                    continue

                subtitles.append(
                    Subtitle(
                        index=subtitle_index,
                        start=start_time,
                        end=last_end,
                        text=text,
                    )
                )

                subtitle_index += 1

                current_words = []
                start_time = None

        if current_words:

            subtitles.append(
                Subtitle(
                    index=subtitle_index,
                    start=start_time,
                    end=last_end,
                    text=" ".join(current_words),
                )
            )

            subtitle_index += 1

    return subtitles


def split_text(text: str) -> str:
    """
    Split subtitle text into two balanced lines.
    """

    if len(text) <= MAX_LINE_LENGTH:
        return text

    words = text.split()

    best_split = 0
    smallest_difference = float("inf")

    for i in range(1, len(words)):

        line1 = " ".join(words[:i])
        line2 = " ".join(words[i:])

        difference = abs(len(line1) - len(line2))

        if (
            len(line1) <= MAX_LINE_LENGTH
            and len(line2) <= MAX_LINE_LENGTH
            and difference < smallest_difference
        ):
            smallest_difference = difference
            best_split = i

    if best_split:
        return " ".join(words[:best_split]) + "\n" + " ".join(words[best_split:])

    return text


def save_srt(subtitles: list[Subtitle], output_file: Path):
    """
    Save Subtitle objects to an SRT file.
    """

    with open(output_file, "w", encoding="utf-8") as file:

        for subtitle in subtitles:

            file.write(f"{subtitle.index}\n")

            file.write(
                f"{format_timestamp(subtitle.start)} --> "
                f"{format_timestamp(subtitle.end)}\n"
            )

            file.write(split_text(subtitle.text))
            file.write("\n\n")

    print(f"✅ SRT creato: {output_file}")
