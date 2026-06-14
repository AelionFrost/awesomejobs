#!/usr/bin/env python3
"""SEO optimization script using Ollama LLM on Mac Mini."""
import json, os, subprocess, re, time
from datetime import datetime

PROJECT = "/Volumes/Data/Deepseek_Awesome"
OUTPUT = "/Volumes/DATA/Awesome_Jobs_WORK"
SITE_URL = "https://awesomejobs.online"
MODEL = "qwen2.5-coder:7b"

PAGES = {
    "/": {"title": "AwesomeJobs — Remote & Niche Career Board", "desc": "Find your next remote job from 8,000+ curated listings. Software engineering, design, marketing, translation, sales and more. Updated every 15 minutes.", "cat": "remote jobs"},
    "/remote-developer-jobs.html": {"title": "Remote Developer Jobs — Software Engineering", "desc": "", "cat": "developer"},
    "/remote-devops-jobs.html": {"title": "Remote DevOps Jobs — Cloud & Infrastructure", "desc": "", "cat": "devops"},
    "/remote-data-jobs.html": {"title": "Remote Data Jobs — Data Science & Analytics", "desc": "", "cat": "data"},
    "/remote-design-jobs.html": {"title": "Remote Design Jobs — UI/UX & Creative", "desc": "", "cat": "design"},
    "/remote-translation-jobs.html": {"title": "Remote Translation Jobs — Localization & Interpreting", "desc": "", "cat": "translation"},
    "/remote-writing-jobs.html": {"title": "Remote Writing Jobs — Content & Copywriting", "desc": "", "cat": "writing"},
    "/remote-marketing-jobs.html": {"title": "Remote Marketing Jobs — Growth & SEO", "desc": "", "cat": "marketing"},
    "/remote-sales-jobs.html": {"title": "Remote Sales Jobs — B2B & Account Management", "desc": "", "cat": "sales"},
    "/remote-support-jobs.html": {"title": "Remote Support Jobs — Customer Success & Help Desk", "desc": "", "cat": "support"},
    "/remote-finance-jobs.html": {"title": "Remote Finance Jobs — Accounting & Financial Analysis", "desc": "", "cat": "finance"},
    "/remote-hr-jobs.html": {"title": "Remote HR Jobs — Talent Acquisition & People Ops", "desc": "", "cat": "hr"},
    "/remote-qa-jobs.html": {"title": "Remote QA Jobs — Testing & Quality Assurance", "desc": "", "cat": "qa"},
}

def call_llm(prompt, max_tokens=120):
    """Call Ollama and return response text."""
    try:
        r = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt.encode(),
            capture_output=True,
            timeout=60,
        )
        text = r.stdout.decode().strip()
        # Clean up thinking tags if any
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        return text
    except Exception as e:
        print(f"  ⚠ LLM error: {e}")
        return ""

def generate_meta_descriptions():
    """Generate SEO meta descriptions using LLM."""
    print("📝 Generating meta descriptions with Ollama...")
    
    for path, info in PAGES.items():
        if info["desc"]:
            print(f"  ✅ {info['title']} — already has description")
            continue
        
        cat = info["cat"]
        prompt = f"""Generate a 150-160 character SEO meta description for a remote jobs page.
Category: {cat} remote jobs
Site: AwesomeJobs.online (8,000+ curated remote job listings)

Write ONE meta description that naturally includes "remote {cat} jobs" and sounds compelling.
Keep it under 160 characters. No quotes. Just the description:"""
        
        print(f"  🔄 Generating for: {info['title']}...", end=" ")
        desc = call_llm(prompt)
        if desc and len(desc) > 30:
            # Truncate to 160 chars
            info["desc"] = desc[:160].rsplit(' ', 1)[0] if len(desc) > 160 else desc
            print(f"✅ ({len(info['desc'])} chars)")
        else:
            # Fallback descriptions
            fallbacks = {
                "developer": "Browse 2,000+ remote developer jobs. Software engineering, frontend, backend, full-stack positions at top companies. Updated hourly.",
                "devops": "Find remote DevOps jobs. Cloud infrastructure, SRE, platform engineering roles at leading tech companies. New listings daily.",
                "data": "Discover remote data jobs. Data science, analytics, machine learning, data engineering positions. Curated from 50+ sources.",
                "design": "Explore remote design jobs. UI/UX, graphic design, product design roles at innovative companies. Updated every 15 minutes.",
                "translation": "Find remote translation jobs. Localization, interpreting, transcription positions. Connect with global language service providers.",
                "writing": "Browse remote writing jobs. Content writing, copywriting, technical writing, editing positions. New opportunities daily.",
                "marketing": "Discover remote marketing jobs. SEO, growth marketing, social media, brand management roles. Curated listings.",
                "sales": "Find remote sales jobs. B2B sales, account management, SaaS sales positions at growing companies. Updated hourly.",
                "support": "Explore remote support jobs. Customer success, help desk, technical support roles. Work from anywhere.",
                "finance": "Browse remote finance jobs. Accounting, financial analysis, bookkeeping positions. Remote opportunities worldwide.",
                "hr": "Find remote HR jobs. Talent acquisition, people operations, HR management roles at distributed companies.",
                "qa": "Discover remote QA jobs. Software testing, quality assurance, test automation positions. Updated daily.",
            }
            info["desc"] = fallbacks.get(cat, f"Browse remote {cat} jobs on AwesomeJobs. Curated listings updated hourly. Find your next remote role today.")
            print(f"✅ fallback")
        
        time.sleep(0.5)  # Rate limit

