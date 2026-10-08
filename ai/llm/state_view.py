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


def _cards_view(cards: Any) -> list[dict[str, Any]]:
    if not isinstance(cards, list):
        return []
    return [_card_view(card) for card in cards if isinstance(card, dict)]


def _own_tamers_view(game: dict[str, Any]) -> list[dict[str, Any]]:
    # This bot version stores Tamers under a shared "Tamers" key rather than
    # player2Tamer. Keep the state view tolerant because the key is absent in
    # some game snapshots.
    tamers = game.get("Tamers", [])
    return _cards_view(tamers)


def build_decision_view(bot: Any) -> dict[str, Any]:
    """Expose allowed strategic information without leaking hidden opponent zones."""
    game = bot.game

    return {
        "turn": getattr(bot, "turn_counter", None),
        "memory": game.get("memory", 0),
        "first_turn": bool(getattr(bot, "first_turn", False)),
        "self": {
            "hand": _cards_view(game.get("player2Hand", [])),
            "deck_count": len(game.get("player2DeckField", [])),
            "egg_deck_count": len(game.get("player2EggDeck", [])),
            "breeding": _cards_view(game.get("player2BreedingArea", [])),
            "battle_area": _battle_area_view(game.get("player2Digi", [])),
            "tamers": _own_tamers_view(game),
            "trash": _cards_view(game.get("player2Trash", [])),
            "security_count": len(game.get("player2Security", [])),
            "revealed": _cards_view(game.get("player2Reveal", [])),
        },
        "opponent": {
            "hand_count": len(game.get("player1Hand", [])),
            "deck_count": len(game.get("player1DeckField", [])),
            "breeding": _cards_view(game.get("player1BreedingArea", [])),
            "battle_area": _battle_area_view(game.get("player1Digi", [])),
            "trash": _cards_view(game.get("player1Trash", [])),
            "security_count": len(game.get("player1Security", [])),
            "revealed": _cards_view(game.get("player1Reveal", [])),
        },
    }
