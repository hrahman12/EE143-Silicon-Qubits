"""Quantum simulations + animations (QuTiP 5) for the deck.

Run from repo root:  python3 figures/src/simulate_qubits.py [esr|rabi|grover|fab|yield|hero]

Physics inputs (all published):
  * Hamiltonian form: Reiner2024 Eq. 1, H = ge B.S + sum_i gn B.I_i + sum_i S.A_i.I_i  (isotropic A here)
  * Hyperfine A1, A2, A3 = 6, 68, 103 MHz (Thorvaldson2025 text)
  * Measured ESR lines 38.980 ... 39.157 GHz and NMR lines (Thorvaldson2025 Fig. 1b,c labels)
  * Electron T2* = 28.1 us; qubit quality Q = T2* f_Rabi = 4.82 -> f_Rabi = 171.5 kHz (derived)
  * Grover: 3 nuclear qubits, marked state |down,down,down>, r = 2; measured 93.46 % = 98.87 % of ideal
The electron and nuclear Zeeman frequencies (and refined A_i) are FITTED to the 14 measured lines.
"""
import os, sys, math, json
import numpy as np
import qutip as qt
from scipy.optimize import least_squares
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

OUT = "figures/final"
INK, MUTED, P_C, AS_C = "#1F2A36", "#5B6770", "#D9731A", "#0F9FA0"
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.edgecolor": "#9AA3AC"})

ESR_MEAS = np.array([38.980, 38.986, 39.048, 39.054, 39.083, 39.089, 39.151, 39.157]) * 1e3  # MHz
NMR_MEAS = {1: (27.182, 20.939), 2: (58.003, 9.824), 3: (75.594, 27.337)}                     # MHz
A_PUB = (6.0, 68.0, 103.0)


def to_gif(frames, path, ms=90):
    pal = [f.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=True, disposal=2)
    print("wrote", path, f"{os.path.getsize(path)/1e6:.2f} MB", len(frames), "frames")


def fig_to_img(fig, dpi=110):
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height(physical=True)
    im = Image.frombuffer("RGBA", (w, h), fig.canvas.buffer_rgba(), "raw", "RGBA", 0, 1).convert("RGB")
    plt.close(fig); return im


# ---------------------------------------------------------------- Hamiltonian (electron + 3 x 31P)
Se = [qt.tensor(op, qt.qeye(2), qt.qeye(2), qt.qeye(2)) for op in (qt.sigmax() / 2, qt.sigmay() / 2, qt.sigmaz() / 2)]
def nuc(i, op):
    ops = [qt.qeye(2)] * 4; ops[i + 1] = op; return qt.tensor(ops)
In = [[nuc(i, op) for op in (qt.sigmax() / 2, qt.sigmay() / 2, qt.sigmaz() / 2)] for i in range(3)]

def hamiltonian(ve, vn, A):
    H = ve * Se[2] - vn * sum(In[i][2] for i in range(3))   # 31P gyromagnetic ratio is positive; electron opposite sign
    for i in range(3):
        H += A[i] * sum(Se[k] * In[i][k] for k in range(3))
    return H

def transitions(ve, vn, A):
    """Return ESR (electron flips) and NMR (one nucleus flips) frequencies with matrix-element weights."""
    H = hamiltonian(ve, vn, A); E, V = H.eigenstates()
    Sx, Ix = Se[0], [In[i][0] for i in range(3)]
    esr, nmr = [], {1: [], 2: [], 3: []}
    for a in range(16):
        for b in range(a + 1, 16):
            f = abs(E[b] - E[a])
            me = abs(Sx.matrix_element(V[a].dag(), V[b])) ** 2
            if me > 0.05: esr.append((f, me))
            for i in range(3):
                mn = abs(Ix[i].matrix_element(V[a].dag(), V[b])) ** 2
                if mn > 0.05 and f < 500: nmr[i + 1].append((f, mn))
    return _uniq(esr), {k: _uniq(v) for k, v in nmr.items()}

def _uniq(lines, tol=0.05):
    """Merge degenerate copies of a transition (same frequency within tol MHz); sum their weights."""
    out = []
    for f, w in sorted(lines):
        if out and abs(f - out[-1][0]) < tol: out[-1] = ((out[-1][0] + f) / 2, out[-1][1] + w)
        else: out.append((f, w))
    return out

def residuals(p):
    ve, vn, a1, a2, a3 = p
    esr, nmr = transitions(ve, vn, (a1, a2, a3))
    fs = np.array([f for f, _ in esr])
    if len(fs) < 8: fs = np.pad(fs, (0, 8 - len(fs)), constant_values=fs.max())
    r = list(fs[:8] - np.sort(ESR_MEAS))
    for i in (1, 2, 3):
        sim = np.sort([f for f, _ in nmr[i]])
        r += [min(abs(sim - m)) for m in NMR_MEAS[i]]
    return np.array(r)


