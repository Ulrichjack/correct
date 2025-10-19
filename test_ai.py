import json
from app.services.ai_service import corriger_question
from app.config import AI_PROVIDER


# ============================================================
# 🧪 TEST DU SERVICE DE CORRECTION IA
# ============================================================

def run_test():
    """Lance un test simple sur la fonction de correction IA."""

    print("=" * 60)
    print(f"🤖 Lancement du test avec le fournisseur d'IA : {AI_PROVIDER.upper()}")
    print("=" * 60)

    # --- DONNÉES D'EXEMPLE ---
    # Imagine une question de SVT sur 5 points.

    # 1. Ce que le professeur a demandé
    enonce_question_test = "Expliquez le processus de la photosynthèse et ses produits principaux."

    # 2. La réponse (partiellement correcte) de l'étudiant
    reponse_etudiant_test = "La photosynthèse c'est quand les plantes utilisent le soleil pour faire de l'oxygène. Elles respirent le CO2."

    # 3. La réponse parfaite attendue par le professeur
    correction_prof_test = """
    La photosynthèse est le processus biochimique par lequel les plantes, les algues et certaines bactéries
    convertissent l'énergie lumineuse du soleil en énergie chimique.
    Elles utilisent le dioxyde de carbone (CO2) et l'eau (H2O) pour produire du glucose (C6H12O6), qui est leur nourriture,
    et rejettent du dioxygène (O2) comme sous-produit.
    """

    # 4. Les paramètres de la question
    points_max_test = 5.0
    numero_question_test = "Q1"

    # --- APPEL AU SERVICE IA ---
    # On appelle notre fonction avec toutes les informations
    print("⏳ Envoi des données à l'IA pour correction... (cela peut prendre quelques secondes)")

    resultat_correction = corriger_question(
        enonce_question=enonce_question_test,
        reponse_etudiant=reponse_etudiant_test,
        correction_prof=correction_prof_test,
        points_max=points_max_test,
        numero_question=numero_question_test
    )

    # --- AFFICHAGE DU RÉSULTAT ---
    print("\n" + "=" * 60)
    print("📊 RÉSULTAT DE LA CORRECTION IA")
    print("=" * 60)

    if resultat_correction and resultat_correction.get("categorie") != "ERREUR":
        # Affiche le JSON de manière lisible
        print(json.dumps(resultat_correction, indent=2, ensure_ascii=False))
    else:
        print("❌ Une erreur est survenue lors de la correction.")
        print(json.dumps(resultat_correction, indent=2, ensure_ascii=False))


# --- Lancement du script ---
if __name__ == "__main__":
    run_test()