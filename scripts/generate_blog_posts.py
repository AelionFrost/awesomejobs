#!/usr/bin/env python3
"""Generate more SEO blog posts using qwen2.5-coder:7b."""
import subprocess, os, re, json
from datetime import datetime

DIR = "/Volumes/Data/Deepseek_Awesome"
MODEL = "qwen2.5-coder:7b"

topics = [
    ("remote-sales-jobs-guide", "Remote Sales Jobs: Complete Guide to 6-Figure Earnings", "sales"),
    ("remote-customer-support", "Best Remote Customer Support Jobs — Entry Level to Manager", "support"),
    ("remote-freelance-guide", "Remote Freelance Jobs: How to Start Making Money Online", "freelance"),
    ("remote-data-entry", "Remote Data Entry Jobs That Pay Well in 2026", "data"),
    ("remote-project-manager", "Remote Project Manager Jobs: Salary, Skills, and Where to Apply", "management"),
    ("remote-jobs-no-experience", "Remote Jobs With No Experience Needed — Start Today", "entry-level"),
    ("remote-part-time", "Best Part-Time Remote Jobs for Extra Income", "part-time"),
    ("remote-accounting", "Remote Accounting Jobs: CPA to Bookkeeping Roles", "finance"),
    ("remote-recruiter", "Remote Recruiter and HR Jobs — Full Guide", "hr"),
    ("remote-gaming-jobs", "Remote Gaming Industry Jobs: QA, Design, Community", "gaming"),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<script>
(function(){try{{var t=localStorage.getItem('aj-theme');if(!t) t=window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}})();
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — AwesomeJobs</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://awesomejobs.online/blog-{slug}.html">
<meta property="og:type" content="article">
<meta property="og:url" content="https://awesomejobs.online/blog-{slug}.html">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<style>
:root{{--bg:#f8fafc;--bg-alt:#f1f5f9;--surface:#fff;--text:#0f172a;--text2:#475569;--muted:#94a3b8;--border:#e2e8f0;--accent:#2563eb;--accent-h:#1d4ed8;--accent-glow:rgba(37,99,235,.08);--green:#16a34a;--header-bg:rgba(255,255,255,.85);--shadow:0 1px 2px rgba(0,0,0,.04);--radius:10px;--font:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}
[data-theme="dark"]{{--bg:#0f172a;--bg-alt:#1e293b;--surface:#1e293b;--text:#e2e8f0;--text2:#94a3b8;--muted:#64748b;--border:#334155;--accent:#3b82f6;--accent-h:#60a5fa;--accent-glow:rgba(59,130,246,.12);--green:#22c55e;--header-bg:rgba(15,23,42,.92);--shadow:0 1px 2px rgba(0,0,0,.2)}}
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}}
.article-hero{{background:linear-gradient(135deg,#0a1628,#0f2647,#1a365d);color:#fff;padding:48px 24px;text-align:center}}
.article-hero h1{{font-size:clamp(1.8rem,4vw,2.8rem);font-weight:900;letter-spacing:-.03em;margin-bottom:12px;line-height:1.05}}
.article-hero p{{font-size:1rem;color:rgba(255,255,255,.7);max-width:600px;margin:0 auto}}
.article-body{{max-width:800px;margin:0 auto;padding:32px 24px 48px}}
.article-body h2{{font-size:1.6rem;font-weight:900;letter-spacing:-.02em;color:var(--text);margin:36px 0 12px}}
.article-body h3{{font-size:1.2rem;font-weight:800;color:var(--text);margin:24px 0 8px}}
.article-body p{{font-size:1rem;color:var(--text2);line-height:1.7;margin-bottom:14px}}
.article-body ul{{padding-left:20px;margin-bottom:16px;color:var(--text2);line-height:1.7}}
.article-body li{{margin-bottom:6px}}
.article-body a{{color:var(--accent);font-weight:600}}
.callout{{border-radius:var(--radius);padding:20px;margin:20px 0;background:var(--accent-glow);border-left:4px solid var(--accent)}}
.callout p{{margin:0}}
.cta-btn{{display:inline-flex;align-items:center;gap:8px;padding:14px 28px;border-radius:10px;background:var(--accent);color:#fff;font-size:1rem;font-weight:800;text-decoration:none;margin:20px auto;transition:background .12s}}
.cta-btn:hover{{background:var(--accent-h)}}
.site-footer{{border-top:1px solid var(--border);background:var(--bg-alt);margin-top:40px}}
.footer-inner{{max-width:1400px;margin:0 auto;padding:24px;text-align:center}}
.footer-inner p{{font-size:.65rem;color:var(--muted);margin-bottom:4px}}
.footer-inner a{{color:var(--accent);text-decoration:none}}
@media(max-width:768px){{.article-hero{{padding:32px 18px}}.article-body{{padding:24px 16px 40px}}.article-body h2{{font-size:1.3rem}}}}
</style>
</head>
<body>
<section class="article-hero">
  <h1>{title}</h1>
  <p>{hero_desc}</p>
</section>
<main class="article-body">
{content}

  <div class="callout">
    <p><strong>🔍 Browse real remote jobs now</strong> — <a href="https://awesomejobs.online/" style="color:var(--accent)">AwesomeJobs</a> has <strong>11,000+ live listings</strong> updated every 15 minutes.</p>
  </div>
  <div style="text-align:center">
    <a class="cta-btn" href="https://awesomejobs.online/">Browse All Remote Jobs →</a>
  </div>
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <p>© 2026 <a href="/">AwesomeJobs.online</a> — Remote job board.</p>
    <p><a href="/">Jobs</a> · <a href="/about.html">About</a> · <a href="/sitemap.html">Sitemap</a> · <a href="/blog-remote-developer-jobs.html">Dev Guide</a> · <a href="/blog-land-remote-job.html">Remote Work Guide</a></p>
  </div>
</footer>
</body>
</html>"""

for slug, title, topic in topics:
    fname = f"blog-{slug}.html"
    fpath = os.path.join(DIR, fname)
    if os.path.exists(fpath):
        print(f"⏭️  {fname} already exists")
        continue
    
    print(f"\n📝 Generating {fname}...")
    
    prompt = f"""Write a complete SEO-optimized blog article about: {title}

The article should be 400-600 words, well-structured with h2 and h3 headings, and written in a helpful, informative tone. Include practical tips and specific examples.

Return ONLY the article HTML body content (what goes between <h2> and </h2> or <p> tags). No wrapper, no html/head/body tags. Just the content inside <main> section. Use proper HTML formatting.

The article should NOT include any CTA buttons or callout boxes - those will be added separately. Just pure content with headers and paragraphs."""
    
    try:
        r = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt.encode(),
            capture_output=True, timeout=120
        )
        content = r.stdout.decode().strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        
        # Generate description
        desc = f"{title}. Find remote {topic} jobs on AwesomeJobs with 11,000+ curated listings updated every 15 minutes."
        hero_desc = f"Your complete guide to {title.lower()} — salaries, skills, and where to find the best remote opportunities."
        
        html = TEMPLATE.format(slug=slug, title=title, desc=desc, hero_desc=hero_desc, content=content)
        
        with open(fpath, "w") as f:
            f.write(html)
        print(f"✅ {fname} ({len(content)} chars)")
    except Exception as e:
        print(f"❌ {fname}: {e}")

# Unload model
subprocess.run(["ollama", "stop", MODEL], capture_output=True)
subprocess.run(["pkill", "-f", "llama-server"], capture_output=True)
print("\nDone! Models unloaded.")