def esr_fit():
    p0 = [ESR_MEAS.mean(), 24.0, *A_PUB]
    sol = least_squares(residuals, p0, x_scale=[1e3, 10, 10, 10, 10])
    ve, vn, a1, a2, a3 = sol.x
    res = residuals(sol.x)
    esr, nmr = transitions(*sol.x[:2], sol.x[2:])
    out = dict(nu_e_MHz=ve, nu_n_MHz=vn, A_fit_MHz=[a1, a2, a3], A_pub_MHz=list(A_PUB),
               rms_residual_kHz=float(np.sqrt(np.mean(res ** 2)) * 1e3), max_residual_kHz=float(np.max(np.abs(res)) * 1e3),
               esr_sim_GHz=[f / 1e3 for f, _ in esr[:8]], nmr_sim_MHz={k: [f for f, _ in v] for k, v in nmr.items()})
    json.dump(out, open("notes/specs/qutip_fit.json", "w"), indent=2)
    print(json.dumps(out, indent=1))
    # ---- figure: simulated stick spectrum (Lorentzians) vs measured line positions
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.6), gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.28))
    f = np.linspace(38.95, 39.19, 3000) * 1e3; spec = np.zeros_like(f)
    for fr, w in esr[:8]: spec += w * (0.6 ** 2) / ((f - fr) ** 2 + 0.6 ** 2)
    a.plot(f / 1e3, spec / spec.max(), color=AS_C, lw=1.6, label="QuTiP simulation")
    for m in ESR_MEAS: a.axvline(m / 1e3, color=INK, lw=0.9, ls=":", ymax=0.92)
    a.plot([], [], color=INK, ls=":", label="measured (Thorvaldson2025)")
    a.set_xlabel("ESR frequency (GHz)"); a.set_yticks([]); a.set_ylim(0, 1.5)
    a.legend(fontsize=7.5, frameon=False, loc="upper left", ncol=2, bbox_to_anchor=(0, 1.02))
    a.set_title("8 electron lines = 2³ nuclear states", fontsize=9.5, loc="left")
    g = np.linspace(0, 85, 3000); s2 = np.zeros_like(g); cols = {1: "#2B6CB0", 2: "#2F9E44", 3: "#C92A2A"}
    for i in (1, 2, 3):
        for fr, w in nmr[i][:2]:
            s2 += 0.3 ** 2 / ((g - fr) ** 2 + 0.3 ** 2)
            b.plot([fr, fr], [0, 1], color=cols[i], lw=1.8)
        for m in NMR_MEAS[i]: b.plot(m, 1.08, "v", color=cols[i], ms=5)
    b.set_xlabel("NMR frequency (MHz)"); b.set_yticks([]); b.set_ylim(0, 1.3); b.set_xlim(0, 85)
    b.set_title("6 nuclear lines (▼ measured)", fontsize=9.5, loc="left")
    for i, x in ((1, 2), (2, 30), (3, 58)): b.text(x, 1.22, f"n{i}", color=cols[i], fontsize=8.5, fontweight="bold")
    for ax in (a, b):
        for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
    fig.savefig(f"{OUT}/S_esr_nmr_fit.png", dpi=300, bbox_inches="tight", facecolor="white"); plt.close(fig)
    print("wrote S_esr_nmr_fit.png")
    return sol.x


