import unittest

from fetch_data import merge_battles


def battle(time):
    return {"battleTime": time, "type": "PvP"}


class MergeBattlesTests(unittest.TestCase):
    def test_keeps_old_battles_and_adds_new_ones_once(self):
        history = [battle("20261020T100000.000Z"), battle("20261019T100000.000Z")]
        latest = [battle("20261021T100000.000Z"), battle("20261020T100000.000Z")]

        merged = merge_battles(history, latest)

        self.assertEqual(
            [item["battleTime"] for item in merged],
            ["20261021T100000.000Z", "20261020T100000.000Z", "20261019T100000.000Z"],
        )


if __name__ == "__main__":
    unittest.main()
