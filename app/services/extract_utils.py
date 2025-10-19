import re


def extraire_nom_et_classe(texte: str):
    """
    Cherche le nom et la classe sur la page.
    Retourne (nom, classe) ou ("Eleve inconnu", "Classe inconnue")
    """
    nom = "Eleve inconnu"
    classe = "Classe inconnue"

    # Recherche "Nom : Xxxx Yyyy"
    m = re.search(r"(?i)Nom\s*[:\-]\s*([A-Za-zÉÈÀÂÎÔÛéèàâîôûçÇ' -]{3,})", texte)
    if m:
        nom = m.group(1).strip()
    else:
        # Sinon, prend la première ligne si elle a au moins 2 mots
        lignes = texte.strip().split('\n')
        if lignes:
            possible_nom = lignes[0].strip()
            # S'assure que la ligne n'est pas juste le mot "nom" ou "classe"
            if len(possible_nom.split()) >= 2 and possible_nom.lower() not in ["nom", "classe"]:
                nom = possible_nom

    # Recherche "Classe : XXX"
    c = re.search(r"(?i)Classe\s*[:\-]\s*([A-Za-z0-9\- _]+)", texte)
    if c:
        classe = c.group(1).strip()

    return nom, classe