def rabi_gif(params=None):
    """Conditional electron Rabi drive on the |down,down,down> ESR line, with T2* quasi-static dephasing."""
    if params is None: params = json.load(open("notes/specs/qutip_fit.json"))
    T2s, Q = 28.1, 4.82                         # us; Thorvaldson2025
    fR = Q / T2s                                # MHz (= 0.1715 MHz)
    t = np.linspace(0, 3.0 / fR, 160)           # us, three Rabi periods
    sig = math.sqrt(2) / (2 * math.pi * T2s)    # MHz, Gaussian detuning spread giving exp(-(t/T2*)^2) decay
    dets = np.linspace(-3 * sig, 3 * sig, 41); wts = np.exp(-dets ** 2 / (2 * sig ** 2)); wts /= wts.sum()
    def drive(delta):  # two-level electron in rotating frame, delta in MHz
        H = 2 * math.pi * (delta / 2 * qt.sigmaz() + fR / 2 * qt.sigmax())
        r = qt.sesolve(H, qt.basis(2, 1), t, e_ops=[qt.sigmax(), qt.sigmay(), qt.sigmaz()])
        return np.array(r.expect)
    on = sum(w * drive(d) for d, w in zip(dets, wts))
    off = drive(6.0)                            # nearest other ESR line is A1 = 6 MHz away
    Pup_on, Pup_off = (1 + on[2]) / 2, (1 + off[2]) / 2
    frames = []
    for k in range(0, len(t), 4):
        fig = plt.figure(figsize=(6.6, 2.9), facecolor="white")
        ax = fig.add_subplot(1, 2, 1, projection="3d", computed_zorder=False)
        u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:20j]
        ax.plot_surface(np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v), color="#E8F4F4", alpha=0.18, lw=0)
        th = np.linspace(0, 2 * np.pi, 100)
        ax.plot(np.cos(th), np.sin(th), 0 * th, color="#C3CAD1", lw=0.6); ax.plot(0 * th, np.cos(th), np.sin(th), color="#C3CAD1", lw=0.6)
        ax.plot(on[0][:k + 1], on[1][:k + 1], on[2][:k + 1], color=AS_C, lw=1.2, alpha=0.7)
        ax.quiver(0, 0, 0, on[0][k], on[1][k], on[2][k], color=AS_C, lw=2.4, arrow_length_ratio=0.12)
        ax.text(0, 0, 1.35, "|↑⟩", ha="center", fontsize=10); ax.text(0, 0, -1.55, "|↓⟩", ha="center", fontsize=10)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=15, azim=40); ax.axis("off")
        ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
        ax.set_title("electron spin, nuclei in |⇓⇓⇓⟩", fontsize=9, color=INK)
        b = fig.add_subplot(1, 2, 2)
        b.plot(t[:k + 1], Pup_on[:k + 1], color=AS_C, lw=2, label="nuclei |⇓⇓⇓⟩ (resonant)")
        b.plot(t[:k + 1], Pup_off[:k + 1], color="#9AA3AC", lw=2, label="other nuclear state (6 MHz off)")
        b.set_xlim(0, t[-1]); b.set_ylim(-0.03, 1.45); b.set_xlabel("drive time (µs)", fontsize=9); b.set_ylabel("P(↑)", fontsize=9)
        b.legend(fontsize=7.5, frameon=False, loc="upper left", ncol=1); b.tick_params(labelsize=8)
        for sp in ("top", "right"): b.spines[sp].set_visible(False)
        b.set_title(f"f_Rabi = {fR*1e3:.0f} kHz, T₂* = 28.1 µs", fontsize=9, loc="left")
        fig.tight_layout(); frames.append(fig_to_img(fig, 100))
    frames[0].save(f"{OUT}/S_rabi_first.png")
    to_gif(frames, f"{OUT}/S_rabi.gif", ms=80)


def grover_gif():
    """Ideal 3-qubit Grover (marked |down,down,down> = |111>), r = 2, in QuTiP; compare to measured 93.46 %."""
    N = 8; marked = 7
    s = qt.Qobj(np.ones(N) / np.sqrt(N))
    oracle = qt.qeye(N) - 2 * qt.basis(N, marked) * qt.basis(N, marked).dag()
    diffusion = 2 * s * s.dag() - qt.qeye(N)
    steps = [("uniform superposition", s)]
    psi = s
    for r in (1, 2):
        psi = oracle * psi; steps.append((f"oracle {r}: flip sign of |⇓⇓⇓⟩", psi))
        psi = diffusion * psi; steps.append((f"diffusion {r}: invert about the mean", psi))
    amps = [np.real(p.full().ravel()) for _, p in steps]
    ideal = float(amps[-1][marked] ** 2)
    print("ideal P(marked) after r=2:", ideal, " measured 93.46% / ideal =", 0.9346 / ideal)
    labels = ["⇑⇑⇑", "⇑⇑⇓", "⇑⇓⇑", "⇑⇓⇓", "⇓⇑⇑", "⇓⇑⇓", "⇓⇓⇑", "⇓⇓⇓"]
    frames = []
    for k in range(len(steps) - 1):
        for a in np.linspace(0, 1, 9):
            frames.append((steps[k + 1][0], (1 - a) * amps[k] + a * amps[k + 1], False))
    frames = [(steps[0][0], amps[0], False)] * 6 + frames + [(steps[-1][0], amps[-1], True)] * 14
    imgs = []
    for title, amp, final in frames:
        fig, ax = plt.subplots(figsize=(5.4, 2.9))
        cols = [AS_C if i == marked else "#9AA3AC" for i in range(N)]
        ax.bar(range(N), amp, color=cols, width=0.7)
        ax.axhline(np.mean(amp), color=P_C, lw=1.2, ls="--"); ax.text(-0.5, np.mean(amp) + 0.03, "mean", color=P_C, fontsize=8)
        ax.axhline(0, color=INK, lw=0.8)
        ax.set_xticks(range(N)); ax.set_xticklabels(labels, fontsize=8); ax.set_ylim(-0.75, 1.05); ax.set_ylabel("amplitude", fontsize=9)
        ax.set_title(title, fontsize=10, loc="left")
        if final:
            ax.text(4.5, 0.95, f"ideal P = {ideal*100:.1f}%\nhardware: 93.46%", ha="center", va="top", fontsize=9,
                    bbox=dict(boxstyle="round", fc="white", ec=AS_C))
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
        ax.tick_params(labelsize=8); fig.tight_layout(); imgs.append(fig_to_img(fig, 100))
    imgs[-1].save(f"{OUT}/S_grover_last.png")
    to_gif(imgs, f"{OUT}/S_grover.gif", ms=110)


