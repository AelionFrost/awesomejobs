#!/usr/bin/env python3
"""Job proxy v5 — instant text extraction, no LLM delay."""
import json, urllib.request, re, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from html.parser import HTMLParser

PORT = 8910

class T(HTMLParser):
    def __init__(self):
        super().__init__()
        self.t = []; self.s = 0
    def handle_starttag(self, tag, a):
        if tag in ('script','style','noscript','svg','nav','footer','header'): self.s += 1
        elif tag in ('br','p','div','li','h1','h2','h3','h4','h5','h6','tr','section','article'): self.t.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript','svg','nav','footer','header'): self.s = max(0,self.s-1)
        elif tag in ('p','div','li','h1','h2','h3','h4','h5'): self.t.append('\n')
    def handle_data(self, d):
        if self.s==0 and d.strip(): self.t.append(d.strip()+' ')

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
    lines = [l.strip() for l in t.split('\n') if len(l.strip())>5]
    deduped = [l for i,l in enumerate(lines) if i==0 or l!=lines[i-1]]
    return '\n'.join(deduped)

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/fetch"):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            url = qs.get("url",[""])[0]
            if not url: self.j({"error":"No URL"}); return
            html = fetch(url)
            if not html: self.j({"text":"Source unavailable"}); return
            self.j({"text": extract(html), "url": url})
        else: self.j({"status":"ok"})
    def j(self, d):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def log_message(self,*a): pass

HTTPServer(("127.0.0.1",PORT),H).serve_forever()
