import pandas as pd 
import numpy as np 
from datetime import date

# ── PORTFOLIO CONSTRUCTION ─────────────────────────────────────────────────────

# Valuation date (today)
VALUATION_DATE = date.today()

# Bond holdings
bonds = [
    {
        "bond_id":      "UST-2Y",
        "issuer":       "US Treasury",
        "face_value":   1_000_000,
        "coupon_rate":  0.0450,       # 4.50%
        "maturity":     date(2027, 3, 31),
        "ytm":          0.0442,       # Yield to Maturity
        "credit_rating":"AAA",
        "sector":       "Government",
        "quantity":     10            # number of bonds held
    },
    {
        "bond_id":      "UST-10Y",
        "issuer":       "US Treasury",
        "face_value":   1_000_000,
        "coupon_rate":  0.0425,
        "maturity":     date(2035, 3, 31),
        "ytm":          0.0438,
        "credit_rating":"AAA",
        "sector":       "Government",
        "quantity":     8
    },
    {
        "bond_id":      "CORP-JPM-5Y",
        "issuer":       "JPMorgan Chase",
        "face_value":   1_000_000,
        "coupon_rate":  0.0510,
        "maturity":     date(2030, 6, 30),
        "ytm":          0.0525,
        "credit_rating":"A",
        "sector":       "Financial",
        "quantity":     5
    },
    {
        "bond_id":      "CORP-MSFT-7Y",
        "issuer":       "Microsoft",
        "face_value":   1_000_000,
        "coupon_rate":  0.0390,
        "maturity":     date(2032, 9, 30),
        "ytm":          0.0405,
        "credit_rating":"AAA",
        "sector":       "Technology",
        "quantity":     6
    },
    {
        "bond_id":      "MUNI-NYC-8Y",
        "issuer":       "NYC Municipal",
        "face_value":   1_000_000,
        "coupon_rate":  0.0320,
        "maturity":     date(2033, 12, 31),
        "ytm":          0.0335,
        "credit_rating":"AA",
        "sector":       "Municipal",
        "quantity":     4
    },
]

# ── BUILD DATAFRAME ────────────────────────────────────────────────────────────

df = pd.DataFrame(bonds)

# Time to maturity in years (from valuation date)
df["years_to_maturity"] = df["maturity"].apply(
    lambda m: round((m - VALUATION_DATE).days / 365.25, 2)
)

# Dirty price approximation (par assumption for simplicity)
# In practice this would come from a pricing model or market feed
df["price_per_bond"] = df.apply(
    lambda row: round(
        sum([
            (row["coupon_rate"] * row["face_value"]) / (1 + row["ytm"]) ** t
            for t in range(1, int(row["years_to_maturity"]) + 1)
        ]) + row["face_value"] / (1 + row["ytm"]) ** row["years_to_maturity"],
        2
    ),
    axis=1
)

# Market value per position
df["market_value"] = df["price_per_bond"] * df["quantity"]

# Portfolio weight
total_portfolio_value = df["market_value"].sum()
df["weight"] = round(df["market_value"] / total_portfolio_value, 4)

# ── DISPLAY ────────────────────────────────────────────────────────────────────

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

print(f"VALUATION DATE: {VALUATION_DATE}")
print(f"TOTAL PORTFOLIO VALUE: ${total_portfolio_value:,.2f}\n")
print(df[[
    "bond_id", "issuer", "sector", "credit_rating",
    "years_to_maturity", "price_per_bond", "market_value", "weight"
]].to_string(index=False))

# ── MODULE 2: RISK & PERFORMANCE ENGINE ───────────────────────────────────────

# ── MODIFIED DURATION (per bond) ──────────────────────────────────────────────
# Modified Duration = Macaulay Duration / (1 + YTM)
# Macaulay Duration = weighted average time to receive cash flows

def macaulay_duration(coupon_rate, face_value, ytm, years_to_maturity):
    periods = max(1, int(round(years_to_maturity)))
    coupon = coupon_rate * face_value
    
    times        = np.arange(1, periods + 1)
    cash_flows   = np.full(periods, coupon, dtype=float)
    cash_flows[-1] += face_value                          # add principal at maturity
    
    discount_factors = (1 + ytm) ** times
    pv_cash_flows    = cash_flows / discount_factors
    
    total_pv         = pv_cash_flows.sum()
    mac_duration     = (times * pv_cash_flows).sum() / total_pv
    return round(mac_duration, 4)

