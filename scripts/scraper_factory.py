#!/usr/bin/env python3
"""
SCRAPER FACTORY — uses qwen2.5-coder:7b to write custom Python parsers
for new job sites, then runs them. LLM writes code → pipeline executes.
"""
import json, subprocess, urllib.request, re, os
from datetime import datetime, timezone

MODEL = "qwen2.5-coder:7b"
OUTPUT = "/Volumes/Data/Deepseek_Awesome/scripts/generated_scrapers"
os.makedirs(OUTPUT, exist_ok=True)

# New job sites we want to write scrapers for
TARGETS = [
    {"name": "weworkremotely", "url": "https://weworkremotely.com/", "desc": "WeWorkRemotely job board with category pages"},
    {"name": "remote-co", "url": "https://remote.co/remote-jobs/", "desc": "Remote.co job listings page"},
    {"name": "jobspresso", "url": "https://jobspresso.co/", "desc": "Jobspresso remote job board"},
    {"name": "nodesk", "url": "https://nodesk.co/remote-jobs/", "desc": "NoDesk remote job listings"},
    {"name": "remoteok", "url": "https://remoteok.com/remote-jobs", "desc": "RemoteOK job board"},
    {"name": "remotive", "url": "https://remotive.com/remote-jobs", "desc": "Remotive job board"},
    {"name": "hackernews", "url": "https://news.ycombinator.com/jobs", "desc": "Hacker News job listings"},
    {"name": "landing-jobs", "url": "https://landing.jobs/jobs", "desc": "Landing.jobs board"},
]

def fetch_sample(url):
    """Get a small sample of HTML from the target site."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=10) as r:
            # Get first 10000 chars (enough to understand page structure)
            return r.read().decode("utf-8", errors="replace")[:10000]
    except Exception as e:
        return f"ERROR: {e}"

def llm_generate_scraper(name, url, html_sample, description):
    """Ask qwen2.5-coder:7b to write a Python scraper for this site."""
    
    prompt = f"""You are an expert Python web scraper. Write a COMPLETE, RUNNABLE Python function 
that extracts job listings from {name} ({description}).

URL: {url}

Here is a sample of the page HTML:
```html
{html_sample}
```

Write a function: def scrape_{name}() that returns a list of dicts with keys:
- title (job title)
- company (company name) 
- location (where the job is)
- url (apply link)
- source = "{name}"

The function must:
1. Use ONLY urllib (no external deps)
2. Handle errors gracefully (return [] on failure)
3. Return actual job listings from the real URL
4. Be complete and runnable — no placeholders, no TODOs

Return ONLY the Python code. No explanation, no markdown fences."""

    try:
        r = subprocess.run(["ollama", "run", MODEL], input=prompt.encode(),
                          capture_output=True, timeout=60)
        code = r.stdout.decode().strip()
        # Clean up
        code = re.sub(r'<think>.*?</think>', '', code, flags=re.DOTALL).strip()
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*', '', code)
        return code
    except:
        return None

def validate_scraper(code):
    """Check if the generated code is valid Python."""
    try:
        compile(code, "<generated>", "exec")
        # Check it has the function
        return "def scrape_" in code and "return" in code and "urllib" in code.lower()
    except SyntaxError as e:
        print(f"    ❌ Syntax error: {e}")
        return False

def test_scraper(code):
    """Actually run the scraper and see if it returns jobs."""
    try:
        namespace = {}
        exec(code, namespace)
        func_name = [k for k in namespace if k.startswith("scrape_")][0]
        jobs = namespace[func_name]()
        if isinstance(jobs, list) and len(jobs) > 0:
            return jobs
        return None
    except Exception as e:
        print(f"    ❌ Runtime error: {e}")
        return None

# ── Main −─
print("🏭 Scraper Factory — qwen2.5-coder:7b writes custom scrapers")
print()

all_jobs = []
total_new = 0

for target in TARGETS:
    name = target["name"]
    url = target["url"]
    desc = target["desc"]
    
    print(f"🔍 {name}...", end=" ", flush=True)
    
    # Check if already have a working scraper
    scraper_file = f"{OUTPUT}/scrape_{name}.py"
    
    # 1: Fetch sample
    html = fetch_sample(url)
    if html.startswith("ERROR"):
        print(f"❌ Can't reach site")
        continue
    
    # 2: Generate scraper with LLM
    code = llm_generate_scraper(name, url, html, desc)
    if not code or not validate_scraper(code):
        print(f"❌ LLM generated invalid code")
        continue
    
    # Save the scraper
    with open(scraper_file, "w") as f:
        f.write(code)
    
    # 3: Test it
    print("testing...", end=" ", flush=True)
    jobs = test_scraper(code)
    
    if jobs and len(jobs) > 0:
        print(f"✅ {len(jobs)} jobs!")
        all_jobs.extend(jobs)
        total_new += len(jobs)
    else:
        print(f"📭 no jobs extracted")

# Merge results
if total_new > 0:
    print(f"\n📊 Got {total_new} jobs from LLM-generated scrapers")
    
    data_file = "/Volumes/Data/Deepseek_Awesome/data/jobs.json"
    with open(data_file) as f:
        main = json.load(f)
    
    existing = set((j.get("title","").lower(), j.get("company","").lower()) for j in main["jobs"])
    added = 0
    for j in all_jobs:
        key = (j.get("title","").lower(), j.get("company","").lower())
        if key not in existing:
            if not j.get("date_posted"):
                j["date_posted"] = datetime.now(timezone.utc).isoformat()
            if not j.get("source"):
                j["source"] = "llm-scraper"
            main["jobs"].append(j)
            existing.add(key)
            added += 1
    
    if added > 0:
        main["meta"]["total_jobs"] = len(main["jobs"])
        with open(data_file, "w") as f:
            json.dump(main, f, indent=2, ensure_ascii=False)
        print(f"✅ Merged {added} new unique jobs (total: {len(main['jobs'])})")
else:
    print("\n📭 No jobs extracted from any site")

# Cleanup LLM
subprocess.run(["ollama", "stop", MODEL], capture_output=True, timeout=5)
