#!/usr/bin/env python3
"""
🧪 TEST OCR AVEC EASYOCR
Plus léger que TrOCR, bon sur manuscrit
"""

import sys
import easyocr
from PIL import Image

def tester_easyocr(image_path):
    print("=" * 70)
    print(f"🧪 TEST EASYOCR SUR : {image_path}")
    print("=" * 70)
    print("")
    
    print("🤖 Chargement du modèle EasyOCR (français)...")
    reader = easyocr.Reader(['fr'], gpu=False, verbose=False)
    
    print(f"📸 Lecture de l'image...")
    result = reader.readtext(image_path, detail=0, paragraph=True)
    
    texte = "\n".join(result)
    
    print("")
    print("=" * 70)
    print("📝 RÉSULTAT EXTRAIT :")
    print("=" * 70)
    print(texte)
    print("")
    print("=" * 70)
    print(f"✅ Total : {len(texte)} caractères extraits")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage : python3 test_ocr_easyocr.py <chemin_vers_fichier>")
        print("")
        print("Exemples :")
        print("  python3 test_ocr_easyocr.py eleve15.jpg")
        print("  python3 test_ocr_easyocr.py test_images/copie.jpg")
        sys.exit(1)
    
    fichier = sys.argv[1]
    tester_easyocr(fichier)