def modified_duration(mac_dur, ytm):
    return round(mac_dur / (1 + ytm), 4)

df["macaulay_duration"] = df.apply(
    lambda row: macaulay_duration(
        row["coupon_rate"], row["face_value"], row["ytm"], row["years_to_maturity"]
    ), axis=1
)

df["modified_duration"] = df.apply(
    lambda row: modified_duration(row["macaulay_duration"], row["ytm"]),
    axis=1
)

# ── PORTFOLIO-LEVEL WEIGHTED METRICS ──────────────────────────────────────────

portfolio_duration = (df["modified_duration"] * df["weight"]).sum()
portfolio_ytm      = (df["ytm"] * df["weight"]).sum()
portfolio_coupon   = (df["coupon_rate"] * df["weight"]).sum()

# ── DV01: DOLLAR VALUE OF A BASIS POINT ───────────────────────────────────────
# DV01 = Market Value × Modified Duration × 0.0001
# Tells you how much the portfolio loses in $ if rates rise by 1 basis point

df["dv01"] = df["market_value"] * df["modified_duration"] * 0.0001
portfolio_dv01 = df["dv01"].sum()

# ── SECTOR CONCENTRATION ──────────────────────────────────────────────────────

sector_allocation = (
    df.groupby("sector")["market_value"]
    .sum()
    .div(total_portfolio_value)
    .round(4)
    .reset_index()
    .rename(columns={"market_value": "allocation"})
    .sort_values("allocation", ascending=False)
)

# ── CREDIT QUALITY BREAKDOWN ──────────────────────────────────────────────────

credit_allocation = (
    df.groupby("credit_rating")["market_value"]
    .sum()
    .div(total_portfolio_value)
    .round(4)
    .reset_index()
    .rename(columns={"market_value": "allocation"})
    .sort_values("allocation", ascending=False)
)

# ── DISPLAY ───────────────────────────────────────────────────────────────────

print("=" * 65)
print("FIXED INCOME PORTFOLIO — RISK & PERFORMANCE SUMMARY")
print("=" * 65)

print(f"\n{'PORTFOLIO-LEVEL METRICS':}")
print(f"  Total Market Value   : ${total_portfolio_value:>15,.2f}")
print(f"  Weighted Avg YTM     : {portfolio_ytm*100:>10.3f}%")
print(f"  Weighted Avg Coupon  : {portfolio_coupon*100:>10.3f}%")
print(f"  Portfolio Duration   : {portfolio_duration:>10.4f} years")
print(f"  Portfolio DV01       : ${portfolio_dv01:>15,.2f}")

print(f"\n{'POSITION-LEVEL DURATION & RISK':}")
print(df[[
    "bond_id", "modified_duration", "macaulay_duration", "dv01", "weight"
]].to_string(index=False))

print(f"\n{'SECTOR ALLOCATION':}")
for _, row in sector_allocation.iterrows():
    bar = "█" * int(row["allocation"] * 40)
    print(f"  {row['sector']:<12} {row['allocation']*100:>6.2f}%  {bar}")

print(f"\n{'CREDIT QUALITY BREAKDOWN':}")
for _, row in credit_allocation.iterrows():
    bar = "█" * int(row["allocation"] * 40)
    print(f"  {row['credit_rating']:<6} {row['allocation']*100:>6.2f}%  {bar}")


# ── MODULE 3: SURVEILLANCE & COMPLIANCE FLAGGING ENGINE ───────────────────────

# ── DEFINE MANDATE LIMITS ─────────────────────────────────────────────────────
# These represent the investment policy statement (IPS) constraints
# In a real mandate these come from the client agreement

MANDATE_LIMITS = {
    "max_portfolio_duration"     : 5.0,    # years
    "min_portfolio_duration"     : 2.0,    # years
    "max_single_position_weight" : 0.35,   # 35% max in any one bond
    "max_sector_concentration"   : 0.50,   # 50% max in any one sector
    "min_credit_quality_aaa_aa"  : 0.60,   # min 60% must be AAA or AA rated
    "max_dv01_per_position"      : 6000,   # $ max DV01 for any single bond
    "min_ytm"                    : 0.030,  # portfolio YTM must exceed 3%
}

