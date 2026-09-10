from pathlib import Path
from copy import deepcopy
import re

from deep_translator import GoogleTranslator

from Modules.subtitles import split_text

# ============================================================
# TERMINOLOGIA DAVINCI RESOLVE
# ============================================================

DAVINCI_PHRASES = {
    "sequenza temporale": "timeline",
    "sequenza temporale esistente": "timeline esistente",
    "gestore del progetto": "Project Manager",
    "pool multimediale": "Media Pool",
    "montaggio in DaVinci Resolve": "editing in DaVinci Resolve",
    "editing in DaVinci Resolve": "editing in DaVinci Resolve",
}

DAVINCI_TERMS = {
    "Risolvi": "Resolve",
    "risolvi": "Resolve",
    "Timeline": "timeline",
    "Timeline.": "timeline.",
    "Clip": "clip",
    "Clip.": "clip.",
    "Bin": "bin",
    "Bin.": "bin.",
}


# ============================================================
# PULIZIA TESTO
# ============================================================


def _clean_translation(text: str) -> str:
    """
    Pulisce una traduzione mantenendo il contenuto.

    Elimina:
    - spazi multipli;
    - spazi all'inizio/fine;
    - ritorni a capo inutili.
    """

    if not text:
        return ""

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# CORREZIONE TERMINOLOGIA DAVINCI
# ============================================================


def correct_davinci_terms(text: str) -> str:
    """
    Corregge la terminologia tipica di DaVinci Resolve.

    Le frasi vengono corrette prima dei singoli termini.
    """

    if not text:
        return ""

    result = text

    # --------------------------------------------------------
    # Prima correggiamo le frasi complete.
    # --------------------------------------------------------

    for wrong, correct in DAVINCI_PHRASES.items():

        result = re.sub(
            re.escape(wrong),
            correct,
            result,
            flags=re.IGNORECASE,
        )

    # --------------------------------------------------------
    # Poi correggiamo i singoli termini.
    # --------------------------------------------------------

    for wrong, correct in DAVINCI_TERMS.items():

        result = re.sub(
            rf"\b{re.escape(wrong)}\b",
            correct,
            result,
            flags=re.IGNORECASE,
        )

    return result


# ============================================================
# TRADUZIONE DI UN TESTO
# ============================================================


def translate_text(
    text: str,
    source: str = "en",
    target: str = "it",
) -> str:
    """
    Traduce un testo utilizzando GoogleTranslator.

    In caso di errore restituisce il testo originale,
    evitando di interrompere l'intero programma.
    """

    text = _clean_translation(text)

    if not text:
        return ""

    try:

        translator = GoogleTranslator(
            source=source,
            target=target,
        )

        translated = translator.translate(text)

        if not translated:
            return text

        return _clean_translation(translated)

    except Exception as error:

        print(f"⚠️ Errore traduzione: {error}")

        return text


# ============================================================
# PAROLE
# ============================================================


def _word_list(text: str) -> list[str]:
    """
    Restituisce la lista delle parole.

    La punteggiatura rimane attaccata alla parola precedente.
    """

    text = _clean_translation(text)

    if not text:
        return []

    return text.split()


# ============================================================
# CONTEGGIO PAROLE ORIGINALI
# ============================================================


def _source_word_count(
    subtitle: dict,
) -> int:
    """
    Conta le parole del sottotitolo originale.
    """

    text = subtitle.get("text", "")

    return len(_word_list(text))


# ============================================================
# PESI ORIGINALI
# ============================================================


def _source_weights(
    group: list[dict],
) -> list[float]:
    """
    Calcola il peso relativo dei sottotitoli originali.

    Il numero di parole viene utilizzato come indicazione
    della quantità di contenuto presente in ogni sottotitolo.
    """

    if not group:
        return []

    counts = [_source_word_count(subtitle) for subtitle in group]

    total = sum(counts)

    if total <= 0:

        return [1.0 / len(group) for _ in group]

    return [count / total for count in counts]


# ============================================================
# CONFINI IDEALI
# ============================================================


