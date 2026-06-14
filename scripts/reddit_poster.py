#!/usr/bin/env python3
"""Reddit auto-poster for awesomejobs.online — posts top jobs daily."""
import json, subprocess, os, random
from datetime import datetime

DATA_FILE = "/Volumes/DATA/Awesome_Jobs_WORK/data/jobs.json"
SITE_URL = "https://awesomejobs.online"

# Subreddits that allow job posts
SUBREDDITS = [
    ("r/remotejobs", "remotejobs"),
    ("r/workonline", "workonline"),
    ("r/forhire", "forhire"),
    ("r/RemoteWork", "RemoteWork"),
    ("r/digitalnomad", "digitalnomad"),
]

def get_top_jobs(n=5):
    """Get top jobs from data file."""
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        jobs = data.get("jobs", [])
        # Sort by recency, prefer salaried
        jobs.sort(key=lambda j: (
            1 if j.get("salary") else 0,
            j.get("date_posted", "")
        ), reverse=True)
        return jobs[:n]
    except:
        return []

def generate_post(jobs, subreddit):
    """Generate a Reddit post for the given subreddit."""
    if not jobs:
        return None
    
    cat_name = subreddit.split("/")[-1].lower()
    
    # Filter jobs relevant to subreddit
    if "remote" in cat_name:
        relevant = jobs
    elif "forhire" in cat_name:
        relevant = [j for j in jobs if j.get("salary")]
    elif "workonline" in cat_name:
        relevant = [j for j in jobs if not j.get("tags") or "entry" in " ".join(j.get("tags",[])).lower()]
    else:
        relevant = jobs
    
    if not relevant:
        relevant = jobs[:3]
    
    # Build post body
    lines = [f"# 🔥 New Remote Jobs - {datetime.now().strftime('%B %d, %Y')}"]
    lines.append("")
    lines.append(f"Found **{len(jobs):,}** remote jobs on [AwesomeJobs]({SITE_URL}). Here are the top picks:")
    lines.append("")
    
    for j in relevant[:5]:
        title = j.get("title", "Remote Job")
        company = j.get("company", "Unknown Company")
        salary = f" · 💰 {j['salary']}" if j.get("salary") else ""
        url = j.get("apply_url", SITE_URL)
        location = j.get("location", "Remote")
        tags = ", ".join(j.get("tags", [])[:3])
        tags_str = f" · 🏷️ {tags}" if tags else ""
        
        lines.append(f"### [{title}]({url})")
        lines.append(f"**{company}** · 📍 {location}{salary}{tags_str}")
        lines.append("")
    
    lines.append("---")
    lines.append(f"🌐 Browse all {len(jobs):,} jobs → [{SITE_URL}]({SITE_URL})")
    lines.append("")
    lines.append("*Posts automatically · Updated daily from 50+ sources*")
    
    return "\n".join(lines)

def create_post_files():
    """Create post files ready for manual submission or PRAW posting."""
    jobs = get_top_jobs(10)
    os.makedirs("/tmp/reddit-posts", exist_ok=True)
    
    for sub, _ in SUBREDDITS:
        body = generate_post(jobs, sub)
        if not body:
            continue
        
        filename = f"/tmp/reddit-posts/{sub.replace('/','-')}-{datetime.now().strftime('%Y%m%d')}.md"
        with open(filename, "w") as f:
            f.write(body)
        print(f"✅ Created: {filename}")

if __name__ == "__main__":
    create_post_files()
    print("\n📝 Posts ready at /tmp/reddit-posts/")
    print("   To post: copy content → paste on Reddit")
