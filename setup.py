import requests, json

url = "https://codeforces.com/api/problemset.problems"
data = requests.get(url).json()

with open("problems.json", "w") as f:
    json.dump(data["result"]["problems"], f)

print("Saved problems.json")