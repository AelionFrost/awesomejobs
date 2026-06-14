#!/usr/bin/env python3
"""Unified monitor - shows both Mac Mini and Debian status."""
import json, subprocess, os
from datetime import datetime

OUTPUT = "/Volumes/Data/Deepseek_Awesome/monitor.html"

def ssh(cmd, timeout=8):
    try:
        r = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
             "aelion@10.10.10.2", cmd],
            capture_output=True, timeout=timeout, text=True
        )
        return r.stdout.strip()
    except:
        return ""

def local(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=5, text=True, shell=True)
        return r.stdout.strip()
    except:
        return ""

# ── Collect Mac Mini data ──
mac_ram = local("ps aux | grep 'llama-server' | grep -v grep | awk '{s+=$4} END {print int(s)}'") or "0"
mac_ollama_status = "🟢 Running" if int(mac_ram) > 0 else "⚪ Idle"
mac_models = local("ps aux | grep 'llama-server' | grep -v grep | awk '{printf \"%s (%s%%)\\n\", $11, $4}'") or "None"
mac_hermes = local("ps aux | grep 'hermes.*dashboard' | grep -v grep | wc -l")
mac_brave = local("ps aux | grep 'Brave Browser' | grep -v grep | wc -l")

# ── Collect Debian data ──
debian_jobs = ssh("python3 -c 'import json;d=json.load(open(\"/home/aelion/awesomejobs/data/jobs.json\"));print(len(d.get(\"jobs\",[])))'")
debian_pipeline = ssh("ps aux | grep -c 'safe_pipeline\\|scraper_fast'")
debian_running = int(debian_pipeline) > 1 if debian_pipeline else False
debian_mem = ssh("free -h | grep Mem | awk '{printf \"%s/%s\", $3, $2}'") or "?"
debian_ollama = ssh("ps aux | grep ollama | grep -v grep | wc -l")
debian_last_log = ssh("tail -20 /home/aelion/awesomejobs/logs/pipeline.log 2>/dev/null") or "No log"
debian_cron = ssh("crontab -l 2>/dev/null") or "No cron"
debian_sources = ssh("""python3 -c '
import json; from collections import Counter
d=json.load(open(\"/home/aelion/awesomejobs/data/jobs.json\"))
c=Counter(j.get(\"source\",\"?\") for j in d.get(\"jobs\",[]))
for s,n in c.most_common():
    print(f\"{s}|{n}\")
' 2>/dev/null""")

