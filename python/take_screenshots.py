"""Launch the Streamlit dashboard and capture one screenshot per tab with a headless browser.

Output: documentation/screenshots/*.png   (needs: pip install playwright; uses installed Chrome/Edge)
Run:    python python/take_screenshots.py
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

os.chdir(Path(__file__).resolve().parents[1])
OUT = Path("documentation/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
PORT = 8599
URL = f"http://localhost:{PORT}"

TABS = [("Delivery performance", "01_delivery_performance"), ("Geography", "02_geography"),
        ("Returns & categories", "03_returns_categories"), ("Sellers", "04_sellers")]

server = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.port", str(PORT),
     "--server.headless", "true", "--client.toolbarMode", "minimal", "--browser.gatherUsageStats", "false"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):                      # wait for the server to come up
        try:
            urllib.request.urlopen(URL, timeout=2)
            break
        except Exception:
            time.sleep(1)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1500, "height": 2300}, device_scale_factor=1)
        page.goto(URL)
        page.wait_for_selector("text=E-Commerce Order Delivery Performance", timeout=60000)
        for label, name in TABS:
            page.get_by_role("tab", name=label).click()
            time.sleep(4)                    # let plotly finish rendering
            box = page.locator('[data-testid="stMainBlockContainer"]').bounding_box()
            height = min(2300, int(box["y"] + box["height"]) + 40)   # crop empty space below content
            page.screenshot(path=str(OUT / f"{name}.png"), clip={"x": 0, "y": 0, "width": 1500, "height": height})
            print("saved", name)
        browser.close()
finally:
    server.terminate()
