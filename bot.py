import requests
import random
import os
import json
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PROBLEMS_FILE = "problems.json"
USED_FILE = "used_problems.json"
CONTEST_REMINDER_FILE = "reminded_contests.json"

IST = timezone(timedelta(hours=5, minutes=30))


# ---------------- TELEGRAM ----------------

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    response = requests.post(url, data=payload)
    print("Telegram response:", response.text)


# ---------------- DAILY PROBLEMS ----------------

def load_problems():
    with open(PROBLEMS_FILE, "r") as f:
        problems = json.load(f)

    # Keep only rated problems
    return [p for p in problems if "rating" in p]


def load_used():
    if not os.path.exists(USED_FILE):
        return set()

    with open(USED_FILE, "r") as f:
        return set(tuple(x) for x in json.load(f))


def save_used(used):
    with open(USED_FILE, "w") as f:
        json.dump(list(used), f)


def pick_unique(problems, used, min_rating=None, max_rating=None):
    candidates = problems

    if min_rating is not None:
        candidates = [
            p for p in problems
            if min_rating <= p["rating"] <= max_rating
        ]

    random.shuffle(candidates)

    for p in candidates:
        key = (p["contestId"], p["index"])
        if key not in used:
            used.add(key)
            return p

    return None


def build_link(problem):
    return f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"


def send_daily_problems():
    problems = load_problems()
    used = load_used()

    p1 = pick_unique(problems, used, 1000, 1200)
    p2 = pick_unique(problems, used, 1400, 1600)
    p3 = pick_unique(problems, used)

    if not all([p1, p2, p3]):
        send_message("Not enough unused problems left.")
        return

    message = "Daily Codeforces Challenge\n\n"

    message += (
        "Easy (1000–1200)\n"
        f"{p1['name']} (Rating {p1['rating']})\n"
        f"{build_link(p1)}\n\n"
    )

    message += (
        "Medium (1400–1600)\n"
        f"{p2['name']} (Rating {p2['rating']})\n"
        f"{build_link(p2)}\n\n"
    )

    message += (
        "Random\n"
        f"{p3['name']} (Rating {p3['rating']})\n"
        f"{build_link(p3)}"
    )

    send_message(message)
    save_used(used)


# ---------------- CONTEST REMINDERS ----------------

def load_reminded():
    if not os.path.exists(CONTEST_REMINDER_FILE):
        return set()

    with open(CONTEST_REMINDER_FILE, "r") as f:
        return set(json.load(f))


def save_reminded(reminded):
    with open(CONTEST_REMINDER_FILE, "w") as f:
        json.dump(list(reminded), f)


def is_div2_or_div3(name):
    name_lower = name.lower()
    return "div. 2" in name_lower or "div. 3" in name_lower


def check_and_send_contest_reminders():
    url = "https://codeforces.com/api/contest.list"
    response = requests.get(url).json()

    if response["status"] != "OK":
        print("Failed to fetch contests")
        return

    contests = response["result"]
    reminded = load_reminded()

    now = datetime.now(timezone.utc)

    for contest in contests:
        if contest["phase"] != "BEFORE":
            continue

        if not is_div2_or_div3(contest["name"]):
            continue

        contest_id = str(contest["id"])

        start_time_utc = datetime.fromtimestamp(
            contest["startTimeSeconds"],
            tz=timezone.utc
        )

        time_diff = (start_time_utc - now).total_seconds()

        # 72 hours = 259200 seconds
        if 0 <= time_diff <= 259200:
            if contest_id not in reminded:

                start_time_ist = start_time_utc.astimezone(IST)

                message = (
                    "Upcoming Codeforces Contest\n\n"
                    f"{contest['name']}\n"
                    f"Starts at {start_time_ist.strftime('%Y-%m-%d %I:%M %p IST')}\n"
                    f"https://codeforces.com/contest/{contest['id']}"
                )

                send_message(message)
                reminded.add(contest_id)

    save_reminded(reminded)


# ---------------- MAIN ----------------

def main():
    try:
        # Always check contest reminders
        check_and_send_contest_reminders()

        # Send daily problems only if RUN_DAILY=true
        if os.environ.get("RUN_DAILY") == "true":
            send_daily_problems()

    except Exception as e:
        print("Error:", e)
        send_message("Bot encountered an error.")


if __name__ == "__main__":
    main()