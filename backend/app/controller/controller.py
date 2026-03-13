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

def get_session(session_id:uuid.UUID)->SessionData:
    session = sessions.get(session_id)
    if session is None:
        raise ValueError("Session not Found")
    return session


async def load_excel(session_id:uuid.UUID, file:UploadFile)->list[str]:
    is_valid = dir_management.is_file_name_valid(file)
    if not is_valid:
        raise ValueError("Invalid file name")

    session = get_session(session_id)
    
    excel_path = await dir_management.store_excel_to_dir(session.session_directory, file)
    session.excel_path = excel_path

    return data_ingestion.extract_sheet_names_from_excel(excel_path)

def load_sheet_names(session_id:uuid.UUID, req_payment_sheet:str, recv_payment_sheet:str)->None:
    session = get_session(session_id)
    session.recv_payment_sheet = recv_payment_sheet
    session.req_payment_sheet = req_payment_sheet

def load_indexes(session_id:uuid.UUID, req_payment_index:int, recv_payment_index:int)->None:
    def adjusted_index(index:int)->int:
        if index == 0:
            return 0
        else:
            return index-1
    session = get_session(session_id)
    session.recv_payment_header_index = adjusted_index(recv_payment_index)
    session.req_payment_header_index = adjusted_index(req_payment_index)


def recv_payment_columns(session_id:uuid.UUID)->list[str]:
    session = get_session(session_id)
    excel_path = session.excel_path
    sheet_name = session.recv_payment_sheet
    header_index = session.recv_payment_header_index

    if excel_path is None:
        raise ValueError("Could not find the excel")
    if sheet_name is None:
        raise ValueError("Invalid Sheet Name")
    if header_index is None:
        raise ValueError("Invalid Header Index")

    data_frame = data_ingestion.extract_data_from_excelsheet(excel_path, sheet_name, header_index)
    columns = data_ingestion.extract_column_names(data_frame)
    return columns

def req_payment_columns(session_id:uuid.UUID)->list[str]:
    session = get_session(session_id)
    excel_path = session.excel_path
    sheet_name = session.req_payment_sheet
    header_index = session.req_payment_header_index

    if excel_path is None:
        raise ValueError("Could not find the excel")
    if sheet_name is None:
        raise ValueError("Invalid Sheet Name")
    if header_index is None:
        raise ValueError("Invalid Header Index")

    data_frame = data_ingestion.extract_data_from_excelsheet(excel_path, sheet_name, header_index)
    columns = data_ingestion.extract_column_names(data_frame)
    return columns

def load_row_names(session_id:uuid.UUID, req_payment_column:str, recv_payment_column:str)->None:
    session = get_session(session_id)
    session.req_payment_column_name = req_payment_column
    session.recv_payment_column_name = recv_payment_column



    

    





