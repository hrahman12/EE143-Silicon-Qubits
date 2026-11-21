"""Build every figure in figures/final/ from figures/raw/ (crops) and from code (original diagrams).

Run from the repo root:  python3 figures/src/make_figures.py
Original diagrams use ONLY numbers from REFERENCES.md "Key numbers" (or pure geometry / the p^n and
Poisson formulas that the Key numbers themselves quote). Everything is labelled schematic / model.
"""
import os, math
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon, FancyArrowPatch, Ellipse, FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = "figures/final"; RAW = "figures/raw"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": 11, "axes.edgecolor": "#1F2A36",
                     "text.color": "#1F2A36", "axes.labelcolor": "#1F2A36", "xtick.color": "#1F2A36",
                     "ytick.color": "#1F2A36", "savefig.dpi": 300})
INK, MUTED = "#1F2A36", "#5B6770"
P_C, AS_C = "#D9731A", "#0F9FA0"
SI, CAP, HR, AL, OX = "#8C96A0", "#C9D1D8", "#9CC8E6", "#5E6A75", "#E3DDF0"
SI_ATOM, H_ATOM, TIP = "#A3ACB5", "#9CC8E6", "#D4A93C"

def save(fig, name, transparent=False):
    fig.savefig(f"{OUT}/{name}", bbox_inches="tight", pad_inches=0.04, transparent=transparent, facecolor="white")
    plt.close(fig); print("wrote", name)

# --------------------------------------------------------------------------------------------
# 1. Crops of CC BY published figures (F-figures). Boxes are fractions (x0, y0, x1, y1).
# --------------------------------------------------------------------------------------------
CROPS = [
 ("F1_stock2024_fig1_2x2.png", f"{RAW}/Stock2024/pdfimg/p3_x27_2050x1929.jpeg", (0.0, 0.0, 0.197, 0.475)),
 ("F1_stock2024_fig1_4x4.png", f"{RAW}/Stock2024/pdfimg/p3_x27_2050x1929.jpeg", (0.488, 0.497, 1.0, 1.0)),
 ("F2_stock2024_fig3_ae.png", f"{RAW}/Stock2024/pdfimg/p8_x115_2050x1507.jpeg", (0.0, 0.0, 0.585, 0.33)),
 ("F2_stock2024_fig3_stats.png", f"{RAW}/Stock2024/pdfimg/p8_x115_2050x1507.jpeg", (0.6, 0.608, 1.0, 0.80)),
 ("F3_schofield2025_s41_fig1.png", f"{RAW}/Schofield2025/pdfimg/p48_x409_1319x852.png", (0, 0, 1, 1)),
 ("F4_schofield2025_s22_line.jpg", f"{RAW}/Schofield2025/pdfimg/p13_x109_833x327.jpeg", (0, 0, 1, 1)),
 ("F4_schofield2025_s22_b.jpg", f"{RAW}/Schofield2025/pdfimg/p13_x110_580x413.jpeg", (0, 0, 1, 1)),
 ("F4_schofield2025_s22_c.jpg", f"{RAW}/Schofield2025/pdfimg/p13_x111_580x413.jpeg", (0, 0, 1, 1)),
 ("F5_schofield2025_s32_fig1.png", f"{RAW}/Schofield2025/pdfimg/p32_x199_1529x1617.png", (0, 0, 1, 1)),
 ("F6_schofield2025_s53_fig1_sem.jpg", f"{RAW}/Schofield2025/pdfimg/p81_x555_840x544.jpeg", (0, 0, 1, 1)),
 ("F6_schofield2025_s53_fig2_flow.png", f"{RAW}/Schofield2025/pdfimg/p81_x556_947x1185.png", (0, 0, 1, 1)),
 ("F7_schofield2025_s24_fig2.jpg", f"{RAW}/Schofield2025/pdfimg/p21_x148_500x695.jpeg", (0, 0, 1, 1)),
 ("F8_constantinou2024_fig5.png", f"{RAW}/Constantinou2024/page9_300dpi.png", (0.148, 0.058, 0.872, 0.402)),
 ("F9_constantinou2023_fig2.jpg", f"{RAW}/Constantinou2023/pdfimg/p4_x9_2050x945.jpeg", (0, 0, 1, 1)),
 ("F10_danna2023_fig1.jpg", f"{RAW}/DAnna2023/pdfimg/p2_x45_1501x535.jpeg", (0, 0, 1, 1)),
 ("F10_danna2023_fig2_maps.jpg", f"{RAW}/DAnna2023/pdfimg/p3_x68_1501x1140.jpeg", (0, 0, 1, 0.575)),
 ("F11_stock2020_fig3_ad.png", f"{RAW}/Stock2020/pdfimg/p6_x696_921x1754.png", (0, 0, 1, 0.555)),
 ("F11_stock2020_fig4_sims.png", f"{RAW}/Stock2020/pdfimg/p7_x699_1950x1373.png", (0.0, 0.30, 0.53, 1.0)),
 ("F11_stock2020_fig4_transport.png", f"{RAW}/Stock2020/pdfimg/p7_x699_1950x1373.png", (0.53, 0.30, 1.0, 1.0)),
 ("F12_hofmann2023_fig1a.jpg", f"{RAW}/Hofmann2023/pdfimg/p2_x3_1498x880.jpeg", (0.0, 0.0, 0.345, 0.42)),
 ("F12b_lundgren2023_fig1.jpg", f"{RAW}/Lundgren2023/jp3c03916_0002.jpg", (0, 0, 1, 1)),
 ("F13_thorvaldson2025_fig1a.png", f"{RAW}/Thorvaldson2025/page2_300dpi.png", (0.06, 0.065, 0.30, 0.345)),
 ("F13_thorvaldson2025_fig4b.png", f"{RAW}/Thorvaldson2025/page5_300dpi.png", (0.19, 0.205, 0.52, 0.395)),
 ("F14_edlbauer2025_fig1ab.png", f"{RAW}/Edlbauer2025/page2_300dpi.png", (0.06, 0.055, 0.63, 0.298)),
 ("F15_wang2022_fig1.jpg", f"{RAW}/Wang2022/41467_2022_34220_Fig1_HTML.jpg", (0, 0, 1, 1)),
 ("F18_kiczynski2022_fig2a.png", f"{RAW}/Kiczynski2022/p4_940x833.png", (0, 0, 1, 1)),
 ("F17_tseng2023_fig7.jpg", f"{RAW}/Tseng2023/pdfimg/p8_x32_1650x1005.jpeg", (0, 0, 1, 1)),
]

def do_crops():
    for name, src, (x0, y0, x1, y1) in CROPS:
        im = Image.open(src).convert("RGB"); W, H = im.size
        c = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        c.save(f"{OUT}/{name}", quality=95); print("crop", name, c.size)

# --------------------------------------------------------------------------------------------
# 2. Tiny ball renderer (orthographic, painter's algorithm, radial shading) for 3D atom scenes
# --------------------------------------------------------------------------------------------
def _mix(c, w, t):
    c = np.array(matplotlib.colors.to_rgb(c)); w = np.array(matplotlib.colors.to_rgb(w)); return tuple(c + (w - c) * t)

