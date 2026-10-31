"""All numbers come from these SQL queries (Exasol-compatible). Leaks use a two-proportion z-test (in SQL) to avoid noise. Profit = contribution after shipping, reverse shipping and write-offs."""
F = "WITH f AS (SELECT * FROM LEAKHUNTER.V_FACT)"
def kpis(): return F + " SELECT COUNT(*) AS orders, SUM(NET_REVENUE) AS revenue, SUM(PROFIT) AS profit, 1.0*SUM(IS_RETURNED)/COUNT(*) AS return_rate, SUM(CASE WHEN IS_RETURNED=1 THEN -PROFIT ELSE 0 END) AS return_cost FROM f"
def weekly(): return F + " SELECT WEEK_NO, COUNT(*) AS orders, 1.0*SUM(IS_RETURNED)/COUNT(*) AS return_rate, SUM(PROFIT) AS profit FROM f GROUP BY WEEK_NO ORDER BY WEEK_NO"
def leaks(cut): return F + f""", a AS (SELECT CATEGORY, CHANNEL,
 SUM(CASE WHEN WEEK_NO >= {cut} THEN 1 ELSE 0 END) AS orders_recent, SUM(CASE WHEN WEEK_NO >= {cut} THEN IS_RETURNED ELSE 0 END) AS ret_recent,
 SUM(CASE WHEN WEEK_NO < {cut} THEN 1 ELSE 0 END) AS orders_base, SUM(CASE WHEN WEEK_NO < {cut} THEN IS_RETURNED ELSE 0 END) AS ret_base,
 AVG(CASE WHEN IS_RETURNED = 1 THEN -PROFIT END) AS avg_ret_cost, AVG(CASE WHEN IS_RETURNED = 0 THEN PROFIT END) AS avg_kept_profit
 FROM f GROUP BY CATEGORY, CHANNEL)
 SELECT a.*, (1.0*ret_recent/NULLIF(orders_recent,0) - 1.0*ret_base/NULLIF(orders_base,0)) /
 NULLIF(SQRT((1.0*(ret_recent+ret_base)/(orders_recent+orders_base)) * (1 - 1.0*(ret_recent+ret_base)/(orders_recent+orders_base)) * (1.0/NULLIF(orders_recent,0) + 1.0/NULLIF(orders_base,0))), 0) AS z
 FROM a"""  # z = two-proportion z-test, computed inside Exasol
def reasons(cat, ch, cut): return F + f" SELECT RETURN_REASON, COUNT(*) AS returns, SUM(-PROFIT) AS cost FROM f WHERE CATEGORY='{cat}' AND CHANNEL='{ch}' AND WEEK_NO >= {cut} AND IS_RETURNED=1 GROUP BY RETURN_REASON ORDER BY returns DESC"
def paymode(): return F + " SELECT PAY_MODE, COUNT(*) AS orders, 1.0*SUM(IS_RETURNED)/COUNT(*) AS return_rate, AVG(CASE WHEN IS_RETURNED=1 THEN -PROFIT END) AS avg_ret_cost FROM f GROUP BY PAY_MODE"

def products(): return F + " SELECT PRODUCT_NAME, CATEGORY, COUNT(*) AS orders, 1.0*SUM(IS_RETURNED)/COUNT(*) AS return_rate, SUM(PROFIT) AS profit, SUM(CASE WHEN IS_RETURNED=1 THEN -PROFIT ELSE 0 END) AS return_cost FROM f GROUP BY PRODUCT_NAME, CATEGORY ORDER BY return_cost DESC LIMIT 10"
def discounts(): return F + """ SELECT band, COUNT(*) AS orders, 1.0*SUM(IS_RETURNED)/COUNT(*) AS return_rate, MIN(DISCOUNT_PCT) AS lo FROM
 (SELECT CASE WHEN DISCOUNT_PCT <= 0 THEN '0%' WHEN DISCOUNT_PCT <= 10 THEN '1-10%' WHEN DISCOUNT_PCT <= 20 THEN '11-20%' ELSE '21%+' END AS band, DISCOUNT_PCT, IS_RETURNED FROM f) t GROUP BY band ORDER BY lo"""
def serial(): return F + " SELECT CUSTOMER_ID, COUNT(*) AS orders, SUM(IS_RETURNED) AS returns, SUM(PROFIT) AS profit, SUM(CASE WHEN IS_RETURNED=1 THEN -PROFIT ELSE 0 END) AS return_cost FROM f GROUP BY CUSTOMER_ID HAVING SUM(IS_RETURNED) >= 3 AND 1.0*SUM(IS_RETURNED)/COUNT(*) >= 0.5 ORDER BY return_cost DESC"
