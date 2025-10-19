import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ====================================
# CONFIGURATION DES API D'IA
# ====================================

# Clés API pour les 3 services
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Choix de l'IA à utiliser : "gemini", "deepseek" ou "groq"
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")  # Par défaut : Gemini

# Configuration des modèles
AI_MODELS = {
    "gemini": "gemini-pro",
    "groq": "llama3-8b-8192"
}

# ====================================
# CONFIGURATION DES FICHIERS
# ====================================

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}

# Taille maximale des fichiers : 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB en bytes

# Dossier principal pour les uploads
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

# Sous-dossiers
COPIES_FOLDER = os.path.join(UPLOAD_FOLDER, "copies")
CORRECTIONS_FOLDER = os.path.join(UPLOAD_FOLDER, "corrections")
EPREUVES_FOLDER = os.path.join(UPLOAD_FOLDER, "epreuves") # <--- NOUVELLE LIGNE
EXPORTS_FOLDER = "exports"

# Sous-dossiers
COPIES_FOLDER = os.path.join(UPLOAD_FOLDER, "copies")

CORRECTIONS_FOLDER = os.path.join(UPLOAD_FOLDER, "corrections")
EXPORTS_FOLDER = "exports"

# ====================================
# CONFIGURATION TESSERACT (OCR)
# ====================================

# Chemin vers Tesseract
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")

# ====================================
# CONFIGURATION API
# ====================================

# Port du serveur
API_PORT = int(os.getenv("API_PORT", 8001))

# Liste des origines autorisées pour CORS (frontend)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]


