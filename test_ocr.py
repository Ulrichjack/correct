"""
Script de test pour l'extraction OCR.
Place un PDF de test dans uploads/copies/ avant de lancer ce script.
"""

from app.services.ocr_service import extract_text, get_text_preview

# ====================================
# CONFIGURATION
# ====================================

# Remplace par le nom de ton fichier de test
TEST_FILE = "uploads/copies/test.pdf"  # ← Change ici !

# ====================================
# TEST
# ====================================

print("=" * 60)
print("🧪 TEST D'EXTRACTION OCR")
print("=" * 60)

# Extraire le texte
print(f"\n📂 Fichier à traiter : {TEST_FILE}\n")
text = extract_text(TEST_FILE)

# Afficher les résultats
print("\n" + "=" * 60)
print("📊 RÉSULTATS")
print("=" * 60)

if text:
    # Obtenir l'aperçu
    preview = get_text_preview(text, max_chars=500)

    print(f"\n✅ Extraction réussie !")
    print(f"📏 Longueur totale : {preview['total_chars']} caractères")
    print(f"📝 Nombre de mots : {preview['total_words']}")
    print(f"📄 Nombre de lignes : {preview['total_lines']}")

    print(f"\n📖 Aperçu (500 premiers caractères) :")
    print("-" * 60)
    print(preview['preview'])
    print("-" * 60)
else:
    print("\n❌ Aucun texte extrait (fichier vide ou erreur)")

print("\n" + "=" * 60)