class Scene:
    def __init__(self, az=-38, el=34):
        self.az, self.el = math.radians(az), math.radians(el); self.balls = []; self.extra = []
    def proj(self, x, y, z):
        ca, sa, ce, se = math.cos(self.az), math.sin(self.az), math.cos(self.el), math.sin(self.el)
        u = x * ca - y * sa; v = x * sa + y * ca
        return u, v * se + z * ce, v * ce - z * se  # screen x, screen y, depth (bigger = further)
    def ball(self, x, y, z, r, color, ec=None):
        self.balls.append((x, y, z, r, color, ec))
    def draw(self, ax):
        items = []
        for (x, y, z, r, c, ec) in self.balls:
            u, w, d = self.proj(x, y, z); items.append((d, u, w, r, c, ec))
        items.sort(key=lambda t: -t[0])
        for i, (d, u, w, r, c, ec) in enumerate(items):
            z0 = 10 + i * 0.01
            ax.add_patch(Circle((u, w), r, color=_mix(c, "#000000", 0.45), zorder=z0, lw=0))
            for k in range(1, 9):
                t = k / 9
                ax.add_patch(Circle((u - 0.28 * r * t, w + 0.28 * r * t), r * (1 - 0.82 * t) * 0.97,
                                    color=_mix(c, "#FFFFFF", 0.62 * t ** 1.6), zorder=z0 + 0.001 * k, lw=0))
        ax.set_aspect("equal"); ax.axis("off")
    def bond(self, ax, a, b, color="#7D868F", lw=2.0, z=5):
        (u1, w1, _), (u2, w2, _) = self.proj(*a), self.proj(*b)
        ax.plot([u1, u2], [w1, w2], color=color, lw=lw, zorder=z, solid_capstyle="round")

A = 3.84  # Si(001) surface lattice constant used only for drawing geometry
def si001(nrows=5, ndim=9):
    """Return list of top-layer dimer atoms [(row, k, side, x, y, z)] and sub-surface atoms."""
    top, sub = [], []
    for r in range(nrows):
        for k in range(ndim):
            xc, y = r * 2 * A, k * A
            for s in (-1, 1):
                top.append((r, k, s, xc + s * 1.1785, y, 0.0))  # dimer bond 2.357 Å (Ren2016)
    for r in range(nrows * 2):
        for k in range(ndim):
            sub.append((r * A - A / 2 + 0.0, k * A + A / 2, -1.35))
            sub.append((r * A, k * A, -2.7))
    return top, sub

def surface_scene(stage, fname, title=None):
    """stage: 'H' | 'window' | 'dose' | 'incorp'. 6-site P window on row 1, 4-site As window on row 3."""
    sc = Scene(az=-32, el=38)
    top, sub = si001(5, 9)
    Pwin = {(1, k) for k in (3, 4, 5)}          # 3 dimers = 6 sites
    Aswin = {(3, k) for k in (3, 4)}            # 2 dimers = 4 sites
    for (x, y, z) in sub:
        if -1.5 < x < 4 * 2 * A + 1.5: sc.ball(x, y, z, 0.95, "#9AA3AC")
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    incorp_site = (3, 3, -1)
    for (r, k, s, x, y, z) in top:
        win = (r, k) in Pwin or (r, k) in Aswin
        if stage == "incorp" and (r, k, s) == incorp_site:
            sc.ball(x, y, z + 0.1, 1.1, AS_C)             # As replaces a surface Si (As-Si heterodimer)
        else:
            tint = SI_ATOM
            if stage != "H" and (r, k) in Pwin: tint = "#EDB98A"
            if stage != "H" and (r, k) in Aswin: tint = "#86D0D0"
            sc.ball(x, y, z, 1.05, tint)
        if not win or stage == "H":
            sc.ball(x + s * 0.45, y, z + 1.44, 0.72, H_ATOM)   # Si–H 1.51 Å (Xiang2025)
    if stage in ("window",):
        pass
    if stage == "dose":
        # P window: PH2 + H fragments (slow, minutes); As window: As + 3H (fast, tens of seconds)
        r1x = 1 * 2 * A
        sc.ball(r1x - 1.17, 4 * A, 1.7, 1.0, P_C); sc.ball(r1x - 1.6, 4 * A + 0.9, 2.6, 0.5, H_ATOM); sc.ball(r1x - 2.0, 4 * A - 0.9, 2.4, 0.5, H_ATOM)
        sc.ball(r1x + 1.7, 3 * A, 1.4, 0.55, H_ATOM)
        r3x = 3 * 2 * A
        sc.ball(r3x - 1.17, 3.5 * A, 1.6, 1.05, AS_C)
        for (dx, dy) in ((1.7, 3 * A), (1.7, 4 * A), (-1.7, 4.4 * A)):
            sc.ball(r3x + dx, dy, 1.4, 0.55, H_ATOM)
    if stage == "incorp":
        sc.ball(3 * 2 * A + 1.2, 6.6 * A, 1.3, 1.05, "#C3CAD1")   # ejected Si ad-atom
        r1x = 1 * 2 * A
        for k in (3, 4, 5):
            for s in (-1, 1): sc.ball(r1x + s * 0.45 + s * 1.1785, k * A, 1.44, 0.72, H_ATOM)
    sc.draw(ax)
    if stage == "window":   # STM tip above the As window
        u, w, _ = sc.proj(3 * 2 * A, 3.5 * A, 0)
        ax.add_patch(Polygon([[u - 2.2, w + 13], [u + 2.2, w + 13], [u, w + 3.2]], color=TIP, zorder=50, lw=0))
        ax.add_patch(Polygon([[u - 0.9, w + 13], [u + 0.4, w + 13], [u, w + 3.2]], color="#F0D27A", zorder=51, lw=0))
        ax.annotate("STM tip writes\n3.5 V, 3000 pA, 50 nm/s", (u + 1.0, w + 8), xytext=(0.66, 0.86), textcoords="axes fraction",
                    fontsize=12, color=INK, zorder=60, arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    def lab(rr, kk, txt, col, pos):
        u, w, _ = sc.proj(rr * 2 * A, kk * A, 1.5)
        ax.annotate(txt, (u, w), xytext=pos, textcoords="axes fraction", color=col, fontsize=12.5, fontweight="bold",
                    zorder=80, ha="left", arrowprops=dict(arrowstyle="-", color=col, lw=1.6, shrinkB=4),
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9))
    if stage in ("window", "dose", "incorp"):
        lab(1, 4, {"window": "P: 6-site (3-dimer) window", "dose": "PH$_3$ → PH$_2$+H … (minutes)", "incorp": "P window (needs 6 sites)"}[stage], P_C, (0.0, 0.93))
        lab(3, 3.5, {"window": "As: 4-site (2-dimer) window", "dose": "AsH$_3$ → As+3H (tens of s)", "incorp": "As–Si heterodimer + ejected Si"}[stage], AS_C, (0.50, 0.02))
    if stage == "H":
        ax.text(0.5, -0.02, "Every surface Si capped by one H atom: a resist one atom thick", transform=ax.transAxes,
                fontsize=12, color=INK, ha="center", zorder=60)
    ax.autoscale_view(); ax.margins(0.02)
    save(fig, fname)

