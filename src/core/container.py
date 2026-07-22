"""Dependency Injection container setup."""

from typing import Any


class DependencyContainer:
    """Lightweight dependency injection provider for assembling application components."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, service_name: str, instance: Any) -> None:
        """Register a service implementation."""
        self._services[service_name] = instance

    def get(self, service_name: str) -> Any:
        """Resolve a service implementation."""
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not registered in container.")
        return self._services[service_name]


container = DependencyContainer()
