"""Repository for managing and retrieving relevant few-shot question-to-SQL pairs."""

from src.domain.entities.prompt import FewShotExample


class FewShotRepository:
    """Stores and dynamically retrieves 3-5 relevant question-to-SQL few-shot pairs."""

    DEFAULT_EXAMPLES: list[FewShotExample] = [
        FewShotExample(
            question="What is the total revenue for the current month?",
            sql="SELECT SUM(amount) AS total_revenue FROM orders WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE) AND status = 'completed';",
            explanation="Aggregates completed order amounts for the current month using PostgreSQL DATE_TRUNC.",
            tags=["revenue", "aggregation", "date_trunc", "orders"]
        ),
        FewShotExample(
            question="List top 5 customers by total order count.",
            sql="SELECT user_id, COUNT(*) AS total_orders FROM orders GROUP BY user_id ORDER BY total_orders DESC LIMIT 5;",
            explanation="Groups orders by user_id, counts total orders, and limits result to top 5.",
            tags=["customer", "top", "group_by", "limit", "orders"]
        ),
        FewShotExample(
            question="Find users who registered in 2024 but have no orders.",
            sql="SELECT u.id, u.username FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.created_at >= '2024-01-01' AND u.created_at < '2025-01-01' AND o.id IS NULL;",
            explanation="Uses LEFT JOIN to identify users with no matching orders.",
            tags=["join", "left_join", "null_check", "users", "orders"]
        ),
        FewShotExample(
            question="What is the average order value per product category?",
            sql="SELECT p.category, ROUND(AVG(o.amount), 2) AS avg_order_value FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.category ORDER BY avg_order_value DESC;",
            explanation="Joins orders and products tables, groups by category, and calculates rounded average.",
            tags=["join", "average", "group_by", "products", "orders"]
        ),
        FewShotExample(
            question="How many active customers placed orders in the last 30 days?",
            sql="SELECT COUNT(DISTINCT user_id) AS active_customer_count FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';",
            explanation="Counts distinct users using PostgreSQL date math with INTERVAL.",
            tags=["distinct", "count", "date_interval", "orders"]
        )
    ]

    def __init__(self, custom_examples: list[FewShotExample] | None = None) -> None:
        self.examples = custom_examples if custom_examples is not None else list(self.DEFAULT_EXAMPLES)

    def get_relevant_examples(self, question: str, limit: int = 4) -> list[FewShotExample]:
        """Selects up to `limit` few-shot examples based on keyword match, falling back to top default examples."""
        q_words = set(question.lower().split())
        
        scored_examples = []
        for example in self.examples:
            score = 0
            # Score based on tag matches
            for tag in example.tags:
                if tag in q_words:
                    score += 2
            # Score based on question word overlap
            ex_words = set(example.question.lower().split())
            score += len(q_words.intersection(ex_words))
            scored_examples.append((score, example))

        # Sort by score descending
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        selected = [ex for score, ex in scored_examples[:limit]]

        # Ensure we always return between 3 and limit examples
        if len(selected) < min(3, len(self.examples)):
            return self.examples[:limit]

        return selected
