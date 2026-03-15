from pathlib import Path
from fastapi import UploadFile
import uuid
import logging
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = PROJECT_ROOT / "tmp"

def create_session_dir(session_id:uuid.UUID)->Path:
    session_id_string = str(session_id)
    new_session_dir = STORAGE_DIR / session_id_string
    new_session_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created directory for session {session_id_string}")
    return new_session_dir

def is_file_name_valid(file:UploadFile)->bool:
    if not file.filename:
        return False

    extension = Path(file.filename).suffix.lower()
    if extension not in {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"}:
        return False

    return True

async def store_excel_to_dir(session_directory:Path, file:UploadFile)->Path:
    if file.filename is None:
        file.filename = "temporary_file"
    normalized = file.filename.replace("\\", '/')
    safe_name = Path(normalized).name
    destination = session_directory / safe_name
    try:
        with destination.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
        return destination
    finally:
        await file.close()

def cleanup_session_artifacts(session_id:uuid.UUID, session_directory:Path, zip_path:Path)->None:
    try:
        zip_path.unlink(missing_ok=True)
    except Exception as exception:
        logging.warning(f"Failed to remove zip for session {session_id}: {exception}")
    try:
        shutil.rmtree(session_directory)
    except FileNotFoundError:
        return
    except Exception as exception:
        logging.warning(
            f"Failed to remove directory for session {session_id}: {exception}"
        )