def _cumulative_boundaries(
    words: list[str],
    weights: list[float],
) -> list[int]:
    """
    Calcola i confini ideali basandosi sui pesi originali.

    Questi confini servono come punto di partenza
    per l'algoritmo grammaticale.
    """

    if not words or not weights:
        return []

    total_words = len(words)

    boundaries = []

    accumulated = 0.0

    for weight in weights[:-1]:

        accumulated += weight

        position = round(accumulated * total_words)

        boundaries.append(position)

    return boundaries


# ============================================================
# PENALITÀ DEL BLOCCO
# ============================================================


def _chunk_penalty(
    words: list[str],
    start: int,
    end: int,
    expected: float,
) -> float:
    """
    Calcola quanto un blocco si allontana dalla quantità
    ideale di parole.

    Penalizza anche blocchi estremamente piccoli.
    """

    count = end - start

    if count <= 0:
        return 10000.0

    difference = abs(count - expected)

    penalty = difference * 3.0

    # --------------------------------------------------------
    # Penalità per blocchi troppo piccoli.
    # --------------------------------------------------------

    if count == 1:
        penalty += 8.0

    elif count == 2:
        penalty += 3.0

    return penalty


# ============================================================
# DISTANZA DAL CONFINE IDEALE
# ============================================================


def _boundary_distance(
    position: int,
    ideal: int,
) -> float:
    """
    Penalizza la distanza dal confine ideale.
    """

    return abs(position - ideal) * 1.5


# ============================================================
# PENALITÀ GRAMMATICALE DEL CONFINE
# ============================================================


def _boundary_penalty(
    words: list[str],
    position: int,
) -> float:
    """
    Penalizza divisioni grammaticalmente poco naturali.
    """

    if position <= 0 or position >= len(words):
        return 10000.0

    previous = words[position - 1].lower().strip(".,!?;:")

    current = words[position].lower().strip(".,!?;:")

    penalty = 0.0

    weak_end = {
        "a",
        "ad",
        "al",
        "alla",
        "allo",
        "ai",
        "agli",
        "alle",
        "da",
        "dal",
        "dalla",
        "dallo",
        "dai",
        "dagli",
        "dalle",
        "di",
        "del",
        "della",
        "dello",
        "dei",
        "degli",
        "delle",
        "in",
        "nel",
        "nella",
        "nello",
        "nei",
        "negli",
        "nelle",
        "con",
        "su",
        "sul",
        "sulla",
        "sullo",
        "sui",
        "sugli",
        "sulle",
        "per",
        "tra",
        "fra",
        "e",
        "ed",
        "o",
        "oppure",
        "che",
        "ma",
        "però",
        "quindi",
    }

    weak_start = weak_end

    # --------------------------------------------------------
    # Non chiudere dopo una preposizione/congiunzione.
    # --------------------------------------------------------

    if previous in weak_end:
        penalty += 80.0

    # --------------------------------------------------------
    # Non iniziare una riga/blocco con parole deboli.
    # --------------------------------------------------------

    if current in weak_start:
        penalty += 80.0

    # --------------------------------------------------------
    # Articolo + aggettivo + sostantivo.
    #
    # Evitiamo di spezzare:
    #
    # "la nuova | timeline"
    # --------------------------------------------------------

    if position >= 2:

        before_previous = words[position - 2].lower().strip(".,!?;:")

        if before_previous in {
            "il",
            "lo",
            "la",
            "i",
            "gli",
            "le",
            "un",
            "uno",
            "una",
        }:

            penalty += 30.0

    # --------------------------------------------------------
    # Punteggiatura forte = ottimo punto di divisione.
    # --------------------------------------------------------

    if words[position - 1].endswith((".", "!", "?")):

        penalty -= 100.0

    elif words[position - 1].endswith((",", ";", ":")):

        penalty -= 35.0

    # --------------------------------------------------------
    # Connettori naturali.
    # --------------------------------------------------------

    natural_breaks = {
        "ma",
        "però",
        "quindi",
        "perché",
        "mentre",
        "quando",
        "se",
        "poi",
        "ora",
        "adesso",
        "inoltre",
        "infatti",
        "tuttavia",
    }

    if current in natural_breaks:
        penalty -= 20.0

    return penalty


