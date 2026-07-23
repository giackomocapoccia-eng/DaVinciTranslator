from deep_translator import GoogleTranslator

input_file = "audio.srt"

output_en = "DaVinciResolve_EN.srt"
output_it = "DaVinciResolve_IT.srt"

translator = GoogleTranslator(source="en", target="it")

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

english = []
italian = []

i = 0

while i < len(lines):

    line = lines[i]

    # numero sottotitolo
    if line.strip().isdigit():
        numero = line
        tempo = lines[i+1]
        testo = lines[i+2].strip()

        traduzione = translator.translate(testo)

        # file inglese
        english.append(numero)
        english.append(tempo)
        english.append(testo + "\n\n")

        # file italiano
        italian.append(numero)
        italian.append(tempo)
        italian.append(traduzione + "\n\n")

        i += 4

    else:
        i += 1


with open(output_en, "w", encoding="utf-8") as f:
    f.writelines(english)

with open(output_it, "w", encoding="utf-8") as f:
    f.writelines(italian)


print("Creati:")
print(output_en)
print(output_it)