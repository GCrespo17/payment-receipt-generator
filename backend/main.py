from fastapi import FastAPI
from app.routes.receipt_gen_routes import router as receipt_router

app = FastAPI()
app.include_router(receipt_router, prefix="/api/v1", tags=["payment_receipts"])
