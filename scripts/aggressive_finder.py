#!/usr/bin/env python3
"""
Aggressive source finder — uses qwen to brainstorm remote job sites,
validates them quickly, and adds working ones to the pipeline.
"""
import json, urllib.request, subprocess, os, time, re

MODEL = "qwen2.5-coder:7b"
MANIFEST = "/Volumes/Data/Deepseek_Awesome/scripts/source_manifest.json"

def llm_ask(prompt, max_tokens=4000):
    try:
        r = subprocess.run(["ollama", "run", MODEL], input=prompt.encode(),
                          capture_output=True, timeout=45)
        return r.stdout.decode().strip()
    except:
        return ""

def quick_test(url, timeout=5):
    """Test if a URL responds."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, len(resp.read())
    except:
        return False, 0

# Phase 1: Brainstorm remote job sources
print("🧠 Phase 1: Brainstorming new sources...")
prompt = """List 20 websites that post REMOTE JOB LISTINGS and have either:
1. A free public API returning JSON
2. A simple HTML page that can be scraped (no JavaScript rendering)

Do NOT include: Remotive, RemoteOK, WeWorkRemotely, Arbeitnow, Working Nomads, LinkedIn, Indeed, Glassdoor, ZipRecruiter, FlexJobs, Upwork, Fiverr, Greenhouse, Lever.

For each, give: name, url (homepage or jobs page), and why it's a good source.
Format: simple list, no markdown."""

response = llm_ask(prompt)
print("   Suggestions from LLM:")
print(response[:500])

# Phase 2: Try known remote job APIs directly
print("\n🔍 Phase 2: Testing known APIs...")
known_apis = [
    {"name": "findwork", "url": "https://findwork.dev/api/jobs/"},
    {"name": "jobicy", "url": "https://jobicy.com/api/v2/remote-jobs?count=50&format=json"},
    {"name": "remotewoman", "url": "https://remotewoman.com/api/jobs"},
    {"name": "nomadlist", "url": "https://nomadlist.com/api/jobs"},
    {"name": "freshremote", "url": "https://www.freshremote.work/api/jobs"},
    {"name": "himalayas", "url": "https://himalayas.app/api/jobs"},
    {"name": "nodesk", "url": "https://nodesk.co/remote-jobs/feed.json"},
    {"name": "remoteleaf", "url": "https://remoteleaf.com/api/jobs"},
]

for api in known_apis:
    print(f"  {api['name']}...", end=" ", flush=True)
    ok, size = quick_test(api["url"])
    if ok and size > 500:
        print(f"✅ ({size//1000}KB)")
        api["status"] = "working"
    else:
        print("❌")
        api["status"] = "dead"
    time.sleep(0.3)

# Phase 3: Try alternative Greenhouse company name formats
print("\n🏢 Phase 3: Testing more Greenhouse companies...")
# Companies that definitely use Greenhouse but might have different slugs
more_greenhouse = []
with open("/Volumes/Data/Deepseek_Awesome/data/jobs.json") as f:
    data = json.load(f)
    # Find companies in our data that might have Greenhouse boards
    companies = set(j.get("company", "").lower().strip() for j in data.get("jobs", []))
    for co in sorted(companies):
        if co in ["", "various", "various (proz)", "unknown"]:
            continue
        slug = re.sub(r'[^a-z0-9]', '-', co).strip('-')
        if slug and len(slug) > 2:
            more_greenhouse.append(slug)

# Test unique slugs
existing = set()
with open(MANIFEST) as f:
    m = json.load(f)
    existing = set(m["ats_boards"]["greenhouse"])

new_greenhouse = []
tested = set()
for slug in more_greenhouse[:200]:  # Test first 200
    if slug in existing or slug in tested:
        continue
    tested.add(slug)
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    ok, size = quick_test(url)
    if ok and size > 1000:
        new_greenhouse.append(slug)
        if len(new_greenhouse) % 20 == 0:
            print(f"  Found {len(new_greenhouse)} new so far...")

print(f"\n  ✅ Found {len(new_greenhouse)} new Greenhouse companies")

# Phase 4: Save results
if new_greenhouse:
    m["ats_boards"]["greenhouse"].extend(new_greenhouse)
    m["ats_boards"]["greenhouse"] = sorted(set(m["ats_boards"]["greenhouse"]))
    with open(MANIFEST, "w") as f:
        json.dump(m, f, indent=2)
    print(f"  Saved! Total Greenhouse: {len(m['ats_boards']['greenhouse'])}")

# Also update Debian
working_apis = [a for a in known_apis if a.get("status") == "working"]
if working_apis:
    print(f"\n✅ Working APIs: {len(working_apis)}")
    for a in working_apis:
        print(f"  {a['name']}: {a['url']}")

# Save results summary
results = {
    "greenhouse_new": len(new_greenhouse),
    "greenhouse_total": len(m["ats_boards"]["greenhouse"]),
    "apis_working": len(working_apis),
    "apis": working_apis,
}
with open("/tmp/source_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n📊 Results saved to /tmp/source_results.json")
