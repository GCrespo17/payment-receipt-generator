from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import app.controller.controller as controller
from app.schemas.responses import SessionCreation
class UploadResponse(BaseModel):
    user_id:str
    file_name:str

router = APIRouter(prefix="/receipts")

@router.post("/excel_sheet", response_model=SessionCreation, status_code=201)
async def upload_excel_sheet(file:UploadFile = File(...))->SessionCreation:
    try:
        session = controller.create_session()
        sheet_names = await controller.load_excel(session, file)
        return SessionCreation(
            session_id=session,
            sheet_names=sheet_names
        )
    except ValueError as exception:
        raise HTTPException(status_code=400, detail=str(exception))



