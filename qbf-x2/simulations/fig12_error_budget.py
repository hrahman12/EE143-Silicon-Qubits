"""Figure 12: the CZ gate error budget, split by source, for three launch cases.

Reads results/D_launcher.json (written by D_launcher.py) and draws one stacked bar per case:
a thermal fluxon source, the coherent launcher as designed, and the launcher as drawn
(inductances extracted from the drawn differential layout). Nothing is re-simulated here.
"""
from __future__ import annotations

from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path
from matplotlib.transforms import blended_transform_factory

from _common import load_json, plt, savefig

D = load_json("D_launcher.json")
CASES = [  # top to bottom: (name, detail, budget)
    ("Thermal fluxon source", "", D["budget_thermal_source"]),
    ("Coherent launcher, as designed", "", D["budget_launcher"]),
    ("Coherent launcher, as drawn", "post-layout · ", D["post_layout"]["budget"]),
]
# Stack order: disorder sits on the baseline because it is the term the launcher changes.
TERMS = [
    ("Disorder\ndephasing", "#1d4ed8", lambda p: p["disorder_dephasing"]),
    ("Damping", "#c2410c", lambda p: p["damping"]),
    ("Collision\nitself", "#7c3aed", lambda p: p.get("gate_thermal", 0.0) + p.get("launched_packet_2D", 0.0)),
]
INK, INK2, GRID, AXIS = "#191919", "#666666", "#e6e6e6", "#c8c8c8"

W, H, DPI = 10.3, 4.6, 150
fig = plt.figure(figsize=(W, H), dpi=DPI, layout="none")
AX_L, AX_R, AX_B, AX_T = 2.60, 6.90, 1.10, 3.28           # axes box, inches
COLS = [7.90, 8.90, 9.90]                                  # table columns (right edges), inches
ax = fig.add_axes([AX_L / W, AX_B / H, (AX_R - AX_L) / W, (AX_T - AX_B) / H])
XMAX, YLO, YHI = 2.8, -0.6, 2.6
ax.set_xlim(0, XMAX)
ax.set_ylim(YLO, YHI)
ax.grid(False)
ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0, 2.5])
ax.set_xticklabels(["0", "0.5", "1.0", "1.5", "2.0", "2.5"], color=INK2, fontsize=8.5)
for x in ax.get_xticks():
    ax.axvline(x, color=GRID, lw=0.8, zorder=0)
