import unittest

from generate_insights import build_analysis_export, build_analysis_markdown, build_insights


class GenerateInsightsTests(unittest.TestCase):
    def test_builds_deck_stats_for_player_battles(self):
        player = {
            "tag": "#PLAYER",
            "name": "Test Player",
            "trophies": 5000,
            "cards": [{"name": "Knight", "id": 1, "level": 12, "maxLevel": 14}],
        }
        battlelog = [
            {
                "team": [{"tag": "#PLAYER", "crowns": 3, "cards": [{"id": 1, "name": "Knight"}]}],
                "opponent": [{"tag": "#ENEMY", "crowns": 1}],
            },
            {
                "team": [{"tag": "#PLAYER", "crowns": 0, "cards": [{"id": 1, "name": "Knight"}]}],
                "opponent": [{"tag": "#ENEMY", "crowns": 1}],
            },
        ]

        insights = build_insights(player, battlelog)

        self.assertEqual(insights["sampleSize"], 2)
        self.assertEqual(insights["decks"][0]["wins"], 1)
        self.assertEqual(insights["decks"][0]["winRate"], 50.0)
        self.assertEqual(insights["upgradeCandidates"][0]["name"], "Knight")

    def test_empty_battlelog_returns_actionable_recommendation(self):
        insights = build_insights({"tag": "#PLAYER", "name": "Test"}, [])

        self.assertEqual(insights["sampleSize"], 0)
        self.assertEqual(insights["decks"], [])
        self.assertEqual(insights["recommendations"][0]["kind"], "info")

    def test_reliable_decks_generates_recommendation(self):
        player = {"tag": "#PLAYER", "name": "Test"}
        battle = {
            "team": [{"tag": "#PLAYER", "crowns": 3, "cards": [{"id": 1, "name": "Knight"}]}],
            "opponent": [{"tag": "#ENEMY", "crowns": 1}],
        }
        battlelog = [battle, battle, battle]
        insights = build_insights(player, battlelog)
        self.assertEqual(len(insights["recommendations"]), 1)
        self.assertEqual(insights["recommendations"][0]["kind"], "positive")
        self.assertIn("100% wins", insights["recommendations"][0]["text"])

    def test_separates_regular_and_war_decks(self):
        regular_battle = {
            "type": "PvP",
            "team": [{"tag": "#PLAYER", "crowns": 3, "cards": [{"id": 1, "name": "Knight"}]}],
            "opponent": [{"tag": "#ENEMY", "crowns": 1}],
        }
        war_battle = {
            "type": "riverRacePvP",
            "deckSelection": "warDeck",
            "team": [{"tag": "#PLAYER", "crowns": 1, "cards": [{"id": 1, "name": "Knight"}]}],
            "opponent": [{"tag": "#ENEMY", "crowns": 0}],
        }

        insights = build_insights({"tag": "#PLAYER", "name": "Test"}, [regular_battle, war_battle])

        self.assertEqual(len(insights["decks"]), 2)
        self.assertEqual({deck["category"] for deck in insights["decks"]}, {"regular", "war"})

    def test_analysis_export_has_llm_friendly_deck_groups(self):
        insights = build_insights(
            {"tag": "#PLAYER", "name": "Test"},
            [{
                "deckSelection": "warDeck",
                "team": [{"tag": "#PLAYER", "crowns": 1, "cards": [{"id": 1, "name": "Knight"}]}],
                "opponent": [{"tag": "#ENEMY", "crowns": 0}],
            }],
        )

        export = build_analysis_export(insights)
        markdown = build_analysis_markdown(export)

        self.assertEqual(export["regularDecks"], [])
        self.assertEqual(len(export["warDecks"]), 1)
        self.assertIn("## War decks", markdown)
        self.assertIn("Knight", markdown)

    def test_war_rounds_are_exported_as_separate_decks(self):
        def cards(start):
            return [{"id": index, "name": f"Card {index}"} for index in range(start, start + 8)]

        battle = {
            "deckSelection": "warDeckPick",
            "team": [{
                "tag": "#PLAYER",
                "rounds": [
                    {"crowns": 1, "cards": cards(1)},
                    {"crowns": 0, "cards": cards(9)},
                ],
            }],
            "opponent": [{"rounds": [{"crowns": 0}, {"crowns": 1}]}],
        }

        insights = build_insights({"tag": "#PLAYER", "name": "Test"}, [battle])

        war_decks = [deck for deck in insights["decks"] if deck["category"] == "war"]
        self.assertEqual(len(war_decks), 2)
        self.assertTrue(all(len(deck["cards"]) == 8 for deck in war_decks))
        self.assertEqual([deck["wins"] for deck in war_decks], [1, 0])
        self.assertEqual(len(insights["warDeckPlan"]), 2)

    def test_war_deck_plan_never_reuses_a_card(self):
        def deck(start):
            return [{"id": index, "name": f"Card {index}"} for index in range(start, start + 8)]

        battles = []
        for start in (1, 9, 17, 25):
            battles.append({
                "deckSelection": "warDeckPick",
                "team": [{"tag": "#PLAYER", "rounds": [{"crowns": 1, "cards": deck(start)}]}],
                "opponent": [{"rounds": [{"crowns": 0}]}],
            })

        insights = build_insights({"tag": "#PLAYER", "name": "Test"}, battles)
        selected = insights["warDeckPlan"]
        selected_ids = [card["id"] for item in selected for card in item["cards"]]

        self.assertEqual(len(selected), 4)
        self.assertEqual(len(selected_ids), len(set(selected_ids)))

    def test_collection_war_composite_is_not_exported_as_a_deck(self):
        battle = {
            "type": "riverRacePvP",
            "deckSelection": "collection",
            "team": [{"tag": "#PLAYER", "cards": [{"id": index} for index in range(12)]}],
            "opponent": [{"crowns": 0}],
        }

        insights = build_insights({"tag": "#PLAYER", "name": "Test"}, [battle])

        self.assertEqual(insights["decks"], [])


if __name__ == "__main__":
    unittest.main()
