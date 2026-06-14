#!/usr/bin/env python3
"""
LLM Source Discovery — uses Ollama on Mac Mini to find NEW remote job websites,
then adds them to the Debian pipeline's manifest for scraping.
"""
import json, os, subprocess, re, time, urllib.request
from datetime import datetime

MODEL = "qwen2.5-coder:7b"
MANIFEST = "/Volumes/Data/Deepseek_Awesome/scripts/source_manifest.json"
OUTPUT = "/tmp/new_sources.json"
DISCOVERED_LOG = "/Volumes/Data/Deepseek_Awesome/scripts/discovered_sources.json"

# Categories we want to find sources for
CATEGORIES = [
    "software development", "devops", "data science", "design",
    "translation", "writing", "marketing", "sales", "customer support",
    "finance", "hr", "qa"
]

def llm_discover(category):
    """Ask Ollama to find job board websites for a category."""
    prompt = f"""List REAL websites that post remote job listings for {category} roles.
Only include sites that:
1. Are actively maintained (not dead)
2. Have a public API or HTML listings that can be scraped
3. Are NOT already on this list: Remotive, RemoteOK, WeWorkRemotely, Arbeitnow, Working Nomads, Greenhouse, Lever, ProZ, LinkedIn, Indeed, FlexJobs, Upwork, Fiverr

For each site, provide:
- name: short identifier
- url: homepage URL
- type: "api" if they have a public JSON API, "html" if needs scraping
- notes: brief description

Return ONLY a JSON array. Example format:
[{{"name": "example", "url": "https://example.com/jobs", "type": "html", "notes": "Remote job board for {category}"}}]

At least 3 sites for {category}:"""

    try:
        r = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt.encode(),
            capture_output=True,
            timeout=60
        )
        text = r.stdout.decode().strip()
        # Clean up JSON - remove control chars and markdown
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        text = re.sub(r'[\x00-\x1f]', '', text)  # Remove control chars
        text = re.sub(r'```json\s*', '', text)  # Remove markdown json fences
        text = re.sub(r'```\s*', '', text)
        # Extract JSON array
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            sources = json.loads(match.group())
            if isinstance(sources, list):
                return sources
        return []
    except Exception as e:
        print(f"    ⚠ LLM error: {e}")
        return []

def verify_source(url, timeout=8):
    """Check if a source is reachable."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200, len(r.read())
    except:
        return False, 0

def load_existing():
    """Load already-known sources from manifest."""
    with open(MANIFEST) as f:
        m = json.load(f)
    known = set()
    for group in ["direct_api_or_feed", "llm_extract_candidates"]:
        for s in m.get(group, []):
            known.add(s["name"])
    # Also load discovered log
    if os.path.exists(DISCOVERED_LOG):
        try:
            with open(DISCOVERED_LOG) as f:
                old = json.load(f)
                for s in old:
                    known.add(s["name"])
        except:
            pass
    return known, m

def main():
    known, manifest = load_existing()
    all_new = []
    
    print(f"🔍 LLM Source Discovery — searching for new job sites across {len(CATEGORIES)} categories")
    print(f"   Already known: {len(known)} sources")
    print()
    
    for cat in CATEGORIES:
        print(f"  📡 {cat}...", end=" ", flush=True)
        sources = llm_discover(cat)
        
        if not sources:
            print("❌ no suggestions")
            continue
        
        print(f"found {len(sources)} candidates")
        
        for src in sources:
            name = src.get("name", "").lower().replace(" ", "-")
            url = src.get("url", "")
            
            if not name or not url:
                continue
            if name in known:
                continue
            
            print(f"    🔍 {name} ({url})...", end=" ", flush=True)
            ok, size = verify_source(url)
            
            if ok and size > 1000:
                src["verified"] = True
                src["discovered_at"] = datetime.now().isoformat()
                src["status"] = "pending_review"
                all_new.append(src)
                known.add(name)
                print(f"✅ ({size//1000}KB)")
            else:
                print(f"❌ unreachable or too small")
            
            time.sleep(0.5)
    
    # Save results
    if all_new:
        # Save to discovered log
        old_discovered = []
        if os.path.exists(DISCOVERED_LOG):
            with open(DISCOVERED_LOG) as f:
                old_discovered = json.load(f)
        
        all_discovered = old_discovered + all_new
        with open(DISCOVERED_LOG, "w") as f:
            json.dump(all_discovered, f, indent=2)
        
        # Also save to /tmp for the Debian pipeline to pick up
        with open(OUTPUT, "w") as f:
            json.dump({"discovered_at": datetime.now().isoformat(), "sources": all_new}, f, indent=2)
        
        print(f"\n✅ Found {len(all_new)} NEW discoverable sources!")
        print("   Saved to:")
        print(f"   - {DISCOVERED_LOG}")
        print(f"   - {OUTPUT}")
        print()
        print("   New sources:")
        for s in all_new:
            print(f"   • {s['name']:30s} | {s['url']:50s} | {s.get('type','?')}")
    else:
        print("\n📭 No new sources discovered this run")
    
    # Unload model to free RAM
    subprocess.run(["ollama", "stop", MODEL], capture_output=True, timeout=5)
    subprocess.run(["pkill", "-f", "llama-server"], capture_output=True, timeout=3)
    print("🧹 RAM freed")

if __name__ == "__main__":
    main()
