#!/usr/bin/env python3
"""
Two-stage pipeline with DUAL scrapers:
  Scraper: qwen2.5-coder:7b
Both run in parallel for max throughput.
"""
import json, urllib.request, subprocess, os, time, queue, threading, re
from datetime import datetime, timezone

DATA_FILE = "/Volumes/DATA/Awesome_Jobs_WORK/data/jobs.json"
OUTPUT = "/tmp/scraper_pipeline_output.json"
WORK_QUEUE = queue.Queue()
RESULTS = []
LOCK = threading.Lock()

MODEL = "qwen2.5-coder:7b"

TARGETS = [
    {"name": "automattic", "url": "https://automattic.com/work-with-us/", "cat": "dev"},
    {"name": "buffer", "url": "https://buffer.com/careers", "cat": "marketing"},
    {"name": "doist", "url": "https://doist.com/careers", "cat": "dev"},
    {"name": "toggl", "url": "https://toggl.com/jobs/", "cat": "dev"},
    {"name": "basecamp", "url": "https://basecamp.com/about/jobs", "cat": "dev"},
    {"name": "gitlab", "url": "https://about.gitlab.com/jobs/", "cat": "dev"},
    {"name": "zapier", "url": "https://zapier.com/jobs/", "cat": "dev"},
    {"name": "tomedes", "url": "https://www.tomedes.com/careers", "cat": "translation"},
    {"name": "smartling", "url": "https://www.smartling.com/careers/", "cat": "translation"},
    {"name": "scale-ai", "url": "https://scale.com/careers", "cat": "data"},
    {"name": "dribbble", "url": "https://dribbble.com/jobs", "cat": "design"},
    {"name": "behance", "url": "https://www.behance.net/joblist", "cat": "design"},
    {"name": "remote-ok", "url": "https://remoteok.com/", "cat": "mixed"},
    {"name": "justjoin", "url": "https://justjoin.it/", "cat": "dev"},
    {"name": "wellfound", "url": "https://wellfound.com/jobs", "cat": "dev"},
    {"name": "hackernews", "url": "https://news.ycombinator.com/jobs", "cat": "dev"},
    {"name": "landing-jobs", "url": "https://landing.jobs/", "cat": "dev"},
    {"name": "remoteurope", "url": "https://remoteurope.com/", "cat": "dev"},
    {"name": "jobspresso", "url": "https://jobspresso.co/", "cat": "mixed"},
    {"name": "remotive", "url": "https://remotive.com/", "cat": "mixed"},
]

def check_source(name, url, timeout=6):
    """Stage 1: Quick HTTP check."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            if len(body) > 2000:
                return True, body[:5000]
            return False, ""
    except:
        return False, ""

def llm_extract(name, url, html, category, model):
    """Extract jobs from HTML using given model."""
    prompt = f"""Extract ALL remote job listings from this career page HTML.

Source: {name}
URL: {url}
Category: {category}

Return a JSON array of objects with fields: title, company, location, url
Include ALL jobs found. If none, return [].
Raw JSON only, no markdown.

HTML:
{html[:3000]}"""
    
    try:
        r = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode(),
            capture_output=True, timeout=60
        )
        text = r.stdout.decode().strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'[\x00-\x1f]', '', text)
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            jobs = json.loads(match.group())
            return [j for j in jobs if j.get("title")] if isinstance(jobs, list) else []
        return []
    except:
        return []

def checker_thread():
    """Producer: checks URLs, puts working ones on queue."""
    print(f"🔍 Checker: Testing {len(TARGETS)} sources...")
    for target in TARGETS:
        ok, body = check_source(target["name"], target["url"])
        if ok:
            print(f"  ✅ {target['name']}")
            WORK_QUEUE.put({"name": target["name"], "url": target["url"],
                           "html": body, "cat": target["cat"]})
        else:
            print(f"  ❌ {target['name']}")
        time.sleep(0.3)
    for _ in range(1):
        WORK_QUEUE.put(None)

def scraper_thread(model, label):
    """Consumer: takes working sources, extracts jobs with qwen2.5-coder:7b."""
    my_results = []
    while True:
        item = WORK_QUEUE.get()
        if item is None:
            break
        
        print(f"  🤖 [{label}] Scraping {item['name']}...", end=" ", flush=True)
        jobs = llm_extract(item["name"], item["url"], item["html"], item["cat"], model)
        
        if jobs:
            now = datetime.now(timezone.utc).isoformat()
            for j in jobs:
                j["source"] = f"llm-{item['name']}"
                j["category"] = item["cat"]
                j["date_posted"] = now
                if not j.get("company"):
                    j["company"] = item["name"].replace("-", " ").title()
                if not j.get("location"):
                    j["location"] = "Remote"
                j["apply_url"] = j.get("url", item["url"])
            my_results.extend(jobs)
            print(f"✅ {len(jobs)} jobs")
        else:
            print("📭 none")
        time.sleep(0.3)
    
    with LOCK:
        RESULTS.extend(my_results)
    print(f"  [{label}] Done — {len(my_results)} jobs")

def merge_results():
    if not RESULTS:
        print("📭 No jobs to merge")
        return
    
    with open(DATA_FILE) as f:
        main = json.load(f)
    
    existing = set(
        (j.get("title", "").lower().strip(), j.get("company", "").lower().strip())
        for j in main.get("jobs", [])
    )
    
    new = []
    for j in RESULTS:
        key = (j.get("title", "").lower().strip(), j.get("company", "").lower().strip())
        if key not in existing:
            new.append(j)
            existing.add(key)
    
    if new:
        main["jobs"].extend(new)
        main["meta"]["total_jobs"] = len(main["jobs"])
        main["meta"]["generated_at"] = datetime.now(timezone.utc).isoformat()
        with open(DATA_FILE, "w") as f:
            json.dump(main, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Merged {len(new)} new jobs (total: {len(main['jobs'])})")
    else:
        print(f"\n📭 No new unique jobs")

def main():
    print("=" * 55)
    print("🚀 Two-Stage Pipeline")
    print(f"   Checker: HTTP (no LLM)")
    print(f"   Scraper: {MODEL}")
    print(f"   Sources: {len(TARGETS)}")
    print("=" * 55)
    print()
    
    threads = [
        threading.Thread(target=checker_thread),
        threading.Thread(target=scraper_thread, args=(MODEL, "qwen7b")),
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print(f"\n📊 Total: {len(RESULTS)} jobs extracted")
    merge_results()
    
    # Unload model to free RAM
    print("🧹 Unloading qwen2.5-coder:7b to free RAM...")
    subprocess.run(["ollama", "stop", "qwen2.5-coder:7b"], capture_output=True, timeout=10)
    # Also kill any stale llama-server processes
    subprocess.run(["pkill", "-f", "llama-server"], capture_output=True, timeout=5)
    print("✅ RAM freed")
    
    with open(OUTPUT, "w") as f:
        json.dump({"results": RESULTS}, f, indent=2)

if __name__ == "__main__":
    main()
