"""API Router for /v1/query and /v1/feedback endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from src.application.dtos.query_dto import TextToSQLRequestDTO, FeedbackRequestDTO
from src.domain.entities.query import QueryRequest
from src.domain.exceptions.domain_exceptions import GuardrailViolationException, SQLSyntaxException
from src.presentation.api.dependencies import get_pipeline_use_case, get_submit_feedback_use_case
from src.application.use_cases.process_text_to_sql import ProcessTextToSQLUseCase
from src.application.use_cases.submit_feedback import SubmitFeedbackUseCase

router = APIRouter(prefix="/v1", tags=["Query Engine"])


@router.post("/query", status_code=status.HTTP_200_OK)
def process_query(
    dto: TextToSQLRequestDTO,
    use_case: ProcessTextToSQLUseCase = Depends(get_pipeline_use_case),
):
    """Processes natural language question into validated SQL and executes it."""
    try:
        req = QueryRequest(question=dto.question, session_id=dto.session_id)
        response = use_case.execute(req)
        return response
    except GuardrailViolationException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "GuardrailViolation", "message": exc.message}
        )
    except SQLSyntaxException as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "SQLSyntaxError", "message": exc.message}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "message": str(exc)}
        )


@router.post("/feedback", status_code=status.HTTP_200_OK)
def submit_feedback(
    dto: FeedbackRequestDTO,
    use_case: SubmitFeedbackUseCase = Depends(get_submit_feedback_use_case),
):
    """Submits user feedback to flywheel repository."""
    return use_case.execute(dto)
