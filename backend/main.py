from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.receipt_gen_routes import router as receipt_router
import app.services.directory_management as dir_management

@asynccontextmanager
async def lifespan(app: FastAPI):
    dir_management.cleanup_storage_dir_on_startup()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(receipt_router, prefix="/api/v1", tags=["payment_receipts"])
