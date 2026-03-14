from dataclasses import dataclass

@dataclass()
class PDFHeader():
    company_name:str
    rif:str
    doc_type:str
    doc_number:str
    sent_date:str
    process_date:str

@dataclass()
class PDFPaymentData():
    information_type:str
    reference:str
    ci_rif:str
    name:str
    account_number:str
    amount:str
    status:str

