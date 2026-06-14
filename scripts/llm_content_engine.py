#!/usr/bin/env python3
"""
LLM Content Engine — generates SEO content, market reports, and social posts.
Uses qwen2.5-coder:7b on Mac Mini to create fresh content daily.
"""
import json, subprocess, os, re
from datetime import datetime

MODEL = "qwen2.5-coder:7b"
DATA_FILE = "/Volumes/Data/Deepseek_Awesome/data/jobs.json"
OUTPUT_DIR = "/Volumes/Data/Deepseek_Awesome"

def llm(prompt, max_tokens=500):
    try:
        r = subprocess.run(["ollama", "run", MODEL], input=prompt.encode(),
                          capture_output=True, timeout=90)
        text = r.stdout.decode().strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        return text
    except:
        return ""

def generate_market_report():
    """Generate a daily remote job market report."""
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    # Get stats
    total = len(data["jobs"])
    companies = len(set(j.get("company","") for j in data["jobs"] if j.get("company")))
    with_salary = sum(1 for j in data["jobs"] if j.get("salary"))
    
    # Get top categories
    from collections import Counter
    cats = Counter(j.get("category","other") for j in data["jobs"])
    top_cats = cats.most_common(5)
    
    prompt = f"""Write a short daily remote job market report (200 words max, no markdown).
    Today's date: {datetime.now().strftime('%B %d, %Y')}
    Total jobs: {total:,}
    Companies hiring: {companies}
    Jobs with salary: {with_salary:,}
    Top categories: {', '.join(f'{c} ({n})' for c,n in top_cats)}
    
    Make it interesting and useful for job seekers. One paragraph about trends, one about what to look for."""
    
    return llm(prompt)

def generate_social_post(platform="linkedin"):
    """Generate social media post for different platforms."""
    with open(DATA_FILE) as f:
        data = json.load(f)
    total = len(data["jobs"])
    
    styles = {
        "linkedin": "Professional, one paragraph, include hashtags. End with link.",
        "x": "Short, punchy, under 200 chars. Use emojis sparingly. End with link.",
        "reddit": "Informal, helpful tone. Include specific numbers. No emojis.",
    }
    
    prompt = f"""Write a {platform} post about AwesomeJobs remote job board.
    Style: {styles[platform]}
    Stats: {total:,} jobs from 86 companies. Updated every 15 minutes.
    Include: https://awesomejobs.online
    Make it engaging and shareable."""
    
    return llm(prompt)

def generate_faq():
    """Generate FAQ content for the website."""
    prompt = """Write an FAQ section for AwesomeJobs remote job board (5 questions/answers).
    Topics: how often updated, how to apply, is it free, what sources, how to search.
    Keep answers under 2 sentences each.
    Format: Q: question\nA: answer\n\n"""
    
    return llm(prompt, max_tokens=600)

# ── Run ──
print("🤖 LLM Content Engine —", datetime.now().strftime("%H:%M"))
print()

# 1. Market report
print("📊 Market Report:")
report = generate_market_report()
print(report[:300])
print()

# 2. Social posts  
print("📱 Social Posts:")
for p in ["linkedin", "x", "reddit"]:
    post = generate_social_post(p)
    with open(f"/tmp/social_{p}_{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
        f.write(post)
    print(f"  {p}: {post[:80]}...")

# 3. FAQ
print("\n❓ FAQ:")
faq = generate_faq()
with open(f"{OUTPUT_DIR}/faq-content.txt", "w") as f:
    f.write(faq)
print(faq[:300])

# 4. Save market report
with open(f"{OUTPUT_DIR}/market-report-{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
    f.write(report)

print("\n✅ All content generated")