# ============================================================
# SCELTA DEI CONFINI
# ============================================================


def _choose_boundaries(
    words: list[str],
    weights: list[float],
    ideal_boundaries: list[int],
) -> list[int]:
    """
    Cerca contemporaneamente tutti i confini migliori.

    Considera:
    - quantità relativa del testo;
    - distanza dai confini ideali;
    - grammatica;
    - punteggiatura;
    - dimensione dei blocchi.
    """

    total_words = len(words)
    parts = len(weights)

    if parts <= 1:
        return []

    if total_words < parts:

        return list(
            range(
                1,
                total_words,
            )
        )

    expected = [weight * total_words for weight in weights]

    best_boundaries = None
    best_score = float("inf")

    def search(
        part_index: int,
        start: int,
        boundaries: list[int],
        score: float,
    ):

        nonlocal best_boundaries
        nonlocal best_score

        # ----------------------------------------------------
        # Ultimo blocco.
        # ----------------------------------------------------

        if part_index == parts - 1:

            end = total_words

            chunk_score = _chunk_penalty(
                words,
                start,
                end,
                expected[part_index],
            )

            final_score = score + chunk_score

            if final_score < best_score:

                best_score = final_score

                best_boundaries = boundaries.copy()

            return

        ideal = ideal_boundaries[part_index]

        remaining_parts = parts - part_index - 1

        min_position = start + 1

        max_position = total_words - remaining_parts

        # ----------------------------------------------------
        # Ricerca locale intorno al confine ideale.
        # ----------------------------------------------------

        search_min = max(
            min_position,
            ideal - 8,
        )

        search_max = min(
            max_position,
            ideal + 8,
        )

        search_min = min(
            search_min,
            min_position,
        )

        search_max = max(
            search_max,
            min_position,
        )

        for position in range(
            search_min,
            search_max + 1,
        ):

            if position <= start:
                continue

            current_score = score

            current_score += _chunk_penalty(
                words,
                start,
                position,
                expected[part_index],
            )

            current_score += _boundary_distance(
                position,
                ideal,
            )

            current_score += _boundary_penalty(
                words,
                position,
            )

            # ------------------------------------------------
            # Penalità se il testo rimanente è sproporzionato.
            # ------------------------------------------------

            remaining_words = total_words - position

            remaining_expected = sum(expected[part_index + 1 :])

            if remaining_expected > 0 and remaining_words > remaining_expected * 1.8:

                current_score += 20.0

            if current_score >= best_score:
                continue

            boundaries.append(position)

            search(
                part_index + 1,
                position,
                boundaries,
                current_score,
            )

            boundaries.pop()

    search(
        part_index=0,
        start=0,
        boundaries=[],
        score=0.0,
    )

    if best_boundaries is None:

        return ideal_boundaries[:]

    return best_boundaries


# ============================================================
# DISTRIBUZIONE DI EMERGENZA
# ============================================================


def _emergency_distribution(
    words: list[str],
    group: list[dict],
) -> list[str]:
    """
    Fallback assoluto.

    Garantisce che:
    - ogni parola venga conservata;
    - ogni sottotitolo riceva un blocco;
    - non vengano perse parole.
    """

    count = len(group)
    total = len(words)

    if count == 1:
        return [" ".join(words)]

    weights = _source_weights(group)

    boundaries = []

    accumulated = 0.0

    for weight in weights[:-1]:

        accumulated += weight

        boundary = round(accumulated * total)

        if boundaries:

            boundary = max(
                boundary,
                boundaries[-1] + 1,
            )

        remaining_parts = len(weights) - len(boundaries) - 1

        boundary = min(
            boundary,
            total - remaining_parts,
        )

        boundaries.append(boundary)

    chunks = []

    start = 0

    for boundary in boundaries:

        chunks.append(" ".join(words[start:boundary]))

        start = boundary

    chunks.append(" ".join(words[start:]))

    return chunks


