import unittest


from llm.state_view import build_decision_view


class FakeBot:
    turn_counter = 7
    first_turn = False

    def __init__(self):
        self.game = {
            "memory": 3,
            "player2Hand": [
                {
                    "uniqueCardNumber": "ST14-02",
                    "name": "Impmon",
                    "cardType": "Digimon",
                    "level": 3,
                    "id": "secret-own",
                }
            ],
            "player2DeckField": [{"id": "d1"}],
            "player2EggDeck": [],
            "player2BreedingArea": [],
            "player2Digi": [],
            "Tamers": [{"uniqueCardNumber": "ST14-11", "name": "Ai & Mako"}],
            "player2Trash": [],
            "player2Security": [{"id": "s1"}],
            "player2Reveal": [],
            "player1Hand": [
                {"uniqueCardNumber": "HIDDEN", "name": "Hidden", "cardType": "Digimon"}
            ],
            "player1DeckField": [{"id": "opponent-hidden-deck"}],
            "player1BreedingArea": [],
            "player1Digi": [],
            "player1Trash": [],
            "player1Security": [{"id": "os1"}, {"id": "os2"}],
            "player1Reveal": [],
        }


class StateViewTests(unittest.TestCase):
    def test_does_not_expose_opponent_hidden_cards(self):
        view = build_decision_view(FakeBot())
        serialized = str(view)
        self.assertNotIn("HIDDEN", serialized)
        self.assertNotIn("opponent-hidden-deck", serialized)
        self.assertEqual(view["opponent"]["hand_count"], 1)
        self.assertEqual(view["opponent"]["deck_count"], 1)

    def test_own_private_information_is_present(self):
        view = build_decision_view(FakeBot())
        self.assertEqual(view["self"]["hand"][0]["uniqueCardNumber"], "ST14-02")
        self.assertEqual(view["self"]["tamers"][0]["uniqueCardNumber"], "ST14-11")


if __name__ == "__main__":
    unittest.main()