# --------------------------------------------------------------------------------------------
# 3. 2D process cross-sections with fixed material colours
# --------------------------------------------------------------------------------------------
def xsec(stage, fname, w=6.0, h=2.6, mini=False):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, 12); ax.set_ylim(-0.2, 5.0); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 12, 2.4, color=SI, lw=0))
    lab = (lambda *a, **k: None) if mini else (lambda x, y, t, **k: ax.text(x, y, t, fontsize=k.pop("fs", 10.5), color=k.pop("c", INK), **k))
    surf = 2.4
    if stage in ("prep", "litho", "dose", "incorp"):
        # H resist bumps
        for i in range(48):
            x = 0.125 + i * 0.25
            inP = 3.0 < x < 4.6; inAs = 7.6 < x < 8.6
            if stage == "prep" or not (inP or inAs):
                ax.add_patch(Circle((x, surf + 0.12), 0.11, color=HR, lw=0))
        if stage == "litho":
            ax.add_patch(Polygon([[7.6, 4.9], [8.6, 4.9], [8.1, 2.95]], color=TIP, lw=0))
            lab(8.75, 4.2, "STM tip", fs=10)
            lab(2.6, 2.95, "window", c=P_C, fs=10); lab(7.2, 2.95, "", fs=10)
        if stage == "dose":
            for (x, c) in ((3.4, P_C), (4.2, P_C), (8.1, AS_C)):
                ax.add_patch(Circle((x, surf + 0.28), 0.22, color=c, lw=0))
                for dx in (-0.22, 0.22): ax.add_patch(Circle((x + dx, surf + 0.6), 0.1, color=HR, lw=0))
            lab(2.4, 3.3, "PH$_3$", c=P_C); lab(8.5, 3.3, "AsH$_3$", c=AS_C)
        if stage == "incorp":
            ax.add_patch(Circle((3.8, surf - 0.2), 0.22, color=P_C, lw=0)); ax.add_patch(Circle((8.1, surf - 0.2), 0.22, color=AS_C, lw=0))
            ax.add_patch(Circle((8.9, surf + 0.25), 0.18, color=CAP, lw=0))
            lab(9.15, 2.9, "ejected Si", fs=10); lab(4.3, 3.0, "350 °C", fs=10)
    if stage in ("cap", "contact"):
        ax.add_patch(Rectangle((0, surf), 12, 0.35, color="#B5BEC6", lw=0))   # locking layer
        ax.add_patch(Rectangle((0, surf + 0.35), 12, 1.25, color=CAP, lw=0))  # epitaxial cap
        for x in np.arange(2.8, 9.4, 0.32):
            ax.add_patch(Circle((x, surf - 0.02), 0.11, color=AS_C, lw=0))
        lab(0.2, surf + 0.75, "Si cap (epitaxial)", fs=10)
        lab(0.2, surf + 0.06, "locking layer", fs=9)
        lab(0.2, 1.0, "Si substrate", fs=10)
        lab(9.6, surf - 0.45, "δ-layer", c=AS_C, fs=10)
    if stage == "contact":
        top = surf + 1.6
        for x0 in (2.0, 9.0):
            ax.add_patch(Rectangle((x0, surf - 0.25), 1.0, top - surf + 0.25, color="white", lw=0))
            ax.add_patch(Polygon([[x0, surf - 0.25], [x0 + 1.0, surf - 0.25], [x0 + 1.0, top + 0.4], [x0 + 1.5, top + 0.4],
                                  [x0 + 1.5, top + 0.75], [x0 - 0.5, top + 0.75], [x0 - 0.5, top + 0.4], [x0, top + 0.4]], color=AL, lw=0))
        ax.add_patch(Rectangle((0, top), 12, 0.0, color=OX))
        lab(4.4, top + 0.5, "Al into etched holes", fs=10)
    if not mini and stage in ("prep", "litho", "dose", "incorp"):
        lab(0.2, 1.0, "Si substrate", fs=10)
    save(fig, fname)

# --------------------------------------------------------------------------------------------
# 4. O1 Kane-style cross-section (Schematic after Kane1998)
# --------------------------------------------------------------------------------------------
def kane():
    """Horizontal axis to scale (nm). Kane2000: donors and gates 'of order 100 Å' apart, B ≃ 1 T, T ≃ 0.1 K.
    Bohr radius ~2 nm (Schofield2025 §3.2). Depth/barrier thickness not stated in open sources: drawn schematically."""
    fig, ax = plt.subplots(figsize=(7.0, 2.7)); ax.set_xlim(-6, 26); ax.set_ylim(-1.8, 10.0); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((-6, 0), 32, 5.0, color=SI, lw=0)); ax.text(-5.6, 0.35, "$^{28}$Si host", fontsize=10.5, color="white")
    ax.add_patch(Rectangle((-6, 5.0), 32, 1.0, color=OX, lw=0)); ax.text(-5.6, 5.2, "barrier", fontsize=9.5, color=INK)
    for x in (0, 10, 20):
        r = np.linspace(2.6 * 2.0, 0.2, 14)
        for rr in r: ax.add_patch(Circle((x, 2.6), rr, color=P_C, alpha=0.03 + 0.5 * math.exp(-2 * rr / 2.0) * 0.25, lw=0))
        ax.add_patch(Circle((x, 2.6), 2.0, fill=False, ec=P_C, lw=0.9, ls="--"))
        ax.add_patch(Circle((x, 2.6), 0.32, color=P_C, lw=0))
        ax.add_patch(Rectangle((x - 1.6, 6.0), 3.2, 1.6, color=AL, lw=0)); ax.text(x, 7.85, "A", ha="center", fontsize=11, fontweight="bold")
    for x in (5, 15):
        ax.add_patch(Rectangle((x - 0.8, 6.0), 1.6, 1.6, color="#3E4852", lw=0)); ax.text(x, 7.85, "J", ha="center", fontsize=11, fontweight="bold")
    ax.annotate("", (10, -0.6), (0, -0.6), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2), annotation_clip=False)
    ax.text(5, -1.15, "≈10 nm (\"of order 100 Å\", Kane2000)", ha="center", fontsize=9.5, annotation_clip=False) if False else ax.text(5, -1.2, "≈10 nm (\"of order 100 Å\", Kane2000)", ha="center", fontsize=9.5)
    ax.annotate("", (22.0, 4.9), (20, 4.9), arrowprops=dict(arrowstyle="<->", color="white", lw=1))
    ax.text(21.0, 5.25 - 1.0, "a$_B$≈2 nm", ha="center", fontsize=8.5, color="white")
    ax.text(-5.6, 8.9, "B ≃ 1 T,  T ≃ 0.1 K  (Kane2000)", fontsize=10, color=INK)
    ax.text(26, 8.9, "x to scale; depth schematic", fontsize=8.5, color=MUTED, ha="right")
    ax.text(0.6, 3.25, "$^{31}$P, I = 1/2", fontsize=9, color="white")
    save(fig, "O1_kane_crosssection.png")