# ============================================================
# SPLIT DELLA TRADUZIONE
# ============================================================


def _split_translation(
    translation: str,
    group: list[dict],
) -> list[str]:
    """
    Divide una traduzione completa nei sottotitoli originali.

    La distribuzione considera:
    - quantità relativa del testo originale;
    - confini ideali;
    - grammatica;
    - punteggiatura;
    - lunghezza dei blocchi.

    Nessuna parola della traduzione viene eliminata.
    """

    if not group:
        return []

    words = _word_list(translation)

    if not words:
        return ["" for _ in group]

    if len(group) == 1:

        return [" ".join(words)]

    if len(words) < len(group):

        result = []

        for index in range(len(group)):

            if index < len(words):
                result.append(words[index])
            else:
                result.append("")

        return result

    weights = _source_weights(group)

    ideal_boundaries = _cumulative_boundaries(
        words,
        weights,
    )

    boundaries = _choose_boundaries(
        words,
        weights,
        ideal_boundaries,
    )

    chunks = []

    start = 0

    for boundary in boundaries:

        chunks.append(" ".join(words[start:boundary]))

        start = boundary

    chunks.append(" ".join(words[start:]))

    # --------------------------------------------------------
    # Sicurezza numero blocchi.
    # --------------------------------------------------------

    if len(chunks) < len(group):

        chunks.extend(["" for _ in range(len(group) - len(chunks))])

    elif len(chunks) > len(group):

        chunks = chunks[: len(group) - 1] + [
            " ".join(part for part in chunks[len(group) - 1 :] if part)
        ]

    # --------------------------------------------------------
    # Sicurezza assoluta:
    # nessuna parola deve essere persa.
    # --------------------------------------------------------

    reconstructed_words = _word_list(" ".join(chunks))

    if reconstructed_words != words:

        return _emergency_distribution(
            words,
            group,
        )

    return chunks


# ============================================================
# DISTRIBUZIONE TRADUZIONE
# ============================================================


def distribute_translation(
    translation: str,
    group: list[dict],
) -> list[dict]:
    """
    Distribuisce una traduzione completa nei sottotitoli
    appartenenti allo stesso gruppo.

    Mantiene:
    - index;
    - timestamp;
    - struttura originale.

    Modifica soltanto il campo text.
    """

    if not group:
        return []

    translation = _clean_translation(translation)

    # --------------------------------------------------------
    # Traduzione vuota.
    # --------------------------------------------------------

    if not translation:

        result = deepcopy(group)

        for subtitle in result:
            subtitle["text"] = ""

        return result

    # --------------------------------------------------------
    # Un solo sottotitolo.
    # --------------------------------------------------------

    if len(group) == 1:

        result = deepcopy(group)

        result[0]["text"] = correct_davinci_terms(translation)

        return result

    # --------------------------------------------------------
    # Distribuzione.
    # --------------------------------------------------------

    chunks = _split_translation(
        translation,
        group,
    )

    result = deepcopy(group)

    for subtitle, chunk in zip(
        result,
        chunks,
    ):

        chunk = _clean_translation(chunk)

        chunk = correct_davinci_terms(chunk)

        subtitle["text"] = chunk

    return result


# ============================================================
# LETTURA SRT
# ============================================================


def _read_srt(
    input_file: Path,
) -> list[dict]:
    """
    Legge un file SRT e restituisce una lista di dizionari.
    """

    if not input_file.exists():

        raise FileNotFoundError(f"File SRT non trovato: {input_file}")

    text = input_file.read_text(encoding="utf-8-sig")

    text = text.replace(
        "\r\n",
        "\n",
    )

    text = text.replace(
        "\r",
        "\n",
    )

    blocks = re.split(
        r"\n\s*\n",
        text.strip(),
    )

    subtitles = []

    for block in blocks:

        lines = block.split("\n")

        if len(lines) < 3:
            continue

        index = lines[0].strip()

        timestamp = lines[1].strip()

        subtitle_text = " ".join(line.strip() for line in lines[2:] if line.strip())

        if not index.isdigit():
            continue

        if "-->" not in timestamp:
            continue

        subtitles.append(
            {
                "index": index,
                "timestamp": timestamp,
                "text": subtitle_text,
            }
        )

    return subtitles