def yield_gif():
    """Monte Carlo: fill 4x4 arrays site by site at p = 0.70 (P) and 0.97 (As); running perfect-array count."""
    rng = np.random.default_rng(7)
    trials = 8; tally = {"P": 0, "As": 0}; imgs = []
    arrays = {k: rng.random((trials, 16)) < p for k, p in (("P", 0.70), ("As", 0.97))}
    for tr in range(trials):
        for site in list(range(0, 16, 2)) + [15]:
            fig, axs = plt.subplots(1, 2, figsize=(5.6, 2.8))
            for ax, (k, col) in zip(axs, (("P", P_C), ("As", AS_C))):
                arr = arrays[k][tr]
                for j in range(16):
                    x, y = j % 4, 3 - j // 4
                    if j > site: ax.add_patch(Circle((x, y), 0.33, fill=False, ec="#C3CAD1", lw=1.2))
                    elif arr[j]: ax.add_patch(Circle((x, y), 0.36, color=col))
                    else:
                        ax.add_patch(Circle((x, y), 0.36, fill=False, ec="#B03030", lw=2)); ax.plot([x - .25, x + .25], [y - .25, y + .25], color="#B03030", lw=1.8)
                done = site == 15
                perfect = tally[k] + (1 if done and arr.all() else 0)
                ax.set_title(f"{k}, p = {0.70 if k=='P' else 0.97}   perfect: {perfect}/{tr + (1 if done else 0)}", fontsize=9.5, loc="left")
                if done and arr.all(): ax.add_patch(Rectangle((-.55, -.55), 4.1, 4.1, fill=False, ec=INK, lw=2))
                ax.set_xlim(-.7, 3.7); ax.set_ylim(-.7, 3.7); ax.set_aspect("equal"); ax.axis("off")
            fig.tight_layout(); imgs.append(fig_to_img(fig, 90))
        for k in tally: tally[k] += int(arrays[k][tr].all())
        imgs += [imgs[-1]] * 3
    to_gif(imgs, f"{OUT}/S_yield_mc.gif", ms=90)


