from pathlib import Path
from dataclasses import dataclass

MAX_LINE_LENGTH = 38
MIN_DURATION = 1.0
MAX_DURATION = 6.0


@dataclass
class Subtitle:
    index: int
    start: float
    end: float
    text: str


def format_timestamp(seconds: float) -> str:
    """
    Converte i secondi nel formato timestamp SRT.
    """

    milliseconds = int(seconds * 1000)

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    seconds = milliseconds // 1000
    milliseconds %= 1000

    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def build_subtitles(result: dict) -> list[Subtitle]:
    """
    Costruisce sottotitoli naturali a partire dai timestamp delle parole Whisper.

    Obiettivi:
    - massimo 76 caratteri per sottotitolo;
    - durata tra 1 e 6 secondi;
    - preferenza per circa 45-65 caratteri;
    - rispetto delle pause e della punteggiatura;
    - forte preferenza per la fine delle frasi;
    - evitare di terminare con parole grammaticalmente deboli;
    - evitare di iniziare una nuova frase nel sottotitolo precedente;
    - mantenere tutte le parole della trascrizione.
    """

    MAX_CHARS = 70
    TARGET_CHARS = 56
    MIN_WORDS = 4

    # IMPORTANTE:
    # build_subtitles() lavora sul testo INGLESE.
    weak_end = {
        "a",
        "an",
        "the",
        "of",
        "to",
        "in",
        "on",
        "at",
        "for",
        "from",
        "with",
        "by",
        "about",
        "into",
        "onto",
        "over",
        "under",
        "between",
        "through",
        "and",
        "or",
        "but",
        "as",
        "if",
        "than",
        "that",
        "which",
        "who",
        "whom",
        "this",
        "these",
        "those",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "am",
        "can",
        "could",
        "will",
        "would",
        "should",
        "may",
        "might",
    }

    weak_start = {
        "and",
        "or",
        "but",
        "so",
        "because",
        "than",
        "that",
        "which",
        "who",
        "whom",
        "to",
        "of",
        "in",
        "on",
        "at",
        "for",
        "from",
        "with",
    }

    all_words = []

    # ---------------------------------------------------------
    # 1. Recuperiamo tutte le parole con timestamp
    # ---------------------------------------------------------

    for segment in result.get("segments", []):
        for word_data in segment.get("words", []):
            word = word_data.get("word", "").strip().replace("\n", " ")

            if not word:
                continue

            start = word_data.get("start")
            end = word_data.get("end")

            if start is None or end is None:
                continue

            all_words.append(
                {
                    "word": word,
                    "start": float(start),
                    "end": float(end),
                }
            )

    if not all_words:
        return []

    # ---------------------------------------------------------
    # 2. Funzioni locali
    # ---------------------------------------------------------

    def clean_word(word: str) -> str:
        return word.lower().strip(".,!?;:\"'()[]{}")

    def text_of(words) -> str:
        return " ".join(item["word"] for item in words)

    def duration_of(words) -> float:
        if not words:
            return 0.0

        return words[-1]["end"] - words[0]["start"]

    def gap_before(index: int) -> float:
        if index <= 0 or index >= len(all_words):
            return 0.0

        return all_words[index]["start"] - all_words[index - 1]["end"]

    def is_sentence_end(word: str) -> bool:
        return word.rstrip().endswith((".", "!", "?"))

    def is_strong_punctuation(word: str) -> bool:
        return word.rstrip().endswith((".", "!", "?"))

    def is_medium_punctuation(word: str) -> bool:
        return word.rstrip().endswith((";", ":"))

    def is_weak_punctuation(word: str) -> bool:
        return word.rstrip().endswith(",")

    # ---------------------------------------------------------
    # 3. Cerca il punto migliore in cui spezzare
    # ---------------------------------------------------------

    def find_best_break(words, force=False):
        if len(words) < 2:
            return None

        best_index = None
        best_score = float("-inf")

        total_words = len(words)

        # Consideriamo soprattutto gli ultimi 12 punti possibili.
        start_index = max(1, total_words - 12)

        for i in range(start_index, total_words):
            left = words[:i]
            right = words[i:]

            if len(left) < MIN_WORDS:
                continue

            left_text = text_of(left)
            right_text = text_of(right)

            left_chars = len(left_text)
            right_chars = len(right_text)

            # Il lato sinistro non può superare il limite.
            if left_chars > MAX_CHARS:
                continue

            previous_word = clean_word(left[-1]["word"])
            next_word = clean_word(right[0]["word"])

            left_duration = duration_of(left)

            score = 0.0

            # -------------------------------------------------
            # PUNTEGGIO PUNTEGGIATURA
            # -------------------------------------------------

            if is_strong_punctuation(left[-1]["word"]):
                score += 150

            elif is_medium_punctuation(left[-1]["word"]):
                score += 80

            elif is_weak_punctuation(left[-1]["word"]):
                score += 35

            # -------------------------------------------------
            # PAROLE DEBOLI
            # -------------------------------------------------

            if previous_word in weak_end:
                score -= 120

            if next_word in weak_start:
                score -= 70

            # -------------------------------------------------
            # DURATA
            # -------------------------------------------------

            if MIN_DURATION <= left_duration <= MAX_DURATION:
                score += 30

            elif left_duration < MIN_DURATION:
                score -= 80

            elif left_duration > MAX_DURATION:
                score -= 150

            # -------------------------------------------------
            # LUNGHEZZA IDEALE
            # -------------------------------------------------

            difference = abs(TARGET_CHARS - left_chars)
            score -= difference * 0.8

            # Penalizziamo fortemente un sottotitolo
            # successivo troppo corto.
            if right_chars < 15:
                score -= 40

            # -------------------------------------------------
            # PAUSA AUDIO
            # -------------------------------------------------

            global_index = None

            # Cerchiamo la posizione della parola nel flusso
            for j in range(len(all_words) - len(words), len(all_words)):
                if (
                    all_words[j]["word"] == right[0]["word"]
                    and all_words[j]["start"] == right[0]["start"]
                ):
                    global_index = j
                    break

            if global_index is not None:
                pause = gap_before(global_index)

                if pause >= 0.50:
                    score += 70
                elif pause >= 0.30:
                    score += 40
                elif pause >= 0.20:
                    score += 20

            # -------------------------------------------------
            # EVITIAMO DI LASCIARE UNA PARTE TROPPO PICCOLA
            # -------------------------------------------------

            if len(right) == 1:
                score -= 100

            elif len(right) == 2:
                score -= 50

            # -------------------------------------------------
            # SE SIAMO OLTRE IL LIMITE, FAVORIAMO I TAGLI
            # CHE RISOLVONO IL PROBLEMA
            # -------------------------------------------------

            if force:
                if left_chars <= MAX_CHARS:
                    score += 100

                if left_duration <= MAX_DURATION:
                    score += 100

            if score > best_score:
                best_score = score
                best_index = i

        return best_index

    # ---------------------------------------------------------
    # 4. Costruzione dei sottotitoli
    # ---------------------------------------------------------

    subtitles = []

    current = []

    def flush_current():
        nonlocal current

        if not current:
            return

        subtitles.append(
            Subtitle(
                index=len(subtitles) + 1,
                start=current[0]["start"],
                end=current[-1]["end"],
                text=text_of(current),
            )
        )

        current = []

    i = 0

    while i < len(all_words):

        word = all_words[i]
        current.append(word)

        text = text_of(current)
        duration = duration_of(current)

        # -----------------------------------------------------
        # A. Fine naturale di frase
        # -----------------------------------------------------

        if is_sentence_end(word["word"]):

            # Se la frase è ragionevole, chiudiamola.
            if MIN_DURATION <= duration <= MAX_DURATION and len(text) <= MAX_CHARS:
                flush_current()
                i += 1
                continue

            # Se la frase è troppo lunga, cerchiamo un punto
            # precedente.
            if len(text) > MAX_CHARS or duration > MAX_DURATION:

                break_index = find_best_break(current, force=True)

                if break_index is not None:
                    left = current[:break_index]
                    right = current[break_index:]

                    if left:
                        current = left
                        flush_current()
                        current = right

                        # Non consumiamo nuovamente le parole.
                        i += 1
                        continue

        # -----------------------------------------------------
        # B. Controllo lunghezza
        # -----------------------------------------------------

        if len(text) > MAX_CHARS:

            # Togliamo l'ultima parola dal blocco.
            overflow = current.pop()

            if current:
                break_index = find_best_break(
                    current,
                    force=True,
                )

                if break_index is not None:

                    left = current[:break_index]
                    right = current[break_index:]

                    if left:
                        current = left
                        flush_current()
                        current = right
                    else:
                        current = [overflow]

                else:
                    # Nessun punto ideale:
                    # chiudiamo prima dell'overflow.
                    flush_current()
                    current = [overflow]

            else:
                current = [overflow]

        # -----------------------------------------------------
        # C. Controllo durata
        # -----------------------------------------------------

        duration = duration_of(current)

        if duration > MAX_DURATION:

            break_index = find_best_break(
                current,
                force=True,
            )

            if break_index is not None:

                left = current[:break_index]
                right = current[break_index:]

                if left:
                    current = left
                    flush_current()
                    current = right

            else:
                # Se non troviamo un punto ideale,
                # chiudiamo comunque il blocco.
                if len(current) > 1:
                    last = current.pop()
                    flush_current()
                    current = [last]

        # -----------------------------------------------------
        # D. Evitiamo che un nuovo periodo venga inglobato
        # -----------------------------------------------------

        if len(current) >= 2 and i + 1 < len(all_words):
            next_word = all_words[i + 1]["word"]

            if (
                is_sentence_end(current[-1]["word"])
                and duration_of(current) >= MIN_DURATION
            ):
                flush_current()

        i += 1

    # ---------------------------------------------------------
    # 5. Ultimo sottotitolo
    # ---------------------------------------------------------

    if current:
        flush_current()

    # ---------------------------------------------------------
    # 6. Normalizzazione finale
    # ---------------------------------------------------------

    normalized = []

    for subtitle in subtitles:

        if not normalized:
            normalized.append(subtitle)
            continue

        duration = subtitle.end - subtitle.start

        if duration >= MIN_DURATION:
            normalized.append(subtitle)
            continue

        previous = normalized[-1]

        combined_text = (previous.text + " " + subtitle.text).strip()

        combined_duration = subtitle.end - previous.start

        if len(combined_text) <= MAX_CHARS and combined_duration <= MAX_DURATION:
            previous.text = combined_text
            previous.end = subtitle.end
        else:
            normalized.append(subtitle)

    # ---------------------------------------------------------
    # 7. Indici finali
    # ---------------------------------------------------------

    for index, subtitle in enumerate(
        normalized,
        start=1,
    ):
        subtitle.index = index

    return normalized


