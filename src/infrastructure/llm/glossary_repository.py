"""Repository for managing business glossary metrics and column domain terminology."""

from src.domain.entities.prompt import BusinessTerm


class BusinessGlossaryRepository:
    """Manages enterprise business metrics and vocabulary definitions for prompt disambiguation."""

    DEFAULT_TERMS: list[BusinessTerm] = [
        BusinessTerm(
            term="revenue",
            definition="Total gross sales amount from completed orders (excluding cancelled or refunded orders).",
            sql_expression="SUM(amount) WHERE status = 'completed'"
        ),
        BusinessTerm(
            term="active customer",
            definition="A customer who has placed at least one completed order within the last 30 days.",
            sql_expression="user_id IN (SELECT DISTINCT user_id FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '30 days')"
        ),
        BusinessTerm(
            term="completed order",
            definition="An order with status equal to 'completed' or 'shipped'.",
            sql_expression="status IN ('completed', 'shipped')"
        ),
        BusinessTerm(
            term="churned customer",
            definition="A customer who registered over 90 days ago but has placed zero orders in the last 90 days.",
            sql_expression="user_id NOT IN (SELECT user_id FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '90 days')"
        )
    ]

    def __init__(self, custom_terms: list[BusinessTerm] | None = None) -> None:
        self.terms = custom_terms if custom_terms is not None else list(self.DEFAULT_TERMS)

    def find_matching_terms(self, question: str) -> list[BusinessTerm]:
        """Finds glossary terms present in the user question for prompt context injection."""
        q_lower = question.lower()
        matched = []
        for term_obj in self.terms:
            if term_obj.term.lower() in q_lower:
                matched.append(term_obj)
        return matched
