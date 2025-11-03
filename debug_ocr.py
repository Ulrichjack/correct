#!/usr/bin/env python3
"""Déboguer l'extraction OCR"""
import sys
from app.services.ocr_hybrid_service import extract_text_from_file
from app.services.extract_utils import extraire_nom_et_classe

if len(sys.argv) < 2:
    print("Usage: python3 debug_ocr.py <image>")
    sys.exit(1)

print("="*70)
print("🔍 EXTRACTION OCR")
print("="*70)
texte = extract_text_from_file(sys.argv[1], force_mode="ocrspace")

print("\n" + "="*70)
print("📝 TEXTE BRUT EXTRAIT PAR OCR.SPACE :")
print("="*70)
print(texte)
print("="*70)

print("\n" + "="*70)
print("🔍 EXTRACTION NOM + CLASSE")
print("="*70)
nom, classe = extraire_nom_et_classe(texte)

print("\n" + "="*70)
print("✅ RÉSULTAT FINAL :")
print("="*70)
print(f"  Nom : {nom}")
print(f"  Classe : {classe}")
print("="*70)
