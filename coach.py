import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_time(value):
    if "-" not in value:
        return datetime.strptime(value, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main_deck_at(log, when):
    when = parse_time(when)
    deck = None
    for event in sorted(log, key=lambda item: parse_time(item["at"])):
        if parse_time(event["at"]) > when:
            break
        if event["type"] == "mainDeckDeclared":
            deck = set(event["cards"])
        elif event["type"] == "experimentStarted" and deck is not None:
            deck = deck - set(event["out"]) | set(event["in"])
    return deck


def global_level(card):
    # The API reports levels relative to rarity; level 16 is max for every card.
    return card["level"] + 16 - card["maxLevel"]


def check_deck(deck, collection):
    owned = {card["name"]: card for card in collection}
    problems = []
    if len(deck) != 8:
        problems.append(f"Deck has {len(deck)} cards, not 8.")
    if len(set(deck)) != len(deck):
        problems.append("Deck lists the same card twice.")
    missing = [name for name in deck if name not in owned]
    if missing:
        problems.append(f"Not in the Collection: {', '.join(missing)}.")
    known = [owned[name] for name in deck if name in owned]
    costs = [card["elixirCost"] for card in known if "elixirCost" in card]
    return {
        "cards": [{"name": card["name"], "level": global_level(card)} for card in known],
        "averageElixir": round(sum(costs) / len(costs), 1) if costs else None,
        "problems": problems,
    }


def check_war_plan(decks, collection):
    reports = [check_deck(deck, collection) for deck in decks]
    problems = [] if len(decks) == 4 else [f"Plan has {len(decks)} decks, not 4."]
    problems += [f"Deck {index}: {problem}" for index, report in enumerate(reports, 1) for problem in report["problems"]]
    decks_by_card = {}
    for index, deck in enumerate(decks, 1):
        for name in dict.fromkeys(deck):
            decks_by_card.setdefault(name, []).append(index)
    problems += [
        f"{name} is in decks {' and '.join(map(str, indexes))}."
        for name, indexes in decks_by_card.items()
        if len(indexes) > 1
    ]
    return {"decks": reports, "problems": problems}


def is_war(battle):
    deck_selection = str(battle.get("deckSelection", "")).lower()
    battle_type = str(battle.get("type", "")).lower()
    return deck_selection in {"wardeck", "wardeckpick"} or battle_type.startswith("riverrace") or battle_type == "boatbattle"


def player_cards(battle):
    return {card["name"] for card in battle["team"][0].get("cards", [])}


def battle_won(battle):
    return battle["team"][0].get("crowns", 0) > battle["opponent"][0].get("crowns", 0)


def experiment_battles(experiment, log, battles):
    start = parse_time(experiment["at"])
    counted = []
    for battle in sorted(battles, key=lambda item: item["battleTime"]):
        if is_war(battle) or parse_time(battle["battleTime"]) < start:
            continue
        cards = player_cards(battle)
        if cards != main_deck_at(log, battle["battleTime"]):
            continue
        if set(experiment["in"]) <= cards and not set(experiment["out"]) & cards:
            counted.append(battle)
    return counted[:experiment["criterion"]["battles"]]


def judge_experiment(experiment_id, log, battles):
    experiment = next(event for event in log if event.get("id") == experiment_id)
    counted = experiment_battles(experiment, log, battles)
    wins = sum(battle_won(battle) for battle in counted)
    criterion = experiment["criterion"]
    latest = max(log, key=lambda event: parse_time(event["at"]))["at"]
    current = main_deck_at(log, latest) or set()
    swap_kept = set(experiment["in"]) <= current and not set(experiment["out"]) & current
    if len(counted) < criterion["battles"]:
        verdict = "pending" if swap_kept else "inconclusive"
    elif wins * 100 >= criterion["winRate"] * len(counted):
        verdict = "succeeded"
    else:
        verdict = "failed"
    counted_times = {battle["battleTime"] for battle in counted}
    shared_with = {}
    for other in log:
        if other["type"] != "experimentStarted" or other["id"] == experiment_id:
            continue
        shared = counted_times & {battle["battleTime"] for battle in experiment_battles(other, log, battles)}
        if shared:
            shared_with[other["id"]] = len(shared)
    return {"battles": len(counted), "wins": wins, "verdict": verdict, "sharedWith": shared_with}


def observations(battle):
    """Every (cards, won) pair the battle holds; a war duel holds one per round."""
    player, opponent = battle["team"][0], battle["opponent"][0]
    if player.get("rounds"):
        opponent_rounds = opponent.get("rounds", [])
        for index, round_data in enumerate(player["rounds"]):
            enemy = opponent_rounds[index] if index < len(opponent_rounds) else {}
            if round_data.get("cards"):
                yield {card["name"] for card in round_data["cards"]}, round_data.get("crowns", 0) > enemy.get("crowns", 0)
    elif player.get("cards"):
        yield player_cards(battle), battle_won(battle)


def observed_decks(battles, war):
    records = {}
    for battle in battles:
        if is_war(battle) != war:
            continue
        for cards, won in observations(battle):
            if len(cards) != 8:
                continue
            record = records.setdefault(frozenset(cards), {"cards": sorted(cards), "battles": 0, "wins": 0})
            record["battles"] += 1
            record["wins"] += won
    return sorted(records.values(), key=lambda record: record["battles"], reverse=True)


def deck_record(cards, battles, war):
    match = next((record for record in observed_decks(battles, war) if set(record["cards"]) == set(cards)), None)
    return {"battles": match["battles"], "wins": match["wins"]} if match else {"battles": 0, "wins": 0}


def status(log, battles, collection):
    latest = max((event["at"] for event in log), key=parse_time, default=None)
    main_deck = main_deck_at(log, latest) if latest else None
    war_plans = [event for event in log if event["type"] == "warDeckPlanDeclared"]
    return {
        "battleHistory": {
            "battles": len(battles),
            "first": min((battle["battleTime"] for battle in battles), default=None),
            "last": max((battle["battleTime"] for battle in battles), default=None),
        },
        "mainDeck": main_deck and {
            **check_deck(sorted(main_deck), collection),
            "record": deck_record(main_deck, battles, war=False),
        },
        "experiments": [
            {**event, **judge_experiment(event["id"], log, battles)}
            for event in log if event["type"] == "experimentStarted"
        ],
        "activeWarDeckPlan": war_plans and [
            {**check_deck(deck, collection), "record": deck_record(deck, battles, war=True)}
            for deck in max(war_plans, key=lambda event: parse_time(event["at"]))["decks"]
        ],
    }


def load(path, default):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main(argv):
    log = load("coaching-log.json", [])
    battles = load("battle-history.json", [])
    collection = load("player.json", {}).get("cards", [])
    command, args = (argv[0], argv[1:]) if argv else ("status", [])
    if command == "status":
        result = status(log, battles, collection)
    elif command == "decks":
        result = observed_decks(battles, war="--war" in args)
    elif command == "check-deck":
        result = check_deck(args, collection)
    elif command == "check-war-plan":
        result = check_war_plan(json.loads(Path(args[0]).read_text(encoding="utf-8")), collection)
    elif command == "collection":
        result = sorted(
            ({"name": card["name"], "level": global_level(card), "elixirCost": card.get("elixirCost")} for card in collection),
            key=lambda card: -card["level"],
        )
    else:
        raise SystemExit(f"Unknown command: {command}. Use status, decks [--war], check-deck CARD..., check-war-plan FILE or collection.")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
