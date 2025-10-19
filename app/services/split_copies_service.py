import os
from collections import defaultdict

# Importer les fonctions nécessaires depuis les autres services
from .ocr_service import extract_text_per_page
from .extract_utils import extraire_nom_et_classe


def decouper_copies_par_eleve(pdf_path: str) -> dict:
    """
    Analyse un PDF contenant plusieurs copies et les regroupe par élève.

    Cette fonction parcourt un fichier PDF page par page, identifie à quel élève
    chaque page appartient en se basant sur le nom et la classe, puis regroupe
    ces pages.

    Args:
        pdf_path: Le chemin vers le fichier PDF groupé.

    Returns:
        Un dictionnaire où les clés sont des tuples (nom_eleve, classe)
        et les valeurs sont des listes de dictionnaires de pages.
        Exemple de retour :
        {
            ("Jean Dupont", "CM2"): [
                {"page_num": 1, "texte": "Texte de la page 1..."},
                {"page_num": 2, "texte": "Texte de la page 2..."}
            ]
        }
    """
    print(f"📖 Découpage du fichier de copies : {os.path.basename(pdf_path)}")

    # 1. Extraire le texte de chaque page du PDF
    textes_par_page = extract_text_per_page(pdf_path)
    if not textes_par_page:
        print("❌ Aucune page n'a pu être extraite du PDF.")
        return {}

    # 2. Regrouper les pages par élève
    # defaultdict simplifie l'ajout d'éléments à une liste dans un dictionnaire
    groupes = defaultdict(list)
    dernier_eleve_identifie = None

    for i, texte_page in enumerate(textes_par_page):
        page_num = i + 1
        nom, classe = extraire_nom_et_classe(texte_page)

        # Si un nom est trouvé, on considère que c'est une nouvelle copie
        if nom != "Eleve inconnu":
            dernier_eleve_identifie = (nom, classe)

        # Si aucun nom n'est trouvé sur cette page, on l'attribue à la dernière copie identifiée
        if dernier_eleve_identifie:
            groupes[dernier_eleve_identifie].append({
                "page_num": page_num,
                "texte": texte_page
            })
            print(f"  - Page {page_num} attribuée à {dernier_eleve_identifie[0]}")
        else:
            print(f"  - ⚠️ Page {page_num} ignorée car aucun élève n'a pu être identifié.")

    print(f"✅ Découpage terminé. {len(groupes)} élèves détectés.")
    return dict(groupes)
