from fastapi import UploadFile 
from fastapi.responses import FileResponse
import uuid
import app.services.directory_management as dir_management
import app.services.data_ingestion as data_ingestion
from app.services.pdf_generation import generate_pdf
from app.models.session_data import SessionData
from app.models.pdf_data import PDFHeader, PDFPaymentData
from app.services.compression import zip_pdf_directory


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

def load_column_names(session_id:uuid.UUID, req_payment_column:str, recv_payment_column:str)->None:
    session = get_session(session_id)
    session.req_payment_column_name = req_payment_column
    session.recv_payment_column_name = recv_payment_column


def generate_all_pdf(session_id:uuid.UUID, pdf_header:PDFHeader)->None:
    session = get_session(session_id)
    excel_path = session.excel_path
    req_payment_sheet = session.req_payment_sheet
    req_payment_index = session.req_payment_header_index
    req_payment_column = session.req_payment_column_name

    recv_payment_sheet = session.recv_payment_sheet
    recv_payment_index = session.recv_payment_header_index
    recv_payment_column = session.recv_payment_column_name

    if excel_path is None:
        raise ValueError("There is no excel in the server")
    if req_payment_sheet is None or recv_payment_sheet is None:
        raise ValueError("A sheet name is missing")
    if req_payment_index is None or recv_payment_index is None:
        raise ValueError("A header index is misssing")
    if req_payment_column is None or recv_payment_column is None:
        raise ValueError("A comparison column is missing")

    req_payment_data = data_ingestion.extract_data_from_excelsheet(
        excel_path,
        req_payment_sheet,
        req_payment_index,
    )

    recv_payment_data = data_ingestion.extract_data_from_excelsheet(
        excel_path,
        recv_payment_sheet,
        recv_payment_index
    )

    data_ingestion.clean_numeric_column(req_payment_data, req_payment_column)
    data_ingestion.clean_numeric_column(recv_payment_data, recv_payment_column)

    company_payment_data = data_ingestion.intersection_of_payments(
        req_payment_data,
        req_payment_column,
        recv_payment_data,
        recv_payment_column
    )

    data_ingestion.clean_numeric_column(company_payment_data, recv_payment_column)

    for _, row in company_payment_data.iterrows():
        payment_data = PDFPaymentData(
            information_type = data_ingestion.data_to_text(row.get("TIPO DE INFORMACIÓN")),
            reference = data_ingestion.normalize_reference(data_ingestion.data_to_text(row.get("REFERENCIA"))),
            ci_rif = data_ingestion.data_to_text(row.get("C.I/R.I.F")),
            name = data_ingestion.data_to_text(row.get("NOMBRE")),
            account_number = data_ingestion.data_to_text(row.get("NÚMERO DE CUENTA")),
            amount = data_ingestion.format_currency_ve(data_ingestion.data_to_text(row.get("MONTO"))),
            status = data_ingestion.data_to_text(row.get("ESTATUS")),
        )
        generate_pdf(pdf_header, payment_data, session.session_directory, data_ingestion.normalize_reference(data_ingestion.data_to_text(row.get("REFERENCIA"))))


def get_zip_file_response(session_id:uuid.UUID)->FileResponse:
    session = get_session(session_id)
    zip_path = zip_pdf_directory(session.session_directory)
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=str(session_id)
    )

