from pydantic import BaseModel
from uuid import UUID

class SessionCreation(BaseModel):
    session_id:UUID
    sheet_names:list[str]
