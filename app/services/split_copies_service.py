import os
from collections import defaultdict

from .ocr_hybrid_service import extract_text_from_file
from .ai_extract_service import extraire_nom_classe_avec_ia  # ✅ IA


def decouper_copies_par_eleve(file_path: str) -> dict:
    """
    Analyse un fichier (PDF ou IMAGE) et regroupe par élève.
    Utilise OCR hybride + IA pour l'extraction du nom/classe.
    """
    print(f"\n{'='*60}")
    print(f"📖 Découpage du fichier de copies")
    print(f"{'='*60}")
    print(f"📁 Fichier : {os.path.basename(file_path)}")
    
    # ÉTAPE 1 : OCR
    print(f"🔍 Extraction du texte avec OCR hybride...")
    texte_complet = extract_text_from_file(file_path, force_mode=None)
    
    if not texte_complet:
        print("❌ Aucun texte extrait.")
        return {}

    print(f"  ✅ Texte extrait : {len(texte_complet)} caractères")
    
    # ÉTAPE 2 : Séparer pages
    if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        textes_par_page = [texte_complet]
    else:
        textes_par_page = texte_complet.split("--- PAGE SUIVANTE ---")
        textes_par_page = [t.strip() for t in textes_par_page if t.strip()]
    
    print(f"  ✅ {len(textes_par_page)} page(s) détectée(s)")

    # ÉTAPE 3 : Identifier élèves avec IA
    print(f"\n🤖 Identification des élèves avec IA...")
    
    groupes = defaultdict(list)
    dernier_eleve_identifie = None

    for i, texte_page in enumerate(textes_par_page):
        page_num = i + 1
        print(f"\n  📄 Page {page_num} :")
        
        # ✅ IA pour extraire nom/classe
        nom, classe = extraire_nom_classe_avec_ia(texte_page)
        
        if nom != "Eleve inconnu":
            dernier_eleve_identifie = (nom, classe)
            print(f"     ✅ Nouvel élève → {nom} ({classe})")
        
        if dernier_eleve_identifie:
            groupes[dernier_eleve_identifie].append({
                "page_num": page_num,
                "texte": texte_page
            })
        else:
            dernier_eleve_identifie = (f"Eleve_{page_num}", "Classe inconnue")
            groupes[dernier_eleve_identifie].append({
                "page_num": page_num,
                "texte": texte_page
            })

    # RÉSUMÉ
    print(f"\n{'='*60}")
    print(f"✅ Découpage terminé - {len(groupes)} élève(s)")
    for (nom, classe), pages in groupes.items():
        print(f"  - {nom} ({classe}) : {len(pages)} page(s)")
    print(f"{'='*60}\n")
    
    return dict(groupes)
