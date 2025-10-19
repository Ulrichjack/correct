from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import os

EXPORT_FOLDER = "exports"


def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=10, leading=12):
    """Dessine du texte avec retour à la ligne automatique."""
    lines = simpleSplit(text, font_name, font_size, max_width)
    y_shift = 0
    for line in lines:
        c.drawString(x, y - y_shift, line)
        y_shift += leading
    return y - y_shift


def _dessiner_rapport_pour_un_eleve(c, resultat_copie):
    """
    Fonction helper qui dessine le contenu d'un rapport pour un élève sur le canevas (c) existant.
    """
    width, height = A4

    # --- EN-TÊTE ---
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, height - 2 * cm, "📝 RAPPORT DE CORRECTION")

    nom_eleve = resultat_copie.get('nom_eleve', 'N/A')
    classe_eleve = resultat_copie.get('classe', 'N/A')
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, height - 3 * cm, f"Élève : {nom_eleve}")
    c.drawString(2 * cm, height - 3.5 * cm, f"Classe : {classe_eleve}")

    c.setFont("Helvetica", 10)
    c.drawString(width - 6 * cm, height - 2 * cm, f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # --- NOTE FINALE ---
    note = resultat_copie.get("note_finale", "N/A")
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.1, 0.1, 0.4)
    c.drawString(2 * cm, height - 5 * cm, f"Note Finale : {note}")
    c.setFillColorRGB(0, 0, 0)

    # --- DÉTAILS DE LA CORRECTION ---
    y = height - 6.5 * cm
    details = resultat_copie.get("details", [])
    max_text_width = width - 4.5 * cm

    for bloc in details:
        for num_q, res in bloc.items():
            if y < 4 * cm:  # S'il ne reste pas assez de place
                c.showPage()  # On passe à une nouvelle page
                y = height - 2 * cm

            c.setFont("Helvetica-Bold", 12)
            points_obtenus = res.get('points_obtenus', 0)
            c.drawString(2 * cm, y,
                         f"{num_q} - {res.get('annotation_courte', '')} ({res.get('categorie', '')}) - {points_obtenus} pts")
            y -= 0.8 * cm

            c.setFont("Helvetica-Oblique", 10)
            y = draw_wrapped_text(c, f"Feedback : {res.get('feedback_detaille', '')}", 2.5 * cm, y, max_text_width)
            y -= 0.3 * cm

            c.setFont("Helvetica-Oblique", 10)
            y = draw_wrapped_text(c, f"Conseil : {res.get('conseil_revision', '')}", 2.5 * cm, y, max_text_width)
            y -= 1 * cm


def generer_rapport_consolide_pdf(resultats_session: list, output_filename: str):
    """
    Génère UN SEUL fichier PDF contenant les rapports de tous les élèves d'une session.
    """
    if not os.path.exists(EXPORT_FOLDER):
        os.makedirs(EXPORT_FOLDER)

    file_path = os.path.join(EXPORT_FOLDER, output_filename)
    c = canvas.Canvas(file_path, pagesize=A4)

    for i, resultat_copie in enumerate(resultats_session):
        _dessiner_rapport_pour_un_eleve(c, resultat_copie)

        # Si ce n'est pas le dernier élève, on ajoute une nouvelle page
        if i < len(resultats_session) - 1:
            c.showPage()

    c.save()
    return file_path