flags = []   # collects all breach records

# ── CHECK 1: PORTFOLIO DURATION ───────────────────────────────────────────────

if portfolio_duration > MANDATE_LIMITS["max_portfolio_duration"]:
    flags.append({
        "check"    : "Portfolio Duration",
        "status"   : "⚠ BREACH",
        "detail"   : f"Duration {portfolio_duration:.2f}y exceeds max {MANDATE_LIMITS['max_portfolio_duration']}y"
    })
elif portfolio_duration < MANDATE_LIMITS["min_portfolio_duration"]:
    flags.append({
        "check"    : "Portfolio Duration",
        "status"   : "⚠ BREACH",
        "detail"   : f"Duration {portfolio_duration:.2f}y below min {MANDATE_LIMITS['min_portfolio_duration']}y"
    })
else:
    flags.append({
        "check"    : "Portfolio Duration",
        "status"   : "✓ PASS",
        "detail"   : f"Duration {portfolio_duration:.2f}y within [{MANDATE_LIMITS['min_portfolio_duration']}y – {MANDATE_LIMITS['max_portfolio_duration']}y]"
    })

# ── CHECK 2: SINGLE POSITION WEIGHT ──────────────────────────────────────────

for _, row in df.iterrows():
    if row["weight"] > MANDATE_LIMITS["max_single_position_weight"]:
        flags.append({
            "check"  : f"Position Concentration [{row['bond_id']}]",
            "status" : "⚠ BREACH",
            "detail" : f"Weight {row['weight']*100:.2f}% exceeds max {MANDATE_LIMITS['max_single_position_weight']*100:.0f}%"
        })
    else:
        flags.append({
            "check"  : f"Position Concentration [{row['bond_id']}]",
            "status" : "✓ PASS",
            "detail" : f"Weight {row['weight']*100:.2f}% within limit"
        })

# ── CHECK 3: SECTOR CONCENTRATION ────────────────────────────────────────────

for _, row in sector_allocation.iterrows():
    if row["allocation"] > MANDATE_LIMITS["max_sector_concentration"]:
        flags.append({
            "check"  : f"Sector Concentration [{row['sector']}]",
            "status" : "⚠ BREACH",
            "detail" : f"Allocation {row['allocation']*100:.2f}% exceeds max {MANDATE_LIMITS['max_sector_concentration']*100:.0f}%"
        })
    else:
        flags.append({
            "check"  : f"Sector Concentration [{row['sector']}]",
            "status" : "✓ PASS",
            "detail" : f"Allocation {row['allocation']*100:.2f}% within limit"
        })

# ── CHECK 4: CREDIT QUALITY FLOOR ────────────────────────────────────────────

aaa_aa_weight = df[df["credit_rating"].isin(["AAA", "AA"])]["weight"].sum()

if aaa_aa_weight < MANDATE_LIMITS["min_credit_quality_aaa_aa"]:
    flags.append({
        "check"  : "Credit Quality (AAA+AA floor)",
        "status" : "⚠ BREACH",
        "detail" : f"AAA+AA = {aaa_aa_weight*100:.2f}%, below min {MANDATE_LIMITS['min_credit_quality_aaa_aa']*100:.0f}%"
    })
else:
    flags.append({
        "check"  : "Credit Quality (AAA+AA floor)",
        "status" : "✓ PASS",
        "detail" : f"AAA+AA = {aaa_aa_weight*100:.2f}%, above min {MANDATE_LIMITS['min_credit_quality_aaa_aa']*100:.0f}%"
    })

# ── CHECK 5: DV01 PER POSITION ────────────────────────────────────────────────

for _, row in df.iterrows():
    if row["dv01"] > MANDATE_LIMITS["max_dv01_per_position"]:
        flags.append({
            "check"  : f"DV01 Limit [{row['bond_id']}]",
            "status" : "⚠ BREACH",
            "detail" : f"DV01 ${row['dv01']:,.2f} exceeds max ${MANDATE_LIMITS['max_dv01_per_position']:,}"
        })
    else:
        flags.append({
            "check"  : f"DV01 Limit [{row['bond_id']}]",
            "status" : "✓ PASS",
            "detail" : f"DV01 ${row['dv01']:,.2f} within limit"
        })

