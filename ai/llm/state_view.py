from typing import Any


_CARD_FIELDS = (
    "uniqueCardNumber",
    "name",
    "cardType",
    "level",
    "color",
    "digiType",
    "dp",
    "DP",
    "playCost",
    "isTilted",
)


def _card_view(card: dict[str, Any]) -> dict[str, Any]:
    """Return only card information that is useful to the strategic layer."""
    result: dict[str, Any] = {}
    for field in _CARD_FIELDS:
        if field in card:
            result[field] = card[field]
    return result


def _stack_view(stack: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "top": _card_view(stack[-1]) if stack else None,
        "digivolution_cards": [_card_view(card) for card in stack[:-1]],
    }


def _battle_area_view(area: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    result = []
    for position, stack in enumerate(area, start=1):
        if stack:
            result.append({"position": position, **_stack_view(stack)})
    return result


def _tamer_view(tamers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"position": i, **_card_view(card)} for i, card in enumerate(tamers, start=1)]


def build_decision_view(bot: Any) -> dict[str, Any]:
    """Build a legal-information view for the LLM.

    The bot's own hand is included because it is private information the bot is
    allowed to use. Opponent hand/deck contents are intentionally not included;
    only counts and public/revealed zones are exposed.
    """
    game = bot.game
    own_hand = game.get("player2Hand", [])
    own_security = game.get("player2Security", [])
    opponent_security = game.get("player1Security", [])

    return {
        "turn": getattr(bot, "turn_counter", None),
        "memory": game.get("memory", 0),
        "first_turn": bool(getattr(bot, "first_turn", False)),
        "my_turn": bool(getattr(bot, "my_turn", False)),
        "self": {
            "hand": [_card_view(card) for card in own_hand],
            "deck_count": len(game.get("player2DeckField", [])),
            "egg_deck_count": len(game.get("player2EggDeck", [])),
            "breeding": [_card_view(card) for card in game.get("player2BreedingArea", [])],
            "battle_area": _battle_area_view(game.get("player2Digi", [])),
            "tamers": _tamer_view(game.get("player2Tamer", [])),
            "trash": [_card_view(card) for card in game.get("player2Trash", [])],
            "security_count": len(own_security),
            "revealed": [_card_view(card) for card in game.get("player2Reveal", [])],
        },
        "opponent": {
            "hand_count": len(game.get("player1Hand", [])),
            "deck_count": len(game.get("player1DeckField", [])),
            "breeding": [_card_view(card) for card in game.get("player1BreedingArea", [])],
            "battle_area": _battle_area_view(game.get("player1Digi", [])),
            "tamers": _tamer_view(game.get("player1Tamer", [])),
            "trash": [_card_view(card) for card in game.get("player1Trash", [])],
            "security_count": len(opponent_security),
            "revealed": [_card_view(card) for card in game.get("player1Reveal", [])],
        },
    }
