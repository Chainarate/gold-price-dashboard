# Gold 96.5% Price Comparison Dashboard

Real-time gold price comparison from 4 Thai brokers, auto-updates every 12 seconds.

| Broker | Source |
|--------|--------|
| YLG | YLG Bullion API |
| Intergold | intergold.co.th |
| GCAP | GCAP Online API |
| TDC | TDC Gold API |

**Bid (Sell)** สูงสุด = highlight แดง, **Offer (Buy)** ต่ำสุด = highlight เขียว

## Requirements

- Python 3.10+

## Setup

```bash
git clone https://github.com/<your-username>/gold-price-dashboard.git
cd gold-price-dashboard
pip install -r requirements.txt
```

## Run

```bash
python3 app.py
```

Open **http://localhost:5050**

## API

```
GET /api/gold-prices
```

```json
{
  "prices": [
    {"name": "YLG", "bid": 76640, "offer": 76735},
    {"name": "Intergold", "bid": 76942, "offer": 77047},
    {"name": "GCAP", "bid": 76605, "offer": 76685},
    {"name": "TDC", "bid": 76546, "offer": 76666}
  ],
  "updated": "2026-03-17 17:06:54"
}
```
