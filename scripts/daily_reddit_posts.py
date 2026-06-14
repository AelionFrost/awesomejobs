#!/usr/bin/env python3
"""Generate Reddit post files."""
import json, os
from datetime import datetime

DATA_FILE = "/Volumes/DATA/Awesome_Jobs_WORK/data/jobs.json"
SITE_URL = "https://awesomejobs.online"

with open(DATA_FILE) as f:
    data = json.load(f)
jobs = data.get("jobs", [])
salaried = sorted([j for j in jobs if j.get("salary")], key=lambda j: str(j.get("date_posted","")), reverse=True)
top = (salaried + jobs)[:5]

os.makedirs("/tmp/reddit-posts", exist_ok=True)

for sub, label in [("remotejobs","Remote Jobs"), ("forhire","Paid Positions"), ("digitalnomad","Travel-Friendly Jobs")]:
    total = len(jobs)
    lines = [f"## 🔥 {label} - {datetime.now().strftime('%B %d, %Y')}", "", f"Found **{total:,}** remote jobs. Top picks:", ""]
    for j in top:
        t = j.get("title", "Position")
        c = j.get("company", "Company")
        s = f" · 💰 {j['salary']}" if j.get("salary") else ""
        l = j.get("location", "Remote")
        u = j.get("apply_url", SITE_URL)
        lines.append(f"• **[{t}]({u})** at *{c}* — {l}{s}")
    lines.extend(["", "---", f"🌐 Browse all {total:,} jobs: {SITE_URL}", "", "*Auto-posted daily*"])
    
    title = f"[HIRING] {total:,} {label} - {datetime.now().strftime('%b %d, %Y')}"
    content = f"TITLE: {title}\nSUBREDDIT: r/{sub}\n---\n" + "\n".join(lines)
    
    with open(f"/tmp/reddit-posts/{sub}-{datetime.now().strftime('%Y%m%d')}.md", "w") as f:
        f.write(content)
    print(f"✅ r/{sub}")
