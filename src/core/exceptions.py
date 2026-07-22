"""Base application level exception definitions."""


class BaseAppException(Exception):
    """Base exception class for all application errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationException(BaseAppException):
    """Raised when application configuration is invalid or missing."""
    pass


class InfrastructureException(BaseAppException):
    """Raised when an infrastructure dependency (DB, LLM, Vector Store) fails."""
    pass