def fab_gif():
    """STM write (H removed one atom at a time) -> AsH3 / PH3 dose -> 350 C anneal, on the Si(001):H geometry."""
    sys.path.insert(0, "figures/src")
    import make_figures as mf
    A = mf.A
    Pwin = [(1, k, s) for k in (3, 4, 5) for s in (-1, 1)]
    Aswin = [(3, k, s) for k in (3, 4) for s in (-1, 1)]
    order = Aswin + Pwin
    states = []
    for n in range(len(order) + 1): states.append(("write", set(order[:n]), None))
    for st in ("dose", "dose", "frag", "frag", "anneal", "anneal", "anneal"): states.append((st, set(order), None))
    top, sub = mf.si001(5, 9)
    imgs = []
    for idx, (stage, removed, _) in enumerate(states):
        sc = mf.Scene(az=-32, el=38)
        for (x, y, z) in sub:
            if -1.5 < x < 4 * 2 * A + 1.5: sc.ball(x, y, z, 0.95, "#9AA3AC")
        fig, ax = plt.subplots(figsize=(6.4, 4.0))
        for (r, k, s, x, y, z) in top:
            key = (r, k, s)
            col = mf.SI_ATOM
            if stage == "anneal" and key == (3, 3, -1): col = AS_C
            elif key in removed: col = "#EDB98A" if r == 1 else "#86D0D0"
            sc.ball(x, y, z, 1.05, col)
            if key not in removed: sc.ball(x + s * 0.45, y, z + 1.44, 0.72, mf.H_ATOM)
        r1x, r3x = 1 * 2 * A, 3 * 2 * A
        if stage == "dose":
            sc.ball(r3x, 3.5 * A, 4.5, 1.05, AS_C); [sc.ball(r3x + dx, 3.5 * A + dy, 5.2, 0.5, mf.H_ATOM) for dx, dy in ((1.2, .6), (-1.2, .6), (0, -1.3))]
            sc.ball(r1x, 4 * A, 4.5, 1.0, P_C); [sc.ball(r1x + dx, 4 * A + dy, 5.2, 0.5, mf.H_ATOM) for dx, dy in ((1.2, .6), (-1.2, .6), (0, -1.3))]
        if stage == "frag":
            sc.ball(r3x - 1.17, 3.5 * A, 1.6, 1.05, AS_C)
            for (dx, dy) in ((1.7, 3 * A), (1.7, 4 * A), (-1.7, 4.4 * A)): sc.ball(r3x + dx, dy, 1.4, 0.55, mf.H_ATOM)
            sc.ball(r1x - 1.17, 4 * A, 1.7, 1.0, P_C); sc.ball(r1x - 1.6, 4 * A + 0.9, 2.6, 0.5, mf.H_ATOM); sc.ball(r1x + 1.7, 3 * A, 1.4, 0.55, mf.H_ATOM)
        if stage == "anneal":
            sc.ball(r3x + 1.2, 6.6 * A, 1.3, 1.05, "#C3CAD1")
        sc.draw(ax)
        if stage == "write" and idx < len(order) and idx > 0 or stage == "write" and idx == 0:
            tgt = order[min(idx, len(order) - 1)]
            u, w, _ = sc.proj(tgt[0] * 2 * A + tgt[2] * 1.18, tgt[1] * A, 0)
            ax.add_patch(Polygon([[u - 2.2, w + 13], [u + 2.2, w + 13], [u, w + 3.2]], color=mf.TIP, zorder=50))
        label = {"write": f"Step 4 · STM tip removes H one atom at a time ({len(removed)}/10)", "dose": "Step 5 · AsH₃ (teal) and PH₃ (orange) arrive",
                 "frag": "Step 5 · molecules dissociate in the windows", "anneal": "Step 6 · 350 °C: As incorporates, ejects one Si"}[stage]
        ax.text(0.0, 1.02, label, transform=ax.transAxes, fontsize=10.5, color=INK, fontweight="bold")
        ax.autoscale_view(); ax.margins(0.02)
        imgs.append(fig_to_img(fig, 85)); print("fab frame", idx)
    imgs = imgs + [imgs[-1]] * 6
    to_gif(imgs, f"{OUT}/S_fab.gif", ms=350)


def hero_gif():
    """Title animation: gentle rotation + spin precession + wavefunction pulse + tip tunnelling flash (24 frames, loops)."""
    sys.path.insert(0, "figures/src")
    import make_figures as mf
    frames = []
    for k in range(24):
        ph = k / 24
        mf.hero(az=-35 + 7 * math.sin(2 * math.pi * ph), fname="_hero_frame.png", phase=ph)
        im = Image.open(f"{OUT}/_hero_frame.png").convert("RGB"); im.thumbnail((1000, 900)); frames.append(im)
    os.remove(f"{OUT}/_hero_frame.png")
    to_gif(frames, f"{OUT}/S_hero.gif", ms=110)


