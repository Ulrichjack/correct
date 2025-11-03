from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.lib.colors import HexColor
from datetime import datetime
import os

EXPORT_FOLDER = "exports"


def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=9, leading=11):
    """Dessine du texte avec retour à la ligne automatique."""
    lines = simpleSplit(text, font_name, font_size, max_width)
    y_shift = 0
    for line in lines:
        c.drawString(x, y - y_shift, line)
        y_shift += leading
    return y - y_shift


def _dessiner_rapport_pour_un_eleve(c, resultat_copie):
    """
    Dessine le rapport complet d'un élève - VERSION COMPACTE
    """
    width, height = A4
    
    # Couleurs
    primary_blue = HexColor('#4285f4')
    red_color = HexColor('#ef4444')
    text_primary = HexColor('#202124')
    text_secondary = HexColor('#5f6368')
    light_bg = HexColor('#f8f9fa')

    # ========== EN-TÊTE COMPACT ==========
    c.setFillColor(primary_blue)
    c.rect(0, height - 2.5 * cm, width, 2.5 * cm, fill=1, stroke=0)
    
    c.setFillColor(HexColor('#ffffff'))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.5 * cm, height - 1.3 * cm, "Rapport de Correction")
    
    nom_eleve = resultat_copie.get('nom_eleve', 'N/A')
    classe_eleve = resultat_copie.get('classe', 'N/A')
    c.setFont("Helvetica", 11)
    c.drawString(1.5 * cm, height - 2 * cm, f"{nom_eleve} - {classe_eleve}")
    
    # Note finale (à droite)
    note = resultat_copie.get("note_finale", 0)
    c.setFont("Helvetica-Bold", 20)
    note_text = f"Note : {note:.1f}/20"
    note_width = c.stringWidth(note_text, "Helvetica-Bold", 20)
    c.drawString(width - note_width - 1.5 * cm, height - 1.5 * cm, note_text)

    # ========== DÉTAILS PAR QUESTION (COMPACT) ==========
    y = height - 3.2 * cm
    details = resultat_copie.get("details", [])
    max_text_width = width - 3.5 * cm

    for idx, bloc in enumerate(details, 1):
        for num_q, res in bloc.items():
            # Vérifier s'il reste assez de place (minimum 4cm)
            if y < 4 * cm:
                c.showPage()
                y = height - 1.5 * cm
            
            # ========== TITRE QUESTION (COMPACT) ==========
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(text_primary)
            
            points = res.get('points_obtenus', 0)
            categorie = res.get('categorie', '')
            
            # Titre : "Exercice 1 - PARTIELLE - 2.5 pts"
            titre = f"{num_q} - {categorie} - {points} pts"
            c.drawString(1.5 * cm, y, titre)
            y -= 0.5 * cm
            
            # ========== FEEDBACK (COMPACT) ==========
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(text_primary)
            c.drawString(1.5 * cm, y, "Feedback :")
            y -= 0.35 * cm
            
            c.setFont("Helvetica", 9)
            c.setFillColor(text_primary)
            feedback_text = res.get('feedback_detaille', 'Aucun feedback.')
            y = draw_wrapped_text(c, feedback_text, 1.5 * cm, y, max_text_width, "Helvetica", 9, 11)
            y -= 0.4 * cm
            
            # ========== ÉLÉMENTS CORRECTS (INLINE) ==========
            elements_corrects = res.get('elements_corrects', [])
            if elements_corrects and len(elements_corrects) > 0:
                c.setFont("Helvetica-Bold", 9)
                c.setFillColor(text_primary)
                c.drawString(1.5 * cm, y, "Éléments corrects :")
                y -= 0.35 * cm
                
                c.setFont("Helvetica", 8)
                for element in elements_corrects:
                    c.drawString(2 * cm, y, f"• {element}")
                    y -= 0.3 * cm
                y -= 0.2 * cm
            
            # ========== ÉLÉMENTS MANQUANTS (INLINE) ==========
            elements_manquants = res.get('elements_manquants', [])
            if elements_manquants and len(elements_manquants) > 0:
                c.setFont("Helvetica-Bold", 9)
                c.setFillColor(text_primary)
                c.drawString(1.5 * cm, y, "Éléments manquants :")
                y -= 0.35 * cm
                
                c.setFont("Helvetica", 8)
                for element in elements_manquants:
                    c.drawString(2 * cm, y, f"• {element}")
                    y -= 0.3 * cm
                y -= 0.2 * cm
            
            # ========== ERREURS DÉTECTÉES (INLINE) ==========
            erreurs = res.get('erreurs_detectees', [])
            if erreurs and len(erreurs) > 0:
                c.setFont("Helvetica-Bold", 9)
                c.setFillColor(text_primary)
                c.drawString(1.5 * cm, y, "Erreurs détectées :")
                y -= 0.35 * cm
                
                c.setFont("Helvetica", 8)
                for erreur in erreurs:
                    c.drawString(2 * cm, y, f"• {erreur}")
                    y -= 0.3 * cm
                y -= 0.2 * cm
            
            # ========== CONSEIL DE RÉVISION (ROUGE COMPACT) ==========
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(red_color)
            c.drawString(1.5 * cm, y, "Conseil de révision :")
            y -= 0.35 * cm
            
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(red_color)
            conseil_text = res.get('conseil_revision', 'Aucun conseil.')
            y = draw_wrapped_text(c, conseil_text, 1.5 * cm, y, max_text_width, "Helvetica-Bold", 9, 11)
            y -= 0.5 * cm
            
            # Séparateur léger entre questions
            if y > 3 * cm and idx < len(details):
                c.setStrokeColor(HexColor('#e4e6eb'))
                c.setLineWidth(0.5)
                c.line(1.5 * cm, y, width - 1.5 * cm, y)
                y -= 0.4 * cm

    # ========== PIED DE PAGE ==========
    c.setFont("Helvetica", 7)
    c.setFillColor(text_secondary)
    footer_text = f"Généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')} - Pour toute question, contactez le professeur."
    c.drawString(1.5 * cm, 1 * cm, footer_text)


def generer_rapport_consolide_pdf(resultats_session: list, output_filename: str):
    """
    Génère UN SEUL fichier PDF contenant les rapports de tous les élèves.
    """
    if not os.path.exists(EXPORT_FOLDER):
        os.makedirs(EXPORT_FOLDER)

    file_path = os.path.join(EXPORT_FOLDER, output_filename)
    c = canvas.Canvas(file_path, pagesize=A4)

    for i, resultat_copie in enumerate(resultats_session):
        _dessiner_rapport_pour_un_eleve(c, resultat_copie)

        if i < len(resultats_session) - 1:
            c.showPage()

    c.save()
    return file_path