from app.services.report_service import generer_rapport_pdf

# Exemple de résultat de correction d'une copie (reprend ton JSON réel)
resultat_copie = {
    "nom_fichier": "Screenshot 2025-10-11 095037.png",
    "note_finale": 2,
    "details": [
        {
            "Q1": {
                "points_obtenus": 2,
                "categorie": "RATEE",
                "annotation_courte": "Réponse incomplète et incorrecte",
                "feedback_detaille": "La réponse de l'étudiant est incomplète et ne mentionne pas les réactifs de la photosynthèse, ni la production de glucose et de dioxygène. Il faut être plus précis et complet dans sa réponse.",
                "conseil_revision": "Relecture de la leçon sur la photosynthèse pour comprendre les réactifs et les produits de cette réaction chimique."
            }
        },
        {
            "Q2": {
                "points_obtenus": 0,
                "categorie": "RATEE",
                "annotation_courte": "Réponse incomplète et incorrecte",
                "feedback_detaille": "La réponse de l'étudiant est incomplète et ne mentionne pas les quatre phases de la mitose. Il faut préciser les étapes de la mitose pour obtenir des points.",
                "conseil_revision": "Révise les étapes de la mitose et précise les quatre phases pour obtenir des points."
            }
        }
    ]
}

output_filename = "rapport_test_Screenshot_2025-10-11_095037.pdf"
pdf_path = generer_rapport_pdf(resultat_copie, output_filename)
print(f"PDF généré : {pdf_path}")