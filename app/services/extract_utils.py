import re


def extraire_nom_et_classe(texte: str):
    """
    Cherche le nom et la classe sur la page.
    Version améliorée pour mieux détecter les noms manuscrits.
    """
    nom = "Eleve inconnu"
    classe = "Classe inconnue"

    # Nettoyer le texte
    texte_nettoye = texte.replace('\n', ' ').strip()
    
    print(f"    🔍 Texte à analyser (100 premiers caractères) :")
    print(f"    {texte_nettoye[:100]}...")
    
    # ============================================================
    # RECHERCHE DU NOM
    # ============================================================
    
    # Pattern 1 : "DUPONT Jean - Matricule" ou "IVANOV Ivan - Matricule"
    m = re.search(r"([A-ZÀ-Ÿ][A-Za-zÀ-ÿ]{2,15}\s+[A-ZÀ-Ÿ][A-Za-zà-ÿ]{2,15})\s*[-–]\s*[Mm]atricule", texte_nettoye, re.IGNORECASE)
    if m:
        nom = m.group(1).strip()
        print(f"    ✅ Nom trouvé (Pattern 1 - avant Matricule) : {nom}")
    
    # Pattern 2 : "Nom : DUPONT Jean" ou "Nom: DuPONT jean"
    if nom == "Eleve inconnu":
        m = re.search(r"Nom\s*[:\-]\s*([A-ZÀ-ÿ][A-Za-zÀ-ÿ'\- ]{2,30})", texte_nettoye, re.IGNORECASE)
        if m:
            nom = m.group(1).strip()
            print(f"    ✅ Nom trouvé (Pattern 2 - Nom:) : {nom}")
    
    # Pattern 3 : Cherche 2 mots CAPITALISÉS (pas "Copie Etudiant")
    if nom == "Eleve inconnu":
        m = re.search(r"\b([A-ZÀ-Ÿ][A-ZÀ-Ÿa-zà-ÿ]{2,15})\s+([A-ZÀ-Ÿ][A-Za-zà-ÿ]{2,15})\b", texte_nettoye)
        if m:
            # Exclure "Copie Etudiant", "Cope Etudiant", etc.
            mot1 = m.group(1).lower()
            mot2 = m.group(2).lower()
            if mot1 not in ["copie", "cope", "cople", "code"] and mot2 not in ["etudiant", "student"]:
                nom = f"{m.group(1)} {m.group(2)}"
                print(f"    ✅ Nom trouvé (Pattern 3 - Capitalisés) : {nom}")
    
    # ============================================================
    # RECHERCHE DE LA CLASSE
    # ============================================================
    
    # Pattern 1 : "Matricule : 3IL2024001" → extraire "3IL"
    m = re.search(r"[Mm]atricule\s*[:\-]\s*([A-Za-z0-9]{3,10})", texte_nettoye, re.IGNORECASE)
    if m:
        code = m.group(1).strip()
        # Prendre les 2-4 premiers caractères (ex: 3IL, L3)
        classe = code[:4] if len(code) >= 3 else code
        print(f"    ✅ Classe trouvée (Pattern 1 - Matricule) : {classe}")
    
    # Pattern 2 : "Classe : 3IL"
    if classe == "Classe inconnue":
        c = re.search(r"Classe\s*[:\-]\s*([A-Za-z0-9\-_ ]{1,15})", texte_nettoye, re.IGNORECASE)
        if c:
            classe = c.group(1).strip()
            print(f"    ✅ Classe trouvée (Pattern 2 - Classe:) : {classe}")
    
    # Pattern 3 : Chercher un code classe dans le texte (ex: "3IL", "L3")
    if classe == "Classe inconnue":
        m = re.search(r"\b([A-Z0-9]{2,4})\b", texte_nettoye)
        if m:
            code = m.group(1).strip()
            # Exclure les codes non pertinents
            if code.lower() not in ["td", "tp", "sql", "mfl", "nfl"]:
                classe = code
                print(f"    ✅ Classe trouvée (Pattern 3 - Code) : {classe}")
    
    if nom == "Eleve inconnu":
        print(f"    ⚠️ AUCUN NOM détecté")
    if classe == "Classe inconnue":
        print(f"    ⚠️ AUCUNE CLASSE détectée")

    return nom, classe