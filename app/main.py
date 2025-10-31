from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
from typing import List
import uuid
import os
from fastapi_offline import FastAPIOffline

from app.config import CORS_ORIGINS, UPLOAD_FOLDER, EPREUVES_FOLDER, COPIES_FOLDER, CORRECTIONS_FOLDER
from app.services.file_service import validate_file, save_file
from app.services.correction_service import lancer_correction_automatique
from app.services.report_service import generer_rapport_consolide_pdf
from app.database import sessions
from app.services.split_copies_service import decouper_copies_par_eleve

app = FastAPIOffline(
    title="API Correction Automatique",
    description="API pour corriger automatiquement des copies d'examens avec l'IA",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(COPIES_FOLDER, exist_ok=True)
    os.makedirs(CORRECTIONS_FOLDER, exist_ok=True)
    os.makedirs(EPREUVES_FOLDER, exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    print("🚀 Démarrage de l'API de correction automatique.")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Arrêt de l'API.")


@app.get("/")
def root():
    return {"message": "API de correction automatique en marche"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/sessions")
def list_sessions():
    """Liste toutes les sessions avec informations basiques"""
    return {
        "total_sessions": len(sessions),
        "sessions": {
            session_id: {
                "status": data.get("status", "unknown"),
                "has_epreuve": "epreuve" in data and data["epreuve"] is not None,
                "copies_count": len(data.get("copies", [])),
                "has_correction": "correction" in data and data["correction"] is not None
            }
            for session_id, data in sessions.items()
        }
    }


# ✅ NOUVEAU : Endpoint pour récupérer les détails complets d'une session
@app.get("/sessions/{session_id}")
def get_session_details(session_id: str):
    """Récupère les détails complets d'une session spécifique"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    session_data = sessions[session_id]

    return {
        "id": session_data.get("id", session_id),
        "status": session_data.get("status", "unknown"),
        "created_at": session_data.get("created_at", datetime.now().isoformat()),
        "epreuve": session_data.get("epreuve"),
        "correction": session_data.get("correction"),
        "copies": session_data.get("copies", []),
        "results": session_data.get("results")
    }


@app.post("/upload-copies-bundle")
async def upload_copies_bundle(file: UploadFile = File(...)):
    validate_file(file)
    file_path = await save_file(file, COPIES_FOLDER.split(os.sep)[-1])
    groupes_par_eleve = decouper_copies_par_eleve(file_path)

    if not groupes_par_eleve:
        os.remove(file_path)
        raise HTTPException(status_code=400,
                            detail="Aucun élève n'a pu être détecté dans le fichier. Assurez-vous que le nom et la classe sont bien visibles.")

    session_id = str(uuid.uuid4())
    copies_pour_session = []

    for (nom, classe), pages in groupes_par_eleve.items():
        texte_complet_eleve = "\n\n--- NOUVELLE PAGE ---\n\n".join([p["texte"] for p in pages])
        copies_pour_session.append({
            "nom_eleve": nom,
            "classe": classe,
            "texte_complet": texte_complet_eleve,
            "pages_sources": [p["page_num"] for p in pages]
        })

    sessions[session_id] = {
        "id": session_id,
        "epreuve": None,
        "copies": copies_pour_session,
        "correction": None,
        "status": "copies_uploaded",
        "created_at": datetime.now().isoformat(),
        "results": None
    }
    os.remove(file_path)

    return {
        "message": "Fichier de copies groupées uploadé et découpé par élève.",
        "session_id": session_id,
        "eleves_detectes": [
            {"nom": c["nom_eleve"], "classe": c["classe"], "pages": c["pages_sources"]} for c in copies_pour_session
        ]
    }


@app.post("/upload-epreuve/{session_id}")
async def upload_epreuve(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    validate_file(file)
    file_path = await save_file(file, EPREUVES_FOLDER.split(os.sep)[-1])
    sessions[session_id]["epreuve"] = {"filename": file.filename, "path": file_path}
    sessions[session_id]["status"] = "epreuve_uploaded"
    return {"message": "Épreuve uploadée.", "session_id": session_id}


@app.post("/upload-correction/{session_id}")
async def upload_correction(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    validate_file(file)
    file_path = await save_file(file, CORRECTIONS_FOLDER.split(os.sep)[-1])
    sessions[session_id]["correction"] = {"filename": file.filename, "path": file_path}
    sessions[session_id]["status"] = "ready_to_correct"
    return {"message": "Correction du professeur uploadée.", "session_id": session_id}


@app.post("/corriger/{session_id}", summary="Lance la correction automatique d'une session")
def corriger_session(session_id: str):
    try:
        resultats = lancer_correction_automatique(session_id)
        if isinstance(resultats, dict) and "error" in resultats:
            raise HTTPException(status_code=500, detail=resultats["error"])
        return {"message": "Correction terminée", "session_id": session_id, "resultats": resultats}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur inattendue est survenue: {str(e)}")


@app.get("/export-pdf/{session_id}", summary="Génère un rapport PDF consolidé pour une session")
def export_pdf_consolide(session_id: str):
    if session_id not in sessions or not sessions[session_id].get("results"):
        raise HTTPException(status_code=404, detail="Session ou résultats introuvables.")

    resultats = sessions[session_id]["results"]
    output_filename = f"rapport_consolide_{session_id}.pdf"

    pdf_path = generer_rapport_consolide_pdf(resultats, output_filename)

    # ✅ FIX : Retourner juste le nom du fichier, pas le chemin complet
    return {"pdf_consolidated_report": output_filename}


@app.get("/download-pdf/{filename}")
def download_pdf(filename: str):
    file_path = os.path.join("exports", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF non trouvé.")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """🗑️ Supprime une session INACHEVÉE (fichiers + DB)"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    # ✅ OPTIONNEL : Bloque si terminée
    if sessions[session_id].get("status") == "corrected":
        raise HTTPException(status_code=400, detail="Impossible de supprimer une session terminée.")

    # 🧹 Nettoie fichiers (ajoute import shutil)
    import shutil
    session_data = sessions[session_id]

    # Supprime fichiers spécifiques
    for file_key in ["epreuve", "correction"]:
        if file_key in session_data and session_data[file_key]:
            file_path = session_data[file_key]["path"]
            if os.path.exists(file_path):
                os.remove(file_path)

    # Supprime dossier copies de cette session (si tu en as un par session)
    # copies_dir = os.path.join(COPIES_FOLDER, session_id)
    # if os.path.exists(copies_dir): shutil.rmtree(copies_dir)

    # 🗑️ Supprime de DB
    del sessions[session_id]

    return {"message": "Session supprimée avec succès."}