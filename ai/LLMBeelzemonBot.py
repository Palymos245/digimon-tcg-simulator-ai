import logging

from BeelzemonXBot import BeelzemonXBot
from llm.action_catalog import build_candidates
from llm.openai_responses import OpenAIResponsesDecisionProvider
from llm.state_view import build_decision_view


class LLMBeelzemonBot(BeelzemonXBot):
    """Beelzemon bot with an LLM choosing concrete legal strategic actions."""

    def __init__(self, username: str):
        super().__init__(username)
        self.decision_provider = OpenAIResponsesDecisionProvider()
        self.llm_log = logging.getLogger("LLMBeelzemonBot")

    async def _choose(self, candidates):
        try:
            state_view = build_decision_view(self)
            action = await self.decision_provider.choose_action(
                state_view, candidates
            )
            valid = {candidate["action"] for candidate in candidates}
            if action in valid:
                self.llm_log.info("LLM selected action: %s", action)
                return action
            self.llm_log.warning(
                "LLM returned action not in candidate set: %r", action
            )
        except Exception as exc:
            self.llm_log.exception("LLM decision failed: %s", exc)

        # Safe fallback: use the existing deterministic strategy, never arbitrary
        # state mutation.
        return "pass"

    async def _execute(self, ws, candidate):
        action = candidate["action"]
        kind = candidate["kind"]

        if kind == "pass":
            return False

        if kind == "attack":
            position = candidate["battle_position"]
            await self.suspend_card(ws, position)
            await self.when_attacking_effects_strategy(ws, position)
            await self.attack_with_digimon(ws, position)
            return True

        if kind == "digivolve":
            position = candidate["battle_position"]
            hand_index = candidate["hand_index"]
            card = self.game["player2Hand"][hand_index]
            digivolution_card_obj = self.card_factory.get_card(
                card["uniqueCardNumber"],
                digimon_index=position,
                card_id=card["id"],
            )
            await self.digivolve(
                ws,
                "Digi",
                position,
                "Hand",
                hand_index,
                candidate["cost"],
            )
            await digivolution_card_obj.when_digivolving_effect(ws)
            if card["uniqueCardNumber"] == "BT12-085":
                await self.use_seventh_full_cluster_trash_if_possible(ws)
            return True

        if kind == "breed_digivolve":
            hand_index = candidate["hand_index"]
            card = self.game["player2Hand"][hand_index]
            await self.digivolve(
                ws,
                "BreedingArea",
                0,
                "Hand",
                hand_index,
                candidate["cost"],
            )
            return True

        if kind == "play":
            hand_index = candidate["hand_index"]
            card = self.game["player2Hand"][hand_index]
            played = await self.play_card(
                ws, "Hand", hand_index, candidate["cost"]
            )
            card_obj = self.card_factory.get_card(
                played["uniqueCardNumber"], card_id=played["id"]
            )
            await card_obj.on_play_effect(ws)
            return True

        if kind == "setup":
            return bool(await self.avoid_brick(ws))

        raise ValueError(f"Unknown candidate kind: {kind}")

    async def main_phase_strategy(self, ws):
        # Preserve deterministic rookie preparation because this routine is a
        # safe mechanical setup step, not an LLM judgment.
        await self.prepare_rookies(ws)

        max_decisions = 20
        for _ in range(max_decisions):
            if self.game["memory"] < 0:
                return

            candidates = build_candidates(self)
            if not candidates:
                return

            action = await self._choose(candidates)
            candidate = next(
                candidate for candidate in candidates
                if candidate["action"] == action
            )
            if candidate["kind"] == "pass":
                return

            try:
                await self._execute(ws, candidate)
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                # State changed while waiting for the response/opponent. Rebuild
                # candidates from the authoritative simulator state.
                self.llm_log.warning("Rejected stale action %s: %s", action, exc)
                continue

        self.llm_log.warning(
            "Reached main-phase decision cap; ending Main Phase safely."
        )