# Parse sources
source_rows = ""
for line in debian_sources.split("\n"):
    if "|" in line:
        s, n = line.split("|", 1)
        pct = min(100, int(n) // 100) if n.isdigit() else 0
        source_rows += f"""
          <tr><td>{s}</td><td><div class="bar-bg"><div class="bar" style="width:{pct}%"></div></div></td><td class="num">{n}</td></tr>"""

# Color log
def color_log(text):
    lines = []
    for line in text.split("\n"):
        if "✅" in line or "pipeline done" in line.lower() or "validated" in line.lower():
            lines.append(f'<span class="ok">{line}</span>\n')
        elif "error" in line.lower() or "fail" in line.lower() or "timed out" in line.lower() or "skipped" in line.lower():
            lines.append(f'<span class="fail">{line}</span>\n')
        elif "pipeline start" in line.lower() or "step" in line.lower():
            lines.append(f'<span class="info">{line}</span>\n')
        elif "llm" in line.lower() or "LLM" in line:
            lines.append(f'<span class="llm">{line}</span>\n')
        else:
            lines.append(line + "\n")
    return "".join(lines)

now = datetime.now().strftime("%H:%M:%S")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Pipeline Monitor</title>
<meta http-equiv="refresh" content="10">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;min-height:100vh}}
h1{{font-size:1.2rem;font-weight:800;color:#fff;display:flex;align-items:center;gap:8px}}
.sub{{color:#64748b;font-size:.7rem;margin-bottom:16px}}

.machine-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}}
.machine{{border-radius:12px;padding:16px;border:1px solid #334155}}
.mac{{background:linear-gradient(135deg,#1e1b4b,#312e81)}}
.debian{{background:linear-gradient(135deg,#0f172a,#1e293b)}}
.machine h2{{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px}}
.machine h2 span{{opacity:.6}}
.stats-row{{display:flex;gap:12px;flex-wrap:wrap}}
.stat{{background:rgba(0,0,0,.3);border-radius:8px;padding:8px 12px;text-align:center;min-width:70px}}
.stat .val{{font-size:1.1rem;font-weight:800}}
.stat .lbl{{font-size:.55rem;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.04em}}

.grid-2{{display:grid;grid-template-columns:2fr 1fr;gap:12px;margin-bottom:16px}}
.panel{{background:#1e293b;border-radius:12px;padding:14px;border:1px solid #334155}}
.panel h3{{font-size:.65rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px}}

.log{{font-family:monospace;font-size:.55rem;line-height:1.5;white-space:pre-wrap;max-height:200px;overflow-y:auto;padding:2px}}
.log .ok{{color:#22c55e}}
.log .fail{{color:#ef4444}}
.log .info{{color:#60a5fa}}
.log .llm{{color:#a78bfa}}

table{{width:100%;border-collapse:collapse;font-size:.65rem}}
td{{padding:3px 6px;border-bottom:1px solid #0f172a}}
td:first-child{{color:#94a3b8}}
td.num{{text-align:right;font-weight:700;color:#e2e8f0}}
.bar-bg{{height:4px;background:#0f172a;border-radius:2px;overflow:hidden}}
.bar{{height:100%;background:#3b82f6;border-radius:2px}}

.footer{{text-align:center;color:#334155;font-size:.55rem;margin-top:16px}}
</style>
</head>
<body>
<h1>📊 Pipeline Monitor</h1>
<p class="sub">Updated: {now} · Auto-refresh 10s</p>

<div class="machine-grid">
  <div class="machine mac">
    <h2>🍎 Mac Mini <span>— M4, 16GB</span></h2>
    <div class="stats-row">
      <div class="stat"><div class="val">{mac_ollama_status}</div><div class="lbl">Ollama</div></div>
      <div class="stat"><div class="val" style="color:{"#22c55e" if int(mac_ram) < 50 else "#ef4444"}">{mac_ram}%</div><div class="lbl">RAM Used</div></div>
      <div class="stat"><div class="val">{mac_hermes}</div><div class="lbl">Hermes</div></div>
      <div class="stat"><div class="val">{mac_brave}</div><div class="lbl">Browser</div></div>
    </div>
    <div class="log" style="margin-top:8px;max-height:60px;font-size:.5rem">{mac_models or "No models loaded"}</div>
  </div>

  <div class="machine debian">
    <h2>🐧 Debian Box <span>— 15GB RAM</span></h2>
    <div class="stats-row">
      <div class="stat"><div class="val" style="color:{"#22c55e" if debian_running else "#64748b"}">{"🟢 Running" if debian_running else "⏸️ Idle"}</div><div class="lbl">Pipeline</div></div>
      <div class="stat"><div class="val" style="color:#22c55e">{debian_jobs or "?"}</div><div class="lbl">Jobs</div></div>
      <div class="stat"><div class="val">{debian_mem}</div><div class="lbl">RAM</div></div>
      <div class="stat"><div class="val">{debian_ollama}</div><div class="lbl">Ollama</div></div>
    </div>
    <div class="log" style="margin-top:8px;max-height:60px;font-size:.5rem;color:#475569">{debian_cron[:80] or "cron: every 15 min"}</div>
  </div>
</div>

<div class="grid-2">
  <div class="panel">
    <h3>📄 Debian Pipeline Log</h3>
    <div class="log">{color_log(debian_last_log)}</div>
  </div>
  <div class="panel">
    <h3>📊 Sources</h3>
    <table>{source_rows}</table>
  </div>
</div>

<p class="footer">Mac: scraper every 10 min · Source discovery every 10 min · Debian: main scraper every 15 min</p>
</body>
</html>"""

with open(OUTPUT, "w") as f:
    f.write(html)
print("✅ Monitor updated")
