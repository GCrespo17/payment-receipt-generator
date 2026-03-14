from pydantic import BaseModel
from uuid import UUID
from app.models.pdf_data import PDFHeader

class SessionCreation(BaseModel):
    session_id:UUID
    sheet_names:list[str]

class SheetNameRequest(BaseModel):
    session_id:UUID
    req_payment_sheet:str
    req_payment_index:int
    recv_payment_sheet:str
    recv_payment_index:int

class SheetNameResponse(BaseModel):
    req_payment_columns:list[str]
    recv_payment_columns:list[str]

class GeneratePDFRequest(BaseModel):
    session_id:UUID
    pdf_header:PDFHeader

