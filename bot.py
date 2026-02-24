import requests
import datetime
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def get_upcoming_contests():
    url = "https://codeforces.com/api/contest.list"
    response = requests.get(url).json()

    contests = response["result"]
    upcoming = []

    for contest in contests:
        if contest["phase"] == "BEFORE":
            start_time = datetime.datetime.fromtimestamp(contest["startTimeSeconds"])
            upcoming.append((contest["name"], start_time))
    
    return upcoming[:3]

def main():
    contests = get_upcoming_contests()
    
    if not contests:
        send_message("No upcoming Codeforces contests found.")
        return
    
    message = "*Upcoming Codeforces Contests:*\n\n"
    for name, start in contests:
        message += f"• {name}\n  Starts at: {start} UTC\n\n"
    
    send_message(message)

if __name__ == "__main__":
    main()