# --------------------------------------------------------------------------------------------
# 5. Donor spin levels (4 states) — schematic, no numbers
# --------------------------------------------------------------------------------------------
def levels():
    fig, ax = plt.subplots(figsize=(3.0, 2.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 10.6); ax.axis("off")
    ys = {"↑⇑": 8.6, "↑⇓": 7.2, "↓⇓": 2.8, "↓⇑": 1.4}
    for k, y in ys.items():
        ax.plot([3.4, 7.0], [y, y], color=INK, lw=2.4); ax.text(7.3, y - 0.35, f"|{k}⟩", fontsize=13)
    ax.add_patch(FancyArrowPatch((4.2, 2.8), (4.2, 7.2), arrowstyle="<->", mutation_scale=14, color=AS_C, lw=2.2))
    ax.text(0.0, 4.6, "ESR", fontsize=14, color=AS_C, fontweight="bold")
    for y0, y1 in ((7.2, 8.6), (1.4, 2.8)):
        ax.add_patch(FancyArrowPatch((6.0, y0), (6.0, y1), arrowstyle="<->", mutation_scale=10, color=P_C, lw=2.2))
    ax.text(5.0, 4.6, "NMR", fontsize=14, color=P_C, fontweight="bold")
    ax.text(0.0, 10.0, "electron × nucleus = 4 states", fontsize=12.5, color=INK)
    save(fig, "O_levels_4state.png")

# --------------------------------------------------------------------------------------------
# 6. O5 overgrowth temperature programs (schematic time axis)
# --------------------------------------------------------------------------------------------
def overgrowth():
    fig, ax = plt.subplots(figsize=(3.6, 2.9))
    t = [0, 1, 1, 1.15, 1.15, 1.3, 1.3, 4]
    asT = [25, 25, 25, 500, 500, 250, 250, 250]
    ax.plot([0, 1.7, 4], [250, 250, 250], color=P_C, lw=2.2)
    ax.plot([0, 1.4, 1.42, 1.55, 1.57, 1.7, 4], [25, 25, 500, 500, 250, 250, 250], color=AS_C, lw=2.2)
    ax.text(1.95, 268, "P: constant 250 °C", color=INK, fontsize=10)
    ax.text(1.72, 470, "As: 500 °C × 10 s RTA", color=INK, fontsize=10)
    ax.text(0.03, 70, "As: unheated\nlock layer", color=INK, fontsize=9.5)
    ax.text(1.95, 200, "As: epitaxy ≈1 ML/min", color=INK, fontsize=10)
    ax.set_ylim(0, 560); ax.set_xlim(0, 4); ax.set_xticks([]); ax.set_ylabel("Substrate T (°C)")
    ax.set_xlabel("time (schematic)")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    save(fig, "O5_overgrowth_program.png")

# --------------------------------------------------------------------------------------------
# 7. Yield model: Monte Carlo 4x4 arrays + 3D surface p^n
# --------------------------------------------------------------------------------------------
def montecarlo():
    rng = np.random.default_rng(143)
    fig, axs = plt.subplots(2, 6, figsize=(7.4, 3.0))
    for row, (p, col, name) in enumerate(((0.70, P_C, "P, p = 0.7"), (0.97, AS_C, "As, p = 0.97"))):
        trials = rng.random((100000, 16)) < p
        perfect = trials.all(axis=1).mean()
        for j in range(6):
            ax = axs[row, j]; s = trials[j].reshape(4, 4)
            for a in range(4):
                for b in range(4):
                    if s[a, b]: ax.add_patch(Circle((b, a), 0.36, color=col, lw=0))
                    else: ax.add_patch(Circle((b, a), 0.36, fill=False, ec="#B03030", lw=1.6)); ax.plot([b - .25, b + .25], [a - .25, a + .25], color="#B03030", lw=1.4)
            ax.set_xlim(-.6, 3.6); ax.set_ylim(-.6, 3.6); ax.set_aspect("equal"); ax.axis("off")
            if s.all(): ax.add_patch(Rectangle((-.55, -.55), 4.1, 4.1, fill=False, ec=INK, lw=1.5))
        axs[row, 0].text(-1.2, 1.5, name, rotation=90, va="center", ha="center", fontsize=11, color=INK)
        axs[row, 5].text(4.0, 1.5, f"{perfect*100:.1f}%\nperfect", va="center", fontsize=11, color=INK, fontweight="bold")
        print(name, "perfect fraction", perfect)
    save(fig, "O_montecarlo_4x4.png")

def yield_surface():
    p = np.linspace(0.6, 1.0, 81); n = np.arange(1, 65)
    Pg, Ng = np.meshgrid(p, n); Y = Pg ** Ng
    fig = plt.figure(figsize=(5.2, 4.2)); ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    ax.plot_surface(Pg, Ng, Y, cmap="Greys", vmin=-0.3, vmax=1.2, alpha=0.75, linewidth=0, rstride=2, cstride=2, antialiased=True, zorder=1)
    for pv, c in ((0.70, P_C), (0.97, AS_C)):
        ax.plot([pv] * len(n), n, pv ** n, color=c, lw=3.2, zorder=10)
    ax.text(0.70, 45, 0.10, "P  p = 0.7", color=P_C, fontsize=11, fontweight="bold", zorder=11)
    ax.text(0.97, 30, 0.62, "As  p = 0.97", color=AS_C, fontsize=11, fontweight="bold", zorder=11)
    ax.set_xlabel("per-site yield p", labelpad=6); ax.set_ylabel("atoms in array n", labelpad=6); ax.set_zlabel("array yield p$^n$", labelpad=4)
    ax.view_init(elev=22, azim=-142); ax.set_box_aspect((1, 1.2, 0.8))
    for a in (ax.xaxis, ax.yaxis, ax.zaxis): a.pane.set_facecolor((1, 1, 1, 0)); a.pane.set_edgecolor("#CCCCCC")
    save(fig, "O_yield_surface3d.png")

# --------------------------------------------------------------------------------------------
# 8. Prototype 3D device render (concept, not to scale)
# --------------------------------------------------------------------------------------------
def cuboid(x0, x1, y0, y1, z0, z1):
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    f = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]
    return [[v[i] for i in face] for face in f]

