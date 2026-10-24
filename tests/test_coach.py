import unittest

from coach import check_war_plan, judge_experiment, main_deck_at

MAIN_DECK = [
    "Firecracker", "Tombstone", "Royal Hogs", "Wall Breakers",
    "Mega Knight", "Bats", "Barbarian Barrel", "Fireball",
]


def declared(at, cards=MAIN_DECK):
    return {"type": "mainDeckDeclared", "at": at, "cards": cards}


def experiment(at, out, into, name="exp", battles=15, win_rate=55):
    return {
        "type": "experimentStarted", "id": name, "at": at, "out": out, "in": into,
        "criterion": {"battles": battles, "winRate": win_rate},
    }


def ladder(time, cards, won=True, battle_type="PvP"):
    return {
        "battleTime": time,
        "type": battle_type,
        "team": [{"crowns": 1 if won else 0, "cards": [{"name": name} for name in cards]}],
        "opponent": [{"crowns": 0 if won else 1}],
    }


WITH_SKELETONS = sorted(set(MAIN_DECK) - {"Bats"} | {"Skeletons"})


class MainDeckAtTests(unittest.TestCase):
    def test_experiment_swap_applies_to_main_deck_from_its_start(self):
        log = [
            declared("2026-10-01T00:00:00Z"),
            experiment("2026-10-10T00:00:00Z", out=["Bats"], into=["Skeletons"]),
        ]

        self.assertEqual(main_deck_at(log, "2026-10-05T00:00:00Z"), set(MAIN_DECK))
        self.assertEqual(
            main_deck_at(log, "20261011T120000.000Z"),
            set(MAIN_DECK) - {"Bats"} | {"Skeletons"},
        )

    def test_stacked_experiments_both_apply(self):
        log = [
            declared("2026-10-01T00:00:00Z"),
            experiment("2026-10-10T00:00:00Z", out=["Bats"], into=["Skeletons"]),
            experiment("2026-10-12T00:00:00Z", out=["Barbarian Barrel"], into=["The Log"]),
        ]

        self.assertEqual(
            main_deck_at(log, "2026-10-13T00:00:00Z"),
            set(MAIN_DECK) - {"Bats", "Barbarian Barrel"} | {"Skeletons", "The Log"},
        )

    def test_nothing_declared_means_no_main_deck(self):
        self.assertIsNone(main_deck_at([], "2026-10-13T00:00:00Z"))


