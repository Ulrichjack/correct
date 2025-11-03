#!/bin/bash
set -e

echo "🔧 Installation du système de correction OCR avec IA"
echo "===================================================================="

# 1. Activer l'environnement virtuel
source venv/bin/activate

# 2. Vérifier que groq est installé
echo "📦 Vérification des dépendances..."
pip install groq python-dotenv --quiet

# 3. Créer le script de correction IA
echo "📝 Création du script corriger_avec_ia.py..."
cat > corriger_avec_ia.py << 'PYEOF'
#!/usr/bin/env python3
"""
Corrige les erreurs OCR avec l'IA Groq
"""
import sys
import os
import easyocr
from groq import Groq
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 corriger_avec_ia.py <image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Vérifier la clé API
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY non trouvée dans .env !")
        sys.exit(1)
    
    # 1. OCR brut
    print("📸 Extraction OCR (EasyOCR)...")
    reader = easyocr.Reader(['fr'], gpu=False, verbose=False)
    result = reader.readtext(image_path, detail=0, paragraph=True)
    texte_brut = "\n".join(result)
    
    print("\n" + "="*70)
    print("📝 TEXTE BRUT (avec erreurs OCR) :")
    print("="*70)
    print(texte_brut)
    print("="*70)
    print(f"Longueur : {len(texte_brut)} caractères\n")
    
    # 2. Correction IA
    print("🤖 Correction avec Groq IA (llama-3.3-70b)...")
    client = Groq(api_key=api_key)
    
    prompt = f"""Tu es un correcteur d'OCR expert en français.
Le texte suivant provient d'une copie d'examen manuscrite (SQL/Base de données).

TÂCHE : Corrige UNIQUEMENT les erreurs évidentes d'OCR (fautes de frappe, symboles mal reconnus).
- Garde la MÊME structure
- Garde le MÊME contenu
- Ne change PAS le sens
- Corrige les mots déformés

TEXTE OCR :
{texte_brut}

TEXTE CORRIGÉ (garde le même format) :"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000
    )
    
    texte_corrige = response.choices[0].message.content
    
    print("\n" + "="*70)
    print("✨ TEXTE CORRIGÉ PAR IA :")
    print("="*70)
    print(texte_corrige)
    print("="*70)
    print(f"Longueur : {len(texte_corrige)} caractères")
    
    # 3. Statistiques
    tokens_used = response.usage.total_tokens
    print("\n" + "="*70)
    print("📊 STATISTIQUES :")
    print("="*70)
    print(f"  • Tokens utilisés : {tokens_used}")
    print(f"  • Coût : GRATUIT (Groq)")
    print("="*70)

if __name__ == "__main__":
    main()
PYEOF

chmod +x corriger_avec_ia.py

echo ""
echo "✅ Installation terminée !"
echo ""