def prototype3d():
    fig = plt.figure(figsize=(6.4, 4.8)); ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    sub = Poly3DCollection(cuboid(-10, 10, -10, 10, -6, 0), facecolor=[SI, "#A7B0B8", "#7E8892", "#7E8892", "#6F7984", "#6F7984"], edgecolor="#6D767F", lw=0.4, alpha=1.0); sub.set_zorder(1); ax.add_collection3d(sub)
    # in-plane delta-layer leads (As) : source, drain, two gates
    leads = [((-10, -3.2), (-1.0, 1.0)), ((3.2, 10), (-1.0, 1.0)), ((-1.2, 1.2), (4.0, 10)), ((-1.2, 1.2), (-10, -4.0))]
    for (xr, yr) in leads:
        ax.add_collection3d(Poly3DCollection([[(xr[0], yr[0], 0.02), (xr[1], yr[0], 0.02), (xr[1], yr[1], 0.02), (xr[0], yr[1], 0.02)]],
                                             facecolor=AS_C, edgecolor=AS_C, alpha=0.85, zorder=2))
    # 2x2 single-As register
    for (x, y) in ((-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)):
        ax.scatter([x], [y], [0.25], s=80, color=AS_C, edgecolor="#075E5F", depthshade=False, zorder=3)
    # translucent epitaxial cap
    ax.add_collection3d(Poly3DCollection(cuboid(-10, 10, -10, 10, 0, 3), facecolor=CAP, edgecolor="#9AA4AD", lw=0.4, alpha=0.16, zorder=4))
    # Al vias at the lead ends
    for (x, y) in ((-8.5, 0), (8.5, 0), (0, 8.5), (0, -8.5)):
        ax.add_collection3d(Poly3DCollection(cuboid(x - 0.8, x + 0.8, y - 0.8, y + 0.8, 0, 4.2), facecolor=AL, edgecolor="#3E4852", lw=0.4, alpha=1, zorder=5))
    ax.text(10, -10, -7.5, "Si substrate", color=INK, fontsize=10.5)
    ax.text(-10, 10, 3.6, "epitaxial Si cap", color=INK, fontsize=10.5)
    ax.plot([0, 0], [0, 0], [0.4, 7.0], color=AS_C, lw=1.2, zorder=6)
    ax.text(-2, 0, 7.4, "2×2 As register", color=AS_C, fontsize=11.5, fontweight="bold", zorder=7)
    ax.text(-15.5, 0, 0, "source", color="#075E5F", fontsize=10, zorder=7); ax.text(10.8, 0, 0, "drain", color="#075E5F", fontsize=10, zorder=7)
    ax.text(0, 11, 0, "gate", color="#075E5F", fontsize=10, zorder=7); ax.text(0, -13.5, 0, "gate", color="#075E5F", fontsize=10, zorder=7)
    ax.set_xlim(-10, 10); ax.set_ylim(-10, 10); ax.set_zlim(-6, 6); ax.set_box_aspect((1, 1, 0.55))
    ax.view_init(elev=28, azim=-60); ax.axis("off")
    save(fig, "O_prototype3d.png")

# --------------------------------------------------------------------------------------------
# 9. Landmark schematics (Schematic after Schofield2003 / Fuechsle2012)
# --------------------------------------------------------------------------------------------
def landmarks():
    """2003, to scale: Si(001) dimer rows 2a = 0.768 nm apart, dimers a = 0.384 nm along the row (Stock2024 Fig. 1i);
    ~1 nm (~3 dimers) H-desorption sites ~12 nm apart on one row (Schofield2003 Fig. 4)."""
    a0 = 0.384
    fig, ax = plt.subplots(figsize=(4.6, 2.3)); ax.set_xlim(-1.0, 14.6); ax.set_ylim(-1.6, 5.0); ax.set_aspect("equal"); ax.axis("off")
    rows = [0.0, 0.768, 1.536, 2.304, 3.072]
    w1, w2 = (1.0, 13.0)
    for ry in rows:
        for k in range(int(14.6 / a0)):
            x = -0.8 + k * a0
            bare = (ry == 1.536) and (abs(x - w1) < 0.6 or abs(x - w2) < 0.6)
            for dy in (-0.118, 0.118):   # dimer bond 0.2357 nm (Ren2016)
                ax.add_patch(Circle((x, ry + dy), 0.105, color="#EDB98A" if bare else "#A3ACB5", lw=0))
                if not bare: ax.add_patch(Circle((x, ry + dy * 2.1), 0.06, color=H_ATOM, lw=0))
    for xc in (w1, w2):
        ax.add_patch(Circle((xc, 1.536), 0.28, color=P_C, ec=INK, lw=0.8, zorder=5))
    ax.annotate("", (w2, 3.75), (w1, 3.75), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2))
    ax.text((w1 + w2) / 2, 4.05, "≈12 nm apart, same dimer row (Kane array: 20 nm)", ha="center", fontsize=8.6)
    ax.plot([-0.8, 0.2], [-0.55, -0.55], color=INK, lw=2); ax.text(-0.8, -1.05, "1 nm", fontsize=8.5)
    ax.text(0.6, -1.05, "sites ≈1 nm (≈3 dimers) · +4 V, 1 nA · 0.3 L PH$_3$, 10$^{-9}$ mbar · ≈350 °C", fontsize=7.4, color=INK)
    save(fig, "O_landmark2003.png")
    fig, ax = plt.subplots(figsize=(3.9, 3.0)); ax.set_xlim(0, 20); ax.set_ylim(0, 15); ax.axis("off")
    ax.add_patch(Polygon([[0.5, 5.5], [7.5, 7.4], [7.5, 8.6], [0.5, 10.5]], color=P_C, alpha=0.85, lw=0))
    ax.add_patch(Polygon([[19.5, 5.5], [12.5, 7.4], [12.5, 8.6], [19.5, 10.5]], color=P_C, alpha=0.85, lw=0))
    ax.add_patch(Polygon([[7, 14.5], [13, 14.5], [10.8, 11.0], [9.2, 11.0]], color=P_C, alpha=0.55, lw=0))
    ax.add_patch(Polygon([[7, 1.5], [13, 1.5], [10.8, 5.0], [9.2, 5.0]], color=P_C, alpha=0.55, lw=0))
    ax.add_patch(Circle((10, 8.0), 0.6, color=P_C, ec=INK, lw=1.2))
    ax.text(1, 11.2, "source", fontsize=10); ax.text(15.5, 11.2, "drain", fontsize=10)
    ax.text(13.4, 13.4, "gate", fontsize=10); ax.text(13.4, 2.3, "gate", fontsize=10)
    ax.annotate("one P atom", (10.5, 8.4), xytext=(12.5, 10.0), fontsize=10, arrowprops=dict(arrowstyle="-", color=INK, lw=1))
    ax.text(10, -0.4, "2012: single-atom transistor, one-lattice-site\naccuracy (illustrative layout: no open dimensions)", ha="center", fontsize=9.5, color=INK)
    save(fig, "O_landmark2012.png")


