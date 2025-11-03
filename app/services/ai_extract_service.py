"""
Service d'extraction intelligente - VERSION ULTRA-ROBUSTE
Gestion d'erreurs et fallbacks multiples
"""
import json
import re
from app.services.groq_client import call_groq
from app.config import AI_PROVIDER

# Compteur global de tokens
TOKENS_UTILISES = {
    "extraction_nom": 0,
    "decoupage_questions": 0,
    "correction": 0,
    "bareme": 0,
    "total": 0
}


def get_tokens_stats():
    """Retourne les statistiques d'usage des tokens."""
    return TOKENS_UTILISES


def reset_tokens_stats():
    """Réinitialise le compteur de tokens."""
    global TOKENS_UTILISES
    TOKENS_UTILISES = {
        "extraction_nom": 0,
        "decoupage_questions": 0,
        "correction": 0,
        "bareme": 0,
        "total": 0
    }


def extraire_nom_classe_avec_ia(texte_ocr: str) -> tuple:
    """Extrait le nom et la classe avec IA + fallback regex."""
    
    # TENTATIVE 1 : IA
    prompt = f"""
Extrait le NOM et la CLASSE de l'élève.

TEXTE (300 premiers caractères) :
{texte_ocr[:300]}

INSTRUCTIONS :
- Cherche "Nom :", "Matricule :", patterns capitalisés
- Ignore "Copie", "Code", "Etudiant"
- Classe : "3IL", "L3", etc. (2-4 caractères)

SORTIE JSON :
{{
  "nom": "<NOM Prénom>",
  "classe": "<code>"
}}

Si rien : {{"nom": "Eleve inconnu", "classe": "Classe inconnue"}}
"""
    
    try:
        response = call_groq(prompt)
        json_text = response.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_text)
        
        nom = data.get("nom", "Eleve inconnu")
        classe = data.get("classe", "Classe inconnue")
        
        tokens_utilises = len(prompt.split()) + len(response.split())
        TOKENS_UTILISES["extraction_nom"] += tokens_utilises
        TOKENS_UTILISES["total"] += tokens_utilises
        
        if nom != "Eleve inconnu":
            print(f"    🤖 IA : {nom} ({classe})")
            return nom, classe
        else:
            print(f"    ⚠️ IA n'a rien trouvé, passage au fallback...")
    
    except Exception as e:
        print(f"    ⚠️ Erreur IA : {e}, passage au fallback...")
    
    # TENTATIVE 2 : REGEX (fallback)
    print(f"    🔧 Extraction avec regex...")
    
    # Pattern 1 : "DUPONT Jean - Matricule"
    m = re.search(r'([A-ZÀ-Ÿ][A-Za-zÀ-ÿ]{2,15}\s+[A-ZÀ-Ÿ][A-Za-zà-ÿ]{2,15})\s*[-–]\s*[Mm]atric', texte_ocr)
    if m:
        nom = m.group(1).strip()
        print(f"    ✅ Nom trouvé (regex) : {nom}")
    else:
        nom = "Eleve inconnu"
    
    # Pattern classe : "3IL", "L3"
    m_classe = re.search(r'\b([0-9][A-Z]{1,3}|[A-Z][0-9])\b', texte_ocr)
    if m_classe:
        classe = m_classe.group(1)
        print(f"    ✅ Classe trouvée (regex) : {classe}")
    else:
        classe = "Classe inconnue"
    
    return nom, classe


