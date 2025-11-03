"""
Service OCR HYBRIDE INTELLIGENT
- Tesseract (gratuit, illimité) pour texte IMPRIMÉ
- OCR.space (25000/mois) pour texte MANUSCRIT
- Détection automatique du type de document
- Support PDF + IMAGES (JPG, PNG)
"""
import os
import cv2
import numpy as np
import pytesseract
import requests
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ====================================
# CONFIGURATION
# ====================================

USAGE_FILE = "ocr_usage.txt"
API_KEY = os.getenv("OCRSPACE_API_KEY", "K87899142388957")
MONTHLY_LIMIT = 25000
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ====================================
# COMPTEUR D'USAGE OCR.SPACE
# ====================================

def get_usage_count():
    """Lit le compteur d'usage du mois en cours"""
    if not os.path.exists(USAGE_FILE):
        return 0, datetime.now().strftime("%Y-%m")
    
    try:
        with open(USAGE_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return 0, datetime.now().strftime("%Y-%m")
            count = int(lines[0].strip())
            month = lines[1].strip()
            return count, month
    except:
        return 0, datetime.now().strftime("%Y-%m")


def update_usage():
    """Incrémente le compteur OCR.space"""
    current_month = datetime.now().strftime("%Y-%m")
    count, saved_month = get_usage_count()
    
    if current_month != saved_month:
        count = 0
    
    count += 1
    
    with open(USAGE_FILE, 'w') as f:
        f.write(f"{count}\n")
        f.write(f"{current_month}\n")
    
    return count


def get_remaining_quota():
    """Retourne le nombre de requêtes restantes ce mois"""
    count, _ = get_usage_count()
    return MONTHLY_LIMIT - count


def print_quota_status():
    """Affiche le quota au démarrage"""
    usage, month = get_usage_count()
    remaining = get_remaining_quota()
    percent = (usage / MONTHLY_LIMIT) * 100
    
    print("\n" + "="*60)
    print("📊 STATUT OCR HYBRIDE")
    print("="*60)
    print(f"  🖨️  Tesseract (imprimé) : ILLIMITÉ (local)")
    print(f"  ✍️  OCR.space (manuscrit) : {remaining:,} / {MONTHLY_LIMIT:,}")
    print(f"  📅 Mois : {month}")
    print(f"  📈 Utilisées : {usage:,} ({percent:.1f}%)")
    
    if remaining < 1000:
        print(f"  ⚠️ ATTENTION : Il reste moins de 1000 requêtes OCR.space !")
    elif remaining < 5000:
        print(f"  ⚠️ Attention : Il reste moins de 5000 requêtes OCR.space")
    else:
        print(f"  ✅ Quota OK")
    
    print("="*60 + "\n")


# ====================================
# DÉTECTION TYPE DE DOCUMENT
# ====================================

def detect_document_type(image: Image.Image) -> str:
    """
    Détecte si une image contient du texte MANUSCRIT ou IMPRIMÉ.
    
    Returns:
        "printed" ou "handwritten"
    """
    try:
        open_cv_image = np.array(image.convert('RGB'))
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
        
        data = pytesseract.image_to_data(gray, lang='fra', output_type=pytesseract.Output.DICT)
        
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        
        if not confidences:
            return "handwritten"
        
        avg_confidence = sum(confidences) / len(confidences)
        
        print(f"    📊 Confiance Tesseract : {avg_confidence:.1f}%")
        
        if avg_confidence > 75:
            return "printed"
        else:
            return "handwritten"
    
    except Exception as e:
        print(f"    ⚠️ Erreur détection : {e}. Défaut : manuscrit")
        return "handwritten"


# ====================================
# OCR AVEC TESSERACT (GRATUIT)
# ====================================

def preprocess_image_for_tesseract(image: Image.Image) -> Image.Image:
    """Pré-traite une image pour Tesseract"""
    open_cv_image = np.array(image)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    final_image = cv2.bitwise_not(thresh)
    return Image.fromarray(final_image)


def ocr_with_tesseract(image: Image.Image) -> str:
    """Extrait le texte avec Tesseract (GRATUIT, illimité)"""
    try:
        preprocessed_img = preprocess_image_for_tesseract(image)
        texte = pytesseract.image_to_string(preprocessed_img, lang="fra")
        return texte.strip()
    except Exception as e:
        print(f"    ❌ Erreur Tesseract : {e}")
        return ""


# ====================================
# OCR AVEC OCR.SPACE (API)
# ====================================

def ocr_with_ocrspace(image_path: str) -> str:
    """Extrait le texte avec OCR.space (manuscrit)"""
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'filename': f},
                data={
                    'apikey': API_KEY,
                    'language': 'fre',
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'scale': True,
                    'OCREngine': 2
                },
                timeout=30
            )
        
        result = response.json()
        
        if result.get('IsErroredOnProcessing'):
            error_msg = result.get('ErrorMessage', 'Erreur inconnue')
            print(f"    ❌ Erreur OCR.space : {error_msg}")
            return ""
        
        texte = result['ParsedResults'][0]['ParsedText']
        
        # Incrémenter le compteur
        usage = update_usage()
        remaining = get_remaining_quota()
        print(f"    📊 OCR.space : {usage}/{MONTHLY_LIMIT} ({remaining} restantes)")
        
        return texte
    
    except Exception as e:
        print(f"    ❌ Erreur OCR.space : {e}")
        return ""


