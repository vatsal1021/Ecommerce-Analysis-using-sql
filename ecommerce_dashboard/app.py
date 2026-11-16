"""
E-Commerce Analysis Dashboard
SQLite + SQL (CTEs, window functions) + Streamlit + Plotly

Run locally:  streamlit run app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).parent / "ecommerce.db"

# Fixed colours: each category always keeps the same colour, whatever the filters.
BLUE, ORANGE = "#2a78d6", "#eb6834"
CATEGORY_COLORS = {
    "Fashion": "#2a78d6",
    "Home & Furniture": "#eb6834",
    "Auto & Accessories": "#1baf7a",
    "Electronic": "#eda100",
}
PRIORITY_ORDER = ["Critical", "High", "Medium", "Low", "Unknown"]

st.set_page_config(page_title="E-Commerce SQL Dashboard", layout="wide")


# ---------------------------------------------------------------- data access
@st.cache_resource
def get_connection():
    # Read-only connection: the dashboard never changes the data.
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)


@st.cache_data
def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_connection(), params=params)


def build_where(filters: dict, alias: str = "") -> tuple[str, tuple]:
    """Turn the sidebar filters into a SQL WHERE clause with ? placeholders.

    Values are passed as parameters (never pasted into the SQL), which avoids
    SQL injection. Dates are filtered with a plain range on Order_Date so the
    idx_orders_date index can be used.
    """
    p = f"{alias}." if alias else ""
    conds = [f"{p}Sales IS NOT NULL", f"{p}Order_Date >= ?", f"{p}Order_Date < ?"]
    params = [filters["start"], filters["end"]]
    for column, values in [
        ("Product_Category", filters["categories"]),
        ("Payment_Method", filters["payments"]),
        ("Device_Type", filters["devices"]),
    ]:
        conds.append(f"{p}{column} IN ({','.join('?' * len(values))})")
        params.extend(values)
    conds.append(f"COALESCE({p}Order_Priority, 'Unknown') IN ({','.join('?' * len(filters['priorities']))})")
    params.extend(filters["priorities"])
    return " AND ".join(conds), tuple(params)


def show_sql(sql: str):
    with st.expander("SQL behind this section"):
        st.code(sql.strip(), language="sql")


def fmt_money(x: float) -> str:
    return f"${x/1e6:.2f}M" if abs(x) >= 1e6 else f"${x/1e3:.0f}K" if abs(x) >= 1e3 else f"${x:,.0f}"


def style(fig, height=360):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="", hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)")
    return fig


# ---------------------------------------------------------------- sidebar filters
opts = run_query("""
    SELECT
      (SELECT GROUP_CONCAT(m, '|') FROM (SELECT DISTINCT strftime('%Y-%m', Order_Date) m FROM Orders ORDER BY m)) AS months,
      (SELECT GROUP_CONCAT(v, '|') FROM (SELECT DISTINCT Product_Category v FROM Orders ORDER BY v)) AS categories,
      (SELECT GROUP_CONCAT(v, '|') FROM (SELECT DISTINCT Payment_Method v FROM Orders ORDER BY v)) AS payments,
      (SELECT GROUP_CONCAT(v, '|') FROM (SELECT DISTINCT Device_Type v FROM Orders ORDER BY v)) AS devices
""").iloc[0]
months = opts["months"].split("|")

st.sidebar.header("Filters")
m_start, m_end = st.sidebar.select_slider("Month range", options=months, value=(months[0], months[-1]))
categories = st.sidebar.multiselect("Category", opts["categories"].split("|"), default=opts["categories"].split("|"))
payments = st.sidebar.multiselect("Payment method", opts["payments"].split("|"), default=opts["payments"].split("|"))
devices = st.sidebar.multiselect("Device", opts["devices"].split("|"), default=opts["devices"].split("|"))
priorities = st.sidebar.multiselect("Order priority", PRIORITY_ORDER, default=PRIORITY_ORDER)

if not (categories and payments and devices and priorities):
    st.warning("Select at least one value in every filter.")
    st.stop()

end_year, end_month = map(int, m_end.split("-"))
end_exclusive = f"{end_year + (end_month == 12)}-{(end_month % 12) + 1:02d}-01"
filters = dict(start=f"{m_start}-01", end=end_exclusive, categories=categories,
               payments=payments, devices=devices, priorities=priorities)
W, P = build_where(filters)
W_O, P_O = build_where(filters, alias="O")

st.sidebar.caption("Data: 51,290 orders, Jan to Dec 2018. Rows with missing sales are excluded.")

# ---------------------------------------------------------------- header + KPIs
st.title("E-Commerce Performance Dashboard")
st.caption("Built on a normalised SQLite database. Every number below is produced by a SQL query; open the expanders to see it.")

KPI_SQL = f"""
SELECT COUNT(*)                     AS Orders,
       SUM(Sales)                   AS Sales,
       SUM(Profit)                  AS Profit,
       AVG(Aging)                   AS Avg_Fulfilment_Days,
       COUNT(DISTINCT Customer_Id)  AS Customers
