#!/usr/bin/env python3
"""Déboguer le découpage des questions"""
import re

QUESTION_REGEX = re.compile(
    r'(?i)\b(question|q|exercice|exo)\s*(\d+)\s*[:.]?'
)

def extraire_reponses_par_question(texte_copie: str) -> dict:
    reponses = {}
    parts = QUESTION_REGEX.split(texte_copie)
    
    if len(parts) < 2:
        return {"Q1": texte_copie.strip()}
    
    i = 1
    while i < len(parts) - 1:
        numero_question = parts[i + 1].strip()
        texte_reponse = parts[i + 2].strip()
        cle = f"Q{numero_question}"
        
        if texte_reponse:
            reponses[cle] = texte_reponse
        
        i += 3
    
    return reponses


# Texte de test (copie-colle le texte OCR ici)
texte_copie = """
Exercice 1 (5 points)
Ma réponse : Le modèle Entité-Association...

Exercice 2 (8 points)
Ma réponse : Patient (Num, Nom)...

Question 1 (3 points)
Ma réponse : CREATE TABLE CLIENT...

Question 2 (4 points)
Ma réponse : SELECT * FROM CLIENT...
"""

print("="*70)
print("🔍 DÉCOUPAGE DES QUESTIONS")
print("="*70)
print(f"Texte à analyser :\n{texte_copie}\n")
print("="*70)

reponses = extraire_reponses_par_question(texte_copie)

print("✅ RÉSULTAT :")
for q, rep in reponses.items():
    print(f"\n{q} :")
    print(f"  {rep[:80]}...")
print("="*70)
