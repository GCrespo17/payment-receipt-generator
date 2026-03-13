from pathlib import Path
from fastapi import UploadFile
import uuid
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = PROJECT_ROOT / "tmp"

def create_user_dir(user_id:uuid.UUID)->Path:
    user_id_string = str(user_id)
    new_user_dir = STORAGE_DIR / user_id_string
    new_user_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created directory for user {user_id_string}")
    return new_user_dir

def is_file_name_valid(file:UploadFile)->bool:
    if not file.filename:
        return False

    extension = Path(file.filename).suffix.lower()
    if extension not in {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"}:
        return False

    return True

async def store_excel_to_dir(user_directory:Path, file:UploadFile)->Path:
    if file.filename is None:
        file.filename = "temporary_file"
    normalized = file.filename.replace("\\", '/')
    safe_name = Path(normalized).name
    destination = user_directory / safe_name
    try:
        with destination.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
        return destination
    finally:
        await file.close()

