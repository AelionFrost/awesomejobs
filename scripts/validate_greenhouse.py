#!/usr/bin/env python3
"""Quick-check which Greenhouse companies work. Saves valid list to Debian."""
import json, urllib.request, time, subprocess, sys

MANIFEST = "/home/aelion/awesomejobs/scripts/source_manifest.json"
VALID_FILE = "/home/aelion/awesomejobs/scripts/valid_greenhouse.json"

# First, get the company list from Debian
r = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
     "aelion@10.10.10.2", f"python3 -c 'import json; m=json.load(open(\"{MANIFEST}\")); print(json.dumps(m[\"ats_boards\"][\"greenhouse\"]))'"],
    capture_output=True, text=True, timeout=15
)
companies = json.loads(r.stdout.strip())

print(f"🔍 Testing {len(companies)} companies from Mac Mini...")
working = []

for i, co in enumerate(companies):
    url = f"https://boards-api.greenhouse.io/v1/boards/{co}/jobs"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            count = len(data.get("jobs", []))
            if count > 0:
                working.append(co)
                if i % 10 == 0:
                    print(f"  [{i}/{len(companies)}] {co}: {count} jobs ✅")
    except:
        if i % 20 == 0:
            print(f"  [{i}/{len(companies)}] {co}: ❌")
    time.sleep(0.1)

print(f"\n✅ Found {len(working)} working companies out of {len(companies)}")

# Save to Debian
valid_json = json.dumps(sorted(working))
subprocess.run([
    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
    "aelion@10.10.10.2",
    f"python3 -c '\"\"\"\nimport json\nm=json.load(open(\"{MANIFEST}\"))\nm[\"ats_boards\"][\"greenhouse\"] = {valid_json}\njson.dump(m, open(\"{MANIFEST}\",\"w\"), indent=2)\nprint(\"Updated manifest with \" + str(len(m[\"ats_boards\"][\"greenhouse\"])) + \" companies\")\n\"\"\"'"
], timeout=15)

print("✅ Pushed to Debian")
