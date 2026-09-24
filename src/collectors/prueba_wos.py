import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WOS_API_KEY")

resp = requests.get(
    "https://api.clarivate.com/apis/wos-starter/v2/documents",
    headers={"X-ApiKey": API_KEY},
    params={
        "db": "WOS",
        "q": "TS=(multi-agent AND scheduling)",
        "limit": 10,
        "publishTimeSpan": "2021-01-01+2026-12-31",
    },
)

print(resp.status_code)
data = resp.json()
print("Total:", data.get("metadata", {}).get("total"))
for hit in data.get("hits", []):
    print(hit.get("title"), "→", hit.get("types"))