# ====================================
# EXTRACTION D'IMAGE
# ====================================

def extract_text_from_image(image_path: str, force_mode=None) -> str:
    """
    Extrait le texte d'une IMAGE avec détection automatique.
    
    Args:
        image_path: Chemin vers l'image (JPG, PNG)
        force_mode: "tesseract", "ocrspace" ou None (auto)
        
    Returns:
        Texte extrait
    """
    try:
        image = Image.open(image_path)
        
        # Mode forcé
        if force_mode == "tesseract":
            print(f"  🖨️  Mode forcé : Tesseract")
            return ocr_with_tesseract(image)
        
        elif force_mode == "ocrspace":
            print(f"  ✍️  Mode forcé : OCR.space")
            return ocr_with_ocrspace(image_path)
        
        # Auto-détection
        else:
            doc_type = detect_document_type(image)
            
            if doc_type == "printed":
                print(f"  🖨️  Détecté : IMPRIMÉ → Tesseract (GRATUIT)")
                return ocr_with_tesseract(image)
            else:
                print(f"  ✍️  Détecté : MANUSCRIT → OCR.space (API)")
                return ocr_with_ocrspace(image_path)
    
    except Exception as e:
        print(f"  ❌ Erreur extraction : {e}")
        return ""


# ====================================
# EXTRACTION DE PDF
# ====================================

def extract_text_from_pdf(pdf_path: str, force_mode=None) -> str:
    """
    Extrait le texte d'un PDF avec détection automatique.
    
    Args:
        pdf_path: Chemin vers le PDF
        force_mode: "tesseract" (imprimé), "ocrspace" (manuscrit), None (auto)
        
    Returns:
        Texte extrait de toutes les pages
    """
    try:
        # Convertir PDF en images
        images = convert_from_path(pdf_path, dpi=300)
        
        # Détection sur la première page si mode auto
        if force_mode is None and images:
            doc_type = detect_document_type(images[0])
            
            if doc_type == "printed":
                print(f"  🖨️  Document IMPRIMÉ détecté → Tesseract (GRATUIT)")
                force_mode = "tesseract"
            else:
                print(f"  ✍️  Document MANUSCRIT détecté → OCR.space (API)")
                force_mode = "ocrspace"
        
        # Si OCR.space, envoyer le PDF directement (1 seule requête)
        if force_mode == "ocrspace":
            return _extract_pdf_with_ocrspace(pdf_path)
        
        # Si Tesseract, traiter page par page
        elif force_mode == "tesseract":
            return _extract_pdf_with_tesseract(images)
        
        else:
            return _extract_pdf_with_tesseract(images)
    
    except Exception as e:
        print(f"  ❌ Erreur extraction PDF : {e}")
        return ""


def _extract_pdf_with_tesseract(images: list) -> str:
    """Extrait le texte d'un PDF avec Tesseract (page par page)"""
    textes = []
    for i, img in enumerate(images):
        print(f"    - Page {i + 1}/{len(images)}...")
        texte = ocr_with_tesseract(img)
        textes.append(texte)
    
    return "\n\n--- PAGE SUIVANTE ---\n\n".join(textes)


def _extract_pdf_with_ocrspace(pdf_path: str) -> str:
    """Extrait le texte d'un PDF avec OCR.space (1 seule requête)"""
    try:
        with open(pdf_path, 'rb') as f:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'filename': f},
                data={
                    'apikey': API_KEY,
                    'language': 'fre',
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'scale': True,
                    'OCREngine': 2,
                    'isTable': True
                },
                timeout=60
            )
        
        result = response.json()
        
        if result.get('IsErroredOnProcessing'):
            error_msg = result.get('ErrorMessage', 'Erreur inconnue')
            print(f"    ❌ Erreur OCR.space : {error_msg}")
            return ""
        
        texte_complet = ""
        for page_result in result.get('ParsedResults', []):
            texte_complet += page_result.get('ParsedText', '') + "\n\n--- PAGE SUIVANTE ---\n\n"
        
        usage = update_usage()
        remaining = get_remaining_quota()
        print(f"    ✅ {len(texte_complet)} caractères")
        print(f"    📊 OCR.space : {usage}/{MONTHLY_LIMIT} ({remaining} restantes)")
        
        return texte_complet.strip()
    
    except Exception as e:
        print(f"    ❌ Erreur OCR.space : {e}")
        return ""


# ====================================
# FONCTION UNIVERSELLE
# ====================================

def extract_text_from_file(file_path: str, force_mode=None) -> str:
    """
    ✅ FONCTION PRINCIPALE : Extrait le texte de n'importe quel fichier.
    
    Args:
        file_path: Chemin vers le fichier (PDF, JPG, PNG)
        force_mode: "tesseract", "ocrspace" ou None (auto)
        
    Returns:
        Texte extrait
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    print(f"📄 Traitement : {os.path.basename(file_path)}")
    print(f"📋 Type : {file_ext}")
    
    # IMAGE
    if file_ext in ['.jpg', '.jpeg', '.png']:
        return extract_text_from_image(file_path, force_mode)
    
    # PDF
    elif file_ext == '.pdf':
        return extract_text_from_pdf(file_path, force_mode)
    
    else:
        print(f"  ❌ Format non supporté : {file_ext}")
        return ""