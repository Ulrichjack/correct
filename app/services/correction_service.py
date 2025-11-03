"""
Service de correction automatique avec parallélisation et filtrage intelligent V2
Version ultra-robuste - Novembre 2025
"""
import re
import traceback
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.ai_service import corriger_question, extraire_bareme_de_epreuve
from app.services.ocr_hybrid_service import extract_text_from_pdf
from app.services.ai_extract_service import (
    decouper_questions_avec_ia, 
    print_tokens_summary, 
    reset_tokens_stats,
    TOKENS_UTILISES
)
from app.database import sessions


def lancer_correction_automatique(session_id: str):
    """
    Lance la correction automatique avec gestion intelligente des erreurs.
    
    Processus :
    1. Extrait le texte de l'épreuve (OCR hybride)
    2. Extrait le barème avec l'IA + filtrage intelligent V2
    3. Extrait le texte de la correction du prof (OCR hybride)
    4. Découpe la correction par question avec l'IA (Groq)
    5. Pour chaque copie d'élève :
        - Découpe les réponses par question avec l'IA (Groq)
        - Corrige TOUTES les questions EN PARALLÈLE ⚡
        - Calcule la note finale
    6. Affiche le résumé de l'usage des tokens Groq
    7. Stocke les résultats dans la session
    
    Args:
        session_id: ID de la session
        
    Returns:
        Liste des résultats par élève
    """
    print(f"\n{'='*70}")
    print(f"🚀 CORRECTION AUTOMATIQUE (MODE PARALLÈLE + FILTRAGE V2 ⚡)")
    print(f"{'='*70}")
    print(f"📋 Session : {session_id}")
    
    start_time = time.time()
    reset_tokens_stats()
    
    session = sessions.get(session_id)
    if not session:
        raise ValueError(f"Session {session_id} introuvable.")

    try:
        # ============================================================
        # ÉTAPE 1 : EXTRAIRE LE TEXTE DE L'ÉPREUVE
        # ============================================================
        print(f"\n{'='*70}")
        print("📄 ÉTAPE 1/5 : Extraction de l'épreuve")
        print(f"{'='*70}")
        
        texte_epreuve = extract_text_from_pdf(
            session["epreuve"]["path"], 
            force_mode=None
        )
        
        if not texte_epreuve:
            raise ValueError("Impossible d'extraire le texte de l'épreuve.")
        
        print(f"  ✅ Épreuve extraite : {len(texte_epreuve)} caractères")
        
        # ============================================================
        # ÉTAPE 2 : EXTRACTION BARÈME + FILTRAGE INTELLIGENT V2
        # ============================================================
        print(f"\n{'='*70}")
        print("🤖 ÉTAPE 2/5 : Extraction du barème avec filtrage intelligent V2")
        print(f"{'='*70}")
        
        bareme_brut = extraire_bareme_de_epreuve(texte_epreuve)
        
        if not bareme_brut or len(bareme_brut) == 0:
            raise ValueError("Impossible d'extraire un barème de l'épreuve.")
        
        print(f"  📊 Barème brut : {bareme_brut}")
        
        # ✅ FILTRAGE INTELLIGENT VERSION 2.0
        print(f"\n🔍 Analyse du barème...")
        
        nb_exercices = sum(1 for k in bareme_brut.keys() if "Exercice" in k or "Exo" in k)
        nb_questions = sum(1 for k in bareme_brut.keys() if "Question" in k and "Exercice" not in k)
        
        print(f"   📊 Détection : {nb_exercices} Exercice(s), {nb_questions} Question(s)")
        
        # Calculer le total
        total_questions = len(bareme_brut)
        total_points = sum(bareme_brut.values())
        
        print(f"   📊 Total : {total_questions} question(s), {total_points} points")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # LOGIQUE DE FILTRAGE INTELLIGENTE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # CAS 1 : Total proche de 20 points (18-22) → Probablement correct
        if 18 <= total_points <= 22:
            print(f"   ✅ Total proche de 20 points → Barème probablement correct")
            print(f"   ✅ Conservation de TOUT le barème")
            bareme = bareme_brut
        
        # CAS 2 : Total proche de 10/15 points → Probablement correct
        elif 8 <= total_points <= 16:
            print(f"   ✅ Total {total_points} points → Barème court, probablement correct")
            print(f"   ✅ Conservation de TOUT le barème")
            bareme = bareme_brut
        
        # CAS 3 : Total anormalement élevé (>25 points) → Filtrage nécessaire
        elif total_points > 25:
            print(f"   ⚠️ Total anormalement élevé ({total_points} pts) → Filtrage nécessaire")
            
            # Si mélange Exercices + Questions
            if nb_exercices > 0 and nb_questions > 0:
                print(f"   🔧 Mélange détecté → Hypothèse : Questions de la correction")
                print(f"   ✅ Conservation des Exercices uniquement")
                
                bareme = {k: v for k, v in bareme_brut.items() if "Exercice" in k or "Exo" in k}
                
                if not bareme:
                    print(f"   ⚠️ Aucun Exercice trouvé, conservation de tout")
                    bareme = bareme_brut
                else:
                    questions_retirees = [k for k in bareme_brut.keys() if k not in bareme.keys()]
                    print(f"   ❌ Questions retirées : {questions_retirees}")
            else:
                print(f"   ✅ Pas de mélange détecté, conservation de tout")
                bareme = bareme_brut
        
        # CAS 4 : Total normal → Garder tout
        else:
            print(f"   ✅ Total {total_points} points → Conservation de tout le barème")
            bareme = bareme_brut
        
        print(f"\n  ✅ Barème final : {bareme}")
        print(f"  📊 Total points : {sum(bareme.values())}")
        
        # ============================================================
        # ÉTAPE 3 : EXTRAIRE LA CORRECTION DU PROF
        # ============================================================
        print(f"\n{'='*70}")
        print("📄 ÉTAPE 3/5 : Extraction de la correction du professeur")
        print(f"{'='*70}")
        
        texte_correction_prof = extract_text_from_pdf(
            session["correction"]["path"], 
            force_mode=None
        )
        
        if not texte_correction_prof:
            raise ValueError("Impossible d'extraire le texte de la correction.")
        
        print(f"  ✅ Correction extraite : {len(texte_correction_prof)} caractères")
        
        # ============================================================
        # ÉTAPE 4 : DÉCOUPER LA CORRECTION PAR QUESTION AVEC IA
        # ============================================================
        print(f"\n{'='*70}")
        print("🤖 ÉTAPE 4/5 : Découpage de la correction")
        print(f"{'='*70}")
        
        corrections_prof_par_question = decouper_questions_avec_ia(
            texte_correction_prof, 
            bareme
        )
        
        print(f"  ✅ Questions détectées : {list(corrections_prof_par_question.keys())}")
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE : {e}")
        traceback.print_exc()
        return {"error": str(e)}

    # ============================================================
    # ÉTAPE 5 : CORRIGER CHAQUE COPIE AVEC PARALLÉLISATION
    # ============================================================
    print(f"\n{'='*70}")
    print("✏️  ÉTAPE 5/5 : Correction des copies")
    print(f"{'='*70}")
    
    resultats_finaux = []
    total_copies = len(session["copies"])
    
    for idx, copie_etudiant in enumerate(session["copies"], 1):
        nom_eleve = copie_etudiant.get("nom_eleve", "Élève Inconnu")
        classe_eleve = copie_etudiant.get("classe", "Classe Inconnue")

        print(f"\n{'─'*70}")
        print(f"👤 Copie {idx}/{total_copies} : {nom_eleve} ({classe_eleve})")
        print(f"{'─'*70}")

        try:
            texte_copie = copie_etudiant["texte_complet"]
            
            print(f"  🤖 Découpage des réponses...")
            reponses_etudiant_par_question = decouper_questions_avec_ia(
                texte_copie, 
                bareme
            )
            
            print(f"  ✅ Réponses : {list(reponses_etudiant_par_question.keys())}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # CALCUL INTELLIGENT DU NOMBRE DE THREADS
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            nb_questions = len(bareme)
            
            if nb_questions <= 2:
                max_workers = nb_questions
            elif nb_questions <= 4:
                max_workers = 2
            elif nb_questions <= 10:
                max_workers = 3
            else:
                max_workers = 4
            
            print(f"\n  ⚡ {max_workers} thread(s) pour {nb_questions} question(s)")
            
            correction_start = time.time()
            resultats_par_question = []
            note_totale_copie = 0.0

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # BLOC PARALLÉLISÉ (CORRECTION DE TOUTES LES QUESTIONS)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                
                for num_question, points_max in bareme.items():
                    reponse_etudiant = reponses_etudiant_par_question.get(
                        num_question, 
                        "AUCUNE RÉPONSE FOURNIE."
                    )
                    
                    correction_prof = corrections_prof_par_question.get(
                        num_question, 
                        "Correction de référence non trouvée."
                    )
                    
                    future = executor.submit(
                        corriger_question,
                        f"Évaluation de la {num_question}",
                        reponse_etudiant,
                        correction_prof,
                        float(points_max),
                        num_question
                    )
                    
                    futures[future] = (num_question, points_max)
                
                questions_completed = 0
                
                for future in as_completed(futures):
                    num_question, points_max = futures[future]
                    questions_completed += 1
                    
                    try:
                        resultat_ia = future.result()
                        
                        points_obtenus = resultat_ia.get("points_obtenus", 0.0)
                        categorie = resultat_ia.get("categorie", "ERREUR")
                        annotation = resultat_ia.get("annotation_courte", "")
                        
                        print(f"  ✅ [{questions_completed}/{nb_questions}] {num_question} : {points_obtenus}/{points_max} pts ({categorie})")
                        
                        if annotation:
                            print(f"     💬 {annotation}")
                        
                        resultats_par_question.append({num_question: resultat_ia})
                        note_totale_copie += points_obtenus
                        
                    except Exception as e:
                        print(f"  ❌ Erreur {num_question} : {e}")
                        
                        resultats_par_question.append({
                            num_question: {
                                "points_obtenus": 0,
                                "categorie": "ERREUR",
                                "annotation_courte": "Erreur technique",
                                "feedback_detaille": "Erreur technique lors de la correction.",
                                "conseil_revision": "Contactez le professeur."
                            }
                        })
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # FIN DU BLOC PARALLÉLISÉ
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            correction_elapsed = time.time() - correction_start
            acceleration = (nb_questions * 20) / correction_elapsed if correction_elapsed > 0 else 1
            
            print(f"\n  ⏱️  Terminé en {correction_elapsed:.2f}s (~{acceleration:.1f}x plus rapide)")

            resultats_finaux.append({
                "nom_eleve": nom_eleve,
                "classe": classe_eleve,
                "note_finale": round(note_totale_copie, 2),
                "details": resultats_par_question
            })
            
            print(f"  📊 Note finale : {round(note_totale_copie, 2)} / {sum(bareme.values())}")

        except Exception as e:
            print(f"\n  ❌ Erreur : {e}")
            traceback.print_exc()
            
            resultats_finaux.append({
                "nom_eleve": nom_eleve, 
                "classe": classe_eleve, 
                "erreur": str(e)
            })

    # ============================================================
    # ÉTAPE 6 : SAUVEGARDER LES RÉSULTATS
    # ============================================================
    sessions[session_id]["results"] = resultats_finaux
    sessions[session_id]["status"] = "corrected"
    
    # ============================================================
    # ÉTAPE 7 : AFFICHER LE RÉSUMÉ FINAL
    # ============================================================
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*70}")
    print(f"🎉 CORRECTION TERMINÉE")
    print(f"{'='*70}")
    print(f"📊 {len(resultats_finaux)} copie(s) corrigée(s)")
    print(f"⏱️  Temps total : {elapsed_time:.2f}s")
    
    if len(resultats_finaux) > 0:
        vitesse_moyenne = elapsed_time / len(resultats_finaux)
        print(f"⚡ Vitesse : {vitesse_moyenne:.2f}s/copie")
    
    print(f"{'='*70}")
    
    print_tokens_summary()
    
    return resultats_finaux