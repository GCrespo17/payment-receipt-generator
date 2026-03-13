from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass()
class SessionData():
    session_directory:Path
    excel_path:Optional[Path] = None
    recv_payment_sheet:Optional[str] = None
    recv_payment_header_index: Optional[int] = None
    recv_payment_column_name:Optional[str] = None
    req_payment_sheet:Optional[str] = None
    req_payment_header_index:Optional[int] = None
    req_payment_column_name:Optional[str] = None
    
