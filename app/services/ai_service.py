import os
import json
import google.generativeai as genai
from groq import Groq

# Importer la configuration
from app.config import GEMINI_API_KEY, GROQ_API_KEY, AI_PROVIDER

# ====================================
# 1. CONFIGURATION DES CLIENTS API
# ====================================

# Configurer Gemini (si la clé est fournie)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configurer Groq (si la clé est fournie)
client_groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# ====================================
# 2. PROMPT DE CORRECTION DE QUESTION
# ====================================

def _construire_prompt(enonce_question, reponse_etudiant, correction_prof, points_max, numero_question):
    """Construit le prompt pour évaluer la réponse d'un étudiant pour UNE question."""
    return f"""
    Tu es un assistant expert pour un enseignant, spécialisé dans la correction de copies.
    Ta tâche est d'évaluer la réponse d'un étudiant pour la question '{numero_question}'.

    **CONTEXTE DE LA QUESTION ({numero_question})**
    - Énoncé de la question : {enonce_question}
    - Points maximum pour cette question : {points_max}

    ---
    **RÉPONSE ATTENDUE (Correction du professeur) :**
    {correction_prof}
    ---

    **RÉPONSE DE L'ÉTUDIANT :**
    {reponse_etudiant}
    ---

    **INSTRUCTIONS DE CORRECTION :**
    1.  **Analyse Sémantique :** Compare la RÉPONSE DE L'ÉTUDIANT à la RÉPONSE ATTENDUE. L'important est le sens, pas les mots exacts.
    2.  **Hors-Sujet :** Si la réponse est complètement hors-sujet, attribue 0 point.
    3.  **Attribution des Points :** Attribue une note sur {points_max}. Sois juste et cohérent.
    4.  **Catégorisation :** 'REUSSIE' (proche de la perfection), 'PARTIELLE' (correcte mais incomplète), ou 'RATEE' (incorrecte ou hors-sujet).
    5.  **Génération de Feedbacks :** Rédige une annotation courte (max 15 mots), un feedback détaillé (explique les points forts/faibles) et un conseil de révision.

    **FORMAT DE SORTIE OBLIGATOIRE :**
    Réponds UNIQUEMENT avec un objet JSON valide avec la structure suivante :
    {{
      "points_obtenus": <nombre>,
      "categorie": "<string>",
      "annotation_courte": "<string>",
      "feedback_detaille": "<string>",
      "conseil_revision": "<string>"
    }}
    """


# ==============================================================
# 3. PROMPT D'EXTRACTION DE BARÈME
# ==============================================================

def _construire_prompt_bareme(texte_epreuve: str) -> str:
    """Construit un prompt pour demander à l'IA d'extraire le barème d'un sujet."""
    return f"""
    Tu es un assistant expert capable d'analyser des sujets d'examen.
    Ta tâche est de lire le texte d'une épreuve et d'en extraire le barème sous forme de JSON.

    **TEXTE DE L'ÉPREUVE :**
    ---
    {texte_epreuve}
    ---

    **INSTRUCTIONS :**
    1.  Identifie chaque question (ex: "Question 1", "Q2", "Exercice 3").
    2.  Pour chaque question, trouve le nombre de points qui lui est associé (ex: "(5 points)", "/ 10 pts", "sur 5").
    3.  Ignore les questions qui n'ont pas de points clairement indiqués.
    4.  Retourne UNIQUEMENT un objet JSON valide. La clé doit être le numéro de la question (ex: "Q1") et la valeur doit être le nombre de points (un nombre, pas une chaîne de caractères).

    **EXEMPLE DE FORMAT DE SORTIE ATTENDU :**
    {{
      "Q1": 5,
      "Q2": 10,
      "Q3": 5
    }}

    Si aucun barème n'est trouvé, retourne un objet JSON vide : {{}}.
    """


# ====================================
# 4. FONCTIONS D'APPEL AUX IA
# ====================================

def _call_gemini(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    response = model.generate_content(prompt)
    return response.text


def _call_groq(prompt):
    if not client_groq:
        raise ValueError("La clé API Groq n'est pas configurée.")
    chat_completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return chat_completion.choices[0].message.content


# ====================================
# 5. FONCTIONS PRINCIPALES (Services)
# ====================================

def extraire_bareme_de_epreuve(texte_epreuve: str) -> dict:
    """Appelle l'IA pour extraire le barème (points par question) du texte d'une épreuve."""
    print("🤖 Appel de l'IA pour extraire le barème de l'épreuve...")
    try:
        prompt = _construire_prompt_bareme(texte_epreuve)
        ia_response_text = ""
        if AI_PROVIDER == "gemini":
            ia_response_text = _call_gemini(prompt)
        elif AI_PROVIDER == "groq":
            ia_response_text = _call_groq(prompt)
        else:
            raise ValueError(f"Fournisseur d'IA non reconnu : {AI_PROVIDER}")

        json_text = ia_response_text.strip().replace("```json", "").replace("```", "")
        bareme = json.loads(json_text)

        if not isinstance(bareme, dict):
            raise ValueError("La réponse de l'IA pour le barème n'est pas un dictionnaire.")

        print(f"✅ Barème extrait avec succès : {bareme}")
        return bareme
    except Exception as e:
        print(f"❌ ERREUR lors de l'extraction du barème : {e}")
        return {}


def corriger_question(enonce_question: str, reponse_etudiant: str, correction_prof: str, points_max: float,
                      numero_question: str):
    """Appelle l'IA pour corriger une question spécifique et retourne le résultat en JSON."""
    error_response = {
        "points_obtenus": 0, "categorie": "ERREUR", "annotation_courte": "Erreur de correction IA.",
        "feedback_detaille": "Impossible de contacter le service d'IA.",
        "conseil_revision": "Vérifiez la connexion et les clés API."
    }
    try:
        prompt = _construire_prompt(enonce_question, reponse_etudiant, correction_prof, points_max, numero_question)
        ia_response_text = ""
        if AI_PROVIDER == "gemini":
            ia_response_text = _call_gemini(prompt)
        elif AI_PROVIDER == "groq":
            ia_response_text = _call_groq(prompt)
        else:
            raise ValueError(f"Fournisseur d'IA non reconnu ou non supporté : {AI_PROVIDER}")

        json_text = ia_response_text.strip().replace("```json", "").replace("```", "")
        result = json.loads(json_text)
        return result
    except Exception as e:
        print(f"❌ ERREUR dans ai_service.py (corriger_question) : {e}")
        return error_response