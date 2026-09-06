import json
import itertools
import math
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


def extract_war_rounds(battle, tag):
    player = next((item for item in battle.get("team", []) or [] if item.get("tag") == tag), None)
    opponent = (battle.get("opponent", []) or [None])[0]
    rounds = (player or {}).get("rounds", []) or []
    opponent_rounds = (opponent or {}).get("rounds", []) or []
    observations = []
    for index, round_data in enumerate(rounds):
        deck = round_data.get("cards", []) or []
        if not deck:
            continue
        enemy_round = opponent_rounds[index] if index < len(opponent_rounds) else {}
        won = None
        if "crowns" in round_data and "crowns" in enemy_round:
            won = round_data["crowns"] > enemy_round["crowns"]
        observations.append((deck, won))
    return observations


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


def battle_category(battle):
    deck_selection = str(battle.get("deckSelection", "")).lower()
    battle_type = str(battle.get("type", "")).lower()
    if deck_selection in {"wardeck", "wardeckpick"} or battle_type.startswith("riverrace") or battle_type == "boatbattle":
        return "war"
    return "regular"


def observed_decks(battle, tag):
    if battle_category(battle) == "war" and str(battle.get("deckSelection", "")).lower() == "wardeckpick":
        return extract_war_rounds(battle, tag)
    deck = extract_player_deck(battle, tag)
    return [(deck, battle_won(battle, tag))] if deck else []


def meta_match_score(deck, meta_decks):
    deck_ids = {card_id(card) for card in deck.get("cards", [])}
    best_score = 0.0
    for meta_deck in meta_decks:
        meta_ids = {card_id(card) for card in meta_deck.get("cards", [])}
        if not meta_ids:
            continue
        overlap = len(deck_ids & meta_ids) / max(len(deck_ids), len(meta_ids))
        best_score = max(best_score, overlap * float(meta_deck.get("weight", 1)))
    return round(best_score, 3)


def choose_war_decks(decks, meta_decks=None, limit=4):
    candidates = [deck for deck in decks if deck.get("category") == "war" and len(deck.get("cards", [])) == 8]
    if not candidates:
        return []
    ranked = []
    for deck in candidates:
        card_ids = {card_id(card) for card in deck["cards"]}
        meta_score = meta_match_score(deck, meta_decks or [])
        evidence_score = deck["winRate"] + min(deck["battles"], 10) * 2
        deck["metaScore"] = meta_score
        ranked.append((deck, card_ids, evidence_score + meta_score * 10))
    best = []
    best_score = (-1, -1.0)
    for count in range(1, min(limit, len(ranked)) + 1):
        for combination in itertools.combinations(ranked, count):
            used = set()
            valid = True
            for _, card_ids, _ in combination:
                if used.intersection(card_ids):
                    valid = False
                    break
                used.update(card_ids)
            if not valid:
                continue
            score = sum(item[2] for item in combination)
            ranking = (count, score)
            if ranking > best_score:
                best_score = ranking
                best = [item[0] for item in combination]
    return best


def build_insights(player, battlelog, meta=None):
    tag = player_tag(player)
    battles = battlelog if isinstance(battlelog, list) else battlelog.get("items", [])
    deck_stats = defaultdict(lambda: {"battles": 0, "wins": 0, "deck": []})
    observed_battles = []

    for battle in battles:
        category = battle_category(battle)
        for deck, won in observed_decks(battle, tag):
            key = (category, deck_key(deck))
            stats = deck_stats[key]
            stats["battles"] += 1
            stats["deck"] = deck
            if won is True:
                stats["wins"] += 1
            observed_battles.append({
                "deck": deck,
                "deckLabel": deck_label(deck),
                "category": category,
                "won": won,
                "type": battle.get("type") or battle.get("gameMode", {}).get("name"),
                "date": battle.get("battleTime") or battle.get("date"),
            })

    decks = []
    for key, stats in deck_stats.items():
        decks.append({
            "label": deck_label(stats["deck"]),
            "category": key[0],
            "cards": stats["deck"],
            "battles": stats["battles"],
            "wins": stats["wins"],
            "winRate": round(stats["wins"] / stats["battles"] * 100, 1),
        })
    decks.sort(key=lambda item: (-item["battles"], -item["winRate"]))

    meta_decks = (meta or {}).get("decks", [])
    war_deck_plan = choose_war_decks(decks, meta_decks)
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
                "text": f"{best['winRate']:.0f}% wins across {best['battles']} recorded battles. Treat this as a signal, not a final verdict.",
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
        "warDeckPlan": war_deck_plan,
        "recommendations": recommendations,
    }


def build_analysis_export(insights):
    decks = insights.get("decks", [])
    return {
        "player": insights["player"],
        "sampleSize": insights["sampleSize"],
        "regularDecks": [deck for deck in decks if deck.get("category") == "regular"],
        "warDecks": [deck for deck in decks if deck.get("category") == "war"],
        "warDeckPlan": insights.get("warDeckPlan", []),
        "recentBattles": insights["recentBattles"],
        "upgradeCandidates": insights["upgradeCandidates"],
    }


def markdown_deck(deck):
    cards = ", ".join(card.get("name", "Unknown card") for card in deck.get("cards", []))
    return f"- {cards} - {deck['wins']}/{deck['battles']} wins ({deck['winRate']}%)"


def build_analysis_markdown(export):
    player = export["player"]
    lines = [
        "# Clash Royale player analysis input",
        "",
        "Use this data to analyze the player's current observed decks. Do not invent cards, battles, or conclusions beyond the supplied sample.",
        "",
        f"Player: {player['name']} ({player['tag']})",
        f"Trophies: {player['trophies']}",
        f"Observed battles: {export['sampleSize']}",
        "",
        "## Regular decks",
    ]
    lines.extend(markdown_deck(deck) for deck in export["regularDecks"])
    if not export["regularDecks"]:
        lines.append("- No regular decks observed.")
    lines.extend(["", "## War decks"])
    lines.extend(markdown_deck(deck) for deck in export["warDecks"])
    if not export["warDecks"]:
        lines.append("- No war decks observed.")
    lines.extend(["", "## Recommended four-deck war plan"])
    if export.get("warDeckPlan"):
        lines.extend(markdown_deck(deck) for deck in export["warDeckPlan"])
    else:
        lines.append("- No four-deck plan available from the current sample.")
    lines.extend(["", "## Upgrade candidates"])
    lines.extend(
        f"- {card['name']}: level {card['level']}/{card['maxLevel']}"
        for card in export["upgradeCandidates"]
    )
    if not export["upgradeCandidates"]:
        lines.append("- No upgrade data available.")
    return "\n".join(lines) + "\n"


def generate_insights(player_path="player.json", battlelog_path="battlelog.json", output_path="insights.json", meta_path="meta.json"):
    meta_file = Path(meta_path)
    meta = load_json(meta_file) if meta_file.exists() else None
    insights = build_insights(load_json(player_path), load_json(battlelog_path), meta)
    Path(output_path).write_text(json.dumps(insights, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    export = build_analysis_export(insights)
    output_file = Path(output_path)
    output_file.with_name("player-analysis.json").write_text(json.dumps(export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_file.with_name("player-analysis.md").write_text(build_analysis_markdown(export), encoding="utf-8")
    return insights


if __name__ == "__main__":
    generate_insights()
