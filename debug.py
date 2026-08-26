import os, urllib.request, json
k = os.environ.get("DAHL_KEY", "")
print("key len:", len(k), "| prefix:", k[:8], "| suffix:", k[-4:])
req = urllib.request.Request("https://inference.dahl.global/v1/models",
    headers={"Authorization": "Bearer " + k,
             "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("models endpoint:", r.status)
except Exception as e:
    print("models endpoint FAILED:", str(e)[:150])
