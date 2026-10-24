import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://proxy.royaleapi.dev/v1"
DEFAULT_PLAYER_TAG = "#URUQ09LVG"
HISTORY_FILE = "battle-history.json"
OUTPUT_FILES = ("player.json", HISTORY_FILE, "metadata.json")


def player_tag():
    return os.environ.get("CLASH_ROYALE_PLAYER_TAG", DEFAULT_PLAYER_TAG).strip()


def fetch_json(url, token):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "clash-royale-player-dashboard/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"API returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API returned HTTP {error.code}: {body[:300]}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach API: {error.reason}") from error


def merge_battles(history, new_battles):
    by_time = {battle["battleTime"]: battle for battle in history}
    by_time.update((battle["battleTime"], battle) for battle in new_battles)
    return sorted(by_time.values(), key=lambda battle: battle["battleTime"], reverse=True)


def write_json_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        json.dump(data, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def main():
    token = os.environ.get("CLASH_ROYALE_TOKEN")
    if not token:
        raise RuntimeError("CLASH_ROYALE_TOKEN is not set")

    tag = player_tag()
    if not tag.startswith("#"):
        tag = f"#{tag}"
    encoded_tag = urllib.parse.quote(tag, safe="")

    history_path = Path(HISTORY_FILE)
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    battlelog = fetch_json(f"{API_BASE}/players/{encoded_tag}/battlelog", token)
    snapshots = {
        "player.json": fetch_json(f"{API_BASE}/players/{encoded_tag}", token),
        HISTORY_FILE: merge_battles(history, battlelog),
    }
    snapshots["metadata.json"] = {
        "playerTag": tag,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "source": API_BASE,
    }

    for filename, data in snapshots.items():
        write_json_atomic(filename, data)

    print(f"Saved {', '.join(OUTPUT_FILES)} for {tag}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Fetch failed: {error}")
        raise SystemExit(1)
