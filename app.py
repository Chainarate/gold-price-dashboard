"""
Gold Price Comparison Dashboard
Scrapes real-time 96.5% gold prices from 4 Thai brokers:
  YLG, Intergold, GCAP, TDC
Serves a live-updating web dashboard via Flask.
"""

import json
import re
import threading
import time
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
_lock = threading.Lock()
_prices: list[dict] = []
_last_update: str = ""

SCRAPE_INTERVAL = 12  # seconds
REQUEST_TIMEOUT = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

# ---------------------------------------------------------------------------
# Individual broker scrapers
# ---------------------------------------------------------------------------

def fetch_ylg() -> dict:
    """YLG Bullion – direct JSON API."""
    resp = requests.get(
        "https://register.ylgbullion.co.th/api/price/gold",
        headers={**HEADERS, "Referer": "https://www.ylg.co.th/"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    bar96 = data["bar96"]
    return {"name": "YLG", "bid": int(bar96["tin"]), "offer": int(bar96["tout"])}


_IG_PATTERN = re.compile(r"var\s+data_gold\s*=\s*'(.+?)'")

def fetch_intergold() -> dict:
    """Intergold – parse embedded JS variable from HTML."""
    resp = requests.get(
        "https://www.intergold.co.th/",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    match = _IG_PATTERN.search(resp.text)
    if not match:
        raise ValueError("data_gold not found in Intergold page")
    data = json.loads(match.group(1))["results"][0]
    return {"name": "Intergold", "bid": int(data["bidPrice96"]), "offer": int(data["offerPrice96"])}


def fetch_gcap() -> dict:
    """GCAP – direct JSON API (assetId 2 = 96.5%)."""
    ts = int(time.time() * 1000)
    resp = requests.get(
        f"https://price.gcaponline.com/api/goldlastprice?timestamp={ts}",
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    for item in resp.json():
        if str(item.get("assetId")) == "2":
            return {
                "name": "GCAP",
                "bid": int(item["bidPrice"]),
                "offer": int(item["offerPrice"]),
            }
    raise ValueError("assetId 2 not found in GCAP response")


def fetch_tdc() -> dict:
    """TDC Gold – direct JSON API."""
    resp = requests.get(
        "https://api.goldcompute.com/api/v1/content/gold_price/latest",
        headers={**HEADERS, "Referer": "https://tdcgold.com/"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"name": "TDC", "bid": int(data["gold965_bid"]), "offer": int(data["gold965_offer"])}


BROKERS = [
    ("YLG", fetch_ylg),
    ("Intergold", fetch_intergold),
    ("GCAP", fetch_gcap),
    ("TDC", fetch_tdc),
]

# ---------------------------------------------------------------------------
# Background scraper thread
# ---------------------------------------------------------------------------

def _scrape_all() -> None:
    """Fetch prices from all brokers and update shared state."""
    global _prices, _last_update
    results = []
    for name, fetcher in BROKERS:
        try:
            results.append(fetcher())
        except Exception as exc:
            print(f"[{datetime.now():%H:%M:%S}] {name} error: {exc}")
            results.append({"name": name, "bid": None, "offer": None})

    with _lock:
        _prices = results
        _last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _background_loop() -> None:
    while True:
        _scrape_all()
        time.sleep(SCRAPE_INTERVAL)

# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/gold-prices")
def gold_prices():
    with _lock:
        return jsonify({"prices": _prices, "updated": _last_update})

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

# Do one immediate scrape so the first page load has data.
_scrape_all()

_thread = threading.Thread(target=_background_loop, daemon=True)
_thread.start()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5050)
