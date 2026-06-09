# n8n Workflow & LLM Node Configuration
## AwesomeJobs Aggregator — AwesomeJobs.online
===============================================

This file documents the exact n8n workflow structure, HTTP node
payloads, and Ollama API calls to build the full ingestion +
processing + deployment pipeline.

The pipeline has 3 phases:
  Phase 1  Ingest    → Fetch raw feeds + ATS company endpoints
  Phase 2  Filter    → Debian cluster (gemma2:2b / qwen2.5:3b / llama3)
  Phase 3  Extract   → Mac Mini M4 (qwen2.5-coder:7b) + Deploy



──────────────────────────────────────────────────
  PHASE 1: INGEST — HTTP Request Nodes
──────────────────────────────────────────────────

All three nodes below feed into a single "Merge + Dedupe" node
(merge by URL/title+company hash) before entering Phase 2.

── NODE 1: "Remotive API" ────────────────────
  Node: HTTP Request
  Method: GET
  URL: https://remotive.com/api/remote-jobs
        
  Expected response shape:
    { "jobs": [
        { "title", "company_name", "description",
          "candidate_required_location", "salary",
          "tags", "url", "publication_date", ... }
    ]}

  Post-process with an Item Lists node:
    Title      → title
    Company    → company_name
    Location   → candidate_required_location
    Salary     → salary
    Tags       → tags
    Apply URL  → url
    Raw HTML   → description  (pass through)

── NODE 2: "Arbeitnow API" ───────────────────
  Node: HTTP Request
  Method: GET
  URL: https://www.arbeitnow.com/api/job-board-api

  Expected response shape:
    { "data": [
        { "title", "company", "location",
          "salary", "tags", "url", ... }
    ]}

  (Same field mapping as Remotive.)

── NODE 3: "We Work Remotely RSS" ───────────
  Node: RSS Feed Read
  URL: https://weworkremotely.com/categories/remote-programming-jobs.rss

  Output per item: title, link, contentSnippet, pubDate
  Pass through directly.



──────────────────────────────────────────────────
  PHASE 1B: ATS COMPANY POLLING (Loop Over Items)
──────────────────────────────────────────────────

Use a "Set" node to define the target company slugs:

  Name: greenhouse_slugs
  Value (json): ["linear","vercel","supabase","railway","planetscale"]

Then: Loop over slugs → HTTP Method: GET
  URL: https://boards-api.greenhouse.io/v1/boards/{{$node["Set_greenhouse"].json.greenhouse_slugs}}/jobs
  Send Header:  Name: Accept  |  Value: application/json

For Lever, a second loop:

  Name: lever_slugs
  Value (json): ["notion","netlify","framer","vercel","stripe"]

  URL: https://api.lever.co/v2/postings/{{$node["Set_lever"].json.lever_slugs}}



──────────────────────────────────────────────────
  PHASE 1C: DEEP CRAWL (Web3.career, etc.)
──────────────────────────────────────────────────

Node  | URL
------+-----------------------------------------
HTTP  | https://web3.career/remote-jobs
HTTP  | https://cryptojobslist.com/

Use "HTML Extract" to pull the container:
  CSS Selector: .job-list-item   (Web3.career)
                  .job-item       (CryptoJobsList — verify on live page)
  Attributes: title, href

Then: split out → "Extract from HTML" → full page body.
Feed the raw HTML body into Phase 2.



──────────────────────────────────────────────────
  PHASE 2: FILTER + SUMMARISE (Debian Cluster)
──────────────────────────────────────────────────

Configure each HTTP node to talk to your Debian worker(s).
Assume Ollama runs on each machine at http://<ip>:11434

── NODE: "gemma2 — Is it a real job?" ────────
  Node: HTTP Request
  Method: POST
  URL: http://<DEBIAN-IP>:11434/api/generate

  Body (JSON, send as body):
  {
    "model": "gemma2:2b",
    "prompt": "You are a strict content classifier. Read the text below and answer with ONLY the word 'VALID' if this is a legitimate job posting, or 'INVALID' if it is a blog post, navigation junk, advertisement, or anything else. Do not explain.\n\nText:\n{{ $json.raw_text }}",
    "stream": false,
    "options": { "temperature": 0.0 }
  }

  Parse response: $json.response
  "VALID"  → continue
  "INVALID" → drop (Router / Filter node)

── NODE: "qwen2.5 — Strip & summarise" ──────
  Node: HTTP Request
  Method: POST
  URL: http://<DEBIAN-IP>:11434/api/generate

  Body (JSON):
  {
    "model": "qwen2.5:3b",
    "prompt": "Convert the following raw job posting HTML/text into clean markdown. Keep ONLY: job title, company name, location, salary (if stated), required skills/technologies (as a bulleted list), and the direct application URL. Remove all navigation, footers, advertisements, and unrelated links. Output ONLY valid markdown.\n\n{{ $json.text }}",
    "stream": false,
    "options": { "temperature": 0.1 }
  }

  Output: $json.response  → pass to llama3 for reinforcement