def split_text(text: str) -> str:
    """
    Divide il testo di un sottotitolo in massimo 2 righe.

    Regole:
    - massimo 38 caratteri per riga;
    - massimo 2 righe;
    - preferisce una divisione equilibrata;
    - evita di iniziare una riga con parole deboli;
    - evita di terminare una riga con parole deboli;
    - preferisce punteggiatura e pause naturali;
    - non elimina mai parole.
    """

    text = " ".join(text.strip().split())

    if not text:
        return ""

    if len(text) <= MAX_LINE_LENGTH:
        return text

    words = text.split()

    if len(words) <= 1:
        return text

    # Il testo è INGLESE in questa fase.
    weak_start = {
        "a",
        "an",
        "the",
        "of",
        "to",
        "in",
        "on",
        "at",
        "for",
        "from",
        "with",
        "by",
        "and",
        "or",
        "but",
        "as",
        "if",
        "than",
        "that",
        "which",
        "who",
        "whom",
        "so",
    }

    weak_end = {
        "a",
        "an",
        "the",
        "of",
        "to",
        "in",
        "on",
        "at",
        "for",
        "from",
        "with",
        "by",
        "and",
        "or",
        "but",
        "as",
        "if",
        "than",
        "that",
        "which",
        "who",
        "whom",
    }

    best_split = None
    best_score = float("-inf")

    for i in range(1, len(words)):

        line1 = " ".join(words[:i])
        line2 = " ".join(words[i:])

        len1 = len(line1)
        len2 = len(line2)

        # Entrambe le righe devono rispettare il limite.
        if len1 > MAX_LINE_LENGTH:
            continue

        if len2 > MAX_LINE_LENGTH:
            continue

        previous = words[i - 1].lower().strip(".,!?;:\"'()[]{}")

        current = words[i].lower().strip(".,!?;:\"'()[]{}")

        score = 0.0

        # -----------------------------------------------------
        # 1. EQUILIBRIO DELLE DUE RIGHE
        # -----------------------------------------------------

        difference = abs(len1 - len2)

        score -= difference * 1.5

        # -----------------------------------------------------
        # 2. PUNTEGGIATURA
        # -----------------------------------------------------

        if words[i - 1].rstrip().endswith((".", "!", "?")):
            score += 100

        elif words[i - 1].rstrip().endswith((";", ":")):
            score += 60

        elif words[i - 1].rstrip().endswith(","):
            score += 30

        # -----------------------------------------------------
        # 3. EVITIAMO PAROLE DEBOLI A FINE PRIMA RIGA
        # -----------------------------------------------------

        if previous in weak_end:
            score -= 100

        # -----------------------------------------------------
        # 4. EVITIAMO PAROLE DEBOLI A INIZIO SECONDA RIGA
        # -----------------------------------------------------

        if current in weak_start:
            score -= 100

        # -----------------------------------------------------
        # 5. EVITIAMO RIGHE TROPPO CORTE
        # -----------------------------------------------------

        if len1 < 15:
            score -= 25

        if len2 < 15:
            score -= 25

        # -----------------------------------------------------
        # 6. PREFERIAMO RIEMPIRE BENE LE DUE RIGHE
        # -----------------------------------------------------

        if len1 >= 30:
            score += 10

        if len2 >= 30:
            score += 10

        # -----------------------------------------------------
        # 7. PREFERIAMO UNA DIVISIONE VICINA ALLA META
        # -----------------------------------------------------

        total_length = len(text)

        ideal = total_length / 2

        score -= abs(len1 - ideal) * 0.5

        # -----------------------------------------------------
        # MIGLIOR CANDIDATO
        # -----------------------------------------------------

        if score > best_score:
            best_score = score
            best_split = i

    # ---------------------------------------------------------
    # DIVISIONE TROVATA
    # ---------------------------------------------------------

    if best_split is not None:

        line1 = " ".join(words[:best_split])
        line2 = " ".join(words[best_split:])

        return f"{line1}\n{line2}"

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    # Normalmente non dovrebbe essere raggiunto perché
    # build_subtitles() ora utilizza un limite più prudente.
    #
    # Non eliminiamo mai parole.

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
