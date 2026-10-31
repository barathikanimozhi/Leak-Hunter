"""SYNTHETIC retail data (seeded). A leak is injected in the last 2 weeks:
Apparel on Marketplace gets +20% discount and +25pt return probability (size issues)."""
import numpy as np, pandas as pd
from datetime import date, timedelta
CATS = {"Apparel": (.17, 499, 1999), "Footwear": (.14, 799, 3499), "Electronics": (.07, 999, 9999), "Home": (.05, 299, 2499), "Beauty": (.06, 199, 1299)}
WO = {"Damaged": .8, "RTO - refused at door": .3, "Size issue": .15, "Not as described": .2, "Changed mind": .1}
def generate(seed=7, weeks=26, per_week=800):
    r = np.random.default_rng(seed); prods = []; pid = 1
    for c, (b, lo, hi) in CATS.items():
        for i in range(8):
            lp = round(float(r.uniform(lo, hi))); prods.append((pid, f"{c} item {i+1}", c, round(lp * float(r.uniform(.4, .6)), 2), lp)); pid += 1
    P = pd.DataFrame(prods, columns=["PRODUCT_ID", "PRODUCT_NAME", "CATEGORY", "COGS_UNIT", "LIST_PRICE"])
    O, R, oid, start = [], [], 1, date(2026, 4, 13)
    for w in range(weeks):
        for _ in range(per_week):
            p = prods[int(r.integers(len(prods)))]; cat = p[2]
            ch = str(r.choice(["Website", "App", "Marketplace"], p=[.35, .3, .35])); pay = "COD" if r.random() < .4 else "Prepaid"
            leak = w >= weeks - 2 and cat == "Apparel" and ch == "Marketplace"
            disc = float(r.choice([0, 10, 20])) + (20 if leak else 0); qty = int(r.integers(1, 3))
            net = round(p[4] * qty * (1 - disc / 100), 2); ship = round(float(r.uniform(50, 90)), 2)
            prob = CATS[cat][0] * (2.3 if pay == "COD" else 1) * (1.15 if ch == "Marketplace" else 1) + (.25 if leak else 0)
            ret = int(r.random() < min(prob, .9))
            O.append((oid, start + timedelta(days=7 * w + int(r.integers(0, 7))), w, p[0], ch, pay, qty, disc, net, ship, ret))
            if ret:
                if leak and r.random() < .7: why = "Size issue"
                elif pay == "COD" and r.random() < .5: why = "RTO - refused at door"
                else: why = str(r.choice(["Size issue", "Damaged", "Not as described", "Changed mind"] if cat in ("Apparel", "Footwear") else ["Damaged", "Not as described", "Changed mind"]))
                R.append((oid, why, 0 if why.startswith("RTO") else net, round(ship * 1.2, 2), round(p[3] * qty * WO[why], 2)))
            oid += 1
    cols = ["ORDER_ID", "ORDER_DATE", "WEEK_NO", "PRODUCT_ID", "CHANNEL", "PAY_MODE", "QTY", "DISCOUNT_PCT", "NET_REVENUE", "SHIP_COST", "IS_RETURNED"]
    O = pd.DataFrame(O, columns=cols); r2 = np.random.default_rng(seed + 99); n = len(O)  # synthetic customers; ~160 serial returners
    serial = r2.random(n) < np.where(O.IS_RETURNED == 1, .25, .015)
    O["CUSTOMER_ID"] = np.where(serial, r2.integers(1, 161, n), r2.integers(161, 4001, n))
    return P, O, pd.DataFrame(R, columns=["ORDER_ID", "RETURN_REASON", "REFUND", "REVERSE_SHIP", "WRITEOFF"])
