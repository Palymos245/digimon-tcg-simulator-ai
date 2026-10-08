import logging

from BeelzemonXBot import BeelzemonXBot
from llm.openai_responses import OpenAIResponsesDecisionProvider
from llm.state_view import build_decision_view


class LLMBeelzemonBot(BeelzemonXBot):
    """Beelzemon bot with an LLM choosing between deterministic strategy routines."""

    STRATEGY_DESCRIPTIONS = {
        "avoid_brick": "Use a setup/resource routine that may play Ai & Mako, use Purple Memory Boost, or resolve a Rivals' Barrage delay.",
        "digivolve": "Use the existing deterministic digivolution strategy for a Battle Area Digimon.",
        "attack": "Use the existing deterministic attack strategy, including simulator-enforced attack/effect resolution.",
        "digivolve_in_breed": "Use the existing deterministic strategy to digivolve in the Breeding Area.",
        "play_digimon": "Use the existing deterministic strategy to play a Digimon from hand.",
        "pass": "Take no further Main Phase action and end the turn.",
    }

    def __init__(self, username: str):
        super().__init__(username)
        self.decision_provider = OpenAIResponsesDecisionProvider()
        self.llm_log = logging.getLogger("LLMBeelzemonBot")

    def _candidates(self) -> list[dict[str, str]]:
        return [
            {"action": action, "description": description}
            for action, description in self.STRATEGY_DESCRIPTIONS.items()
        ]

    async def _choose(self, failed_actions: set[str]) -> str:
        candidates = [
            c for c in self._candidates()
            if c["action"] not in failed_actions
        ]
        if not candidates:
            return "pass"

        try:
            state_view = build_decision_view(self)
            action = await self.decision_provider.choose_action(
                state_view, candidates
            )
            candidate_names = {c["action"] for c in candidates}
            if action in candidate_names:
                self.llm_log.info("LLM selected strategy: %s", action)
                return action
            self.llm_log.warning(
                "LLM selected invalid candidate %r; falling back.", action
            )
        except Exception as exc:
            self.llm_log.exception("LLM decision failed: %s", exc)

        fallback_order = [
            "avoid_brick",
            "digivolve",
            "attack",
            "digivolve_in_breed",
            "play_digimon",
            "pass",
        ]
        candidate_names = {c["action"] for c in candidates}
        for action in fallback_order:
            if action not in failed_actions and action in candidate_names:
                self.llm_log.info(
                    "Using deterministic fallback strategy: %s", action
                )
                return action
        return "pass"

    async def main_phase_strategy(self, ws):
        # Existing simulator setup stays deterministic.
        await self.prepare_rookies(ws)

        failed_actions: set[str] = set()
        max_decisions = 20

        for _ in range(max_decisions):
            if self.game["memory"] < 0:
                return

            action = await self._choose(failed_actions)
            if action == "pass":
                return

            if action == "avoid_brick":
                did_action = await self.avoid_brick(ws)
            elif action == "digivolve":
                did_action = await self.digivolve_strategy(ws)
            elif action == "attack":
                did_action = await self.attack_loop(ws)
            elif action == "digivolve_in_breed":
                did_action = await self.digivolve_in_breed_strategy(ws)
            elif action == "play_digimon":
                did_action = await self.play_digimon_strategy(ws)
            else:
                return

            if did_action:
                failed_actions.clear()
            else:
                failed_actions.add(action)

        self.llm_log.warning(
            "Reached main-phase decision cap; ending Main Phase safely."
        )
