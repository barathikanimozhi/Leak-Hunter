import queries as Q
def max_week(db): return int(db.q("SELECT MAX(WEEK_NO) AS m FROM LEAKHUNTER.ORDERS").m[0])
def find_leaks(db, recent_weeks=2, min_orders=30, min_delta=.12, min_z=3.5):
    cut = max_week(db) - recent_weeks + 1
    d = db.q(Q.leaks(cut))
    d["rate_recent"] = d.ret_recent / d.orders_recent; d["rate_base"] = d.ret_base / d.orders_base
    d["delta"] = d.rate_recent - d.rate_base
    d["excess_returns"] = (d.delta * d.orders_recent).clip(lower=0)
    d["est_loss"] = d.excess_returns * (d.avg_ret_cost + d.avg_kept_profit)  # ESTIMATE, not verified savings
    out = d[(d.orders_recent >= min_orders) & (d.delta >= min_delta) & (d.z >= min_z)].sort_values("est_loss", ascending=False)
    return out.reset_index(drop=True), cut
def briefing(db, leaks, cut):
    if leaks.empty: return "No significant profit leaks detected this period."
    t = leaks.iloc[0]; rs = db.q(Q.reasons(t.category, t.channel, cut)); top = rs.iloc[0]
    return (f"**{len(leaks)} leak(s) found.** Biggest: **{t.category} on {t.channel}** - return rate rose from {t.rate_base:.0%} to {t.rate_recent:.0%} "
            f"in the last {max_week(db) - cut + 1} weeks. Main reason: **{top.return_reason}** "
            f"({int(top.returns)} of {int(rs.returns.sum())} returns). Estimated loss: **₹{t.est_loss:,.0f}** (estimate, not verified).")

PLAYBOOK = {"Size issue": "Fix the size chart, add fit guidance and size-based reviews; offer size exchange instead of refund.",
 "Damaged": "Audit packaging and courier handling for this category; add a quality check before dispatch.",
 "Not as described": "Review photos and descriptions; show real images and exact specs.",
 "Changed mind": "Tighten the return window or add a restocking fee on deep-discount items.",
 "RTO - refused at door": "Add OTP/WhatsApp order confirmation and nudge COD buyers to prepaid with a small incentive."}
def playbook(reason): return PLAYBOOK.get(reason, "Review this segment's recent orders and returns.")
