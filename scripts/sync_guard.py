#!/usr/bin/env python3
"""
Data sync guard — checks if Mac data is stale vs Debian, auto-fixes it.
Run as a cron job to prevent data loss.
"""
import subprocess, json, os
from datetime import datetime

MAC_DATA = "/Volumes/Data/Deepseek_Awesome/data/jobs.json"
REPO_DIR = "/Volumes/Data/Deepseek_Awesome"

def ssh(cmd):
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
             "aelion@10.10.10.2", cmd],
            capture_output=True, timeout=10, text=True
        )
        return r.stdout.strip()
    except:
        return None

# Get Debian count
debian_count = ssh("python3 -c 'import json;d=json.load(open(\"/home/aelion/awesomejobs/data/jobs.json\"));print(len(d.get(\"jobs\",[])))'")
if not debian_count:
    print("❌ Can't reach Debian")
    exit(1)

# Get Mac count
try:
    with open(MAC_DATA) as f:
        mac_data = json.load(f)
    mac_count = len(mac_data.get("jobs", []))
except:
    mac_count = 0

print(f"Debian: {debian_count} jobs")
print(f"Mac: {mac_count} jobs")

if int(debian_count) > int(mac_count):
    print(f"⚠ Mac is STALE! Syncing from Debian...")
    subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
         "aelion@10.10.10.2:/home/aelion/awesomejobs/data/jobs.json", MAC_DATA],
        timeout=30
    )
    print("✅ Synced from Debian")
    
    # Push to GitHub
    subprocess.run(["git", "-C", REPO_DIR, "add", "data/jobs.json"], timeout=5)
    subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", f"auto: sync {debian_count} jobs from debian"], timeout=5)
    subprocess.run(["git", "-C", REPO_DIR, "push"], timeout=30)
    print("✅ Pushed to GitHub")
else:
    print("✅ In sync — no action needed")
