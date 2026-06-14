#!/usr/bin/env python3
"""
LLM Job Scout — uses Ollama on Mac Mini to find & extract remote job listings
from the web, then feeds them into the Debian pipeline.
"""
import json, os, subprocess, re, time, urllib.request
from datetime import datetime, timezone

MODEL = "qwen2.5-coder:7b"
DATA_FILE = "/Volumes/DATA/Awesome_Jobs_WORK/data/jobs.json"
OUTPUT_FILE = "/tmp/llm_scouted_jobs.json"
KNOWN_SOURCES = "/Volumes/Data/Deepseek_Awesome/scripts/source_manifest.json"

# New sources to try — career pages with remote job listings
TARGETS = [
    # Translation / Writing
    {"name": "gotranslate", "url": "https://www.gotranslate.com/careers", "cat": "translation"},
    {"name": "bureau-works", "url": "https://www.bureauworks.com/careers", "cat": "translation"},
    {"name": "euro-lang", "url": "https://www.euro-lang.com/careers", "cat": "translation"},
    {"name": "tomedes", "url": "https://www.tomedes.com/careers", "cat": "translation"},
    {"name": "languagewire", "url": "https://www.languagewire.com/en/careers", "cat": "translation"},
    # Data / AI
    {"name": "scale-ai", "url": "https://scale.com/careers", "cat": "data"},
    {"name": "surge-ai", "url": "https://www.surgehq.ai/careers", "cat": "data"},
    {"name": "labelbox", "url": "https://labelbox.com/careers", "cat": "data"},
    # Remote-first companies
    {"name": "automattic", "url": "https://automattic.com/work-with-us/", "cat": "dev"},
    {"name": "buffer", "url": "https://buffer.com/careers", "cat": "marketing"},
    {"name": "doist", "url": "https://doist.com/careers", "cat": "dev"},
    {"name": "toggl", "url": "https://toggl.com/jobs/", "cat": "dev"},
    {"name": "basecamp", "url": "https://basecamp.com/about/jobs", "cat": "dev"},
    {"name": "wistia", "url": "https://wistia.com/about/jobs", "cat": "marketing"},
    {"name": "help-scout", "url": "https://helpscout.com/careers/", "cat": "support"},
    {"name": "baremetrics", "url": "https://baremetrics.com/about", "cat": "dev"},
]

def quick_check(url, timeout=5):
    """Quick HEAD/GET to see if source is reachable."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="replace")[:5000]
            return True, body
    except:
        return False, ""

def llm_extract(url, html_snippet, category):
    """Ask Ollama to find job listings in HTML."""
    snippet = html_snippet[:3000]
    prompt = f"""Extract remote job listings from this HTML career page.
URL: {url}
Category: {category} remote jobs

Look for job titles, locations (must include "remote"), and apply links.
Return ONLY a JSON array of objects with fields: title, location, url
If no remote jobs found, return empty array [].
Do NOT wrap in markdown. Just raw JSON array.

HTML snippet:
{snippet}"""
    
    try:
        r = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt.encode(),
            capture_output=True,
            timeout=30
        )
        text = r.stdout.decode().strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        # Extract JSON array
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            jobs = json.loads(match.group())
            if isinstance(jobs, list):
                return jobs
        return []
    except:
        return []

def save_results(all_jobs):
    """Save scouted jobs for the pipeline to pick up."""
    now = datetime.now(timezone.utc).isoformat()
    output = {
        "meta": {"generated_at": now, "total": len(all_jobs), "source": "llm_scout"},
        "jobs": all_jobs
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✅ Saved {len(all_jobs)} scouted jobs to {OUTPUT_FILE}")

def merge_with_main(scouted):
    """Merge scouted jobs into the main data file."""
    if not os.path.exists(DATA_FILE):
        print("⚠ Main data file not found")
        return
    
    with open(DATA_FILE) as f:
        main_data = json.load(f)
    
    existing = set(
        (j.get("title", "").lower().strip(), j.get("company", "").lower().strip())
        for j in main_data.get("jobs", [])
    )
    
    new_jobs = []
    for j in scouted:
        key = (j.get("title", "").lower().strip(), j.get("company", "").lower().strip())
        if key not in existing and j.get("title"):
            new_jobs.append(j)
            existing.add(key)
    
    if new_jobs:
        main_data["jobs"].extend(new_jobs)
        main_data["meta"]["total_jobs"] = len(main_data["jobs"])
        main_data["meta"]["generated_at"] = datetime.now(timezone.utc).isoformat()
        
        with open(DATA_FILE, "w") as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Merged {len(new_jobs)} new jobs into main DB (total: {len(main_data['jobs'])})")
    else:
        print("📭 No new unique jobs found")

def main():
    all_jobs = []
    
    print(f"🔍 LLM Job Scout — {len(TARGETS)} sources")
    print(f"   Model: {MODEL}")
    print()
    
    for target in TARGETS:
        name = target["name"]
        url = target["url"]
        cat = target["cat"]
        
        print(f"  Checking {name}...", end=" ", flush=True)
        ok, html = quick_check(url)
        
        if not ok:
            print("❌ unreachable")
            continue
        
        print("✅ parsing...", end=" ", flush=True)
        jobs = llm_extract(url, html, cat)
        
        if jobs:
            for j in jobs:
                j["source"] = name
                j["category"] = cat
                j["date_posted"] = datetime.now(timezone.utc).isoformat()
                j["apply_url"] = j.get("url", url)
                if not j.get("company"):
                    j["company"] = name.replace("-", " ").title()
                if not j.get("location"):
                    j["location"] = "Remote"
                all_jobs.append(j)
            print(f"✅ {len(jobs)} jobs")
        else:
            print("📭 no listings found")
        
        time.sleep(1)  # Rate limit
    
    if all_jobs:
        save_results(all_jobs)
        merge_with_main(all_jobs)
    else:
        print("\n📭 No jobs found from any source")

if __name__ == "__main__":
    main()
