import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from app.config import TESSERACT_PATH
import cv2
import numpy as np

# Configurer le chemin vers Tesseract (s'assure que l'application sait où le trouver)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def _preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Prépare une image pour une meilleure reconnaissance OCR en utilisant OpenCV.
    Cette fonction est cruciale pour améliorer la qualité sur les scans et l'écriture manuscrite.
    """
    print("  - Pré-traitement de l'image pour l'OCR...")

    # 1. Convertir l'image de format PIL (utilisé par pdf2image) en format OpenCV (numpy array)
    open_cv_image = np.array(image)

    # 2. Convertir l'image couleur en niveaux de gris. C'est une étape standard qui simplifie l'analyse.
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # 3. Binarisation (Seuillage) : C'est l'étape la plus importante.
    #    Elle transforme l'image en noir et blanc pur, faisant ressortir le texte.
    #    - cv2.THRESH_OTSU calcule automatiquement le meilleur seuil pour séparer le texte du fond.
    #    - cv2.THRESH_BINARY_INV inverse les couleurs (texte en blanc, fond en noir), ce qui est utile pour certaines opérations morphologiques.
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 4. Inverser l'image pour que le texte soit noir sur fond blanc.
    #    C'est le format que Tesseract préfère pour une meilleure reconnaissance.
    final_image = cv2.bitwise_not(thresh)

    # 5. Reconvertir l'image de format OpenCV en format PIL, pour que pytesseract puisse la lire.
    return Image.fromarray(final_image)


def extract_text_per_page(pdf_path: str) -> list:
    """
    Extrait le texte page par page d'un fichier PDF, en appliquant un pré-traitement sur chaque page.
    Retourne une liste de chaînes de caractères, où chaque chaîne est le texte d'une page.
    """
    print(f"🔄 Lancement de l'extraction page par page pour {os.path.basename(pdf_path)}")
    try:
        # dpi=300 offre une meilleure résolution, ce qui est essentiel pour l'OCR.
        images = convert_from_path(pdf_path, dpi=300)
        textes = []
        for i, img in enumerate(images):
            print(f"  - OCR sur la page {i + 1}/{len(images)}...")

            # On applique notre nouvelle fonction de pré-traitement sur chaque page
            preprocessed_img = _preprocess_image_for_ocr(img)

            # On envoie l'image "nettoyée" à Tesseract
            texte = pytesseract.image_to_string(preprocessed_img, lang="fra")
            textes.append(texte)

        print(f"✅ Extraction terminée. {len(textes)} pages traitées.")
        return textes
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction page par page du PDF {pdf_path}: {str(e)}")
        return []


def extract_text(file_path: str) -> str:
    """
    Fonction principale qui détecte le type de fichier et extrait le texte.
    Elle est maintenant basée sur la fonction `extract_text_per_page` pour les PDF.
    """
    if not os.path.exists(file_path):
        print(f"❌ Fichier introuvable : {file_path}")
        return ""

    file_extension = os.path.splitext(file_path)[1].lower()
    print(f"📂 Fichier : {os.path.basename(file_path)}")
    print(f"📌 Extension : {file_extension}")

    if file_extension == '.pdf':
        pages_text = extract_text_per_page(file_path)
        # On combine le texte de toutes les pages en une seule chaîne de caractères
        return "\n\n--- PAGE SUIVANTE ---\n\n".join(pages_text)

    elif file_extension in ['.jpg', '.jpeg', '.png']:
        try:
            image = Image.open(file_path)
            preprocessed_image = _preprocess_image_for_ocr(image)
            text = pytesseract.image_to_string(preprocessed_image, lang='fra')
            print(f"✅ Texte extrait de l'image : {len(text)} caractères")
            return text.strip()
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction de l'image {file_path}: {str(e)}")
            return ""

    else:
        print(f"❌ Extension non supportée : {file_extension}")
        return ""
