#!/usr/bin/env python3
"""
Two-stage pipeline on Mac Mini:
  Stage 1 (Checker): Fast HTTP checks - tests if sources are reachable
  Stage 2 (Scraper): llama3.2:3b extracts jobs from working sources
Both run in parallel using a producer-consumer queue.
"""
import json, urllib.request, subprocess, os, time, queue, threading, re
from datetime import datetime, timezone

MODEL = "llama3.2:3b"
DATA_FILE = "/Volumes/DATA/Awesome_Jobs_WORK/data/jobs.json"
OUTPUT = "/tmp/scraper_pipeline_output.json"
WORK_QUEUE = queue.Queue()
RESULTS = []
LOCK = threading.Lock()

# Sources to check and scrape
TARGETS = [
    # Remote-first companies
    {"name": "automattic", "url": "https://automattic.com/work-with-us/", "cat": "dev"},
    {"name": "buffer", "url": "https://buffer.com/careers", "cat": "marketing"},
    {"name": "doist", "url": "https://doist.com/careers", "cat": "dev"},
    {"name": "toggl", "url": "https://toggl.com/jobs/", "cat": "dev"},
    {"name": "basecamp", "url": "https://basecamp.com/about/jobs", "cat": "dev"},
    {"name": "gitlab", "url": "https://about.gitlab.com/jobs/", "cat": "dev"},
    {"name": "zapier", "url": "https://zapier.com/jobs/", "cat": "dev"},
    
    # Translation / Writing
    {"name": "tomedes", "url": "https://www.tomedes.com/careers", "cat": "translation"},
    {"name": "gengo", "url": "https://gengo.com/translator/jobs", "cat": "translation"},
    {"name": "unbabel", "url": "https://unbabel.com/careers/", "cat": "translation"},
    {"name": "smartling", "url": "https://www.smartling.com/careers/", "cat": "translation"},
    
    # Data / AI
    {"name": "scale-ai", "url": "https://scale.com/careers", "cat": "data"},
    {"name": "labelbox", "url": "https://labelbox.com/careers", "cat": "data"},
    {"name": "hugging-face", "url": "https://huggingface.co/join", "cat": "data"},
    
    # Design
    {"name": "dribbble", "url": "https://dribbble.com/jobs", "cat": "design"},
    {"name": "behance", "url": "https://www.behance.net/joblist", "cat": "design"},
    
    # General remote job boards
    {"name": "remote-co", "url": "https://remote.co/remote-jobs/", "cat": "mixed"},
    {"name": "europeremotely", "url": "https://europeremotely.com/", "cat": "mixed"},
    {"name": "remote-ok", "url": "https://remoteok.com/", "cat": "mixed"},
]

def check_source(name, url, timeout=6):
    """Stage 1: Quick HTTP check. Returns True if reachable."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")
            if len(body) > 2000:
                return True, body[:5000]
            return False, ""
    except Exception as e:
        return False, str(e)

def llm_extract(name, url, html, category):
    """Stage 2: Use llama3.2:3b to extract jobs from HTML."""
    prompt = f"""Extract remote job listings from this career page HTML.

Source: {name}
URL: {url}
Category: {category}

Return ONLY a JSON array of objects with: title, company, location, url (apply link)
If no remote jobs found, return empty array [].
No markdown, no explanation. Raw JSON only.

HTML snippet:
{html[:3000]}"""
    
    try:
        r = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt.encode(),
            capture_output=True, timeout=45
        )
        text = r.stdout.decode().strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'[\x00-\x1f]', '', text)
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            jobs = json.loads(match.group())
            if isinstance(jobs, list):
                return [j for j in jobs if j.get("title")]
        return []
    except:
        return []

def checker_thread():
    """Producer: checks URLs and puts working ones on the queue."""
    print(f"🔍 Checker: Testing {len(TARGETS)} sources...")
    for target in TARGETS:
        ok, body = check_source(target["name"], target["url"])
        if ok:
            print(f"  ✅ {target['name']} - reachable, queuing for scrape")
            WORK_QUEUE.put({"name": target["name"], "url": target["url"], 
                           "html": body, "cat": target["cat"]})
        else:
            print(f"  ❌ {target['name']} - unreachable")
        time.sleep(0.3)
    
    # Signal done
    WORK_QUEUE.put(None)

def scraper_thread():
    """Consumer: takes working sources from queue and extracts jobs."""
    while True:
        item = WORK_QUEUE.get()
        if item is None:
            WORK_QUEUE.put(None)  # Pass signal to other consumers
            break
        
        print(f"  🤖 Scraping {item['name']}...", end=" ", flush=True)
        jobs = llm_extract(item["name"], item["url"], item["html"], item["cat"])
        
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
                if not j.get("url") or j["url"] == item["url"]:
                    j["apply_url"] = item["url"]
                else:
                    j["apply_url"] = j.get("url", item["url"])
            
            with LOCK:
                RESULTS.extend(jobs)
            print(f"✅ {len(jobs)} jobs")
        else:
            print("📭 no jobs found")
        
        time.sleep(0.5)

def merge_results():
    """Merge scraped jobs into main database."""
    if not RESULTS:
        print("📭 No jobs to merge")
        return
    
    if not os.path.exists(DATA_FILE):
        print(f"⚠ Data file not found: {DATA_FILE}")
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
        print(f"\n📭 No new unique jobs (already in DB)")

def main():
    print("=" * 50)
    print("🚀 Two-Stage Pipeline")
    print(f"   Checker: HTTP (fast, no LLM needed)")
    print(f"   Scraper: {MODEL}")
    print(f"   Sources: {len(TARGETS)}")
    print("=" * 50)
    print()
    
    # Start threads
    c = threading.Thread(target=checker_thread)
    s = threading.Thread(target=scraper_thread)
    
    print("▶️  Starting checker + scraper in parallel...")
    c.start()
    s.start()
    
    c.join()
    s.join()
    
    print(f"\n📊 Results: {len(RESULTS)} jobs extracted")
    merge_results()
    
    # Save raw results
    with open(OUTPUT, "w") as f:
        json.dump({"results": RESULTS}, f, indent=2)
    print(f"💾 Raw output saved to {OUTPUT}")

if __name__ == "__main__":
    main()
