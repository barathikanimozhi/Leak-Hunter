"""DB layer: Exasol (set EXASOL_DSN) or local DuckDB demo mode (no setup)."""
import os, ssl, pandas as pd
S = "LEAKHUNTER"
DDL = [
 f"CREATE SCHEMA IF NOT EXISTS {S}",
 f"CREATE OR REPLACE TABLE {S}.PRODUCTS(PRODUCT_ID INT, PRODUCT_NAME VARCHAR(100), CATEGORY VARCHAR(50), COGS_UNIT DECIMAL(12,2), LIST_PRICE DECIMAL(12,2))",
 f"CREATE OR REPLACE TABLE {S}.ORDERS(ORDER_ID INT, ORDER_DATE DATE, WEEK_NO INT, PRODUCT_ID INT, CHANNEL VARCHAR(30), PAY_MODE VARCHAR(10), QTY INT, DISCOUNT_PCT DECIMAL(5,2), NET_REVENUE DECIMAL(12,2), SHIP_COST DECIMAL(12,2), IS_RETURNED INT, CUSTOMER_ID INT)",
 f"CREATE OR REPLACE TABLE {S}.RETURN_EVENTS(ORDER_ID INT, RETURN_REASON VARCHAR(60), REFUND DECIMAL(12,2), REVERSE_SHIP DECIMAL(12,2), WRITEOFF DECIMAL(12,2))",
f"CREATE OR REPLACE VIEW {S}.V_FACT AS SELECT o.ORDER_ID, o.CUSTOMER_ID, o.PRODUCT_ID, o.DISCOUNT_PCT, p.PRODUCT_NAME, o.WEEK_NO, o.CHANNEL, o.PAY_MODE, o.IS_RETURNED, o.NET_REVENUE, p.CATEGORY, r.RETURN_REASON, CASE WHEN o.IS_RETURNED = 1 THEN -(o.SHIP_COST + r.REVERSE_SHIP + r.WRITEOFF) ELSE o.NET_REVENUE - p.COGS_UNIT * o.QTY - o.SHIP_COST END AS PROFIT FROM {S}.ORDERS o JOIN {S}.PRODUCTS p ON p.PRODUCT_ID = o.PRODUCT_ID LEFT JOIN {S}.RETURN_EVENTS r ON r.ORDER_ID = o.ORDER_ID",
]
class DB:
    def __init__(s):
        s.ex = bool(os.getenv("EXASOL_DSN"))
        if not s.ex and os.getenv("DEV_DUCKDB") != "1":
            raise SystemExit("Exasol Personal is required: set EXASOL_DSN, EXASOL_USER, EXASOL_PASSWORD. (Offline dev only: DEV_DUCKDB=1)")
        if s.ex:
            import pyexasol
            s.c = pyexasol.connect(dsn=os.environ["EXASOL_DSN"], user=os.getenv("EXASOL_USER", "sys"),
                password=os.environ["EXASOL_PASSWORD"], encryption=True,
                websocket_sslopt={"cert_reqs": ssl.CERT_NONE})
        else:
            import duckdb; s.c = duckdb.connect("demo.duckdb")
    def run(s, sql): s.c.execute(sql)
    def q(s, sql):
        df = s.c.export_to_pandas(sql) if s.ex else s.c.execute(sql).df()
        df.columns = [x.lower() for x in df.columns]
        for c in df.columns:
            if df[c].dtype == object:
                try: df[c] = pd.to_numeric(df[c])
                except Exception: pass
        return df
    def load(s, name, df):
        if s.ex: s.c.import_from_pandas(df, (S, name.upper()))
        else:
            s.c.register("tmp_df", df); s.c.execute(f"INSERT INTO {S}.{name} SELECT * FROM tmp_df"); s.c.unregister("tmp_df")
