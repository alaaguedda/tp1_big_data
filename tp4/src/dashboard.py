"""Task 4: build an interactive HTML dashboard from data/higgs_clean.csv
Output: output/dashboard.html (open it in any browser)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

INPUT_FILE = "output/higgs_clean.csv"
OUTPUT_FILE = "output/dashboard.html"
HIGH_PT_TARGET = 50  # % shown on the gauge

df = pd.read_csv(INPUT_FILE, usecols=["lepton_pT", "m_bb", "pT_level", "pT_bin", "m_bb_bin"])

total_events = len(df)
avg_pt = df["lepton_pT"].mean()
avg_mbb = df["m_bb"].mean()
high_pct = (df["pT_level"] == "High").mean() * 100

by_level = df.groupby("pT_level").size().reindex(["Low", "High"]).fillna(0)
by_pt = df.groupby("pT_bin").agg(events=("m_bb", "size"), avg_mbb=("m_bb", "mean"),
                                 std_mbb=("m_bb", "std")).reset_index()
by_pt["gap"] = by_pt["avg_mbb"] - avg_mbb
by_mbb = df.groupby("m_bb_bin").agg(
    events=("lepton_pT", "size"),
    high_share=("pT_level", lambda s: (s == "High").mean() * 100)).reset_index()
cnt = df.groupby(["m_bb_bin", "pT_level"]).size().unstack(fill_value=0)
cnt = cnt.reindex(columns=["Low", "High"], fill_value=0).reindex(by_mbb["m_bb_bin"])
low_pct = cnt["Low"] / cnt.sum(axis=1) * 100
high_pct_bins = cnt["High"] / cnt.sum(axis=1) * 100

specs = [
    [{"type": "indicator"}] * 4,
    [{"type": "domain"}, {"type": "xy", "colspan": 2}, None, {"type": "indicator"}],
    [{"type": "xy", "colspan": 2}, None, {"type": "xy", "colspan": 2}, None],
    [{"type": "xy", "colspan": 2}, None, {"type": "xy"}, {"type": "domain"}],
]
titles = ["", "", "", "",
          "Events by pT level", "Low vs High pT by m_bb bin (100%)", "High pT % vs target",
          "Events per lepton pT bin", "High pT % by m_bb bin",
          "Bubbles: one circle per lepton pT bin", "Avg m_bb gap vs overall", "Events by m_bb bin"]
fig = make_subplots(rows=4, cols=4, specs=specs, subplot_titles=titles,
                    vertical_spacing=0.09, horizontal_spacing=0.06)
colors = {"Low": "#00C2FF", "High": "#FF6B9D"}

for i, (name, v, fmt, suf) in enumerate([
        ("Total events", total_events, ",.0f", ""), ("Avg lepton pT", avg_pt, ".3f", ""),
        ("Avg m_bb", avg_mbb, ".3f", ""), ("High pT %", high_pct, ".1f", "%")], start=1):
    fig.add_trace(go.Indicator(mode="number", value=v, title={"text": name},
                               number={"valueformat": fmt, "suffix": suf}), row=1, col=i)

fig.add_trace(go.Pie(labels=by_level.index, values=by_level.values, hole=0.6,
                     marker={"colors": [colors[k] for k in by_level.index]}), row=2, col=1)
xl = by_mbb["m_bb_bin"].astype(str)
fig.add_trace(go.Bar(x=xl, y=low_pct, name="Low pT", marker_color=colors["Low"]), row=2, col=2)
fig.add_trace(go.Bar(x=xl, y=high_pct_bins, name="High pT", marker_color=colors["High"]), row=2, col=2)
fig.add_trace(go.Indicator(mode="gauge+number", value=high_pct, number={"suffix": "%"},
              gauge={"axis": {"range": [0, 100]}, "bar": {"color": colors["High"]},
                     "threshold": {"line": {"color": "white", "width": 4}, "value": HIGH_PT_TARGET}}),
              row=2, col=4)
fig.add_trace(go.Bar(x=by_pt["pT_bin"].astype(str), y=by_pt["events"], marker_color="#7C5CFF",
                     showlegend=False), row=3, col=1)
fig.add_trace(go.Scatter(x=by_mbb["m_bb_bin"], y=by_mbb["high_share"], mode="lines+markers",
                         line={"color": colors["High"], "width": 3}, showlegend=False), row=3, col=3)
fig.add_trace(go.Scatter(x=by_pt["avg_mbb"], y=by_pt["std_mbb"], mode="markers", showlegend=False,
              marker={"size": by_pt["events"], "sizemode": "area",
                      "sizeref": 2.0 * by_pt["events"].max() / (50.0 ** 2), "sizemin": 4,
                      "color": by_pt["pT_bin"], "colorscale": "Turbo", "opacity": 0.8}), row=4, col=1)
fig.add_trace(go.Bar(y=by_pt["pT_bin"].astype(str), x=by_pt["gap"], orientation="h", showlegend=False,
                     marker_color=np.where(by_pt["gap"] >= 0, "#2ECC71", "#E74C3C")), row=4, col=3)
fig.add_trace(go.Treemap(labels=[f"{b:.2f}+" for b in by_mbb["m_bb_bin"]], parents=[""] * len(by_mbb),
                         values=by_mbb["events"], textinfo="label+percent root"), row=4, col=4)

fig.update_layout(template="plotly_dark", height=1500, barmode="stack",
                  title={"text": "HIGGS sample dashboard", "x": 0.5},
                  legend={"orientation": "h", "y": 1.02, "x": 0.5, "xanchor": "center"})
fig.write_html(OUTPUT_FILE)
fig.write_html("output/index.html")
print(f"Rows used: {total_events:,} | Avg lepton pT {avg_pt:.3f} | Avg m_bb {avg_mbb:.3f} | High pT {high_pct:.1f}%")
print(f"Saved {OUTPUT_FILE}")
