"""Start the Streamlit app AND create a public link you can open on any phone.
 
How to run (from the top Hospital-Assistant folder):
    python start_public.py
 
It prints a link like https://something.trycloudflare.com
- Open that link on your phone (works on mobile data too).
- It also writes the link into website/index.html (the "Book an appointment" button).
- Keep this window open. Press Ctrl+C to stop.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path
 
PORT = 8502
BASE = Path(__file__).parent
WEBSITE = BASE / "website" / "index.html"
LINK_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
 
 
def update_website(url: str) -> None:
    """Put the new link into the website's Book button."""
    if not WEBSITE.exists():
        print(f"(website file not found at {WEBSITE}, skipping)")
        return
    html = WEBSITE.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(href=")(http://localhost:\d+|https://[a-z0-9-]+\.trycloudflare\.com)(")')
    new_html, n = pattern.subn(rf"\g<1>{url}\g<3>", html)
    if n:
        WEBSITE.write_text(new_html, encoding="utf-8")
        print(f"Updated {n} link(s) in website/index.html")
    else:
        print("No Book button link found in website/index.html to update.")
 
 
def main() -> None:
    if shutil.which("cloudflared") is None:
        print("cloudflared is not installed.")
        print("Install it once with:  winget install --id Cloudflare.cloudflared")
        print("Then close and reopen VS Code, and run this file again.")
        sys.exit(1)
 
    print("Starting the Streamlit app...")
    app = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", str(BASE / "app.py"),
        "--server.port", str(PORT), "--server.headless", "true",
    ])
 
    print("Creating the public link (this takes a few seconds)...")
    tunnel = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
 
    try:
        for line in tunnel.stdout:
            match = LINK_RE.search(line)
            if match:
                url = match.group(0)
                print("\n" + "=" * 60)
                print("OPEN THIS LINK ON YOUR PHONE:")
                print(url)
                print("=" * 60 + "\n")
                update_website(url)
                print("Keep this window open. Press Ctrl+C to stop.")
                break
        tunnel.wait()  # keep running until stopped
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        tunnel.terminate()
        app.terminate()
 
 
if __name__ == "__main__":
    main()