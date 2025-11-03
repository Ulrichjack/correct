"""
Service IA pour la correction de copies - VERSION ULTRA-ROBUSTE
Gestion intelligente des erreurs et extraction améliorée
"""
import json
import re
from app.config import AI_PROVIDER
from app.services.groq_client import call_gemini, call_groq


def _get_tokens_dict():
    """Récupère le dictionnaire de tokens depuis ai_extract_service"""
    from app.services import ai_extract_service
    return ai_extract_service.TOKENS_UTILISES


# ====================================
# 1. EXTRACTION BARÈME AVEC FALLBACK
# ====================================

def _extraire_bareme_regex(texte_epreuve: str) -> dict:
    """Extraction du barème avec regex (fallback si IA échoue)"""
    bareme = {}
    
    # Pattern 1: "Exercice 1 (5 points)"
    pattern1 = re.compile(r'(Exercice|Question)\s+(\d+)\s*\((\d+)\s*points?\)', re.IGNORECASE)
    matches = pattern1.findall(texte_epreuve)
    
    for match in matches:
        type_question = match[0].capitalize()
        numero = match[1]
        points = int(match[2])
        cle = f"{type_question} {numero}"
        bareme[cle] = points
    
    # Pattern 2: "TD N°1: Question 1 (3 points)"
    pattern2 = re.compile(r'(?:TD|TP)\s*N[°o]\s*\d+\s*:\s*(Question|Exercice)\s+(\d+)\s*\((\d+)\s*points?\)', re.IGNORECASE)
    matches2 = pattern2.findall(texte_epreuve)
    
    for match in matches2:
        type_question = match[0].capitalize()
        numero = match[1]
        points = int(match[2])
        cle = f"{type_question} {numero}"
        if cle not in bareme:  # Éviter les doublons
            bareme[cle] = points
    
    return bareme


def _construire_prompt_bareme(texte_epreuve: str) -> str:
    """Construit le prompt pour extraire le barème."""
    return f"""
Tu es un expert en analyse de sujets d'examen.

MISSION : Extraire UNIQUEMENT les questions/exercices du SUJET (pas de la correction).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 DOCUMENT (premiers 1500 caractères)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{texte_epreuve[:1500]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **CHERCHE les patterns suivants :**
   - "Exercice 1 (5 points)"
   - "Question 1 (3 points)"
   - "TD N°1: Question 1 (4 points)"

2. **IGNORE tout après :**
   - "Solution correcte"
   - "Correction -"
   - "Barème détaillé"

3. **Si tu ne trouves RIEN :**
   - Retourne un objet vide : {{}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 FORMAT DE SORTIE (JSON STRICT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
  "Exercice 1": 5,
  "Exercice 2": 8
}}

OU

{{
  "Question 1": 3,
  "Question 2": 4
}}

Si rien trouvé : {{}}
"""


def extraire_bareme_de_epreuve(texte_epreuve: str) -> dict:
    """Extrait le barème avec IA + fallback regex."""
    print("🤖 Extraction du barème...")
    
    # TENTATIVE 1 : Extraction avec IA
    try:
        prompt = _construire_prompt_bareme(texte_epreuve)
        
        if AI_PROVIDER == "gemini":
            ia_response_text = call_gemini(prompt)
        elif AI_PROVIDER == "groq":
            ia_response_text = call_groq(prompt)
        else:
            raise ValueError(f"❌ Fournisseur d'IA non reconnu : {AI_PROVIDER}")

        json_text = ia_response_text.strip().replace("```json", "").replace("```", "")
        bareme = json.loads(json_text)

        if not isinstance(bareme, dict):
            raise ValueError("Réponse invalide")

        tokens = len(prompt.split()) + len(ia_response_text.split())
        tokens_dict = _get_tokens_dict()
        tokens_dict["bareme"] += tokens
        tokens_dict["total"] += tokens

        if len(bareme) > 0:
            print(f"✅ Barème extrait avec IA : {bareme}")
            return bareme
        else:
            print("⚠️ IA n'a trouvé aucune question, passage au fallback...")
            
    except Exception as e:
        print(f"⚠️ Erreur IA : {e}, passage au fallback...")
    
    # TENTATIVE 2 : Extraction avec REGEX (fallback)
    print("🔧 Tentative d'extraction avec regex...")
    bareme_regex = _extraire_bareme_regex(texte_epreuve)
    
    if len(bareme_regex) > 0:
        print(f"✅ Barème extrait avec regex : {bareme_regex}")
        return bareme_regex
    
    # TENTATIVE 3 : Barème par défaut (dernière chance)
    print("⚠️ Aucune question détectée automatiquement")
    print("📋 Création d'un barème par défaut...")
    
    # Chercher "Exercice" ou "Question" dans le texte
    if "Exercice" in texte_epreuve:
        # Compter le nombre d'exercices
        nb_exercices = len(re.findall(r'Exercice\s+\d+', texte_epreuve, re.IGNORECASE))
        if nb_exercices > 0:
            bareme_default = {f"Exercice {i+1}": 10 for i in range(nb_exercices)}
            print(f"✅ Barème par défaut créé : {bareme_default}")
            return bareme_default
    
    if "Question" in texte_epreuve:
        nb_questions = len(re.findall(r'Question\s+\d+', texte_epreuve, re.IGNORECASE))
        if nb_questions > 0:
            bareme_default = {f"Question {i+1}": 5 for i in range(nb_questions)}
            print(f"✅ Barème par défaut créé : {bareme_default}")
            return bareme_default
    
    print("❌ Impossible de créer un barème")
    return {}


