from fastapi import UploadFile
import uuid
import app.services.directory_management as dir_management
import app.services.data_ingestion as data_ingestion
from app.models.session_data import SessionData

sessions:dict[uuid.UUID, SessionData] = {}

def create_session()->uuid.UUID:
    new_session_id = uuid.uuid4()
    new_session_dir = dir_management.create_session_dir(new_session_id)
    new_session = SessionData(session_directory=new_session_dir)
    sessions[new_session_id] = new_session
    return new_session_id

async def load_excel(session_id:uuid.UUID, file:UploadFile)->list[str]:
    is_valid = dir_management.is_file_name_valid(file)
    if not is_valid:
        raise ValueError("Invalid file name")

    session = sessions.get(session_id)
    if session is None:
        raise ValueError("Session not Found")
    
    excel_path = await dir_management.store_excel_to_dir(session.session_directory, file)
    session.excel_path = excel_path

    return data_ingestion.extract_sheet_names_from_excel(excel_path)






