import json
from collections import defaultdict
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def player_tag(player):
    return player.get("tag", "#URUQ09LVG")


def extract_player_deck(battle, tag):
    for side in (battle.get("team", []), battle.get("opponent", [])):
        for participant in side or []:
            if participant.get("tag") == tag and participant.get("cards"):
                return participant.get("cards", [])
    for participant in battle.get("team", []) or []:
        if participant.get("cards"):
            return participant.get("cards", [])
    return []


def battle_won(battle, tag):
    team = battle.get("team", []) or []
    opponent = battle.get("opponent", []) or []
    player = next((item for item in team if item.get("tag") == tag), None)
    enemy = opponent[0] if opponent else None
    if player and enemy and "crowns" in player and "crowns" in enemy:
        return player["crowns"] > enemy["crowns"]
    if battle.get("result"):
        return str(battle["result"]).lower() in {"win", "won", "victory"}
    return None


def card_id(card):
    return str(card.get("id") or card.get("name") or "unknown")


def deck_key(deck):
    return "|".join(sorted(card_id(card) for card in deck))


def deck_label(deck):
    names = [card.get("name") for card in deck if card.get("name")]
    return ", ".join(names) if names else "Observed deck"


def build_insights(player, battlelog, meta=None):
    tag = player_tag(player)
    battles = battlelog if isinstance(battlelog, list) else battlelog.get("items", [])
    deck_stats = defaultdict(lambda: {"battles": 0, "wins": 0, "deck": []})
    observed_battles = []

    for battle in battles:
        deck = extract_player_deck(battle, tag)
        if not deck:
            continue
        won = battle_won(battle, tag)
        key = deck_key(deck)
        stats = deck_stats[key]
        stats["battles"] += 1
        stats["deck"] = deck
        if won is True:
            stats["wins"] += 1
        observed_battles.append({
            "deck": deck,
            "deckLabel": deck_label(deck),
            "won": won,
            "type": battle.get("type") or battle.get("gameMode", {}).get("name"),
            "date": battle.get("battleTime") or battle.get("date"),
        })

    decks = []
    for stats in deck_stats.values():
        decks.append({
            "label": deck_label(stats["deck"]),
            "cards": stats["deck"],
            "battles": stats["battles"],
            "wins": stats["wins"],
            "winRate": round(stats["wins"] / stats["battles"] * 100, 1),
        })
    decks.sort(key=lambda item: (-item["battles"], -item["winRate"]))

    recommendations = []
    if not observed_battles:
        recommendations.append({
            "title": "Collect more battle data",
            "text": "No usable deck was found in the current battle log. Play a few matches and refresh the dashboard.",
            "kind": "info",
        })
    else:
        reliable_decks = [deck for deck in decks if deck["battles"] >= 3]
        if reliable_decks:
            best = max(reliable_decks, key=lambda item: item["winRate"])
            recommendations.append({
                "title": "Keep testing your strongest observed deck",
                "text": f"{best.winRate:.0f}% wins across {best.battles} recorded battles. Treat this as a signal, not a final verdict.",
                "kind": "positive",
            })
        else:
            recommendations.append({
                "title": "Build a larger sample",
                "text": "Each observed deck has fewer than three recorded battles, so win-rate comparisons are still tentative.",
                "kind": "info",
            })

    upgrade_candidates = []
    for card in player.get("cards", []) or []:
        level = card.get("level")
        max_level = card.get("maxLevel")
        if isinstance(level, int) and isinstance(max_level, int) and level < max_level:
            upgrade_candidates.append({
                "name": card.get("name", "Unknown card"),
                "level": level,
                "maxLevel": max_level,
                "gap": max_level - level,
            })
    upgrade_candidates.sort(key=lambda item: (-item["gap"], item["name"]))

    return {
        "player": {
            "tag": tag,
            "name": player.get("name", "Unknown player"),
            "trophies": player.get("trophies", 0),
            "bestTrophies": player.get("bestTrophies", 0),
            "arena": (player.get("arena") or {}).get("name", "Unknown arena"),
        },
        "sampleSize": len(observed_battles),
        "decks": decks,
        "recentBattles": observed_battles[:20],
        "upgradeCandidates": upgrade_candidates[:12],
        "metaAvailable": bool(meta and meta.get("decks")),
        "metaDecks": (meta or {}).get("decks", [])[:10],
        "recommendations": recommendations,
    }


def generate_insights(player_path="player.json", battlelog_path="battlelog.json", output_path="insights.json", meta_path="meta.json"):
    meta_file = Path(meta_path)
    meta = load_json(meta_file) if meta_file.exists() else None
    insights = build_insights(load_json(player_path), load_json(battlelog_path), meta)
    Path(output_path).write_text(json.dumps(insights, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return insights


if __name__ == "__main__":
    generate_insights()