# ── CHECK 6: MINIMUM PORTFOLIO YTM ───────────────────────────────────────────

if portfolio_ytm < MANDATE_LIMITS["min_ytm"]:
    flags.append({
        "check"  : "Minimum Portfolio YTM",
        "status" : "⚠ BREACH",
        "detail" : f"YTM {portfolio_ytm*100:.3f}% below floor {MANDATE_LIMITS['min_ytm']*100:.1f}%"
    })
else:
    flags.append({
        "check"  : "Minimum Portfolio YTM",
        "status" : "✓ PASS",
        "detail" : f"YTM {portfolio_ytm*100:.3f}% above floor {MANDATE_LIMITS['min_ytm']*100:.1f}%"
    })

# ── DISPLAY SURVEILLANCE REPORT ───────────────────────────────────────────────

flags_df = pd.DataFrame(flags)
breaches = flags_df[flags_df["status"] == "⚠ BREACH"]
passes   = flags_df[flags_df["status"] == "✓ PASS"]

print("=" * 65)
print("PORTFOLIO SURVEILLANCE REPORT")
print(f"Valuation Date : {VALUATION_DATE}")
print(f"Total Checks   : {len(flags_df)}")
print(f"Breaches       : {len(breaches)}")
print(f"Passes         : {len(passes)}")
print("=" * 65)

print("\n── BREACHES ──────────────────────────────────────────────────")
if breaches.empty:
    print("  No breaches detected.")
else:
    for _, row in breaches.iterrows():
        print(f"  {row['status']}  {row['check']}")
        print(f"           → {row['detail']}")

print("\n── PASSING CHECKS ────────────────────────────────────────────")
for _, row in passes.iterrows():
    print(f"  {row['status']}  {row['check']}")
    print(f"           → {row['detail']}")

print("\n" + "=" * 65)
print(f"SURVEILLANCE STATUS: {'ALL CLEAR ✓' if breaches.empty else f'{len(breaches)} BREACH(ES) REQUIRE ATTENTION ⚠'}")
print("=" * 65)


# ── MODULE 4: VISUAL DASHBOARD ────────────────────────────────────────────────

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")

# ── COLOUR SCHEME ─────────────────────────────────────────────────────────────

PASS_COLOR   = "#2ecc71"
BREACH_COLOR = "#e74c3c"
BLUE_PALETTE = ["#1a3a5c", "#2e6da4", "#4a9fd4", "#7abde8", "#b0d9f5"]
BG_COLOR     = "#f7f9fc"
PANEL_COLOR  = "#ffffff"

fig = plt.figure(figsize=(18, 14), facecolor=BG_COLOR)
fig.suptitle(
    f"Fixed Income Portfolio Monitor  |  Valuation Date: {VALUATION_DATE}",
    fontsize=16, fontweight="bold", color="#1a3a5c", y=0.98
)

gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# ── PANEL 1: KPI SCORECARD (top left, spans 2 columns) ───────────────────────

ax_kpi = fig.add_subplot(gs[0, :2])
ax_kpi.set_facecolor(PANEL_COLOR)
ax_kpi.axis("off")

kpis = [
    ("Total Portfolio Value", f"${total_portfolio_value/1e6:.2f}M"),
    ("Weighted Avg YTM",      f"{portfolio_ytm*100:.3f}%"),
    ("Portfolio Duration",    f"{portfolio_duration:.2f} yrs"),
    ("Portfolio DV01",        f"${portfolio_dv01:,.0f}"),
    ("AAA / AA Weight",       f"{aaa_aa_weight*100:.1f}%"),
]

for i, (label, value) in enumerate(kpis):
    x = 0.05 + i * 0.19
    ax_kpi.add_patch(mpatches.FancyBboxPatch(
        (x, 0.15), 0.16, 0.70,
        boxstyle="round,pad=0.02",
        facecolor="#1a3a5c", edgecolor="none"
    ))
    ax_kpi.text(x + 0.08, 0.72, label, ha="center", va="center",
                fontsize=7.5, color="#b0d9f5", fontweight="bold",
                transform=ax_kpi.transAxes)
    ax_kpi.text(x + 0.08, 0.42, value, ha="center", va="center",
                fontsize=13, color="white", fontweight="bold",
                transform=ax_kpi.transAxes)

