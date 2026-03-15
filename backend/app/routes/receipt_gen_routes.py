import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import app.controller.controller as controller
from app.schemas.responses import SessionCreation, SheetNameRequest, SheetNameResponse, GeneratePDFRequest
class UploadResponse(BaseModel):
    user_id:str
    file_name:str

router = APIRouter(prefix="/receipts")

@router.post("/excel_file", response_model=SessionCreation, status_code=201)
async def upload_excel_file(file:UploadFile = File(...))->SessionCreation:
    try:
        session = controller.create_session()
        sheet_names = await controller.load_excel(session, file)
        return SessionCreation(
            session_id=session,
            sheet_names=sheet_names
        )
    except ValueError as exception:
        raise HTTPException(status_code=400, detail=str(exception))

@router.post("/excel_sheets", response_model=SheetNameResponse)
def upload_sheet_names(request_values:SheetNameRequest)->SheetNameResponse:
    session_id = request_values.session_id
    req_payment_sheet = request_values.req_payment_sheet
    recv_payment_sheet = request_values.recv_payment_sheet
    req_payment_index = request_values.req_payment_index
    recv_payment_index = request_values.recv_payment_index
    try:
        controller.load_sheet_names(session_id, req_payment_sheet, recv_payment_sheet)
        controller.load_indexes(session_id, req_payment_index, recv_payment_index)
        return SheetNameResponse(
            req_payment_columns=controller.req_payment_columns(session_id),
            recv_payment_columns=controller.recv_payment_columns(session_id)
        )
    except ValueError as exception:
        raise HTTPException(status_code=400, detail=str(exception))

@router.post("/columns", status_code=200)
def input_columns(session_id:uuid.UUID, req_column:str, recv_column:str)->None:
    controller.load_column_names(session_id, req_column, recv_column)

@router.post("/pdf", status_code=201)
def create_pdf_batch(request_values:GeneratePDFRequest):
    try:
        controller.generate_all_pdf(request_values.session_id, request_values.pdf_header)
    except ValueError as exception:
        raise HTTPException(status_code=400, detail=str(exception))

@router.get("/zip", status_code=200)
async def download_pdfs(session_id:uuid.UUID, background_tasks:BackgroundTasks):
    try:
        return controller.get_zip_file_response(session_id, background_tasks)
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))







