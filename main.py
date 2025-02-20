import requests
import csv
import time
from tqdm import tqdm


def fetch_game_id(game_name):
    url = f"https://www.speedrun.com/api/v1/games?name={game_name}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: Unable to fetch game ID. Status code: {response.status_code}")
        return None

    data = response.json().get("data", [])

    if not data:
        print("No games found with that name.")
        return None

    print("Multiple games found:")
    for i, game in enumerate(data):
        print(f"{i + 1}: {game['names']['international']} ({game['id']})")

    try:
        choice = int(input("Enter the number of the correct game: ")) - 1
        if 0 <= choice < len(data):
            return data[choice]["id"], data[choice]["weblink"].split("/")[-1]
    except ValueError:
        pass

    print("Invalid choice.")
    return None, None


def fetch_category_ids(game_id):
    url = f"https://www.speedrun.com/api/v1/games/{game_id}/categories"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: Unable to fetch category IDs. Status code: {response.status_code}")
        return []

    data = response.json().get("data", [])
    return [(category["id"], category["name"]) for category in data]


def fetch_leaderboard_placements(game_id, category_id):
    url = f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category_id}?embed=players,run"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: Unable to fetch leaderboard data. Status code: {response.status_code}")
        return {}

    placements = {}
    data = response.json().get("data", {}).get("runs", [])
    for entry in data:
        run = entry.get("run", {})
        if run.get("status", {}).get("status") == "verified":
            placements[run["id"]] = entry.get("place", "N/A")

    return placements


def fetch_all_runs(category_id, request_count):
    runs = []
    offset = 0
    while True:
        if request_count % 100 == 0 and request_count > 0:
            print("Rate limit reached, waiting for 1 minute...")
            time.sleep(60)

        url = f"https://www.speedrun.com/api/v1/runs?category={category_id}&max=200&embed=players,videos,status&offset={offset}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: Unable to fetch run data. Status code: {response.status_code}")
            return None

        data = response.json().get("data", [])
        if not data:
            break

        runs.extend(data)
        offset += 200

    return {"data": {"runs": runs}}


def save_to_csv(data, category_name, filename, leaderboard_placements):
    if not data:
        print(f"No data to save for {category_name}.")
        return

    runs = data.get("data", {}).get("runs", [])

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([category_name])
        writer.writerow(["Place", "Runner", "Run Link", "Video Link"])

        for run in tqdm(runs, desc=f"Saving {category_name}"):
            if run.get("status", {}).get("status") == "rejected":
                continue  # Skip rejected runs

            videos = run.get("videos")
            if not videos or "links" not in videos:
                continue  # Skip runs without videos

            video_links = videos.get("links", [])
            twitch_links = [link.get("uri", "") for link in video_links if "twitch.tv" in link.get("uri", "")]
            if not twitch_links:
                continue  # Skip runs without Twitch links

            run_id = run.get("id", "N/A")
            players = run.get("players", {}).get("data", [])

            runner_name = "Unknown"
            if players:
                for player_info in players:
                    if isinstance(player_info, dict):
                        if player_info.get("rel") == "guest":
                            runner_name = player_info.get("name", "Guest")
                            break
                        elif player_info.get("id"):
                            runner_name = fetch_runner_name(player_info["id"])
                            break

            run_link = f"https://www.speedrun.com/run/{run_id}" if run_id != "N/A" else "N/A"
            place = leaderboard_placements.get(run_id, "N/A")

            for twitch_link in twitch_links:
                writer.writerow([place, runner_name, run_link, twitch_link])

    print(f"Runs for {category_name} saved to {filename}")


def fetch_runner_name(runner_id):
    if not runner_id:
        return "Unknown"

    url = f"https://www.speedrun.com/api/v1/users/{runner_id}"
    response = requests.get(url)

    if response.status_code != 200:
        return "Unknown"

    return response.json().get("data", {}).get("names", {}).get("international", "Unknown")


if __name__ == "__main__":
    game_name = input("Enter the Speedrun.com game name: ")
    game_id, game_url = fetch_game_id(game_name)

    if not game_id:
        print("Invalid game name or not found.")
        exit()

    categories = fetch_category_ids(game_id)

    if not categories:
        print("No categories found for this game.")
        exit()

    request_count = 0
    filename = f"leaderboard_{game_url}.csv"

    for category_id, category_name in categories:
        print(f"Fetching runs for category: {category_name} ({category_id})")
        leaderboard_placements = fetch_leaderboard_placements(game_id, category_id)
        run_data = fetch_all_runs(category_id, request_count)
        request_count += 1
        save_to_csv(run_data, category_name, filename, leaderboard_placements)
