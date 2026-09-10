
from pathlib import Path

SRT_FILE = Path("Output/DaVinciResolve_EN.srt")

MAX_LINE_LENGTH = 38
MAX_CHARS = 76
MIN_DURATION = 1.0
MAX_DURATION = 6.0


def timestamp_to_seconds(timestamp: str) -> float:
    hours, minutes, seconds = timestamp.split(":")
    seconds, milliseconds = seconds.split(",")

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000
    )


def analyze_srt():
    if not SRT_FILE.exists():
        print("ERRORE: file SRT non trovato:")
        print(SRT_FILE.resolve())
        return

    text = SRT_FILE.read_text(encoding="utf-8").strip()
    blocks = text.split("\n\n")

    total = 0

    over_76 = []
    long_lines = []
    under_1 = []
    over_6 = []

    longest_text = ""
    longest_line = ""

    shortest_duration = None
    longest_duration = 0

    # ---------------------------------------------------------
    # ANALISI
    # ---------------------------------------------------------

    for block in blocks:

        lines = block.splitlines()

        if len(lines) < 3:
            continue

        index = lines[0].strip()
        timestamp = lines[1].strip()

        subtitle_lines = lines[2:]
        subtitle_text = " ".join(
            line.strip() for line in subtitle_lines
        )

        try:
            start_text, end_text = timestamp.split(" --> ")

            start = timestamp_to_seconds(start_text)
            end = timestamp_to_seconds(end_text)

        except ValueError:
            print(f"ERRORE nel blocco {index}:")
            print(block)
            print()
            continue

        duration = end - start

        total += 1

        # -----------------------------------------------------
        # TESTO OLTRE 76 CARATTERI
        # -----------------------------------------------------

        if len(subtitle_text) > MAX_CHARS:
            over_76.append(
                {
                    "index": index,
                    "timestamp": timestamp,
                    "duration": duration,
                    "text": subtitle_text,
                    "chars": len(subtitle_text),
                }
            )

        # -----------------------------------------------------
        # RIGHE OLTRE 38 CARATTERI
        # -----------------------------------------------------

        for line_number, line in enumerate(
            subtitle_lines,
            start=1,
        ):

            line_length = len(line)

            if line_length > MAX_LINE_LENGTH:
                long_lines.append(
                    {
                        "index": index,
                        "timestamp": timestamp,
                        "duration": duration,
                        "line_number": line_number,
                        "line": line,
                        "chars": line_length,
                        "text": subtitle_text,
                    }
                )

        # -----------------------------------------------------
        # DURATA SOTTO 1 SECONDO
        # -----------------------------------------------------

        if duration < MIN_DURATION:
            under_1.append(
                {
                    "index": index,
                    "timestamp": timestamp,
                    "duration": duration,
                    "text": subtitle_text,
                    "chars": len(subtitle_text),
                }
            )

        # -----------------------------------------------------
        # DURATA OLTRE 6 SECONDI
        # -----------------------------------------------------

        if duration > MAX_DURATION:
            over_6.append(
                {
                    "index": index,
                    "timestamp": timestamp,
                    "duration": duration,
                    "text": subtitle_text,
                    "chars": len(subtitle_text),
                }
            )

        # -----------------------------------------------------
        # TESTO PIÙ LUNGO
        # -----------------------------------------------------

        if len(subtitle_text) > len(longest_text):
            longest_text = subtitle_text

        # -----------------------------------------------------
        # RIGA PIÙ LUNGA
        # -----------------------------------------------------

        for line in subtitle_lines:
            if len(line) > len(longest_line):
                longest_line = line

        # -----------------------------------------------------
        # DURATA MINIMA / MASSIMA
        # -----------------------------------------------------

        if (
            shortest_duration is None
            or duration < shortest_duration
        ):
            shortest_duration = duration

        if duration > longest_duration:
            longest_duration = duration

    # ---------------------------------------------------------
    # RIEPILOGO
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print(" ANALISI DaVinciResolve_EN.srt")
    print("=" * 70)
    print()

    print(f"Sottotitoli totali: {total}")
    print()

    print(
        f"Sottotitoli oltre {MAX_CHARS} caratteri: "
        f"{len(over_76)}"
    )

    print(
        f"Righe oltre {MAX_LINE_LENGTH} caratteri: "
        f"{len(long_lines)}"
    )

    print(
        f"Sottotitoli sotto {MIN_DURATION} secondo: "
        f"{len(under_1)}"
    )

    print(
        f"Sottotitoli oltre {MAX_DURATION} secondi: "
        f"{len(over_6)}"
    )

    print()

    if shortest_duration is not None:
        print(
            f"Durata minima: "
            f"{shortest_duration:.2f} secondi"
        )

    print(
        f"Durata massima: "
        f"{longest_duration:.2f} secondi"
    )

    print()

    print("TESTO PIÙ LUNGO:")
    print(longest_text)

    print()

    print("RIGA PIÙ LUNGA:")
    print(longest_line)

    # =========================================================
    # DETTAGLIO PROBLEMI
    # =========================================================

    # ---------------------------------------------------------
    # 1. SOTTOTITOLI OLTRE 76 CARATTERI
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print(
        f"1. SOTTOTITOLI OLTRE {MAX_CHARS} CARATTERI"
    )
    print("=" * 70)

    if not over_76:
        print("Nessun problema.")
    else:
        for item in over_76:
            print()
            print(f"ID       : {item['index']}")
            print(f"Timestamp: {item['timestamp']}")
            print(f"Durata   : {item['duration']:.2f} s")
            print(f"Caratteri: {item['chars']}")
            print(f"Testo    : {item['text']}")

    # ---------------------------------------------------------
    # 2. RIGHE OLTRE 38 CARATTERI
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print(
        f"2. RIGHE OLTRE {MAX_LINE_LENGTH} CARATTERI"
    )
    print("=" * 70)

    if not long_lines:
        print("Nessun problema.")
    else:
        for item in long_lines:
            print()
            print(f"ID       : {item['index']}")
            print(f"Timestamp: {item['timestamp']}")
            print(f"Durata   : {item['duration']:.2f} s")
            print(f"Riga     : {item['line_number']}")
            print(f"Caratteri: {item['chars']}")
            print(f"Riga     : {item['line']}")
            print(f"Testo    : {item['text']}")

    # ---------------------------------------------------------
    # 3. SOTTOTITOLI SOTTO 1 SECONDO
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print(
        f"3. SOTTOTITOLI SOTTO {MIN_DURATION} SECONDO"
    )
    print("=" * 70)

    if not under_1:
        print("Nessun problema.")
    else:
        for item in under_1:
            print()
            print(f"ID       : {item['index']}")
            print(f"Timestamp: {item['timestamp']}")
            print(f"Durata   : {item['duration']:.2f} s")
            print(f"Caratteri: {item['chars']}")
            print(f"Testo    : {item['text']}")

    # ---------------------------------------------------------
    # 4. SOTTOTITOLI OLTRE 6 SECONDI
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print(
        f"4. SOTTOTITOLI OLTRE {MAX_DURATION} SECONDI"
    )
    print("=" * 70)

    if not over_6:
        print("Nessun problema.")
    else:
        for item in over_6:
            print()
            print(f"ID       : {item['index']}")
            print(f"Timestamp: {item['timestamp']}")
            print(f"Durata   : {item['duration']:.2f} s")
            print(f"Caratteri: {item['chars']}")
            print(f"Testo    : {item['text']}")

    print()
    print("=" * 70)
    print(" FINE ANALISI")
    print("=" * 70)
    print()


if __name__ == "__main__":
    analyze_srt()

