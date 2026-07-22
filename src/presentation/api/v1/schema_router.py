"""API Router for /v1/schema endpoints."""

from fastapi import APIRouter, Depends, status
from src.presentation.api.dependencies import get_extract_schema_use_case
from src.application.use_cases.extract_schema import ExtractSchemaUseCase

router = APIRouter(prefix="/v1", tags=["Schema Engine"])


@router.get("/schema", status_code=status.HTTP_200_OK)
def get_schema(
    use_case: ExtractSchemaUseCase = Depends(get_extract_schema_use_case),
):
    """Retrieves introspected database schema."""
    return use_case.execute()
