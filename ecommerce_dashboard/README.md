# E-Commerce Performance Dashboard

An interactive Python dashboard for the E-Commerce Analysis Using Advanced SQL project. It analyses 51,290 orders from 2018 stored in a normalised SQLite database. Every chart and number is produced by a SQL query that you can view inside the app.

## What it shows

| Tab | What you see | SQL techniques |
|---|---|---|
| KPIs (top row) | Sales, profit, margin, orders, average order value, average fulfilment time | Aggregates, `COUNT(DISTINCT)` |
| Sales trend | Monthly sales, month-over-month growth, running total | CTE, `SUM() OVER` running total, `LAG()` |
| Products | Sales share and margin by category, top N products, best product in each category | `JOIN`, CTE, `RANK() OVER`, `RANK() OVER (PARTITION BY)`, window over an aggregate |
| Customers | Orders per customer, segments by frequency and recency, gender split, top 10 customers | CTEs, `CASE`, `julianday`, `DENSE_RANK()` |
| Fulfilment & discounts | Fulfilment days and % of orders over 7 days by priority, margin by discount level | `COALESCE`, conditional aggregation |
| Payments & channels | Revenue share by payment method, device and login type | Window share of total |

Filters in the sidebar (month range, category, payment method, device, priority) apply to every query. Filter values are passed as SQL parameters, and the date filter uses a plain range on `Order_Date` so the date index can be used.

## Files

- `app.py`: the dashboard
- `ecommerce.db`: the SQLite database (Orders, Customers, Products, with indexes)
- `requirements.txt`: Python packages

## Run it on your computer

1. Install Python 3.11 or newer.
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. The dashboard opens in your browser at http://localhost:8501.

## Put it online for free (Streamlit Community Cloud)

1. Create a new public GitHub repository and upload the three files (`app.py`, `ecommerce.db`, `requirements.txt`).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Create a new app, choose your repository, branch `main` and main file `app.py`. In the advanced settings, choose Python 3.12.
4. Deploy. You get a public URL you can add to your resume next to the project.
