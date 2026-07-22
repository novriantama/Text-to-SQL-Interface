"""Global pytest test fixtures and configuration."""

import pytest
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter
from src.infrastructure.llm.prompt_builder import DynamicPromptBuilder


@pytest.fixture
def guardrail_adapter():
    return ASTGuardrailAdapter()


@pytest.fixture
def prompt_builder():
    return DynamicPromptBuilder()