# --------------------------------------------------------------------------------------------
# 10. Title hero: diamond-cubic Si block (a = 5.431 Å, geometry only) with single As/P dopants
# --------------------------------------------------------------------------------------------
def hero():
    a0 = 5.431
    basis = [(0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0), (.25, .25, .25), (.25, .75, .75), (.75, .25, .75), (.75, .75, .25)]
    N, NZ = 5, 2
    pts = set()
    for i in range(N + 1):
        for j in range(N + 1):
            for k in range(NZ + 1):
                for (bx, by, bz) in basis:
                    x, y, z = (i + bx) * a0, (j + by) * a0, (k + bz) * a0
                    if x <= N * a0 + 0.01 and y <= N * a0 + 0.01 and z <= NZ * a0 + 0.01:
                        pts.add((round(x, 3), round(y, 3), round(z, 3)))
    pts = sorted(pts)
    P = np.array(pts)
    dnn0 = a0 * math.sqrt(3) / 4
    for _ in range(2):  # drop dangling edge atoms (fewer than 2 bonds)
        D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
        keep = ((D > 0.1) & (D < dnn0 + 0.05)).sum(1) >= 2
        P = P[keep]
    pts = [tuple(p) for p in P]; zt = P[:, 2].max()
    sc = Scene(az=-35, el=32)
    fig = plt.figure(figsize=(7.0, 6.2), facecolor="#111A22"); ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#111A22")
    # bonds (nearest neighbours, a*sqrt(3)/4)
    dnn = a0 * math.sqrt(3) / 4
    from itertools import combinations
    idx = {p: n for n, p in enumerate(pts)}
    for n, p in enumerate(P):
        d = np.linalg.norm(P - p, axis=1)
        for m in np.where((d > 0.1) & (d < dnn + 0.05))[0]:
            if m > n:
                (u1, w1, _), (u2, w2, _) = sc.proj(*p), sc.proj(*P[m])
                ax.plot([u1, u2], [w1, w2], color="#6B7986", lw=1.0, zorder=2, alpha=0.8)
    # dopants on the top layer: a 2x2 As register and one P
    top = [tuple(p) for p in P if abs(p[2] - zt) < 0.01]
    def nearest(x, y):
        return min(top, key=lambda t: (t[0] - x) ** 2 + (t[1] - y) ** 2)
    c = N * a0 / 2
    dop = {nearest(c - 5.5, c - 5.5): AS_C, nearest(c + 5.5, c - 5.5): AS_C, nearest(c - 5.5, c + 5.5): AS_C, nearest(c + 5.5, c + 5.5): AS_C,
           nearest(c + 10.5, c - 10.5): P_C}
    aB = 20.0  # donor Bohr radius ~2 nm (Schofield2025 §3.2), in Å, same units as the lattice
    for p in pts:
        col = dop.get(p)
        if col:  # |psi|^2 ~ exp(-2r/aB) glow, drawn as stacked translucent discs
            u, w, _ = sc.proj(*p)
            for r in np.linspace(7.5, 1.0, 18):
                ax.add_patch(Circle((u, w), r, color=col, alpha=0.05 * math.exp(-2 * r / (aB / 2.5)) * 3.0, lw=0, zorder=3))
            for rr in (2.6, 4.6):
                ax.add_patch(Circle((u, w), rr, fill=False, ec=col, lw=0.7, alpha=0.55, zorder=3))
        shade = 0.25 + 0.75 * (p[2] / zt)
        sc.ball(*p, 0.95 if col else 0.62, col or _mix("#3E4A56", "#B9C3CC", shade))
    sc.draw(ax)
    # exchange links (dashed) and spin arrows on the As register
    As_sites = [q for q, c_ in dop.items() if c_ == AS_C]
    proj = {q: sc.proj(*q)[:2] for q in dop}
    for i_, q1 in enumerate(As_sites):
        for q2 in As_sites[i_ + 1:]:
            (u1, w1), (u2, w2) = proj[q1], proj[q2]
            if math.hypot(u1 - u2, w1 - w2) < 9.5:
                ax.plot([u1, u2], [w1, w2], color="#9FF0EE", lw=1.6, ls=(0, (3, 2)), alpha=0.85, zorder=150)
    spins = [1, -1, -1, 1]
    for q, sp in zip(sorted(As_sites), spins):
        u, w = proj[q]
        ax.add_patch(FancyArrowPatch((u, w + (1.2 if sp > 0 else 5.4)), (u, w + (5.4 if sp > 0 else 1.2)), arrowstyle="-|>", mutation_scale=13, color="#FFFFFF", lw=2.0, zorder=160))
    up, wp = proj[[q for q, c_ in dop.items() if c_ == P_C][0]]
    ax.add_patch(FancyArrowPatch((up, wp + 1.2), (up + 2.6, wp + 4.8), arrowstyle="-|>", mutation_scale=12, color="#FFE2C4", lw=1.8, zorder=160))
    # STM tip above the register
    u, w, _ = sc.proj(c, c, zt)
    ax.add_patch(Polygon([[u - 3.0, w + 27], [u + 3.0, w + 27], [u, w + 9.5]], color=TIP, zorder=200, lw=0))
    ax.add_patch(Polygon([[u - 1.1, w + 27], [u + 0.6, w + 27], [u, w + 9.5]], color="#F0D27A", zorder=201, lw=0))
    for r, al in ((1.3, .18), (0.7, .4)):
        ax.add_patch(Circle((u, w + 9.3), r, color="#F6E3A1", alpha=al, lw=0, zorder=202))
    ax.plot([u, u], [w + 9.0, w + 2.5], color="#F6E3A1", lw=1.2, ls=(0, (2, 2)), alpha=0.7, zorder=199)
    ax.set_aspect("equal"); ax.axis("off"); ax.autoscale_view(); ax.margins(0.03)
    fig.savefig(f"{OUT}/O_hero_title.png", dpi=300, facecolor="#111A22"); plt.close(fig); print("wrote O_hero_title.png")

def bloch():
    fig = plt.figure(figsize=(3.4, 3.4)); ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    u_, v_ = np.mgrid[0:2 * np.pi:60j, 0:np.pi:30j]
    ax.plot_surface(np.cos(u_) * np.sin(v_), np.sin(u_) * np.sin(v_), np.cos(v_), color="#E8F4F4", alpha=0.25, lw=0, zorder=1)
    t = np.linspace(0, 2 * np.pi, 120)
    for z0 in (0,):
        ax.plot(np.cos(t), np.sin(t), 0 * t, color="#9AA3AC", lw=0.8, zorder=2)
    ax.plot(np.cos(t), 0 * t, np.sin(t), color="#C3CAD1", lw=0.6, zorder=2)
    ax.plot(0 * t, np.cos(t), np.sin(t), color="#C3CAD1", lw=0.6, zorder=2)
    for (x, y, z) in ((1.25, 0, 0), (0, 1.25, 0), (0, 0, 1.25)):
        ax.plot([-x, x], [-y, y], [-z, z], color="#9AA3AC", lw=0.7, zorder=2)
    th, ph = 0.95, 0.75
    vx, vy, vz = np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)
    ax.quiver(0, 0, 0, vx, vy, vz, color=AS_C, lw=2.6, arrow_length_ratio=0.12, zorder=10)
    ax.plot([vx, vx], [vy, vy], [0, vz], color=AS_C, lw=0.8, ls=":", zorder=9)
    ax.text(0, 0, 1.42, "|0⟩", fontsize=13, ha="center", zorder=11); ax.text(0, 0, -1.6, "|1⟩", fontsize=13, ha="center", zorder=11)
    ax.text(vx * 1.25, vy * 1.25, vz * 1.2, "|ψ⟩", fontsize=13, color=AS_C, fontweight="bold", zorder=11)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=18, azim=35); ax.axis("off")
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-1.1, 1.1); ax.set_zlim(-1.1, 1.1)
    save(fig, "O_bloch.png")

