# Fonctions pour gérer les fichiers uploadés avec FastAPI : validation, sauvegarde, nettoyage et récupération d'informations

import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_FOLDER


def validate_file(file: UploadFile) -> bool:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400,
                            detail=f"Extension non autorisée. Formats acceptés : {', '.join(ALLOWED_EXTENSIONS)}")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400,
                            detail=f"Fichier trop volumineux. Taille max : {MAX_FILE_SIZE / (1024 * 1024):.1f} MB")

    return True


async def save_file(file: UploadFile, subfolder: str) -> str:
    destination_folder = os.path.join(UPLOAD_FOLDER, subfolder)
    os.makedirs(destination_folder, exist_ok=True)
    file_path = os.path.join(destination_folder, file.filename)

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde du fichier : {str(e)}")


def cleanup_folder(folder_path: str) -> None:
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage de {folder_path} : {str(e)}")


def get_file_info(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return None

    file_stats = os.stat(file_path)
    return {
        "name": os.path.basename(file_path),
        "path": file_path,
        "size": file_stats.st_size,
        "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
        "extension": os.path.splitext(file_path)[1]
    }