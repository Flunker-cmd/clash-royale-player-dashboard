import unittest

from generate_insights import build_insights


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


if __name__ == "__main__":
    unittest.main()
