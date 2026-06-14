#!/usr/bin/env python3
"""
Reddit auto-poster for awesomejobs.online
Uses browser automation (no API keys needed).
"""
import json, os, random, time
from datetime import datetime

DATA_FILE = "/Volumes/DATA/Awesome_Jobs_WORK/data/jobs.json"
SITE_URL = "https://awesomejobs.online"

SUBREDDITS = [
    "remotejobs",
    "RemoteWork", 
    "digitalnomad",
    "forhire",
    "workonline",
]

def get_top_jobs(n=6):
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        jobs = data.get("jobs", [])
        jobs.sort(key=lambda j: (1 if j.get("salary") else 0, j.get("date_posted", "")), reverse=True)
        return jobs[:n]
    except:
        return []

def build_post(jobs, sub):
    """Build post title and body for a subreddit."""
    if not jobs:
        return None, None
    
    total = 6874  # approximate total
    
    # Title
    if sub in ("remotejobs", "RemoteWork"):
        title = f"[HIRING] {len(jobs):,} New Remote Jobs - {datetime.now().strftime('%b %d')}"
    elif sub == "forhire":
        title = f"[HIRING] Remote Jobs with Salary - {datetime.now().strftime('%b %d, %Y')}"
    elif sub == "digitalnomad":
        title = f"🌍 {len(jobs):,} Remote Jobs You Can Do from Anywhere - {datetime.now().strftime('%b %d')}"
    else:
        title = f"🔥 {len(jobs):,} New Remote Job Openings - Work From Home"
    
    # Body
    lines = [
        f"# 🔥 Remote Jobs - {datetime.now().strftime('%B %d, %Y')}",
        "",
        f"Found **{total:,}** remote jobs on [AwesomeJobs]({SITE_URL}). Top picks:",
        "",
    ]
    
    for j in jobs[:5]:
        title_j = j.get("title", "Remote Position")
        company = j.get("company", "Company")
        salary = f"💰 {j['salary']}" if j.get("salary") else ""
        loc = j.get("location", "Remote")
        url = j.get("apply_url", SITE_URL)
        
        line = f"**[{title_j}]({url})** at *{company}* — {loc}"
        if salary:
            line += f" · {salary}"
        lines.append(f"- {line}")
    
    lines.extend([
        "",
        "---",
        f"🌐 Browse all {total:,} jobs: [{SITE_URL}]({SITE_URL})",
        "",
        "*Auto-posted daily from 50+ sources*",
    ])
    
    return title, "\n".join(lines)

def save_posts():
    """Save posts to files so user can review before posting."""
    jobs = get_top_jobs()
    os.makedirs("/tmp/reddit-posts", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d")
    
    for sub in SUBREDDITS:
        title, body = build_post(jobs, sub)
        if not title:
            continue
        
        content = f"""TITLE: {title}
SUBREDDIT: r/{sub}
---
{body}
"""
        fname = f"/tmp/reddit-posts/{sub}-{ts}.md"
        with open(fname, "w") as f:
            f.write(content)
        print(f"✅ r/{sub} — ready")

if __name__ == "__main__":
    save_posts()
