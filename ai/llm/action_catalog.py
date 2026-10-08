from typing import Any


def _hand_cards(bot: Any, unique_card_number: str) -> list[tuple[int, dict[str, Any]]]:
    return [
        (index, card)
        for index, card in enumerate(bot.game.get("player2Hand", []))
        if card.get("uniqueCardNumber") == unique_card_number
    ]


def build_candidates(bot: Any) -> list[dict[str, Any]]:
    """Build concrete strategic choices from the simulator's current state.

    The LLM receives these as choices. It never receives a function name that
    can mutate arbitrary state or a free-form command.
    """
    game = bot.game
    memory = game.get("memory", 0)
    candidates: list[dict[str, Any]] = []

    def add(action: str, kind: str, description: str, **extra: Any) -> None:
        candidates.append({
            "action": action,
            "kind": kind,
            "description": description,
            **extra,
        })

    # Security attacks: the simulator remains responsible for blockers,
    # Security resolution, attack effects, and all resulting state changes.
    for position, stack in enumerate(game.get("player2Digi", [])):
        if not stack:
            continue
        card = stack[-1]
        if card.get("cardType") == "Digimon" and bot.can_attack(card):
            add(
                f"attack:{card['id']}",
                "attack",
                (
                    f"Attack Security with {card.get('name')} "
                    f"({card.get('uniqueCardNumber')}, Lv{card.get('level')})."
                ),
                card_id=card["id"],
                battle_position=position,
            )

    # Beelzemon X Antibody: only expose it when its explicit requirement is met.
    if len(game.get("player2Trash", [])) >= 10 and memory >= 1:
        for hand_index, card in _hand_cards(bot, "BT12-085"):
            for position, stack in enumerate(game.get("player2Digi", [])):
                if stack and stack[-1].get("name") == "Beelzemon":
                    add(
                        f"digivolve:{card['id']}:{stack[-1]['id']}",
                        "digivolve",
                        (
                            f"Digivolve {stack[-1].get('name')} at position {position + 1} "
                            f"into {card.get('name')} for 1 memory."
                        ),
                        card_id=card["id"],
                        base_id=stack[-1]["id"],
                        hand_index=hand_index,
                        battle_position=position,
                        cost=1,
                    )

    # Impmon X Antibody is a zero-cost concrete option.
    for hand_index, card in _hand_cards(bot, "BT12-073"):
        for position, stack in enumerate(game.get("player2Digi", [])):
            if stack and stack[-1].get("name") == "Impmon" and memory >= 0:
                add(
                    f"digivolve:{card['id']}:{stack[-1]['id']}",
                    "digivolve",
                    (
                        f"Digivolve Impmon at position {position + 1} "
                        f"into {card.get('name')} for 0 memory."
                    ),
                    card_id=card["id"],
                    base_id=stack[-1]["id"],
                    hand_index=hand_index,
                    battle_position=position,
                    cost=0,
                )

    # Other level-up evolutions are exposed only when their printed cost fits.
    for position, stack in enumerate(game.get("player2Digi", [])):
        if not stack or stack[-1].get("cardType") != "Digimon":
            continue
        base = stack[-1]
        base_level = base.get("level")
        if not isinstance(base_level, int):
            continue
        for hand_index, card in enumerate(game.get("player2Hand", [])):
            if card.get("cardType") != "Digimon" or card.get("level") != base_level + 1:
                continue
            try:
                cost = bot.digivolution_cost(card)
            except (KeyError, IndexError, TypeError):
                continue
            if cost <= memory and memory >= 0:
                add(
                    f"digivolve:{card['id']}:{base['id']}",
                    "digivolve",
                    (
                        f"Digivolve {base.get('name')} at position {position + 1} "
                        f"into {card.get('name')} for {cost} memory."
                    ),
                    card_id=card["id"],
                    base_id=base["id"],
                    hand_index=hand_index,
                    battle_position=position,
                    cost=cost,
                )

    # Breeding-area evolution choices.
    breeding = game.get("player2BreedingArea", [])
    if breeding and memory >= 0:
        base = breeding[-1]
        for hand_index, card in enumerate(game.get("player2Hand", [])):
            if card.get("cardType") != "Digimon" or card.get("level") != base.get("level", -1) + 1:
                continue
            try:
                cost = bot.digivolution_cost(card)
            except (KeyError, IndexError, TypeError):
                continue
            if cost <= memory:
                add(
                    f"breed_digivolve:{card['id']}:{base['id']}",
                    "breed_digivolve",
                    (
                        f"Digivolve the Breeding Area {base.get('name')} "
                        f"into {card.get('name')} for {cost} memory."
                    ),
                    card_id=card["id"],
                    base_id=base["id"],
                    hand_index=hand_index,
                    cost=cost,
                )

    # Playing a Digimon is a concrete choice rather than a generic "play something".
    has_front_slot = any(not stack for stack in game.get("player2Digi", [])[:10])
    if has_front_slot and memory >= 0:
        for hand_index, card in enumerate(game.get("player2Hand", [])):
            if card.get("cardType") != "Digimon":
                continue
            cost = card.get("playCost")
            if isinstance(cost, int) and cost <= memory:
                add(
                    f"play:{card['id']}",
                    "play",
                    f"Play {card.get('name')} ({card.get('uniqueCardNumber')}) for {cost} memory.",
                    card_id=card["id"],
                    hand_index=hand_index,
                    cost=cost,
                )

    # Keep the existing deterministic setup routine available, but only when it
    # currently has something it can actually do.
    has_setup_option = False
    if any(
        card.get("uniqueCardNumber") == "P-040" and isinstance(card.get("playCost"), int)
        and card["playCost"] <= memory
        for card in game.get("player2Hand", [])
    ):
        has_setup_option = True
    if any(
        card.get("uniqueCardNumber") == "ST14-11" and isinstance(card.get("playCost"), int)
        and card["playCost"] <= memory
        for card in game.get("player2Hand", [])
    ):
        has_setup_option = True
    if has_setup_option:
        add(
            "setup",
            "setup",
            "Use the existing deterministic setup/resource routine.",
        )

    add("pass", "pass", "End the Main Phase with no further action.")
    return candidates