def lindblad_gif():
    """Ramsey free evolution of one electron spin: Lindblad (Markovian) vs quasi-static (non-Markovian) dephasing.
    Same characteristic time T2* = 28.1 us (Thorvaldson2025). Detuning 0.2 MHz is illustrative.
    Also: driven Rabi under Lindblad with T2^Rabi = Q_gate / f_Rabi = 34 / 0.1715 MHz = 198 us (derived)."""
    T2s, delta = 28.1, 0.2
    t = np.linspace(0, 60, 241)
    H = 2 * math.pi * delta / 2 * qt.sigmaz()
    psi0 = (qt.basis(2, 0) + qt.basis(2, 1)).unit()
    gamma = 1 / T2s
    L = [math.sqrt(gamma / 2) * qt.sigmaz()]          # pure dephasing: coherence decays as exp(-t/T2)
    rl = qt.mesolve(H, psi0, t, c_ops=L, e_ops=[qt.sigmax(), qt.sigmay(), qt.sigmaz()])
    lx, ly, lz = [np.array(e) for e in rl.expect]
    sig = math.sqrt(2) / (2 * math.pi * T2s)
    dets = np.linspace(-3.5 * sig, 3.5 * sig, 61); w = np.exp(-dets ** 2 / (2 * sig ** 2)); w /= w.sum()
    qx = np.zeros_like(t); qy = np.zeros_like(t)
    for d, wt in zip(dets, w):
        r = qt.sesolve(2 * math.pi * (delta + d) / 2 * qt.sigmaz(), psi0, t, e_ops=[qt.sigmax(), qt.sigmay()])
        qx += wt * np.array(r.expect[0]); qy += wt * np.array(r.expect[1])
    # check analytic envelopes
    print("Lindblad |r| at T2*:", np.hypot(lx, ly)[np.argmin(abs(t - T2s))], "(e^-1 = 0.368)")
    print("quasi-static |r| at T2*:", np.hypot(qx, qy)[np.argmin(abs(t - T2s))], "(e^-1 = 0.368)")
    frames = []
    for k in range(0, len(t), 6):
        fig = plt.figure(figsize=(7.4, 3.0), facecolor="white")
        for j, (X, Y, col, ttl) in enumerate(((lx, ly, AS_C, "Lindblad (Markovian)"), (qx, qy, P_C, "quasi-static noise"))):
            ax = fig.add_subplot(1, 3, j + 1, projection="3d", computed_zorder=False)
            u, v = np.mgrid[0:2 * np.pi:30j, 0:np.pi:15j]
            ax.plot_surface(np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v), color="#EEF2F5", alpha=0.18, lw=0)
            th = np.linspace(0, 2 * np.pi, 80); ax.plot(np.cos(th), np.sin(th), 0 * th, color="#C3CAD1", lw=0.6)
            ax.plot(X[:k + 1], Y[:k + 1], 0 * X[:k + 1], color=col, lw=1.0, alpha=0.6)
            ax.quiver(0, 0, 0, X[k], Y[k], 0, color=col, lw=2.4, arrow_length_ratio=0.15)
            ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=28, azim=35); ax.axis("off")
            ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1); ax.set_title(ttl, fontsize=9, color=INK)
        b = fig.add_subplot(1, 3, 3)
        b.plot(t[:k + 1], np.hypot(lx, ly)[:k + 1], color=AS_C, lw=2, label="Lindblad: e$^{-t/T_2}$")
        b.plot(t[:k + 1], np.hypot(qx, qy)[:k + 1], color=P_C, lw=2, label="quasi-static: e$^{-(t/T_2^*)^2}$")
        b.axvline(T2s, color="#9AA3AC", ls=":", lw=1); b.text(T2s + 1, 0.92, "T₂* = 28.1 µs", fontsize=7.5, color=MUTED)
        b.set_xlim(0, 60); b.set_ylim(0, 1.05); b.set_xlabel("free evolution (µs)", fontsize=8.5); b.set_ylabel("coherence |⟨σ⊥⟩|", fontsize=8.5)
        b.legend(fontsize=7, frameon=False, loc="lower left"); b.tick_params(labelsize=7.5)
        for sp in ("top", "right"): b.spines[sp].set_visible(False)
        fig.tight_layout(); frames.append(fig_to_img(fig, 100))
    to_gif(frames, f"{OUT}/S_lindblad.gif", ms=90)


def overlap_gif():
    """Two hydrogenic envelopes (a_B = 2 nm, Schofield2025 §3.2) pulled apart from 6 to 20 nm on the Si(001) lattice;
    overlap S(R) = e^{-R/a}(1 + R/a + R^2/3a^2) (textbook 1s overlap; our envelope model, no valley oscillations)."""
    aB, a = 2.0, 0.384
    Rs = np.concatenate([np.linspace(6, 20, 15), np.linspace(20, 6, 15)[1:-1]])
    S = lambda R: np.exp(-R / aB) * (1 + R / aB + R ** 2 / (3 * aB ** 2))
    from matplotlib.colors import LinearSegmentedColormap
    cm = LinearSegmentedColormap.from_list("q", ["#FFFFFF", "#CFEFEF", "#5FC9C9", "#0F9FA0", "#075E5F"])
    x = np.linspace(-6, 26, 520); y = np.linspace(-5, 5, 170); X, Y = np.meshgrid(x, y)
    frames = []
    for R in Rs:
        fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.4, 2.6), gridspec_kw=dict(width_ratios=[2.1, 1], wspace=0.25))
        d = np.exp(-2 * np.hypot(X, Y) / aB) + np.exp(-2 * np.hypot(X - R, Y) / aB)
        ax.imshow(np.log10(d + 1e-9), extent=(x[0], x[-1], y[0], y[-1]), origin="lower", cmap=cm, vmin=-3.2, vmax=0, aspect="equal")
        gx, gy = np.meshgrid(np.arange(x[0], x[-1], a), np.arange(y[0], y[-1], 2 * a)); ax.scatter(gx, gy, s=0.3, color="#5B6770", alpha=0.5, lw=0)
        for x0 in (0, R): ax.add_patch(Circle((x0, 0), 0.28, color=P_C, zorder=3))
        ax.annotate("", (R, -4.0), (0, -4.0), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.1))
        ax.text(R / 2, -3.7, f"R = {R:.1f} nm  (≈{R / a:.0f} lattice sites)", ha="center", fontsize=8.5)
        ax.set_xticks([]); ax.set_yticks([]); [sp.set_visible(False) for sp in ax.spines.values()]
        ax.set_title("two P donors, |ψ|² (log scale), a_B ≈ 2 nm", fontsize=9, loc="left")
        rr = np.linspace(5, 21, 200); bx.semilogy(rr, S(rr), color=AS_C, lw=2); bx.semilogy([R], [S(R)], "o", color=P_C, ms=8)
        bx.axvline(13.0, color="#9AA3AC", ls=":", lw=1); bx.text(13.3, 0.3, "He2019\n13 nm", fontsize=7, color=MUTED)
        bx.set_xlabel("donor spacing R (nm)", fontsize=8.5); bx.set_ylabel("overlap S(R)", fontsize=8.5); bx.tick_params(labelsize=7.5)
        bx.set_title("coupling falls exponentially", fontsize=9, loc="left")
        for sp in ("top", "right"): bx.spines[sp].set_visible(False)
        fig.subplots_adjust(left=0.02, right=0.98, bottom=0.2, top=0.88); frames.append(fig_to_img(fig, 100))
    to_gif(frames, f"{OUT}/S_overlap.gif", ms=110)


