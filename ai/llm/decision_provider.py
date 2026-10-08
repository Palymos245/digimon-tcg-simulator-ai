from abc import ABC, abstractmethod
from typing import Any


class DecisionProvider(ABC):
    """Chooses a high-level strategy without directly mutating game state."""

    @abstractmethod
    async def choose_action(
        self,
        state_view: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> str:
        """Return the identifier of one candidate action."""
        raise NotImplementedError
