"""Base validator class for strategy validation."""

from abc import ABC, abstractmethod
from typing import List

from src.agent.models import Strategy


class BaseValidator(ABC):
    """
    Abstract base class for strategy validators.

    Validators check semantic correctness beyond Pydantic schema validation.
    They return error messages compatible with the retry mechanism.
    """

    @abstractmethod
    def validate(self, strategy: Strategy) -> List[str]:
        """
        Validate a strategy and return list of error messages.

        Args:
            strategy: Strategy to validate

        Returns:
            List of error messages (empty if valid).
            Error format: "Priority X (TYPE): description"
            where X is 1-4 and TYPE is REJECT/RETRY/SUGGESTION/NOTE
        """
        pass
