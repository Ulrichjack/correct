import re
import traceback

from app.services.ai_service import corriger_question, extraire_bareme_de_epreuve
from app.services.ocr_service import extract_text
from app.database import sessions

QUESTION_REGEX = re.compile(
    r'(?i)\b(question|q|exercice|exo)\s*(\d+)\s*[:.]?'
)


def _extraire_reponses_par_question(texte_copie: str) -> dict:
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


def lancer_correction_automatique(session_id: str):
    print(f"\n🚀 Lancement de la correction automatique pour la session : {session_id}")
    session = sessions.get(session_id)
    if not session:
        raise ValueError(f"Session {session_id} introuvable.")

    try:
        print("📄 Extraction du texte de l'épreuve...")
        texte_epreuve = extract_text(session["epreuve"]["path"])
        bareme = extraire_bareme_de_epreuve(texte_epreuve)
        if not bareme:
            raise ValueError("Impossible d'extraire un barème de l'épreuve.")

        print("📄 Extraction du texte de la correction du professeur...")
        texte_correction_prof = extract_text(session["correction"]["path"])
        corrections_prof_par_question = _extraire_reponses_par_question(texte_correction_prof)
    except Exception as e:
        print(f"❌ Erreur critique lors de la préparation : {e}")
        return {"error": str(e)}

    resultats_finaux = []
    # MODIFICATION : On boucle sur les copies dans la session
    for copie_etudiant in session["copies"]:
        nom_eleve = copie_etudiant.get("nom_eleve", "Élève Inconnu")
        classe_eleve = copie_etudiant.get("classe", "Classe Inconnue")

        print(f"\n--- Traitement de la copie de : {nom_eleve} ({classe_eleve}) ---")

        try:
            # On utilise directement le texte complet stocké dans la session
            texte_copie = copie_etudiant["texte_complet"]
            reponses_etudiant_par_question = _extraire_reponses_par_question(texte_copie)

            resultats_par_question = []
            note_totale_copie = 0.0

            for num_question, points_max in bareme.items():
                print(f"  - Correction de la {num_question} (sur {points_max} pts)...")
                reponse_etudiant = reponses_etudiant_par_question.get(num_question, "AUCUNE RÉPONSE FOURNIE.")
                correction_prof = corrections_prof_par_question.get(num_question,
                                                                    "Correction de référence non trouvée.")

                resultat_ia = corriger_question(
                    enonce_question=f"Évaluation de la {num_question}",
                    reponse_etudiant=reponse_etudiant,
                    correction_prof=correction_prof,
                    points_max=float(points_max),
                    numero_question=num_question
                )
                resultats_par_question.append({num_question: resultat_ia})
                note_totale_copie += resultat_ia.get("points_obtenus", 0.0)

            resultats_finaux.append({
                "nom_eleve": nom_eleve,  # Ajout du nom
                "classe": classe_eleve,  # Ajout de la classe
                "note_finale": round(note_totale_copie, 2),
                "details": resultats_par_question
            })
            print(f"  - ✅ Correction terminée pour {nom_eleve}. Note finale : {round(note_totale_copie, 2)}")

        except Exception as e:
            traceback.print_exc()
            resultats_finaux.append({"nom_eleve": nom_eleve, "classe": classe_eleve, "erreur": str(e)})

    sessions[session_id]["results"] = resultats_finaux
    sessions[session_id]["status"] = "corrected"
    print(f"\n🎉 Correction automatique terminée pour la session {session_id}.")
    return resultats_finaux