── NODE: "llama3 — Final clean markdown" ────
  Node: HTTP Request
  Method: POST
  URL: http://<DEBIAN-IP>:11434/api/generate

  Body (JSON):
  {
    "model": "llama3:latest",
    "prompt": "You are a data-cleaning assistant. The following markdown is an extracted and summarised job posting. Polish it: fix any duplicated sections, ensure every skill tag is a real technology/trademark (not generic words like \"experience\"), and make sure the final output is concise clean markdown of MAX 400 words. If no salary is mentioned, omit that line.\n\n{{ $json.clean_text }}",
    "stream": false,
    "options": { "temperature": 0.15 }
  }

  Output: $json.response  → send to Mac Mini M4 (Phase 3)



──────────────────────────────────────────────────
  PHASE 3: STRUCTURED EXPORT  (Mac Mini M4)
──────────────────────────────────────────────────

── NODE: "qwen2.5-coder — Emit JSON" ────────
  Node: HTTP Request
  Method: POST
  URL: http://<MAC-MINI-IP>:11434/api/chat

  // Using /api/chat with format:"json" for strict schema adherence
  Body (JSON):
  {
    "model": "qwen2.5-coder:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are a JSON extractor. Given a job posting in markdown, emit ONLY a JSON object with the exact schema below. Do NOT wrap in markdown fences. Do NOT add commentary. Use empty string for unknown fields. Salary must include currency symbol. Tags array maximum 8 items, lowercase, real technologies only.\n\nSchema:\n{\n  \"title\": \"string\",\n  \"company\": \"string\",\n  \"location\": \"string\",\n  \"salary\": \"string\",\n  \"tags\": [\"string\"],\n  \"apply_url\": \"string\"\n}"
      },
      {
        "role": "user",
        "content": "{{ $json.final_markdown }}"
      }
    ],
    "format": "json",
    "stream": false,
    "options": {
      "temperature": 0.1
    }
  }

  Parse response:
    $json.message.content  (already a JSON object thanks to format:"json")

── NODE: "Merge + Write jobs.json" ──────────
  Step A: Existing "Read Existing jobs.json" via FTP or filesystem.
          Load current jobs array.
  Step B: "Merge Collections" → union by title+company key.
  Step C: Deduplicate (item lists node).
  Step D: "Write Binary File" → path: data/jobs.json
          Content (JSON):
            {
              "meta": {
                "generated_at": "{{ $now.toISO() }}",
                "source": "awesomejobs.online",
                "pipeline": "n8n → Ollama (gemma2/qwen2.5/llama3) → qwen2.5-coder:7b"
              },
              "jobs": [ ...merged array... ]
            }

  Step E: "Execute Command" (bash on Mac Mini):
          bash /Users/scion/awesomejobs/scripts/deploy_sync.sh "auto: job sync {{ $now.toISO() }}"



──────────────────────────────────────────────────
  SCHEDULING & ALERTS
──────────────────────────────────────────────────

1. Place a "Schedule Trigger" at the top of workflow #1.
   Interval: Every 3 hours (cron: "0 */3 * * *").

2. Add an "Error Trigger" → "Send Email" node.
   To: your@admin.email
   Subject: ⚠️ AwesomeJobs pipeline failed
   Body:   {{ $execution.error.message }}

3. Rate-limit the ATS loop: use "Wait" node (1s) between
   each company poll to avoid GH/Lever throttling.



──────────────────────────────────────────────────
  END-TO-END QUICK-VALIDATE COMMANDS
──────────────────────────────────────────────────

# Test gemma2:2b filter
curl -s http://<DEBIAN>:11434/api/generate \
  -d '{"model":"gemma2:2b","prompt":"Is this a job post? Answer VALID or INVALID.\n\nRemote Senior React Engineer at Stripe","stream":false,"options":{"temperature":0}}'

# Test qwen2.5-coder:7b JSON extraction
curl -s http://<MACMINI>:11434/api/chat \
  -d '{
    "model":"qwen2.5-coder:7b",
    "messages":[
      {"role":"system","content":"Extract job details as JSON with keys: title, company, location, salary, tags, apply_url. No markdown fences."},
      {"role":"user","content":"Senior Frontend Engineer at Acme Corp. Remote US. $120k-$180k. Tech: React, TypeScript, Next.js. Apply: https://example.com/apply"}
    ],
    "format":"json",
    "stream":false,
    "options":{"temperature":0.1}
  }' | python3 -m json.tool
