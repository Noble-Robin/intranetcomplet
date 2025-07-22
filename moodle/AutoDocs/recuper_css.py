import fitz  # PyMuPDF
from collections import defaultdict
import os

# === CONFIGURATION ===
pdf_path = "DRAFT CDI CAPLOGY groupe (1).docx.pdf"

# Dossier où enregistrer les fichiers CSS
css_dir = "CSS"
os.makedirs(css_dir, exist_ok=True)  # Crée le dossier s'il n'existe pas

# Ouvre le PDF
doc = fitz.open(pdf_path)

# === Boucle sur chaque page ===
for page_number, page in enumerate(doc, start=1):
    # Dictionnaire pour les styles uniques de CETTE page
    styles = defaultdict(list)

    # Récupère tous les blocs de texte de la page
    blocks = page.get_text("dict")["blocks"]

    for b in blocks:
        if "lines" in b:
            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    font = span["font"]
                    size = round(span["size"])
                    color = span["color"]
                    key = (font, size, color)
                    if text:
                        styles[key].append(text)

    # === Génère un fichier CSS pour CETTE page DANS LE DOSSIER CSS ===
    output_css = os.path.join(css_dir, f"page_{page_number}.css")
    with open(output_css, "w", encoding="utf-8") as f:
        f.write(f"/* === CSS auto-généré depuis la page {page_number} du PDF === */\n\n")
        for idx, (key, texts) in enumerate(styles.items(), start=1):
            font, size, color = key
            r = (color >> 16) & 255
            g = (color >> 8) & 255
            b = color & 255

            # === Définit la classe CSS ===
            f.write(f".page{page_number}_style{idx} {{\n")
            f.write(f"  font-family: '{font}';\n")
            f.write(f"  font-size: {size}px;\n")
            f.write(f"  color: rgb({r}, {g}, {b});\n")
            f.write("}\n\n")

            # === Exemple de texte pour voir ce que ça formate ===
            f.write(f"/* Exemple (page {page_number}): {texts[0][:50]} */\n\n")

    print(f"✅ Fichier CSS généré pour la page {page_number} : {output_css}")

print("✅✅ Tous les fichiers CSS ont été générés avec succès dans le dossier 'CSS'.")