def burial_gif():
    """DAnna2023 stack grown in time: 2 nm at RT, RTA 500 C x 15 s, 28 nm at 250 C, 0.003 nm/s (thickness axis to scale)."""
    prog = [(0, 25), (2, 25), (2, 500), (2, 250), (30, 250)]
    fr = list(np.linspace(0, 2, 8)) + [2] * 4 + list(np.linspace(2, 30, 22)) + [30] * 6
    phase = ["lock"] * 8 + ["rta"] * 4 + ["cap"] * 22 + ["done"] * 6
    frames = []
    for th, ph in zip(fr, phase):
        fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.4, 2.8), gridspec_kw=dict(width_ratios=[1.3, 1], wspace=0.3))
        ax.add_patch(Rectangle((0, -10), 40, 10, color="#8C96A0"))
        ax.add_patch(Rectangle((0, -0.4), 40, 0.8, color=AS_C))
        if th > 0: ax.add_patch(Rectangle((0, 0.4), 40, min(th, 2), color="#B5BEC6"))
        if th > 2: ax.add_patch(Rectangle((0, 2.4), 40, th - 2, color="#C9D1D8"))
        if ph == "rta":
            for k in range(6): ax.add_patch(Rectangle((0, -10), 40, 42, color="#E8590C", alpha=0.05 + 0.02 * k))
        ax.text(1, -6, "Si(001) substrate", color="white", fontsize=8.5); ax.text(41, -0.5, "As δ-layer", fontsize=8, color="#075E5F")
        if th > 2: ax.text(1, 2.4 + (th - 2) / 2, f"Si cap {th - 2:.0f} nm, 250 °C", fontsize=8, va="center")
        ax.text(1, 31, {"lock": "2 nm lock layer, room temperature", "rta": "RTA 500 °C × 15 s", "cap": "28 nm epitaxy at 250 °C, 0.003 nm/s", "done": "As layer buried 30 nm"}[ph], fontsize=9.5, fontweight="bold")
        ax.set_xlim(0, 52); ax.set_ylim(-10, 34); ax.set_xticks([]); ax.set_ylabel("height above δ-layer (nm)", fontsize=8); ax.tick_params(labelsize=7.5)
        for sp in ("top", "right", "bottom"): ax.spines[sp].set_visible(False)
        tt = [0, 2, 2.05, 2.1, 30]; TT = [25, 25, 500, 250, 250]
        bx.plot(tt, TT, color="#C3CAD1", lw=1.5)
        if ph == "lock": px, py = [0, th], [25, 25]
        elif ph == "rta": px, py = [0, 2, 2.05], [25, 25, 500]
        else: px, py = [0, 2, 2.05, 2.1, th], [25, 25, 500, 250, 250]
        bx.plot(px, py, color=AS_C, lw=2.2)
        cur = 500 if ph == "rta" else (25 if th <= 2 else 250); bx.plot([min(th, 30)], [cur], "o", color=P_C, ms=8)
        bx.set_xlim(0, 30); bx.set_ylim(0, 560); bx.set_xlabel("Si deposited (nm)", fontsize=8.5); bx.set_ylabel("T (°C)", fontsize=8.5); bx.tick_params(labelsize=7.5)
        bx.set_title("DAnna2023 thermal program", fontsize=9, loc="left")
        for sp in ("top", "right"): bx.spines[sp].set_visible(False)
        fig.subplots_adjust(left=0.08, right=0.97, bottom=0.18, top=0.92); frames.append(fig_to_img(fig, 100))
    to_gif(frames, f"{OUT}/S_burial.gif", ms=120)


