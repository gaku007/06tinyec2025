# ApparelShop (Flask demo)

Run the development server:

```bash
python3 -m pip install -r web_app/requirements.txt
python3 web_app/app.py
```

Open http://127.0.0.1:5000

Notes:
- DB is SQLite at `web_app/app.db` and seeded with 10 products from `req.md`.
- Checkout issues a payment code and stores the order; `/api/payments/simulate` can simulate a payment for testing.
