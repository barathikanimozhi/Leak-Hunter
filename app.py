import re
import streamlit as st, pandas as pd, altair as alt, queries as Q
from db import DB
from leakhunter import find_leaks, briefing, max_week, playbook
st.set_page_config(page_title="LeakHunter", page_icon="🕵️", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.5rem;max-width:1200px}
.hero{background:linear-gradient(120deg,#4f46e5,#0ea5a4);color:#fff;padding:26px 30px;border-radius:18px;margin-bottom:18px}
.hero h1{margin:0;font-size:2rem;color:#fff}.hero p{margin:6px 0 0;font-size:1.05rem;opacity:.95}
.hero small{opacity:.8}
.kpi{background:#fff;border-radius:14px;padding:16px 18px;box-shadow:0 2px 10px rgba(30,27,58,.07)}
.kpi .l{font-size:.8rem;color:#6b7280;text-transform:uppercase;letter-spacing:.05em}.kpi .v{font-size:1.7rem;font-weight:700}
.card{background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 2px 10px rgba(30,27,58,.07);margin-bottom:12px}
.leak{border-left:6px solid #ef4444}.good{border-left:6px solid #10b981}
.big{font-size:1.5rem;font-weight:700;color:#ef4444}.mut{color:#6b7280;font-size:.9rem}
</style>""", unsafe_allow_html=True)
@st.cache_resource
def get_db(): return DB()
db = get_db(); leaks, cut = find_leaks(db); mx = max_week(db)
st.markdown(f"""<div class="hero"><h1>🕵️ LeakHunter</h1>
<p>Online sellers can see what they <b>sold</b> but not where they <b>lose money</b>. LeakHunter finds the leak, explains why, and shows what fixing it is worth.</p>
<small>Team Lumora · ExaThon India 2026 · Track 2 · Backend: {"Exasol" if db.ex else "DuckDB demo mode"} · Data is synthetic</small></div>""", unsafe_allow_html=True)
k = db.q(Q.kpis()).iloc[0]; c = st.columns(4)
for col, (l, v) in zip(c, [("Orders", f"{int(k.orders):,}"), ("Net profit", f"₹{k.profit/1e5:,.1f} L"), ("Return rate", f"{k.return_rate:.1%}"), ("Lost to returns", f"₹{k.return_cost/1e5:,.1f} L")]):
    col.markdown(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div></div>', unsafe_allow_html=True)
st.write("")
def act(r):
    t = db.q(Q.reasons(r.category, r.channel, cut)); return playbook(t.return_reason.iloc[0]) if len(t) else playbook('')
t1, t2, t3, t4, t5 = st.tabs(["🚨 What's leaking", "🔍 Why it's happening", "📈 Trends", "💡 What if we fix it?", "🧑 Customers & products"])
with t1:
    st.markdown('<div class="card">' + re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", briefing(db, leaks, cut)) + '</div>', unsafe_allow_html=True)
    st.download_button("⬇ Download briefing (.txt)", briefing(db, leaks, cut).replace('**', ''), "leakhunter_briefing.txt")
    if not leaks.empty: st.download_button("⬇ Download leaks (.csv)", leaks.to_csv(index=False), "leakhunter_leaks.csv")
    if leaks.empty: st.success("No leaks detected.")
    for r in leaks.head(3).itertuples():
        st.markdown(f"""<div class="card leak"><b>{r.category} · {r.channel}</b><br>
        <span class="mut">Return rate</span> {r.rate_base:.0%} → <b>{r.rate_recent:.0%}</b><br>
        <span class="big">≈ ₹{r.est_loss:,.0f}</span> <span class="mut">estimated loss in the last {mx - cut + 1} weeks (estimate, not verified)</span><br>🛠 <b>Suggested action:</b> {act(r)}</div>""", unsafe_allow_html=True)
    with st.expander("How is a leak detected? (show SQL)"): st.code(Q.leaks(cut), language="sql")
with t2:
    if leaks.empty: st.info("Nothing to drill into.")
    else:
        pick = st.selectbox("Choose a leak", [f"{r.category} | {r.channel}" for r in leaks.itertuples()]); cat, ch = pick.split(" | ")
        rs = db.q(Q.reasons(cat, ch, cut)); st.subheader("Why customers returned")
        st.altair_chart(alt.Chart(rs).mark_bar(color="#ef4444", cornerRadiusEnd=6).encode(x=alt.X("returns:Q", title="Returns"), y=alt.Y("return_reason:N", sort="-x", title=None), tooltip=["return_reason", "returns", "cost"]).properties(height=220), use_container_width=True)
        with st.expander("Show the SQL behind this chart"): st.code(Q.reasons(cat, ch, cut), language="sql")
with t3:
    w = db.q(Q.weekly())
    def line(y, title, fmt, color):
        rect = alt.Chart(pd.DataFrame({"s": [cut - .5], "e": [mx + .5]})).mark_rect(opacity=.12, color="#ef4444").encode(x="s:Q", x2="e:Q")
        ln = alt.Chart(w).mark_line(point=True, color=color).encode(x=alt.X("week_no:Q", title="Week"), y=alt.Y(f"{y}:Q", title=title, axis=alt.Axis(format=fmt)))
        return (rect + ln).properties(height=260)
    a, b = st.columns(2)
    a.subheader("Return rate"); a.altair_chart(line("return_rate", "Return rate", "%", "#ef4444"), use_container_width=True)
    b.subheader("Weekly profit"); b.altair_chart(line("profit", "Profit (₹)", ",.0f", "#4f46e5"), use_container_width=True)
    st.caption("Red band = the recent weeks LeakHunter compares against the earlier baseline.")
with t4:
    pm = db.q(Q.paymode()); l, r = st.columns(2)
    l.markdown("#### Fix the top leak")
    if not leaks.empty:
        fix = l.slider("Share of the extra returns we can remove (%)", 0, 100, 50)
        l.markdown(f'<div class="card good"><span class="mut">Estimated recovery per month</span><br><span class="big" style="color:#10b981">₹{leaks.iloc[0].est_loss / (mx - cut + 1) * 4.3 * fix / 100:,.0f}</span></div>', unsafe_allow_html=True)
    r.markdown("#### Nudge COD buyers to prepaid")
    if len(pm) == 2:
        x = pm.set_index("pay_mode"); cod, pre = x.loc["COD"], x.loc["Prepaid"]
        sh = r.slider("Share of COD orders moved to prepaid (%)", 0, 50, 10)
        av = cod.orders * sh / 100 * (cod.return_rate - pre.return_rate)
        r.markdown(f'<div class="card good"><span class="mut">Returns avoided</span> <b>{av:,.0f}</b><br><span class="mut">Estimated saving</span><br><span class="big" style="color:#10b981">₹{av * cod.avg_ret_cost:,.0f}</span></div>', unsafe_allow_html=True)
        r.caption(f"COD return rate {cod.return_rate:.0%} vs prepaid {pre.return_rate:.0%}")
    st.caption("All savings are estimates from the data, not verified results.")

with t5:
    st.subheader("Worst products by return cost")
    st.dataframe(db.q(Q.products()).style.format({"return_rate": "{:.0%}", "profit": "₹{:,.0f}", "return_cost": "₹{:,.0f}"}), use_container_width=True)
    st.subheader("Do bigger discounts bring more returns?")
    dq = db.q(Q.discounts())
    st.altair_chart(alt.Chart(dq).mark_bar(color="#4f46e5", cornerRadiusEnd=6).encode(x=alt.X("band:N", sort=None, title="Discount"), y=alt.Y("return_rate:Q", axis=alt.Axis(format="%"), title="Return rate")).properties(height=240), use_container_width=True)
    st.caption("A pattern in the data, not proof of cause: other factors (channel, payment mode) also differ between bands.")
    st.subheader("Serial returners (3+ returns and at least half of orders returned)")
    sr = db.q(Q.serial())
    if sr.empty: st.info("No serial returners found.")
    else:
        m = st.columns(3); m[0].metric("Customers", f"{len(sr)}"); m[1].metric("Share of all return cost", f"{sr.return_cost.sum() / k.return_cost:.0%}"); m[2].metric("Their net profit", f"₹{sr.profit.sum():,.0f}")
        st.dataframe(sr.head(15).style.format({"profit": "₹{:,.0f}", "return_cost": "₹{:,.0f}"}), use_container_width=True)
        st.caption("Suggested action: limit free returns or COD for repeat offenders. Customer IDs are synthetic.")