def wavefunction_scale():
    """Two donors 13.0 nm apart (He2019) with hydrogenic envelopes |psi|^2 ~ exp(-2r/aB), aB = 2 nm
    (Schofield2025 §3.2, 'of order 2 nm'), over the Si(001) surface lattice (a = 0.384 nm, Stock2024 Fig. 1)."""
    aB, d, a = 2.0, 13.0, 0.384
    x = np.linspace(-4.5, d + 4.5, 900); y = np.linspace(-4, 4, 420); X, Y = np.meshgrid(x, y)
    psi1 = np.exp(-np.hypot(X, Y) / aB); psi2 = np.exp(-np.hypot(X - d, Y) / aB)
    dens = psi1 ** 2 + psi2 ** 2
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    from matplotlib.colors import LinearSegmentedColormap
    cm = LinearSegmentedColormap.from_list("q", ["#FFFFFF", "#CFEFEF", "#5FC9C9", "#0F9FA0", "#075E5F"])
    ax.imshow(np.log10(dens + 1e-9), extent=(x[0], x[-1], y[0], y[-1]), origin="lower", cmap=cm, vmin=-3.2, vmax=0, aspect="equal", zorder=1)
    gx = np.arange(x[0], x[-1], a); gy = np.arange(y[0], y[-1], 2 * a)
    GX, GY = np.meshgrid(gx, gy); ax.scatter(GX, GY, s=1.4, color="#5B6770", alpha=0.6, zorder=2, lw=0)
    for x0 in (0, d):
        ax.add_patch(Circle((x0, 0), aB, fill=False, ec=INK, lw=1.0, ls="--", zorder=3))
        ax.add_patch(Circle((x0, 0), 0.22, color=P_C, zorder=4))
    ax.annotate("", (d, -3.3), (0, -3.3), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.3), zorder=5)
    ax.text(d / 2, -3.05, "13.0 ± 0.5 nm donor spacing (He2019)", ha="center", fontsize=10.5, zorder=5)
    ax.annotate("", (aB, 2.6), (0, 2.6), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2), zorder=5)
    ax.text(aB / 2, 2.85, "a$_B$ ≈ 2 nm", ha="center", fontsize=10.5, zorder=5)
    ax.text(d / 2, 0.9, "the faint overlap of |ψ|²\nsets the exchange J\n(log colour scale)", ha="center", fontsize=10, color=INK, zorder=5)
    ax.plot([d + 0.6, d + 0.6 + 10 * a], [3.55, 3.55], color=INK, lw=2, zorder=5)
    ax.text(d + 0.6, 3.0, "10 surface sites = 3.84 nm", fontsize=8.5, zorder=5)
    ax.set_xlabel("x (nm)"); ax.set_yticks([]); ax.set_xlim(x[0], x[-1]); ax.set_ylim(y[0], y[-1])
    for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
    save(fig, "O_wavefunction_scale.png")

def xsec_scaled(stage, fname):
    """To-scale vertical cross-section of the DAnna2023 stack: CZ Si(001) substrate, As delta-layer,
    2 nm lock layer (RT) + RTA 500 C x 15 s, 28 nm Si cap at 250 C, 0.003 nm/s -> layer 30 nm deep."""
    fig, ax = plt.subplots(figsize=(6.2, 2.75))
    X0, X1 = 0, 60
    ax.add_patch(Rectangle((X0, -14), X1, 14, color=SI, lw=0))
    ax.add_patch(Rectangle((X0, 0), X1, 2, color="#B5BEC6", lw=0))
    ax.add_patch(Rectangle((X0, 2), X1, 28, color=CAP, lw=0))
    ax.add_patch(Rectangle((X0, -0.45), X1, 0.9, color=AS_C, lw=0))
    if stage == "contact":
        for xc in (10, 46):
            ax.add_patch(Rectangle((xc, -3.0), 4.5, 33.0, color="white", lw=0))
            ax.add_patch(Polygon([[xc, -3.0], [xc + 4.5, -3.0], [xc + 4.5, 30], [xc + 8.5, 30], [xc + 8.5, 34], [xc - 4, 34], [xc - 4, 30], [xc, 30]], color=AL, lw=0))
        ax.text(19.5, 31.0, "Al in RIE-etched holes", fontsize=9.5, color=INK)
        ax.text(X0 + 1, -11.2, "Hall bar 20 × 200 µm² · lateral not to scale · Al thickness not stated", fontsize=8.2, color="white")
    # depth axis (to scale)
    ax.plot([X1 + 2, X1 + 2], [0, 30], color=INK, lw=1)
    for d in (0, 10, 20, 30):
        ax.plot([X1 + 2, X1 + 3], [30 - d, 30 - d], color=INK, lw=1); ax.text(X1 + 3.6, 30 - d - 0.9, f"{d}", fontsize=8.5)
    ax.text(X1 + 7.5, 13, "depth (nm)", rotation=90, fontsize=8.5, va="center")
    lab = dict(fontsize=9.5, color=INK)
    ax.text(X0 + 1, 15, "Si cap 28 nm · 250 °C · 0.003 nm/s", **lab)
    ax.text(X0 + 1, 2.6, "lock layer 2 nm · RT, then RTA 500 °C × 15 s", fontsize=8.6, color=INK)
    ax.text(X0 + 1, -3.4, "As δ-layer, buried 30 nm", fontsize=9.5, color="#075E5F", fontweight="bold")
    ax.text(X0 + 1, -7.4, "CZ Si(001) substrate, 0.5 mm, >15 Ω cm", fontsize=9.5, color="white")
    ax.set_xlim(X0, X1 + 9); ax.set_ylim(-14, 35 if stage == "contact" else 31.5); ax.axis("off")
    save(fig, fname)