ax_kpi.set_title("Portfolio KPI Scorecard", fontsize=11,
                 fontweight="bold", color="#1a3a5c", pad=10)

# ── PANEL 2: SURVEILLANCE STATUS (top right) ─────────────────────────────────

ax_sur = fig.add_subplot(gs[0, 2])
ax_sur.set_facecolor(PANEL_COLOR)
ax_sur.axis("off")

total_checks  = len(flags_df)
n_breaches    = len(breaches)
n_passes      = len(passes)
pass_rate     = n_passes / total_checks * 100

ax_sur.add_patch(mpatches.FancyBboxPatch(
    (0.05, 0.55), 0.90, 0.35,
    boxstyle="round,pad=0.03",
    facecolor=BREACH_COLOR if n_breaches else PASS_COLOR,
    edgecolor="none", transform=ax_sur.transAxes
))
status_text = f"{n_breaches} BREACH" if n_breaches else "ALL CLEAR"
ax_sur.text(0.50, 0.73, status_text, ha="center", va="center",
            fontsize=14, color="white", fontweight="bold",
            transform=ax_sur.transAxes)

ax_sur.text(0.50, 0.42, f"{n_passes} / {total_checks} checks passed",
            ha="center", fontsize=10, color="#1a3a5c",
            transform=ax_sur.transAxes)
ax_sur.text(0.50, 0.28, f"Pass Rate: {pass_rate:.1f}%",
            ha="center", fontsize=9, color="#555",
            transform=ax_sur.transAxes)

ax_sur.set_title("Surveillance Status", fontsize=11,
                 fontweight="bold", color="#1a3a5c", pad=10)

# ── PANEL 3: SECTOR ALLOCATION PIE ───────────────────────────────────────────

ax_sec = fig.add_subplot(gs[1, 0])
ax_sec.set_facecolor(PANEL_COLOR)

sector_labels  = sector_allocation["sector"].tolist()
sector_values  = sector_allocation["allocation"].tolist()
explode        = [0.05] * len(sector_labels)

wedges, texts, autotexts = ax_sec.pie(
    sector_values, labels=sector_labels, autopct="%1.1f%%",
    colors=BLUE_PALETTE[:len(sector_labels)],
    explode=explode, startangle=140,
    textprops={"fontsize": 8}
)
for at in autotexts:
    at.set_color("white")
    at.set_fontweight("bold")

ax_sec.set_title("Sector Allocation", fontsize=11,
                 fontweight="bold", color="#1a3a5c", pad=10)

# ── PANEL 4: CREDIT QUALITY BAR ───────────────────────────────────────────────

ax_cred = fig.add_subplot(gs[1, 1])
ax_cred.set_facecolor(PANEL_COLOR)

credit_labels = credit_allocation["credit_rating"].tolist()
credit_values = [v * 100 for v in credit_allocation["allocation"].tolist()]
colors_credit = [PASS_COLOR if r in ["AAA", "AA"] else "#f39c12"
                 for r in credit_labels]

bars = ax_cred.bar(credit_labels, credit_values,
                   color=colors_credit, width=0.5, edgecolor="white")
ax_cred.set_ylabel("Portfolio Weight (%)", fontsize=8, color="#555")
ax_cred.set_ylim(0, 100)
ax_cred.axhline(
    MANDATE_LIMITS["min_credit_quality_aaa_aa"] * 100,
    color="#e74c3c", linestyle="--", linewidth=1.2,
    label=f"Min AAA+AA floor ({MANDATE_LIMITS['min_credit_quality_aaa_aa']*100:.0f}%)"
)
ax_cred.legend(fontsize=7)
for bar, val in zip(bars, credit_values):
    ax_cred.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1.5,
                 f"{val:.1f}%", ha="center", fontsize=8,
                 color="#1a3a5c", fontweight="bold")
ax_cred.set_title("Credit Quality Breakdown", fontsize=11,
                  fontweight="bold", color="#1a3a5c", pad=10)
ax_cred.tick_params(labelsize=8)

# ── PANEL 5: MODIFIED DURATION BY POSITION ────────────────────────────────────

ax_dur = fig.add_subplot(gs[1, 2])
ax_dur.set_facecolor(PANEL_COLOR)