THEMES = [("Dopant chemistry & placement", "#0F9FA0"), ("Imaging & metrology", "#2F6FB0"), ("Lithography & scaling", "#A87F12"),
          ("Quantum devices & theory", "#7A4E9C"), ("Noise & interfaces", "#B03A48"), ("Ge & other surfaces", "#9AA3AC")]

def curson_gif():
    """All of N. J. Curson's papers (ORCID + Crossref): bubbles appear year by year; size and height = citations."""
    P = json.load(open("notes/curson/curson_papers.json"))
    col = dict(THEMES); rng = np.random.default_rng(3)
    for p in P: p["jit"] = rng.uniform(-0.32, 0.32); p["c"] = max(p["cites"] or 0, 0)
    top = sorted(P, key=lambda p: -p["c"])[:6]
    short = {"10.1103/physrevlett.91.136104": "single P placed (2003)", "10.1063/1.1516859": "P encapsulation (2002)",
             "10.1038/s41534-020-0253-9": "topological Hubbard (2020)", "10.1038/ncomms2679": "dangling-bond quantum (2013)",
             "10.1103/physrevlett.93.226102": "PH₃ dissociation (2004)", "10.1103/physrevb.64.161401": "P qubit arrays (2001)",
             "10.1088/0953-8984/26/1/012001": "single As by STM (2014)", "10.1021/nl048808v": "contacting buried devices (2004)",
             "10.1103/physrevb.74.195310": "PH₃ desorption (2006)", "10.1126/sciadv.1602586": "buried-device imaging (2017)",
             "10.1021/acsnano.9b08943": "As patterned by STM (2020)"}
    offs = {"10.1103/physrevlett.91.136104": (10, -2), "10.1103/physrevb.64.161401": (-8, 10), "10.1103/physrevlett.93.226102": (-30, 16),
            "10.1103/physrevb.74.195310": (10, 2), "10.1126/sciadv.1602586": (-40, 14), "10.1021/acsnano.9b08943": (8, 8)}
    years = list(range(1994, 2027))
    frames = []
    for k, Y in enumerate(years + [2026] * 10):
        fig, ax = plt.subplots(figsize=(7.4, 3.6))
        shown = [p for p in P if p["year"] <= Y]
        for name, c in THEMES[::-1]:
            pts = [p for p in shown if p["theme"] == name]
            if pts:
                ax.scatter([p["year"] + p["jit"] for p in pts], [p["c"] + 1 for p in pts], s=[18 + 2.2 * p["c"] for p in pts],
                           color=c, alpha=0.8, edgecolor="white", lw=0.8, zorder=3 if c != "#9AA3AC" else 2)
        for p in top:
            if p["year"] <= Y:
                ax.annotate(short.get(p["doi"], p["title"][:28]), (p["year"] + p["jit"], p["c"] + 1), xytext=offs.get(p["doi"], (6, 4)), textcoords="offset points", fontsize=7.5, color=INK)
        ax.set_yscale("log"); ax.set_ylim(0.8, 1500); ax.set_xlim(1993, 2027)
        ax.set_ylabel("citations + 1 (log)", fontsize=8.5); ax.tick_params(labelsize=8)
        ax.text(0.99, 0.97, f"{Y}:  {len(shown)} papers,  {sum(p['c'] for p in shown):,} citations (Crossref)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="top", ha="right")
        handles = [plt.Line2D([], [], marker="o", ls="", color=c, ms=7, label=n) for n, c in THEMES]
        ax.legend(handles=handles, fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
        fig.tight_layout(); frames.append(fig_to_img(fig, 100))
    frames[-1].save(f"{OUT}/S_curson_last.png")
    to_gif(frames, f"{OUT}/S_curson.gif", ms=170)


if __name__ == "__main__":
    jobs = sys.argv[1:] or ["esr", "rabi", "grover", "yield", "fab", "hero", "lindblad", "overlap", "burial"]
    for j in jobs:
        {"esr": esr_fit, "rabi": rabi_gif, "grover": grover_gif, "yield": yield_gif, "fab": fab_gif, "hero": hero_gif, "lindblad": lindblad_gif, "overlap": overlap_gif, "burial": burial_gif, "curson": curson_gif}[j]()
