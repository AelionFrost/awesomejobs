#!/usr/bin/env python3
"""
Auto-Reddit: Posts to Reddit automatically using browser automation.
No manual copy-paste needed.
"""
import json, os, time
from playwright.sync_api import sync_playwright

POSTS_DIR = "/tmp/reddit-posts"
REDDIT_USER = ""
REDDIT_PASS = ""
CRED_FILE = os.path.expanduser("~/.reddit_creds.json")

def load_creds():
    if os.path.exists(CRED_FILE):
        with open(CRED_FILE) as f:
            c = json.load(f)
            return c.get("user",""), c.get("pass","")
    return "", ""

def save_creds(user, pw):
    os.makedirs(os.path.dirname(CRED_FILE), exist_ok=True)
    with open(CRED_FILE, "w") as f:
        json.dump({"user": user, "pass": pw}, f)

def get_latest_post():
    """Find the latest generated post file."""
    files = sorted(os.listdir(POSTS_DIR)) if os.path.exists(POSTS_DIR) else []
    if not files:
        return None, None
    latest = files[-1]
    with open(os.path.join(POSTS_DIR, latest)) as f:
        content = f.read()
    
    # Parse title and body
    lines = content.split("\n")
    title = ""
    body = []
    in_body = False
    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("SUBREDDIT:"):
            sub = line.replace("SUBREDDIT:", "").strip()
        elif line.startswith("---"):
            in_body = True
            continue
        elif in_body:
            body.append(line)
    
    return title, "\n".join(body).strip(), sub

def post_to_reddit(user, pw, title, body, subreddit):
    print(f"🚀 Posting to r/{subreddit}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Log in
        print("  Logging in...")
        page.goto("https://www.reddit.com/login")
        page.wait_for_timeout(2000)
        page.fill("input[name='username']", user)
        page.fill("input[name='password']", pw)
        page.click("button[type='submit']")
        page.wait_for_timeout(5000)
        
        # Go to submit page
        print(f"  Opening r/{subreddit} submit...")
        page.goto(f"https://www.reddit.com/r/{subreddit}/submit")
        page.wait_for_timeout(3000)
        
        # Fill title
        print("  Filling title...")
        page.fill("textarea, [name='title'], [slot='title']", title)
        page.wait_for_timeout(1000)
        
        # Fill body
        print("  Filling body...")
        page.fill("div[role='textbox'], [slot='text'], [name='text']", body)
        page.wait_for_timeout(1000)
        
        # Submit
        print("  Submitting...")
        page.click("button[type='submit'], button:has-text('Post')")
        page.wait_for_timeout(5000)
        
        print(f"✅ Posted to r/{subreddit}!")
        browser.close()

def main():
    user, pw = load_creds()
    
    if not user or not pw:
        print("📝 First time setup — need your Reddit credentials")
        print("   (Saved locally, never shared)")
        user = input("  Reddit username: ").strip()
        pw = input("  Reddit password: ").strip()
        save_creds(user, pw)
        print("   ✅ Credentials saved")
    
    title, body, subreddit = get_latest_post()
    if not title:
        print("⚠ No posts found. Run reddit_poster.py first")
        return
    
    print(f"📄 Post: {title[:60]}...")
    print(f"   Subreddit: r/{subreddit}")
    print()
    
    post_to_reddit(user, pw, title, body, subreddit)
    
    # Also post to other subreddits
    for sub in ["forhire", "digitalnomad"]:
        print(f"\n📄 Also posting to r/{sub}...")
        # Re-read the file for this sub
        for f in sorted(os.listdir(POSTS_DIR)):
            if sub in f:
                with open(os.path.join(POSTS_DIR, f)) as fh:
                    content = fh.read()
                    lines = content.split("\n")
                    title2 = ""
                    body2 = []
                    it = False
                    for line in lines:
                        if line.startswith("TITLE:"):
                            title2 = line.replace("TITLE:", "").strip()
                        elif line.startswith("---"):
                            it = True
                            continue
                        elif it:
                            body2.append(line)
                    if title2:
                        post_to_reddit(user, pw, title2, "\n".join(body2).strip(), sub)

if __name__ == "__main__":
    main()