def overgrowth2():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.6), gridspec_kw=dict(width_ratios=[1.15, 1], wspace=0.32))
    # (a) Stock2020 Fig. 4e program: 40 C locking layer 10 min (10 ML at 1 ML/min), 500 C RTA, 250 C LTE to ~240 min
    def m(t):  # broken time axis: 0-16 min linear, 16-240 compressed
        t = np.asarray(t, float); return np.where(t <= 16, t, 16 + (t - 16) * 6 / 224)
    tt = [0, 10, 12.4, 12.6, 12.9, 13.1, 240]; TT = [40, 40, 500, 500, 250, 250, 250]
    a1.plot(m([0, 240]), [250, 250], color=P_C, lw=2)
    a1.plot(m(tt), TT, color=AS_C, lw=2)
    a1.set_xticks(m([0, 5, 10, 15, 240])); a1.set_xticklabels(["0", "5", "10", "15", "240"])
    a1.text(m(19.5), 0, "//", fontsize=11, ha="center", va="center", clip_on=False, backgroundcolor="white")
    a1.set_ylim(0, 560); a1.set_xlim(0, m(240)); a1.set_ylabel("T (°C)"); a1.set_xlabel("growth time (min)")
    a1.text(0.4, 70, "As: 40 °C lock\nlayer, 10 ML", fontsize=8.5); a1.text(m(13.4), 475, "500 °C RTA", fontsize=8.5)
    a1.text(m(13.4), 265, "250 °C", fontsize=8.5, color=INK); a1.text(0.4, 285, "P: 250 °C", fontsize=8.5, color=INK)
    a1.set_title("(a) Stock2020 As program (Fig. 4e)", fontsize=9.5, loc="left")
    # (b) DAnna2023 vs deposited thickness
    a2.plot([0, 30], [250, 250], color=P_C, lw=2, alpha=0.0)
    a2.plot([0, 2, 2, 2, 30], [25, 25, 500, 250, 250], color=AS_C, lw=2)
    a2.set_xlim(0, 30); a2.set_ylim(0, 560); a2.set_xlabel("Si deposited (nm)")
    a2.text(0.4, 70, "2 nm, RT", fontsize=8.5); a2.text(2.6, 475, "500 °C × 15 s", fontsize=8.5)
    a2.text(6, 265, "28 nm at 250 °C, 0.003 nm/s", fontsize=8.5)
    a2.text(6, 150, "≈2.6 h of growth (our calc.)", fontsize=8, color=MUTED)
    a2.set_title("(b) DAnna2023 stack", fontsize=9.5, loc="left")
    for a_ in (a1, a2):
        for sp in ("top", "right"): a_.spines[sp].set_visible(False)
    save(fig, "O5_overgrowth_program.png")

def prototype_layout():
    """Top view to scale. Inputs: 2x2 As register, pitch ~12 surface lattice vectors = 4.6 nm, 4-site windows (Stock2024);
    SET 17 nm from the register and two gates 146.6 nm apart (Edlbauer2025 design values); burial 30 nm (DAnna2023).
    Lead/gate widths are not stated in the papers: drawn illustratively."""
    fig = plt.figure(figsize=(6.6, 3.4)); ax = fig.add_axes([0.0, 0.08, 0.6, 0.9]); ax.set_aspect("equal")
    ax.set_xlim(-95, 95); ax.set_ylim(-60, 60); ax.axis("off")
    ax.add_patch(Rectangle((-95, -60), 190, 120, color="#F2F4F6", lw=0))
    for sx in (-1, 1):   # gates 146.6 nm apart (centre lines at +/-73.3 nm)
        x0 = sx * 73.3
        ax.add_patch(Polygon([[x0, -6], [x0, 6], [x0 + sx * 22, 30], [x0 + sx * 22, -30]], color=AS_C, alpha=0.75, lw=0))
        ax.text(x0 + sx * 12, 36, "gate", ha="center", fontsize=9, color="#075E5F")
    ax.add_patch(Rectangle((-6, 17), 12, 9, color=AS_C, alpha=0.9, lw=0)); ax.text(9, 19.5, "SET island", fontsize=9, color="#075E5F")
    for sx in (-1, 1):
        ax.add_patch(Polygon([[sx * 6, 21.5], [sx * 60, 50], [sx * 60, 58], [sx * 6, 23.5]], color=AS_C, alpha=0.75, lw=0))
    ax.text(-62, 52, "S", fontsize=9, color="#075E5F"); ax.text(58, 52, "D", fontsize=9, color="#075E5F")
    for (x, y) in ((-2.3, -2.3), (2.3, -2.3), (-2.3, 2.3), (2.3, 2.3)): ax.add_patch(Circle((x, y), 1.0, color=AS_C, ec="#075E5F", lw=0.6))
    ax.annotate("", (0, 17), (0, 3.3), arrowprops=dict(arrowstyle="<->", color=INK, lw=1)); ax.text(1.5, 9, "17 nm", fontsize=8.5)
    ax.annotate("", (73.3, -42), (-73.3, -42), arrowprops=dict(arrowstyle="<->", color=INK, lw=1)); ax.text(0, -50, "146.6 nm gate separation", ha="center", fontsize=8.5)
    ax.plot([-90, -40], [-56, -56], color=INK, lw=2); ax.text(-90, -54, "50 nm", fontsize=8)
    ax.add_patch(Rectangle((-6, -6), 12, 12, fill=False, ec=INK, lw=0.8))
    # inset: register at atomic scale
    bx = fig.add_axes([0.63, 0.12, 0.36, 0.84]); bx.set_aspect("equal"); bx.axis("off")
    a0 = 0.384; L = 7.0
    bx.set_xlim(-L / 2, L / 2); bx.set_ylim(-L / 2, L / 2)
    for iy in range(-5, 6):
        y = iy * 2 * a0
        for ix in range(-10, 11):
            x = ix * a0
            for dy in (-0.118, 0.118):
                bx.add_patch(Circle((x, y + dy), 0.095, color="#C3CAD1", lw=0))
    for (x, y) in ((-2.3, -2.3), (2.3, -2.3), (-2.3, 2.3), (2.3, 2.3)):
        xs = round(x / a0) * a0; ys = round(y / (2 * a0)) * 2 * a0
        bx.add_patch(Rectangle((xs - a0 * 0.75, ys - 0.32), 1.5 * a0 * 1.0 + 0.0, 0.64, color="#86D0D0", lw=0, alpha=0.8))
        bx.add_patch(Circle((xs, ys), 0.22, color=AS_C, ec="#075E5F", lw=0.6))
    bx.annotate("", (2.3, -3.15), (-2.3, -3.15), arrowprops=dict(arrowstyle="<->", color=INK, lw=1))
    bx.text(0, -3.05, "4.6 nm ≈ 12 lattice vectors", ha="center", va="bottom", fontsize=8.5, backgroundcolor="white")
    bx.text(-3.4, 3.15, "zoom: 2×2 As in 4-site windows", fontsize=8.5, va="top", backgroundcolor="white")
    fig.text(0.01, 0.01, "Si(001) surface sites to scale (0.384 nm). Buried 30 nm. Lead widths illustrative.", fontsize=8, color=MUTED)
    save(fig, "O_prototype_layout.png")

def mini_icons():
    for st in ("prep", "litho", "dose", "incorp", "cap", "contact"):
        xsec(st, f"icon_{st}.png", w=1.6, h=0.9, mini=True)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for fn in sys.argv[1:]: globals()[fn]()
        raise SystemExit
    do_crops(); hero(); bloch(); wavefunction_scale(); prototype_layout()
    surface_scene("H", "O2_surface_H.png"); surface_scene("window", "O2_surface_window.png")
    surface_scene("dose", "O2_surface_dose.png"); surface_scene("incorp", "O2_surface_incorp.png")
    for st in ("prep", "litho", "dose", "incorp", "cap", "contact"): xsec(st, f"xsec_{st}.png")
    xsec_scaled("cap", "xsec_cap.png"); xsec_scaled("contact", "xsec_contact.png")
    mini_icons(); kane(); levels(); overgrowth2(); montecarlo(); yield_surface(); prototype3d(); landmarks()
