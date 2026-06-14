#!/usr/bin/env python3
"""Job proxy — extracts text, cuts before forms/salary disclosures."""
import json, urllib.request, re, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from html.parser import HTMLParser

PORT = 8910

class T(HTMLParser):
    def __init__(self):
        super().__init__()
        self.t = []; self.stop = False
    def handle_starttag(self, tag, a):
        if tag in ('br','p','div','li','h1','h2','h3','h4','h5','h6','tr','section','article'): self.t.append('\n')
    def handle_data(self, d):
        if not d.strip() or self.stop: return
        if re.match(r'^(Apply for this job|First Name|Last Name|Preferred First|Email \*|Phone|Resume/CV|Cover Letter|Submit application)', d.strip()):
            self.stop = True; return
        self.t.append(d.strip()+' ')

def fetch(url):
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode("utf-8",errors="replace")
    except: return None

def extract(html):
    e = T(); e.feed(html)
    t = re.sub(r' {2,}',' ',''.join(e.t))
    t = re.sub(r'\n{3,}','\n\n',t)
    lines = [l.strip() for l in t.split('\n') if l.strip() and len(l.strip())>5]
    # Merge broken lines
    merged = []; buf = ''
    for l in lines:
        ends = l.endswith(('.','?','!',':'))
        if buf and not ends: buf += ' ' + l
        elif buf: merged.append(buf); buf = l
        else: buf = l
    if buf: merged.append(buf)
    # Cut at salary disclosure / EEO / form markers
    result = []
    for l in merged:
        if re.match(r'^(Pay Transparency|This job posting|In addition to base salary|To provide greater transparency|In select roles|During the interview|Reddit is proud|Answering these|We invite you|What gender|Please select|The base salary range)', l): break
        if re.search(r'(Apply for this job|First Name|Submit application)', l): break
        result.append(l)
    # Dedupe
    deduped = []
    for l in result:
        if not deduped or l != deduped[-1]: deduped.append(l)
    return '\n'.join(deduped)

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/fetch"):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            url = qs.get("url",[""])[0]
            if not url: self.j({"error":"No URL"}); return
            html = fetch(url)
            if not html: self.j({"text":"Source unavailable"}); return
            self.j({"text": extract(html)})
        else: self.j({"status":"ok"})
    def j(self, d):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def log_message(self,*a): pass

HTTPServer(("127.0.0.1",PORT),H).serve_forever()