ax.set_yticks([])
for side in ("left", "top", "right"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(AXIS)
ax.spines["bottom"].set_linewidth(0.8)
ax.tick_params(axis="x", color=AXIS, length=3, width=0.8)
ax.set_xlabel("average gate infidelity (%)", color=INK2, fontsize=8.5, labelpad=5)

# pixel <-> data scale (figure dpi equals savefig dpi, so these are output pixels)
px_x = (AX_R - AX_L) * DPI / XMAX
px_y = (AX_T - AX_B) * DPI / (YHI - YLO)
BAR_H = 22 / px_y            # 22 px thick, under the 24 px cap
GAP = 2 / px_x               # 2 px surface gap between segments
RX, RY = 4 / px_x, 4 / px_y  # 4 px rounded data end (circular on screen)
K = 0.5523                   # cubic Bezier circle constant


def bar(x0, x1, yc, color, round_end):
    y0, y1 = yc - BAR_H / 2, yc + BAR_H / 2
    if not round_end:
        verts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        codes = [Path.MOVETO] + [Path.LINETO] * 3 + [Path.CLOSEPOLY]
    else:
        rx = min(RX, x1 - x0)
        verts = [(x0, y0), (x1 - rx, y0), (x1 - rx + K * rx, y0), (x1, y0 + RY - K * RY), (x1, y0 + RY),
                 (x1, y1 - RY), (x1, y1 - RY + K * RY), (x1 - rx + K * rx, y1), (x1 - rx, y1),
                 (x0, y1), (x0, y0)]
        codes = [Path.MOVETO, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                 Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none", zorder=3))


label_tf = blended_transform_factory(fig.dpi_scale_trans, ax.transData)   # x in inches, y in data
for (name, detail, bud), yc in zip(CASES, [2, 1, 0]):
    parts = bud["parts"]
    vals = [f(parts) * 100 for _, _, f in TERMS]
    drawn = [i for i, v in enumerate(vals) if v * px_x > 1.0]      # a part under 1 px draws nothing
    x = 0.0
    for i, v in enumerate(vals):
        if i in drawn:
            left = x + (GAP / 2 if x > 0 else 0)
            right = x + v - (GAP / 2 if i != drawn[-1] else 0)
            bar(left, right, yc, TERMS[i][1], round_end=(i == drawn[-1]))
        x += v
    total = bud["total"] * 100
    ax.text(total + 7 / px_x, yc, f"{total:.2f} %", ha="left", va="center", fontsize=9.5, fontweight="bold",
            color=INK, zorder=5, bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none"))
    spread = bud["velocity_spread_rel"] * 100
    ax.text(AX_L - 0.14, yc + 0.03, name, transform=label_tf, ha="right", va="bottom", fontsize=9.5, color=INK)
    ax.text(AX_L - 0.14, yc - 0.03, f"{detail}speed spread {spread:.1f} %", transform=label_tf,
            ha="right", va="top", fontsize=8, color=INK2)
    for j, v in enumerate(vals):                                   # table twin, right of the plot
        s = "<0.01" if v < 0.005 else f"{v:.2f}"
        ax.text(COLS[j], yc, s, transform=label_tf, ha="right", va="center", fontsize=9, color=INK)

# 1 % target, labelled inside the plot above the top bar
ax.axvline(1.0, color="#8a8a8a", lw=0.9, ls=(0, (4, 3)), zorder=1)
ax.text(1.0 + 5 / px_x, 2.42, "1 % target", ha="left", va="center", fontsize=8, color=INK2, zorder=5,
        bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none"))

# legend row above the plot, in stack order; table headers on the same line
r = fig.canvas.get_renderer()
LEG_Y = AX_T + 0.20
xl = AX_L
for lab, col, _ in TERMS:
    fig.add_artist(FancyBboxPatch((xl, LEG_Y - 0.06), 0.12, 0.12, boxstyle="round,pad=0,rounding_size=0.025",
                                  transform=fig.dpi_scale_trans, facecolor=col, edgecolor="none"))
    t = fig.text((xl + 0.18) / W, LEG_Y / H, lab.replace("\n", " "), ha="left", va="center", fontsize=8.5, color=INK)
    xl += 0.18 + t.get_window_extent(r).width / DPI + 0.32
for j, (lab, _, _) in enumerate(TERMS):
    fig.text(COLS[j] / W, LEG_Y / H, lab.split("\n")[0], ha="right", va="center", fontsize=8.5, color=INK2)
fig.text(COLS[-1] / W, (AX_B - 0.22) / H, "breakdown, % infidelity", ha="right", va="top", fontsize=7.5, color=INK2)

ratio = CASES[0][2]["total"] / CASES[1][2]["total"]
fig.text(0.18 / W, 1 - 0.32 / H, "Error budget of the fluxon-collision CZ gate", ha="left", va="baseline",
         fontsize=12, fontweight="bold", color=INK)
fig.text(0.18 / W, 1 - 0.50 / H,
         f"Simulated gate infidelity by source. The coherent launcher narrows the fluxon speed spread and cuts the "
         f"error {ratio:.0f}×.\nWith the launcher as drawn (inductances extracted from the layout) the gate still "
         f"comes in under the 1 % target.",
         ha="left", va="top", fontsize=8.8, color=INK2, linespacing=1.4)
fig.text(0.18 / W, 0.10 / H,
         "Simulated, not measured. Model: 374 dual-rail cells per rail, 2 % fabrication spread in E_J, E_L and C, "
         "20 mK, sub-gap damping α = 2×10⁻⁶, 10 ps launch jitter.\n'Collision' is the exact 2D gate error with "
         "the launched wavepackets. Timing and coupler terms are below 10⁻⁵ and not drawn. "
         "Data: results/D_launcher.json.",
         ha="left", va="bottom", fontsize=7.3, color=INK2, linespacing=1.4)

savefig(fig, "fig12_error_budget.png")