class JudgeExperimentTests(unittest.TestCase):
    def test_counts_only_main_deck_battles_after_start_and_is_pending_below_target(self):
        log = [
            declared("2026-10-01T00:00:00Z"),
            experiment("2026-10-10T00:00:00Z", out=["Bats"], into=["Skeletons"], name="skeletons"),
        ]
        battles = [
            ladder("20261009T120000.000Z", WITH_SKELETONS),          # before start
            ladder("20261011T120000.000Z", WITH_SKELETONS),
            ladder("20261011T130000.000Z", WITH_SKELETONS, won=False),
            ladder("20261011T140000.000Z", MAIN_DECK),               # not the main deck of that moment
            ladder("20261011T150000.000Z", WITH_SKELETONS, battle_type="riverRacePvP"),  # war
            ladder("20261011T160000.000Z", ["Golem"] * 8),           # another deck
        ]

        judgement = judge_experiment("skeletons", log, battles)

        self.assertEqual((judgement["battles"], judgement["wins"]), (2, 1))
        self.assertEqual(judgement["verdict"], "pending")

    def test_is_judged_on_the_first_target_battles(self):
        battles = [
            ladder("20261011T120000.000Z", WITH_SKELETONS),
            ladder("20261011T130000.000Z", WITH_SKELETONS),
            ladder("20261011T140000.000Z", WITH_SKELETONS, won=False),
            ladder("20261011T150000.000Z", WITH_SKELETONS, won=False),
            ladder("20261011T160000.000Z", WITH_SKELETONS, won=False),  # after the target
        ]
        for win_rate, verdict in ((50, "succeeded"), (75, "failed")):
            with self.subTest(win_rate=win_rate):
                log = [
                    declared("2026-10-01T00:00:00Z"),
                    experiment("2026-10-10T00:00:00Z", out=["Bats"], into=["Skeletons"],
                               name="skeletons", battles=4, win_rate=win_rate),
                ]

                judgement = judge_experiment("skeletons", log, battles)

                self.assertEqual((judgement["battles"], judgement["wins"]), (4, 2))
                self.assertEqual(judgement["verdict"], verdict)

    def test_is_inconclusive_when_the_swap_leaves_the_main_deck_before_the_target(self):
        log = [
            declared("2026-10-01T00:00:00Z"),
            experiment("2026-10-10T00:00:00Z", out=["Bats"], into=["Skeletons"], name="skeletons"),
            declared("2026-10-12T00:00:00Z"),
        ]
        battles = [ladder("20261011T120000.000Z", WITH_SKELETONS)]

        judgement = judge_experiment("skeletons", log, battles)

        self.assertEqual(judgement["battles"], 1)
        self.assertEqual(judgement["verdict"], "inconclusive")

    def test_reports_battles_shared_with_stacked_experiments(self):
        log = [
            declared("2026-10-01T00:00:00Z"),
            experiment("2026-10-10T00:00:00Z", out=["Bats"], into=["Skeletons"], name="skeletons"),
            experiment("2026-10-12T00:00:00Z", out=["Barbarian Barrel"], into=["The Log"], name="log"),
        ]
        both_swaps = sorted(set(WITH_SKELETONS) - {"Barbarian Barrel"} | {"The Log"})
        battles = [
            ladder("20261011T120000.000Z", WITH_SKELETONS),
            ladder("20261013T120000.000Z", both_swaps),
            ladder("20261013T130000.000Z", both_swaps, won=False),
        ]

        skeletons = judge_experiment("skeletons", log, battles)
        the_log = judge_experiment("log", log, battles)

        self.assertEqual((skeletons["battles"], skeletons["wins"]), (3, 2))
        self.assertEqual(skeletons["sharedWith"], {"log": 2})
        self.assertEqual((the_log["battles"], the_log["wins"]), (2, 1))
        self.assertEqual(the_log["sharedWith"], {"skeletons": 2})


COLLECTION = [
    {"name": f"Card {number}", "level": 12, "maxLevel": 14, "elixirCost": 2 + number % 3}
    for number in range(1, 33)
] + [{"name": "Mega Knight", "level": 8, "maxLevel": 8, "elixirCost": 7}]


def war_deck(first):
    return [f"Card {number}" for number in range(first, first + 8)]


class CheckWarPlanTests(unittest.TestCase):
    def test_valid_plan_reports_global_levels_and_average_elixir(self):
        plan = [war_deck(1), war_deck(9), war_deck(17), war_deck(25)]
        plan[0] = plan[0][:7] + ["Mega Knight"]

        report = check_war_plan(plan, COLLECTION)

        self.assertEqual(report["problems"], [])
        first = report["decks"][0]
        self.assertEqual(first["cards"][0], {"name": "Card 1", "level": 14})
        self.assertEqual(first["cards"][7], {"name": "Mega Knight", "level": 16})
        # Card 1-7 cost 3,4,2,3,4,2,3 and Mega Knight 7: 28 / 8
        self.assertEqual(first["averageElixir"], 3.5)

    def test_reports_every_rule_the_plan_breaks(self):
        plan = [
            war_deck(1),
            war_deck(8),                   # Card 8 is also in deck 1
            war_deck(17)[:7] + ["Golem"],  # Golem is not owned
        ]

        problems = check_war_plan(plan, COLLECTION)["problems"]

        self.assertIn("Plan has 3 decks, not 4.", problems)
        self.assertIn("Card 8 is in decks 1 and 2.", problems)
        self.assertIn("Deck 3: Not in the Collection: Golem.", problems)

    def test_reports_a_deck_without_eight_cards(self):
        plan = [war_deck(1)[:7], war_deck(9), war_deck(17), war_deck(25)]

        self.assertEqual(check_war_plan(plan, COLLECTION)["problems"], ["Deck 1: Deck has 7 cards, not 8."])


if __name__ == "__main__":
    unittest.main()