# ============================================================
# RICONOSCIMENTO GRUPPI
# ============================================================


def _is_sentence_end(text: str) -> bool:
    """
    Determina se un sottotitolo termina chiaramente una frase.
    """

    text = text.strip()

    if not text:
        return False

    return text.endswith((".", "!", "?", "…"))


def _build_translation_groups(
    subtitles: list[dict],
) -> list[list[dict]]:
    """
    Raggruppa i sottotitoli che appartengono alla stessa frase.

    Il gruppo termina quando il testo originale contiene
    una chiusura di frase.
    """

    groups = []

    current_group = []

    for subtitle in subtitles:

        current_group.append(subtitle)

        if _is_sentence_end(subtitle.get("text", "")):

            groups.append(current_group)

            current_group = []

    if current_group:
        groups.append(current_group)

    return groups


# ============================================================
# SCRITTURA SRT
# ============================================================


def _write_srt(
    subtitles: list[dict],
    output_file: Path,
):
    """
    Scrive i sottotitoli in formato SRT.
    """

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        for subtitle in subtitles:

            index = subtitle["index"]
            timestamp = subtitle["timestamp"]
            text = subtitle.get(
                "text",
                "",
            )

            # ------------------------------------------------
            # split_text crea massimo due righe
            # rispettando la logica di subtitles.py.
            # ------------------------------------------------

            text = split_text(text)

            file.write(f"{index}\n")

            file.write(f"{timestamp}\n")

            file.write(f"{text}\n\n")


# ============================================================
# TRADUZIONE SRT
# ============================================================


def translate_srt(
    input_file: Path,
    output_file: Path,
    source: str = "en",
    target: str = "it",
):
    """
    Traduce un file SRT completo.

    Procedura:

    1. legge l'SRT originale;
    2. raggruppa i sottotitoli appartenenti
       alla stessa frase;
    3. traduce l'intero gruppo;
    4. distribuisce la traduzione nei sottotitoli originali;
    5. corregge la terminologia DaVinci Resolve;
    6. salva il nuovo SRT.
    """

    print("\n🌍 Traduzione SRT...")
    print(f"📄 Input: {input_file}")

    subtitles = _read_srt(input_file)

    if not subtitles:

        raise ValueError("Il file SRT non contiene sottotitoli validi.")

    print(f"📝 Sottotitoli trovati: {len(subtitles)}")

    groups = _build_translation_groups(subtitles)

    print(f"🔗 Gruppi di traduzione: {len(groups)}")

    translated_subtitles = []

    for group_number, group in enumerate(
        groups,
        start=1,
    ):

        original_text = _clean_translation(
            " ".join(subtitle["text"] for subtitle in group)
        )

        if not original_text:
            translated_group = deepcopy(group)

        else:

            print(f"🌍 Gruppo {group_number}/{len(groups)}...")

            translated_text = translate_text(
                original_text,
                source=source,
                target=target,
            )

            translated_group = distribute_translation(
                translated_text,
                group,
            )

        translated_subtitles.extend(translated_group)

    # --------------------------------------------------------
    # Rinumera per sicurezza.
    # --------------------------------------------------------

    for index, subtitle in enumerate(
        translated_subtitles,
        start=1,
    ):

        subtitle["index"] = str(index)

    _write_srt(
        translated_subtitles,
        output_file,
    )

    print(f"✅ SRT italiano creato: {output_file}")

    return output_file


# ============================================================
# ALIAS COMPATIBILITÀ
# ============================================================


def translate(
    text: str,
    source: str = "en",
    target: str = "it",
) -> str:
    """
    Alias semplice per translate_text().
    """

    return translate_text(
        text,
        source=source,
        target=target,
    )
