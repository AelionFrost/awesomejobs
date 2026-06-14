#!/usr/bin/env python3
"""Generate SEO blog pages for awesomejobs.online using Ollama."""
import subprocess, os, json, re, time

PROJECT = "/Volumes/Data/Deepseek_Awesome"
MODEL = "qwen2.5-coder:7b"

def llm(prompt):
    try:
        r = subprocess.run(["ollama", "run", MODEL], input=prompt.encode(), capture_output=True, timeout=120)
        text = r.stdout.decode().strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        return text
    except: return ""

def load_header():
    with open(os.path.join(PROJECT, "index.html")) as f:
        html = f.read()
    # Extract header and CSS
    header_start = html.index('<div class="hs-banner">')
    header_end = html.index('</header>') + len('</header>')
    head_end = html.index('</head>')
    css_start = html.index(':root{')
    css_end = html.index('/* ── FOOTER ── */')
    # Also get the inline theme script
    theme_script = html[html.index('<script>'):html.index('</script>')+len('</script>')]
    return {
        'header': html[header_start:header_end],
        'head_start': html[:head_end],
        'css': html[css_start:css_end],
        'theme_script': theme_script
    }

PAGES = [
    {
        "file": "blog-remote-developer-jobs.html",
        "title": "Top 10 Remote Developer Jobs in 2026",
        "desc": "Discover the highest-paying remote developer jobs in 2026. Software engineering, frontend, backend, and full-stack roles at top companies hiring remotely.",
        "slug": "remote-developer-jobs",
        "content_prompt": "Write a 500-word SEO article about the top 10 remote developer jobs in 2026. Include: trending languages (Python, JavaScript, Go), salary ranges ($100k-$250k), top companies hiring, and required skills. Use natural language, no marketing fluff."
    },
    {
        "file": "blog-land-remote-job.html",
        "title": "How to Land a Remote Job from Anywhere",
        "desc": "A practical guide to landing a remote job in 2026. Resume tips, interview prep, platforms to use, and strategies for standing out to global employers.",
        "slug": "land-remote-job",
        "content_prompt": "Write a 500-word practical guide on how to land a remote job. Cover: resume optimization for remote roles, best job platforms (LinkedIn, WeWorkRemotely, RemoteOK), interview tips for video interviews, and building a remote-work portfolio."
    },
    {
        "file": "blog-highest-paying-remote-jobs.html",
        "title": "Highest Paying Remote Jobs Right Now",
        "desc": "See which remote jobs pay the most in 2026. From software engineering to product management, find high-salary remote positions updated daily.",
        "slug": "highest-paying-remote-jobs",
        "content_prompt": "Write a 500-word article about the highest paying remote jobs in 2026. Include salary data: Software Engineer $150k-$300k, Product Manager $130k-$250k, DevOps $140k-$280k, Data Scientist $120k-$220k. Explain why these roles pay well remotely."
    },
    {
        "file": "blog-remote-work-tools.html",
        "title": "Remote Work Guide: Tools & Tips for Success",
        "desc": "Essential remote work tools and productivity tips. From communication to project management, set yourself up for remote work success.",
        "slug": "remote-work-tools",
        "content_prompt": "Write a 500-word guide about essential remote work tools. Cover: communication (Slack, Zoom, Discord), project management (Notion, Linear, Asana), time tracking (Toggl), and productivity tips for working from home."
    },
    {
        "file": "blog-best-remote-companies.html",
        "title": "Best Companies Hiring Remotely in 2026",
        "desc": "Top companies hiring remote workers in 2026. From startups to FAANG, find employers that embrace remote-first culture and offer competitive compensation.",
        "slug": "best-remote-companies",
        "content_prompt": "Write a 500-word article about the best companies hiring remotely in 2026. Include: GitLab (remote-first), Automattic, Zapier, Buffer, Toggl, and tech companies with strong remote policies like Shopify, Airbnb, and Spotify."
    }
]

def make_page(info, header_data, content):
    css = header_data['css']
    header = header_data['header']
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{header_data['theme_script']}
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{info['title']} — AwesomeJobs</title>
<meta name="description" content="{info['desc']}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://awesomejobs.online/{info['file']}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://awesomejobs.online/{info['file']}">
<meta property="og:title" content="{info['title']}">
<meta property="og:description" content="{info['desc']}">
<style>
{css}
.blog-content{{max-width:800px;margin:0 auto;padding:0 24px 60px}}
.blog-content h1{{font-size:2.4rem;font-weight:900;letter-spacing:-.03em;color:var(--text);line-height:1.1;margin-bottom:8px}}
.blog-content .meta{{font-size:.85rem;color:var(--muted);margin-bottom:32px}}
.blog-content h2{{font-size:1.5rem;font-weight:800;color:var(--text);margin:32px 0 12px;letter-spacing:-.02em}}
.blog-content p{{font-size:1rem;color:var(--text2);line-height:1.7;margin-bottom:16px}}
.blog-content ul{{padding-left:20px;margin-bottom:16px;color:var(--text2);line-height:1.7}}
.blog-content li{{margin-bottom:6px}}
.blog-back{{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;background:var(--accent-glow);color:var(--accent);font-size:.85rem;font-weight:700;text-decoration:none;margin-bottom:24px;transition:all .12s}}
.blog-back:hover{{background:var(--accent);color:#fff}}
@media(max-width:768px){{.blog-content h1{{font-size:1.8rem}}}}
</style>
</head>
<body>
{header}
<main class="blog-content">
  <a class="blog-back" href="/">← Back to jobs</a>
  <article>
    <h1>{info['title']}</h1>
    <p class="meta">Published June 14, 2026 · AwesomeJobs Editorial Team</p>
    {content}
  </article>
</main>
<footer class="site-footer" style="margin-top:60px">
  <div class="footer-inner">
    <p>© 2026 <a href="/">AwesomeJobs.online</a> — Remote job board.</p>
    <p><a href="/">Jobs</a> · <a href="/about.html">About</a> · <a href="/sitemap.xml">Sitemap</a></p>
  </div>
</footer>
</body>
</html>'''

for page in PAGES:
    print(f"📝 Generating: {page['title']}...", end=" ")
    content = llm(page['content_prompt'])
    if not content or len(content) < 100:
        # Fallback content
        content = f"<p>Discover the best {page['slug'].replace('-', ' ')} opportunities on AwesomeJobs. We aggregate listings from 50+ sources to bring you the most comprehensive collection of remote jobs. Browse thousands of positions updated every 15 minutes.</p><p>Our platform curates jobs from top companies including Greenhouse and Lever partners, ensuring you see quality opportunities from verified employers. Whether you're a seasoned professional or just starting your career, AwesomeJobs helps you find the perfect remote role.</p><p>Start your search today and join thousands of professionals who found their dream remote job through our platform.</p>"
    # Wrap in proper HTML
    content_html = f"<div class='blog-body'>{content}</div>"
    # Clean up - convert plain text paragraphs to <p> tags
    paragraphs = content.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        if p.startswith('#') or p.startswith('<'):
            html_paragraphs.append(p)
        else:
            html_paragraphs.append(f'<p>{p}</p>')
    content_html = '\n'.join(html_paragraphs)
    
    header_data = load_header()
    page_html = make_page(page, header_data, content_html)
    
    with open(os.path.join(PROJECT, page['file']), 'w') as f:
        f.write(page_html)
    print(f"✅ saved")
    time.sleep(1)

print("\n✨ All 5 blog pages created!")
