#!/usr/bin/env python3
"""
SOLUTION FINALE : OCR.space + Groq (correction IA)
GRATUIT, Sans carte bancaire, Meilleure précision
"""
import sys
import requests
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) < 2:
    print("Usage: python3 ocr_space_groq.py <image>")
    sys.exit(1)

# 1. OCR avec OCR.space
print("🤖 Étape 1/2 : Extraction OCR.space...")

api_key = os.getenv("OCRSPACE_API_KEY", "K87899142388957")

with open(sys.argv[1], 'rb') as f:
    response = requests.post(
        'https://api.ocr.space/parse/image',
        files={'filename': f},
        data={
            'apikey': api_key,
            'language': 'fre',
            'isOverlayRequired': False,
            'detectOrientation': True,
            'scale': True,
            'OCREngine': 2
        }
    )

result = response.json()

if result['IsErroredOnProcessing']:
    print(f"❌ Erreur OCR.space : {result.get('ErrorMessage', 'Inconnue')}")
    sys.exit(1)

texte_brut = result['ParsedResults'][0]['ParsedText']

print(f"   ✅ {len(texte_brut)} caractères extraits")

print("\n" + "="*70)
print("📝 TEXTE BRUT (OCR.space) :")
print("="*70)
print(texte_brut)
print("="*70)

# 2. Correction avec Groq
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    print("\n⚠️ Pas de GROQ_API_KEY → Résultat OCR.space seul")
    texte_final = texte_brut
    tokens = 0
else:
    print("\n🤖 Étape 2/2 : Correction Groq IA...")
    client = Groq(api_key=groq_key)
    
    prompt = f"""Tu es un correcteur OCR expert en français.

Corrige UNIQUEMENT les erreurs OCR évidentes dans ce texte de copie d'examen.
Garde la même structure et le même contenu.

TEXTE OCR :
{texte_brut}

TEXTE CORRIGÉ :"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000
    )
    
    texte_final = response.choices[0].message.content
    tokens = response.usage.total_tokens
    print(f"   ✅ {tokens} tokens utilisés")

print("\n" + "="*70)
print("✨ TEXTE FINAL (Corrigé par IA) :")
print("="*70)
print(texte_final)
print("="*70)

# Sauvegarder
output = sys.argv[1].replace('.jpg', '_final_corrige.txt')
with open(output, 'w', encoding='utf-8') as f:
    f.write("=== OCR.SPACE BRUT ===\n\n")
    f.write(texte_brut)
    f.write("\n\n=== CORRIGÉ PAR GROQ ===\n\n")
    f.write(texte_final)

print(f"\n💾 Sauvegardé : {output}")
print(f"💰 100% GRATUIT")
print(f"   • OCR.space : 25000/mois gratuit")
print(f"   • Groq : Gratuit illimité")