def _decouper_questions_regex(texte_copie: str, bareme: dict) -> dict:
    """Découpe avec regex (fallback si IA échoue)."""
    reponses = {}
    
    # Trier les questions par ordre d'apparition
    questions_triees = sorted(bareme.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    
    # Créer des patterns pour chaque question
    for i, question in enumerate(questions_triees):
        # Ex: "Exercice 1" → pattern "Exercice\s*1"
        pattern_question = re.escape(question).replace(r'\ ', r'\s*')
        
        # Chercher la position de cette question
        match = re.search(pattern_question, texte_copie, re.IGNORECASE)
        if match:
            debut = match.end()
            
            # Chercher la fin (début de la question suivante ou fin du texte)
            if i + 1 < len(questions_triees):
                question_suivante = questions_triees[i + 1]
                pattern_suivant = re.escape(question_suivante).replace(r'\ ', r'\s*')
                match_suivant = re.search(pattern_suivant, texte_copie[debut:], re.IGNORECASE)
                if match_suivant:
                    fin = debut + match_suivant.start()
                    reponses[question] = texte_copie[debut:fin].strip()
                else:
                    reponses[question] = texte_copie[debut:].strip()
            else:
                reponses[question] = texte_copie[debut:].strip()
        else:
            reponses[question] = "AUCUNE RÉPONSE FOURNIE."
    
    return reponses


def decouper_questions_avec_ia(texte_copie: str, bareme: dict) -> dict:
    """Découpe les réponses par question avec IA + fallback regex."""
    
    if not bareme or len(bareme) == 0:
        print("    ⚠️ Barème vide, impossible de découper")
        return {}
    
    liste_questions = "\n".join([f"- {q} ({pts} pts)" for q, pts in bareme.items()])
    
    # TENTATIVE 1 : IA
    prompt = f"""
Découpe la copie en associant chaque partie à la bonne question.

QUESTIONS ATTENDUES :
{liste_questions}

⚠️ UTILISE UNIQUEMENT CES CLÉS (pas d'invention)

COPIE :
{texte_copie[:1500]}...

SORTIE JSON :
{{
  "Exercice 1": "<texte réponse>",
  "Exercice 2": "<texte réponse>"
}}

Si question absente : "AUCUNE RÉPONSE FOURNIE."
"""
    
    try:
        response = call_groq(prompt)
        json_text = response.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_text)
        
        # Validation : vérifier les clés
        invalid_keys = [k for k in data.keys() if k not in bareme.keys()]
        if invalid_keys:
            print(f"    ⚠️ Clés invalides : {invalid_keys}")
            data = {k: v for k, v in data.items() if k in bareme.keys()}
        
        # Ajouter les questions manquantes
        for question in bareme.keys():
            if question not in data:
                data[question] = "AUCUNE RÉPONSE FOURNIE."
        
        tokens_utilises = len(prompt.split()) + len(response.split())
        TOKENS_UTILISES["decoupage_questions"] += tokens_utilises
        TOKENS_UTILISES["total"] += tokens_utilises
        
        print(f"    🤖 IA : {len(data)} question(s) détectée(s)")
        return data
    
    except Exception as e:
        print(f"    ⚠️ Erreur IA : {e}, passage au fallback...")
    
    # TENTATIVE 2 : REGEX (fallback)
    print(f"    🔧 Découpage avec regex...")
    reponses_regex = _decouper_questions_regex(texte_copie, bareme)
    
    if len(reponses_regex) > 0:
        print(f"    ✅ Regex : {len(reponses_regex)} question(s)")
        return reponses_regex
    
    # TENTATIVE 3 : Tout mettre dans la première question (dernière chance)
    print(f"    ⚠️ Fallback : tout dans la première question")
    premiere_question = list(bareme.keys())[0]
    reponses_default = {q: "AUCUNE RÉPONSE FOURNIE." for q in bareme.keys()}
    reponses_default[premiere_question] = texte_copie
    
    return reponses_default


def print_tokens_summary():
    """Affiche le résumé de l'usage des tokens."""
    total = TOKENS_UTILISES['total']
    
    if total == 0:
        print("\n📊 Aucun token utilisé")
        return
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE L'USAGE DES TOKENS GROQ")
    print("="*60)
    print(f"  🔍 Extraction nom/classe : {TOKENS_UTILISES['extraction_nom']:>8,} tokens ({TOKENS_UTILISES['extraction_nom']/total*100:>5.1f}%)")
    print(f"  ✂️  Découpage questions  : {TOKENS_UTILISES['decoupage_questions']:>8,} tokens ({TOKENS_UTILISES['decoupage_questions']/total*100:>5.1f}%)")
    print(f"  📋 Extraction barème     : {TOKENS_UTILISES['bareme']:>8,} tokens ({TOKENS_UTILISES['bareme']/total*100:>5.1f}%)")
    print(f"  ✅ Correction copies     : {TOKENS_UTILISES['correction']:>8,} tokens ({TOKENS_UTILISES['correction']/total*100:>5.1f}%)")
    print(f"  {'─'*58}")
    print(f"  📈 TOTAL                 : {total:>8,} tokens")
    print(f"  💰 Coût estimé Groq      : ${total * 0.0000001:.6f}")
    print("="*60 + "\n")