def update_html_files():
    """Add comprehensive SEO tags to all HTML files."""
    print("\n📄 Updating HTML files with SEO tags...")
    
    for path, info in PAGES.items():
        filename = path.lstrip("/") or "index.html"
        filepath = os.path.join(PROJECT, filename)
        
        if not os.path.exists(filepath):
            print(f"  ⚠ {filename} not found, skipping")
            continue
        
        with open(filepath, encoding="utf-8") as f:
            html = f.read()
        
        # Build meta tags to insert after <title>
        meta_tags = f"""<meta name="description" content="{info['desc']}">
<meta name="keywords" content="{info['cat']} remote jobs, remote work, work from home, {info['cat']} careers, remote {info['cat']} positions">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE_URL}{path}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}{path}">
<meta property="og:title" content="{info['title']}">
<meta property="og:description" content="{info['desc'][:200]}">
<meta property="og:image" content="{SITE_URL}/assets/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{info['title']}">
<meta name="twitter:description" content="{info['desc'][:200]}">"""
        
        # Replace existing meta description or insert after title
        old_meta = f'<meta name="description" content="{info["title"]}">'
        
        # Remove old meta tags if they exist
        html = re.sub(
            r'<meta name="description" content="[^"]*">',
            '',
            html
        )
        html = re.sub(
            r'<meta name="keywords" content="[^"]*">',
            '',
            html
        )
        html = re.sub(
            r'<meta name="robots" content="[^"]*">',
            '',
            html
        )
        html = re.sub(
            r'<link rel="canonical"[^>]*>',
            '',
            html
        )
        
        # Insert meta tags after <title>
        html = html.replace(
            "</title>",
            f"</title>\n{meta_tags}"
        )
        
        # Add JSON-LD Organization schema on index page
        if path == "/":
            org_schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "AwesomeJobs",
  "url": "{SITE_URL}",
  "description": "Remote job board aggregating listings from 50+ sources.",
  "sameAs": [
    "https://x.com/_AwesomeJobs_",
    "https://www.instagram.com/awesome_jobs_/",
    "https://www.linkedin.com/in/awesomejobs"
  ]
}}
</script>"""
            html = html.replace("</head>", f"{org_schema}\n</head>")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"  ✅ {filename} — SEO tags added")

def generate_sitemap():
    """Generate XML sitemap."""
    print("\n🗺️  Generating sitemap.xml...")
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for path, info in PAGES.items():
        priority = "1.0" if path == "/" else "0.8"
        xml += f"""  <url>
    <loc>{SITE_URL}{path}</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>daily</changefreq>
    <priority>{priority}</priority>
  </url>\n"""
    
    xml += '</urlset>'
    
    with open(os.path.join(PROJECT, "sitemap.xml"), "w") as f:
        f.write(xml)
    print(f"  ✅ sitemap.xml created")

def generate_robots():
    """Generate robots.txt."""
    print("\n🤖 Generating robots.txt...")
    robots = f"""User-agent: *
Allow: /
Disallow: /data/
Disallow: /assets/

Sitemap: {SITE_URL}/sitemap.xml

# Crawl delay for polite crawling
Crawl-delay: 10
"""
    with open(os.path.join(PROJECT, "robots.txt"), "w") as f:
        f.write(robots)
    print("  ✅ robots.txt created")

def deploy_seo():
    """Copy SEO files to working directory."""
    print("\n🚀 Deploying SEO files...")
    import shutil
    
    # Copy HTML files
    for path in PAGES.keys():
        filename = path.lstrip("/") or "index.html"
        src = os.path.join(PROJECT, filename)
        dst = os.path.join(OUTPUT, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  ✅ {filename}")
    
    # Copy sitemap and robots
    for f in ["sitemap.xml", "robots.txt"]:
        src = os.path.join(PROJECT, f)
        dst = os.path.join(OUTPUT, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  ✅ {f}")

if __name__ == "__main__":
    generate_meta_descriptions()
    update_html_files()
    generate_sitemap()
    generate_robots()
    deploy_seo()
    print("\n✨ SEO optimization complete!")