dur_colors = [BREACH_COLOR if d > MANDATE_LIMITS["max_portfolio_duration"]
              else "#2e6da4" for d in df["modified_duration"]]

ax_dur.barh(df["bond_id"], df["modified_duration"],
            color=dur_colors, edgecolor="white")
ax_dur.axvline(portfolio_duration, color="#1a3a5c",
               linestyle="--", linewidth=1.2,
               label=f"Portfolio Avg: {portfolio_duration:.2f}y")
ax_dur.set_xlabel("Modified Duration (years)", fontsize=8, color="#555")
ax_dur.legend(fontsize=7)
ax_dur.set_title("Duration by Position", fontsize=11,
                 fontweight="bold", color="#1a3a5c", pad=10)
ax_dur.tick_params(labelsize=8)

# ── PANEL 6: DV01 BY POSITION ─────────────────────────────────────────────────

ax_dv = fig.add_subplot(gs[2, 0])
ax_dv.set_facecolor(PANEL_COLOR)

dv01_colors = [BREACH_COLOR if d > MANDATE_LIMITS["max_dv01_per_position"]
               else "#4a9fd4" for d in df["dv01"]]

ax_dv.bar(df["bond_id"], df["dv01"],
          color=dv01_colors, edgecolor="white", width=0.5)
ax_dv.axhline(MANDATE_LIMITS["max_dv01_per_position"],
              color=BREACH_COLOR, linestyle="--", linewidth=1.2,
              label=f"Max DV01 limit: ${MANDATE_LIMITS['max_dv01_per_position']:,}")
ax_dv.set_ylabel("DV01 ($)", fontsize=8, color="#555")
ax_dv.legend(fontsize=7)
ax_dv.set_title("DV01 by Position", fontsize=11,
                fontweight="bold", color="#1a3a5c", pad=10)
ax_dv.tick_params(axis="x", rotation=20, labelsize=7)
ax_dv.tick_params(axis="y", labelsize=8)

# ── PANEL 7: SECTOR CONCENTRATION VS LIMIT ───────────────────────────────────

ax_slim = fig.add_subplot(gs[2, 1])
ax_slim.set_facecolor(PANEL_COLOR)

s_labels = sector_allocation["sector"].tolist()
s_values = [v * 100 for v in sector_allocation["allocation"].tolist()]
s_colors = [BREACH_COLOR if v > MANDATE_LIMITS["max_sector_concentration"] * 100
            else PASS_COLOR for v in s_values]

ax_slim.barh(s_labels, s_values, color=s_colors, edgecolor="white")
ax_slim.axvline(
    MANDATE_LIMITS["max_sector_concentration"] * 100,
    color=BREACH_COLOR, linestyle="--", linewidth=1.2,
    label=f"Max limit: {MANDATE_LIMITS['max_sector_concentration']*100:.0f}%"
)
ax_slim.set_xlabel("Allocation (%)", fontsize=8, color="#555")
ax_slim.legend(fontsize=7)
ax_slim.set_title("Sector Concentration vs Limit", fontsize=11,
                  fontweight="bold", color="#1a3a5c", pad=10)
ax_slim.tick_params(labelsize=8)

# ── PANEL 8: PORTFOLIO COMPOSITION BY MARKET VALUE ───────────────────────────

ax_mv = fig.add_subplot(gs[2, 2])
ax_mv.set_facecolor(PANEL_COLOR)

ax_mv.bar(df["bond_id"], df["market_value"] / 1e6,
          color=BLUE_PALETTE[:len(df)], edgecolor="white", width=0.5)
ax_mv.set_ylabel("Market Value ($M)", fontsize=8, color="#555")
ax_mv.set_title("Market Value by Position", fontsize=11,
                fontweight="bold", color="#1a3a5c", pad=10)
ax_mv.tick_params(axis="x", rotation=20, labelsize=7)
ax_mv.tick_params(axis="y", labelsize=8)

for ax in fig.get_axes():
    ax.set_facecolor(PANEL_COLOR)
    for spine in ax.spines.values():
        spine.set_edgecolor("#e0e0e0")

plt.savefig("portfolio_monitor_dashboard.png",
            dpi=150, bbox_inches="tight",
            facecolor=BG_COLOR)
plt.show()
print("\nDashboard saved as: portfolio_monitor_dashboard.png")