FROM Orders
WHERE {W}
"""
k = run_query(KPI_SQL, P).iloc[0]
if not k["Orders"]:
    st.info("No orders match these filters.")
    st.stop()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total sales", fmt_money(k["Sales"]))
c2.metric("Total profit", fmt_money(k["Profit"]))
c3.metric("Profit margin", f"{100 * k['Profit'] / k['Sales']:.1f}%")
c4.metric("Orders", f"{int(k['Orders']):,}")
c5.metric("Avg order value", f"${k['Sales'] / k['Orders']:.0f}")
c6.metric("Avg fulfilment", f"{k['Avg_Fulfilment_Days']:.2f} days")
show_sql(KPI_SQL)

tab_trend, tab_products, tab_customers, tab_ops, tab_pay = st.tabs(
    ["Sales trend", "Products", "Customers", "Fulfilment & discounts", "Payments & channels"]
)

# ---------------------------------------------------------------- 1. sales trend
with tab_trend:
    MONTHLY_SQL = f"""
WITH monthly AS (                              -- CTE: one row per month
    SELECT strftime('%Y-%m', Order_Date) AS Month,
           SUM(Sales)  AS Sales,
           SUM(Profit) AS Profit,
           COUNT(*)    AS Orders
    FROM Orders
    WHERE {W}
    GROUP BY Month
)
SELECT Month, Sales, Profit, Orders,
       ROUND(Sales / Orders, 1) AS Avg_Order_Value,
       SUM(Sales) OVER (ORDER BY Month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS Running_Sales,   -- running total
       ROUND(100.0 * (Sales - LAG(Sales) OVER (ORDER BY Month))
             / LAG(Sales) OVER (ORDER BY Month), 1)      AS MoM_Growth_Pct       -- vs previous month
FROM monthly
ORDER BY Month
"""
    df = run_query(MONTHLY_SQL, P)
    best, worst = df.loc[df["Sales"].idxmax()], df.loc[df["Sales"].idxmin()]
    st.markdown(f"**Peak month:** {best['Month']} ({fmt_money(best['Sales'])}). "
                f"**Lowest:** {worst['Month']} ({fmt_money(worst['Sales'])}). "
                f"Average order value stays between ${df['Avg_Order_Value'].min():.0f} and "
                f"${df['Avg_Order_Value'].max():.0f}, so peaks come from more orders, not bigger baskets.")

    left, right = st.columns(2)
    fig = px.line(df, x="Month", y="Sales", markers=True, title="Monthly sales",
                  color_discrete_sequence=[BLUE])
    fig.update_traces(line_width=2, marker_size=8, hovertemplate="%{x}<br>Sales: $%{y:,.0f}<extra></extra>")
    left.plotly_chart(style(fig), width="stretch")

    g = df.dropna(subset=["MoM_Growth_Pct"]).copy()
    g["Direction"] = g["MoM_Growth_Pct"].apply(lambda v: "Growth" if v >= 0 else "Decline")
    fig = px.bar(g, x="Month", y="MoM_Growth_Pct", color="Direction", title="Month-over-month growth (%)",
                 color_discrete_map={"Growth": BLUE, "Decline": ORANGE}, labels={"MoM_Growth_Pct": "Growth %"})
    fig.update_traces(hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>")
    right.plotly_chart(style(fig), width="stretch")

    st.dataframe(df, width="stretch", hide_index=True)
    show_sql(MONTHLY_SQL)

# ---------------------------------------------------------------- 2. products
with tab_products:
    CATEGORY_SQL = f"""
SELECT Product_Category                           AS Category,
       SUM(Sales)                                 AS Sales,
       ROUND(100.0 * SUM(Sales) / SUM(SUM(Sales)) OVER (), 1) AS Share_Pct,   -- window over the grouped result
       ROUND(100.0 * SUM(Profit) / SUM(Sales), 1) AS Margin_Pct,
       COUNT(*)                                   AS Orders
FROM Orders
WHERE {W}
GROUP BY Product_Category
ORDER BY Sales DESC
"""
    cat = run_query(CATEGORY_SQL, P)
    top = cat.iloc[0]
    st.markdown(f"**{top['Category']}** brings in **{top['Share_Pct']}%** of sales at a "
                f"**{top['Margin_Pct']}%** margin.")

    left, right = st.columns([1, 1])
    fig = px.bar(cat, x="Sales", y="Category", orientation="h", color="Category",
                 color_discrete_map=CATEGORY_COLORS, title="Sales by category", text="Share_Pct")
    fig.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br>Sales: $%{x:,.0f}<extra></extra>")
    fig.update_layout(showlegend=False, yaxis=dict(categoryorder="total ascending", title=""))
    fig.update_xaxes(range=[0, cat["Sales"].max() * 1.15])   # room for the % labels
    left.plotly_chart(style(fig), width="stretch")
    right.dataframe(cat, width="stretch", hide_index=True)
    show_sql(CATEGORY_SQL)

    PRODUCT_SQL = f"""
WITH product_sales AS (                         -- CTE: totals per product
    SELECT P.Product_Name     AS Product,
           P.Product_Category AS Category,
           SUM(O.Sales)       AS Sales,
           SUM(O.Profit)      AS Profit,
           SUM(O.Quantity)    AS Units
    FROM Orders O
    JOIN Products P ON O.Product_Id = P.Product_Id
    WHERE {W_O}
    GROUP BY P.Product_Id, P.Product_Name, P.Product_Category
)
SELECT RANK() OVER (ORDER BY Sales DESC)                        AS Overall_Rank,
       RANK() OVER (PARTITION BY Category ORDER BY Sales DESC)  AS Rank_In_Category,
       Product, Category, Sales, Profit, Units
FROM product_sales
ORDER BY Overall_Rank
"""
    prod = run_query(PRODUCT_SQL, P_O)
    n = st.slider("Show top N products", 5, min(25, len(prod)), min(10, len(prod)))
    fig = px.bar(prod.head(n), x="Sales", y="Product", orientation="h", color="Category",
                 color_discrete_map=CATEGORY_COLORS, title=f"Top {n} products by sales",
                 hover_data={"Units": ":,", "Profit": ":,.0f", "Overall_Rank": True})
    fig.update_layout(yaxis=dict(categoryorder="total ascending", title=""))
    st.plotly_chart(style(fig, 80 + 28 * n), width="stretch")

    st.markdown("**Best-selling product in each category** (`RANK() OVER (PARTITION BY Category ...)` = 1)")
    st.dataframe(prod[prod["Rank_In_Category"] == 1], width="stretch", hide_index=True)
    show_sql(PRODUCT_SQL)

# ---------------------------------------------------------------- 3. customers
with tab_customers:
    REPEAT_SQL = f"""
WITH per_customer AS (
    SELECT Customer_Id, COUNT(*) AS Orders
    FROM Orders
    WHERE {W}
    GROUP BY Customer_Id
)
SELECT CASE WHEN Orders >= 4 THEN '4+' ELSE CAST(Orders AS TEXT) END AS Orders_Per_Customer,
       COUNT(*) AS Customers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS Pct_Of_Customers
FROM per_customer
GROUP BY Orders_Per_Customer
ORDER BY Orders_Per_Customer
"""
    rep = run_query(REPEAT_SQL, P)
    one_time = rep.loc[rep["Orders_Per_Customer"] == "1", "Pct_Of_Customers"].sum()
    st.markdown(f"**{one_time:.0f}% of customers ordered only once.** "
                "Turning first-time buyers into repeat buyers is the largest growth opportunity.")

    SEGMENT_SQL = f"""
WITH per_customer AS (
    SELECT Customer_Id,
           COUNT(*)        AS Orders,
           SUM(Sales)      AS Spend,
           MAX(Order_Date) AS Last_Order
    FROM Orders
    WHERE {W}
    GROUP BY Customer_Id
),
ref AS (SELECT MAX(Last_Order) AS Ref_Date FROM per_customer)    -- latest date in the selection
SELECT CASE WHEN Orders >= 2 THEN 'Repeat' ELSE 'One-time' END || ', ' ||
       CASE WHEN julianday(Ref_Date) - julianday(Last_Order) <= 90
            THEN 'active (last 90 days)' ELSE 'lapsed (90+ days)' END AS Segment,
       COUNT(*)              AS Customers,
       ROUND(SUM(Spend), 0)  AS Revenue,
       ROUND(AVG(Spend), 1)  AS Avg_Spend_Per_Customer
FROM per_customer, ref
GROUP BY Segment
ORDER BY Revenue DESC
"""
    seg = run_query(SEGMENT_SQL, P)

    left, right = st.columns(2)
    fig = px.bar(rep, x="Orders_Per_Customer", y="Customers", title="Customers by number of orders",
                 color_discrete_sequence=[BLUE], text="Pct_Of_Customers")
    fig.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False,
                      hovertemplate="%{x} order(s)<br>%{y:,} customers<extra></extra>")
    fig.update_xaxes(title="Orders per customer", type="category")
    left.plotly_chart(style(fig), width="stretch")

    fig = px.bar(seg, x="Customers", y="Segment", orientation="h", title="Customer segments (frequency x recency)",
                 color_discrete_sequence=[BLUE], hover_data={"Revenue": ":,.0f", "Avg_Spend_Per_Customer": True})
    fig.update_layout(yaxis=dict(categoryorder="total ascending", title=""))
    right.plotly_chart(style(fig), width="stretch")
    st.dataframe(seg, width="stretch", hide_index=True)
    show_sql(REPEAT_SQL + "\n-- Segments\n" + SEGMENT_SQL)

    GENDER_SQL = f"""
SELECT Gender,
       COUNT(*)              AS Orders,
       SUM(Sales)            AS Sales,
       ROUND(AVG(Sales), 1)  AS Avg_Order_Value
FROM Orders
WHERE {W}
GROUP BY Gender
"""
    TOPCUST_SQL = f"""
WITH spend AS (
    SELECT Customer_Id, COUNT(*) AS Orders, SUM(Sales) AS Spend
    FROM Orders
    WHERE {W}
    GROUP BY Customer_Id
)
SELECT DENSE_RANK() OVER (ORDER BY Spend DESC) AS Rank, Customer_Id, Orders, Spend
FROM spend
ORDER BY Spend DESC
LIMIT 10
"""
    left, right = st.columns(2)
    left.markdown("**Gender: total sales vs spend per order**")
    left.dataframe(run_query(GENDER_SQL, P), width="stretch", hide_index=True)
    left.caption("Male customers place more orders, but spend per order is almost the same.")
    right.markdown("**Top 10 customers by spend**")
    right.dataframe(run_query(TOPCUST_SQL, P), width="stretch", hide_index=True)
    show_sql(GENDER_SQL + "\n-- Top customers\n" + TOPCUST_SQL)

# ---------------------------------------------------------------- 4. fulfilment & discounts
with tab_ops:
    PRIORITY_SQL = f"""
SELECT COALESCE(Order_Priority, 'Unknown')       AS Priority,
       COUNT(*)                                  AS Orders,
       ROUND(AVG(Aging), 2)                      AS Avg_Fulfilment_Days,
       ROUND(100.0 * SUM(Aging > 7) / COUNT(*), 1) AS Pct_Over_7_Days,
       ROUND(AVG(Shipping_Cost), 2)              AS Avg_Shipping_Cost
FROM Orders
WHERE {W}
GROUP BY Priority
"""
    pr = run_query(PRIORITY_SQL, P)
    pr["Priority"] = pd.Categorical(pr["Priority"], PRIORITY_ORDER, ordered=True)
    pr = pr.sort_values("Priority")

    left, right = st.columns(2)
    fig = px.bar(pr, x="Priority", y="Avg_Fulfilment_Days", title="Average fulfilment time by priority (days)",
                 color_discrete_sequence=[BLUE], text="Avg_Fulfilment_Days")
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="%{x}<br>%{y:.2f} days<extra></extra>")
    fig.update_yaxes(range=[0, pr["Avg_Fulfilment_Days"].max() * 1.15])
    left.plotly_chart(style(fig), width="stretch")
    right.markdown("**Fulfilment and shipping by priority**")
    right.dataframe(pr, width="stretch", hide_index=True)
    right.caption("Data note: Shipping_Cost equals exactly 10% of Profit in every row, so it is a "
                  "derived field. Treat shipping comparisons as low confidence.")
    show_sql(PRIORITY_SQL)

    DISCOUNT_SQL = f"""
SELECT CAST(ROUND(Discount * 100) AS INTEGER) || '%'     AS Discount_Level,
       COUNT(*)                                          AS Orders,
       ROUND(AVG(Sales), 1)                              AS Avg_Order_Value,
       ROUND(100.0 * SUM(Profit) / SUM(Sales), 1)        AS Margin_Pct
FROM Orders
WHERE {W} AND Discount IS NOT NULL
GROUP BY Discount
ORDER BY Discount
"""
    disc = run_query(DISCOUNT_SQL, P)
    left, right = st.columns(2)
    fig = px.line(disc, x="Discount_Level", y="Margin_Pct", markers=True, title="Profit margin by discount level (%)",
                  color_discrete_sequence=[BLUE])
    fig.update_traces(line_width=2, marker_size=8, hovertemplate="%{x} discount<br>Margin: %{y:.1f}%<extra></extra>")
    left.plotly_chart(style(fig), width="stretch")
    right.markdown("**Discount effectiveness**")
    right.dataframe(disc, width="stretch", hide_index=True)
    right.caption("Deeper discounts lower the margin. The question to test: do they bring enough extra orders?")
    show_sql(DISCOUNT_SQL)

# ---------------------------------------------------------------- 5. payments & channels
with tab_pay:
    PAYMENT_SQL = f"""
SELECT Payment_Method,
       COUNT(*)    AS Orders,
       SUM(Sales)  AS Revenue,
       ROUND(100.0 * SUM(Sales) / SUM(SUM(Sales)) OVER (), 1) AS Revenue_Share_Pct
FROM Orders
WHERE {W}
GROUP BY Payment_Method
ORDER BY Revenue DESC
"""
    pay = run_query(PAYMENT_SQL, P)
    st.markdown(f"**{pay.iloc[0]['Payment_Method']}** accounts for **{pay.iloc[0]['Revenue_Share_Pct']}%** of revenue.")
    left, right = st.columns(2)
    fig = px.bar(pay, x="Revenue", y="Payment_Method", orientation="h", title="Revenue by payment method",
                 color_discrete_sequence=[BLUE], text="Revenue_Share_Pct")
    fig.update_traces(texttemplate="%{text}%", textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>")
    fig.update_layout(yaxis=dict(categoryorder="total ascending", title=""))
    fig.update_xaxes(range=[0, pay["Revenue"].max() * 1.15])
    left.plotly_chart(style(fig), width="stretch")

    CHANNEL_SQL = f"""
SELECT Device_Type, Customer_Login_type AS Login_Type,
       COUNT(*)   AS Orders,
       SUM(Sales) AS Revenue,
       ROUND(100.0 * SUM(Sales) / SUM(SUM(Sales)) OVER (), 1) AS Revenue_Share_Pct
FROM Orders
WHERE {W}
GROUP BY Device_Type, Customer_Login_type
ORDER BY Revenue DESC
"""
    right.markdown("**Revenue by device and login type**")
    right.dataframe(run_query(CHANNEL_SQL, P), width="stretch", hide_index=True)
    show_sql(PAYMENT_SQL + "\n-- Channels\n" + CHANNEL_SQL)
