"""Combined API Version 1 Router."""

from fastapi import APIRouter
from src.presentation.api.v1.query_router import router as query_router
from src.presentation.api.v1.schema_router import router as schema_router

api_v1_router = APIRouter()
api_v1_router.include_router(query_router)
api_v1_router.include_router(schema_router)
