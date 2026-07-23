"""API Router for /v1/query, /v1/history, and /v1/feedback endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.application.dtos.query_dto import TextToSQLRequestDTO, FeedbackRequestDTO
from src.domain.entities.query import QueryRequest
from src.domain.exceptions.domain_exceptions import GuardrailViolationException, SQLSyntaxException
from src.presentation.api.dependencies import (
    get_pipeline_use_case,
    get_submit_feedback_use_case,
    get_history_repository
)
from src.application.use_cases.process_text_to_sql import ProcessTextToSQLUseCase
from src.application.use_cases.submit_feedback import SubmitFeedbackUseCase
from src.infrastructure.history.history_repository import QueryHistoryRepository

router = APIRouter(prefix="/v1", tags=["Query Engine"])


@router.post("/query", status_code=status.HTTP_200_OK)
def process_query(
    dto: TextToSQLRequestDTO,
    use_case: ProcessTextToSQLUseCase = Depends(get_pipeline_use_case),
    history_repo: QueryHistoryRepository = Depends(get_history_repository),
):
    """Processes natural language question into validated SQL, executes it safely, and records session history."""
    try:
        req = QueryRequest(question=dto.question, session_id=dto.session_id)
        response = use_case.execute(req)
        # Store execution in session history
        history_repo.add_entry(dto.session_id, response)
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


@router.get("/history", status_code=status.HTTP_200_OK)
def get_query_history(
    session_id: str = Query(default="default_session", description="Session ID filter"),
    limit: int = Query(default=50, ge=1, le=100, description="Max history items returned"),
    history_repo: QueryHistoryRepository = Depends(get_history_repository),
):
    """Retrieves past queries and results for the given session."""
    return history_repo.get_session_history(session_id=session_id, limit=limit)


@router.post("/feedback", status_code=status.HTTP_200_OK)
def submit_feedback(
    dto: FeedbackRequestDTO,
    use_case: SubmitFeedbackUseCase = Depends(get_submit_feedback_use_case),
):
    """Submits user feedback to flywheel repository."""
    return use_case.execute(dto)