# ====================================
# 2. PROMPT DE CORRECTION AMÉLIORÉ
# ====================================

def _construire_prompt_correction(enonce_question, reponse_etudiant, correction_prof, points_max, numero_question):
    """Construit le prompt de correction avec feedbacks détaillés."""
    return f"""
Tu es un professeur expert en correction de copies.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 {numero_question} ({points_max} points)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Énoncé :** {enonce_question}

**Correction attendue :** {correction_prof}

**Réponse étudiant :** {reponse_etudiant}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 BARÈME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- {points_max} pts : Réponse complète et correcte
- {points_max * 0.75:.1f} pts : Correcte avec petites erreurs
- {points_max * 0.5:.1f} pts : Partiellement correcte
- {points_max * 0.25:.1f} pts : Très incomplète
- 0 pt : Incorrecte ou absente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CONSIGNES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**TOLÉRANCE :**
- Variantes de formulation (sens correct)
- Fautes d'orthographe
- Erreurs OCR ("NIM" = "N:M", "Maticule" = "Matricule")
- Différences de notation ("1:N" = "1..N")

**VALORISE :**
- Compréhension du concept
- Raisonnement valide

**RÈGLE D'OR :**
Si l'étudiant a compris le concept principal → au moins 50% des points

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 FORMAT DE SORTIE (JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
  "points_obtenus": <nombre entre 0 et {points_max}>,
  "categorie": "REUSSIE" | "PARTIELLE" | "RATEE",
  "annotation_courte": "<feedback en 10-15 mots>",
  "feedback_detaille": "<ce qui est correct, ce qui manque, les erreurs>",
  "conseil_revision": "<conseil concret avec ressources>",
  "elements_corrects": ["<élément 1>", "<élément 2>"],
  "elements_manquants": ["<élément 1>", "<élément 2>"],
  "erreurs_detectees": ["<erreur 1>", "<erreur 2>"]
}}

**Exemples de conseils :**
- "Révisez les cardinalités : 1:N (un à plusieurs), N:M (plusieurs à plusieurs)"
- "Entraînez-vous avec CREATE TABLE : spécifiez PRIMARY KEY pour la clé"
- "Pour compter : utilisez COUNT() avec GROUP BY"
"""


def corriger_question(enonce_question: str, reponse_etudiant: str, correction_prof: str, 
                      points_max: float, numero_question: str):
    """Corrige une question avec gestion d'erreurs robuste."""
    error_response = {
        "points_obtenus": 0, 
        "categorie": "ERREUR", 
        "annotation_courte": "Erreur technique",
        "feedback_detaille": "Le service d'IA n'a pas pu traiter cette réponse.",
        "conseil_revision": "Contactez le professeur pour une correction manuelle.",
        "elements_corrects": [],
        "elements_manquants": [],
        "erreurs_detectees": ["Erreur technique"]
    }
    
    try:
        prompt = _construire_prompt_correction(enonce_question, reponse_etudiant, correction_prof, 
                                               points_max, numero_question)
        
        if AI_PROVIDER == "gemini":
            ia_response_text = call_gemini(prompt)
        elif AI_PROVIDER == "groq":
            ia_response_text = call_groq(prompt)
        else:
            raise ValueError(f"❌ Fournisseur d'IA non reconnu : {AI_PROVIDER}")

        json_text = ia_response_text.strip().replace("```json", "").replace("```", "")
        result = json.loads(json_text)
        
        # Validation et valeurs par défaut
        if "points_obtenus" not in result:
            result["points_obtenus"] = 0
        if "categorie" not in result:
            result["categorie"] = "ERREUR"
        if "feedback_detaille" not in result:
            result["feedback_detaille"] = "Feedback non disponible"
        if "elements_corrects" not in result:
            result["elements_corrects"] = []
        if "elements_manquants" not in result:
            result["elements_manquants"] = []
        if "erreurs_detectees" not in result:
            result["erreurs_detectees"] = []
        
        tokens = len(prompt.split()) + len(ia_response_text.split())
        tokens_dict = _get_tokens_dict()
        tokens_dict["correction"] += tokens
        tokens_dict["total"] += tokens
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Réponse IA invalide : {e}")
        return error_response
    except Exception as e:
        print(f"⚠️ Erreur correction : {e}")
        return error_response