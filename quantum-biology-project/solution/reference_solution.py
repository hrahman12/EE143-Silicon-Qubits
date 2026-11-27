"""Instructor reference solution for the FMO quantum-biology term project.

INSTRUCTOR ONLY. Do not distribute to students.

Every quantum object and every piece of quantum dynamics goes through QuTiP 5.
NumPy is used only to load the CSV, for unit constants, for the Haken-Strobl
rate table, for the FFT and for printing. There are no hand-written integrators,
matrix exponentials or HEOM; the only superoperator assembled here (the
t -> infinity check in Part 3) is composed from QuTiP's liouvillian, spre and
spost and does not feed the reported eta. Tested with QuTiP 5.3.1, NumPy 2.5.3, SciPy 1.18.1 and
Python 3.13, and gives identical output on QuTiP 5.2.0. QuTiP 5.2 is the minimum
because Part 4 needs DrudeLorentzEnvironment.approximate().

Part 1  Qobj(H).eigenstates(): exciton energies and participation numbers
        N_k = 1 / sum_j |c_jk|^4, with |c_jk|^2 = expect(|j><j|, |k>).
Part 2  sesolve with the exact 'diag' propagator: site populations from 0 to
        1 ps for each starting site. The FFT of the starting-site population is
        compared with the exciton gaps |E_k - E_l|, weighted by
        2 |c_sk|^2 |c_sl|^2, the amplitude of that beat in P_s(t).
Part 3  mesolve on N + 2 levels (sites, sink |s>, ground |g>) with c_ops
        sqrt(gamma)|j><j|, sqrt(kappa)|s><trap| and sqrt(Gamma)|g><j|, using
        the exact 'diag' propagator. eta is the sink population at the first
        output time at which less than 1e-3 remains on the sites (the handout
        definition). The stopping time and residual are reported, and the
        t -> infinity limit, eta = kappa <trap| (-L_T^-1 rho0) |trap>, is
        computed from QuTiP's Liouvillian as a check. The classical Haken-Strobl
        model runs through the same mesolve with H = 0 and jump operators
        sqrt(k_ij)|i><j|, which give the Pauli rate equation exactly.
Part 4  HEOMSolver with one independent Drude-Lorentz bath per site, in the
        high-temperature (Ishizaki-Fleming) form
        C(t) = (2 lambda kT - i lambda gamma_c) exp(-gamma_c t), with no
        Matsubara terms. It raises the hierarchy depth until the populations
        change by less than --tol between successive depths, and reports the
        minimum site population and density-matrix eigenvalue (the high-T model
        is not guaranteed positive). As a benchmark beyond the high-temperature
        approximation (the handout hint), it also runs the exact-coefficient
        Pade (Nk=1) expansion of DrudeLorentzEnvironment plus the terminator at
        depths 3 and 4.

Units: QuTiP has no built-in units (hbar = k_B = 1). Energies, rates and kT are
in rad/fs (omega = 2 pi c nu), and times are in fs.

Usage (from any directory):
  python3 reference_solution.py                        # parts 1 2 3
  python3 reference_solution.py --parts 1 2 3 4        # all parts, incl. HEOM
  python3 reference_solution.py --parts 4 --depths 3 4 # HEOM at fixed depths
  python3 reference_solution.py --hamiltonian other.csv --trap 2 --starts 1 4
"""
import argparse
import os
import time

import numpy as np
import qutip as qt
from qutip.solver.heom import HEOMSolver

HERE = os.path.dirname(os.path.abspath(__file__))
C_CM = 2.99792458e10        # speed of light, cm/s
W = 2*np.pi*C_CM*1e-15      # rad/fs per cm^-1 (1.884e-4)
KB = 0.6950348              # Boltzmann constant, cm^-1 per K
KAPPA = 1e-3                # trap rate, 1/fs (1 ps^-1)
LOSS = 1e-6                 # loss rate to ground on every site, 1/fs (1 ns^-1)
STOP = 1e-3                 # eta is read once less than this remains on the sites
LAM_CM, TAU_C = 35.0, 50.0  # Drude-Lorentz lambda (cm^-1) and 1/gamma_c (fs)
TEMPS = (77, 300)           # K
GAMMAS = np.r_[0.0, np.logspace(-1, 5, 25)]          # Part 3 sweep, cm^-1
GAMMAS_100PS = (0, 1, 10, 30, 100, 300, 1000, 1e4, 1e5)
DIAG = {"method": "diag", "normalize_output": False}  # exact exponentiation
HEOM_OPTS = {"progress_bar": "", "method": "adams", "store_states": True,
             "rtol": 1e-8, "atol": 1e-10, "nsteps": 20000}
HEOM_TOL, HEOM_MAX_DEPTH = 1e-3, 8                    # Part 4 depth convergence


def fmt(xs, f="{:.3f}"):
    return " ".join(f.format(x) for x in xs)


# ------------------------------------------------------------------ Part 1
def part1(Hcm, show=True):
    N = Hcm.shape[0]
    E, kets = qt.Qobj(Hcm).eigenstates()                 # ascending energies
    P = [qt.projection(N, j, j) for j in range(N)]
    w = np.array(qt.expect(P, list(kets)))               # w[j, k] = |c_jk|^2
    pn = 1/np.sum(w**2, axis=0)
    if show:
        print("Part 1  exciton energies (cm^-1, offset removed):", fmt(E, "{:.1f}"))
        print("        participation numbers N_k:                 ", fmt(pn, "{:.2f}"))
        print("        two largest sites per exciton (BChl):     ",
              " ".join("{}/{}".format(*(np.argsort(-w[:, k])[:2] + 1))
                       for k in range(N)))
    return E, w


# ------------------------------------------------------------------ Part 2
def part2(Hcm, E, w, starts, trap):
    N = Hcm.shape[0]
    t = np.linspace(0, 1000, 4001)                       # fs
    P = [qt.projection(N, j, j) for j in range(N)]
    f = np.fft.rfftfreq(t.size, d=(t[1]-t[0])*1e-15)/C_CM  # cm^-1
    print(f"Part 2  coherent sesolve 0-1 ps; FFT resolution {f[1]:.0f} cm^-1")
    for s in starts:
        res = qt.sesolve(qt.Qobj(Hcm*W), qt.basis(N, s), t, e_ops=P,
                         options=DIAG)               # no renormalization: real norm check
        pop = np.array(res.expect).real                  # (N, len(t))
        S = np.abs(np.fft.rfft(pop[s] - pop[s].mean()))
        loc = [i for i in range(1, S.size-1) if S[i] > S[i-1] and S[i] >= S[i+1]]
        loc = sorted(loc, key=lambda i: -S[i])[:3]
        pairs = sorted(((2*w[s, k]*w[s, l], E[l]-E[k], k, l)
                        for k in range(N) for l in range(k+1, N)), reverse=True)[:3]
        if loc:
            print(f"        start BChl {s+1}: FFT peaks of P{s+1} at "
                  + ", ".join(f"{f[i]:.0f}" for i in loc)
                  + f" cm^-1 (main period {1e15/(f[loc[0]]*C_CM):.0f} fs)")
        else:
            print(f"        start BChl {s+1}: no beats (P{s+1} is constant; site uncoupled)")
        print("          strongest predicted beats E_l-E_k (weight 2|c_sk|^2|c_sl|^2): "
              + ", ".join(f"{g:.0f} cm^-1 (E{l+1}-E{k+1}, {a:.2f})" for a, g, k, l in pairs))
        print(f"          P{trap+1} (trap site): max {pop[trap].max():.3f}, "
              f"mean {pop[trap].mean():.3f}; norm drift {abs(pop.sum(0)-1).max():.1e}")


# ------------------------------------------------------------------ Part 3
def hs_rates(Hw, g):
    """Haken-Strobl rate table k[i, j] for j -> i, all in rad/fs."""
    eps = np.diag(Hw)
    k = 2*np.abs(Hw)**2*g/(g**2 + (eps[:, None] - eps[None, :])**2)
    np.fill_diagonal(k, 0.0)
    return k


def site_model(Hw, gamma_cm, classical, D):
    """Hamiltonian and site c_ops (dephasing or hopping) in a D-level space."""
    N = Hw.shape[0]
    g = gamma_cm*W
    if classical:
        H = qt.qzero(D)
        if g == 0:
            return H, []
        k = hs_rates(Hw, g)
        return H, [np.sqrt(k[i, j])*qt.projection(D, i, j)
                   for i in range(N) for j in range(N) if k[i, j] > 0]
    H = qt.Qobj(np.pad(Hw, (0, D-N)))                    # sink/ground at zero energy
    return H, ([np.sqrt(g)*qt.projection(D, j, j) for j in range(N)] if g > 0 else [])


def efficiency(Hw, gamma_cm, start, trap, classical=False):
    """eta by the handout rule (N+2 levels) and the t -> infinity limit."""
    N = Hw.shape[0]
    D, S, G = N + 2, N, N + 1
    H, c_ops = site_model(Hw, gamma_cm, classical, D)
    c_ops += [np.sqrt(KAPPA)*qt.projection(D, S, trap)]
    c_ops += [np.sqrt(LOSS)*qt.projection(D, G, j) for j in range(N)]
    sites = sum(qt.projection(D, j, j) for j in range(N))
    # Loss on every site gives P_sites(t) <= exp(-LOSS t), so t_max always suffices.
    t_max = 1.2*np.log(1/STOP)/LOSS
    tl = np.unique(np.r_[0.0, 1e5, np.logspace(1, np.log10(t_max), 2001)])  # 0.45% steps
    r = qt.mesolve(H, qt.fock_dm(D, start), tl, c_ops,
                   e_ops=[qt.projection(D, S, S), sites, qt.qeye(D)], options=DIAG)
    sink, ps, tr = (np.asarray(x).real for x in r.expect)
    i = int(np.argmax(ps < STOP))
    assert ps[i] < STOP, "sites never emptied"
    # Infinite time on the N sites: X = int rho dt = -L_T^-1 rho0, eta = kappa X_tt.
    Hn, cn = site_model(Hw, gamma_cm, classical, N)
    Pt = qt.projection(N, trap, trap)
    A = KAPPA*Pt + LOSS*qt.qeye(N)                       # -1/2 {A, rho}: trap and loss out
    LT = qt.liouvillian(Hn, cn) - 0.5*(qt.spre(A) + qt.spost(A))
    X = qt.vector_to_operator(-(LT.inv() @ qt.operator_to_vector(qt.fock_dm(N, start))))
    eta_inf = float(np.real(KAPPA*qt.expect(Pt, X)))
    loss_inf = float(np.real(LOSS*X.tr()))
    return dict(eta=sink[i], t=tl[i], resid=ps[i], eta100=sink[tl == 1e5][0],
                trace=abs(tr - 1).max(), eta_inf=eta_inf, sum_inf=eta_inf + loss_inf)


def part3(Hcm, starts, trap):
    Hw = Hcm*W
    lab = [f"q:BChl{s+1}" for s in starts] + [f"cl:BChl{s+1}" for s in starts]
    print(f"Part 3  Lindblad, {Hcm.shape[0]+2} levels; trap BChl {trap+1} at 1 ps^-1, "
          f"loss 1 ns^-1 per site. eta = sink population once < {STOP:g} is left "
          "on the sites (q: quantum, cl: classical Haken-Strobl)")
    print("        gamma[cm^-1] " + " ".join(f"{x:>10}" for x in lab))
    out = {}
    for g in GAMMAS:
        row = [efficiency(Hw, g, s, trap, cl) for cl in (False, True) for s in starts]
        out[g] = row
        print(f"        {g:12.4g} " + " ".join(f"{r['eta']:10.4f}" for r in row))
    rs = [r for row in out.values() for r in row]
    print(f"        stop time {min(r['t'] for r in rs)/1e6:.2f}-{max(r['t'] for r in rs)/1e6:.2f} ns, "
          f"residual on sites <= {max(r['resid'] for r in rs):.1e}, "
          f"max |trace-1| = {max(r['trace'] for r in rs):.1e}")
    ok = all(-1e-8 <= r['eta_inf'] - r['eta'] <= r['resid'] + 1e-8 for r in rs)
    print(f"        check vs t -> inf (QuTiP Liouvillian solve): eta <= eta_inf <= eta + residual "
          f"for every run: {ok}; max eta_inf - eta = "
          f"{max(r['eta_inf']-r['eta'] for r in rs):.1e}; "
          f"max |eta_inf + loss_inf - 1| = {max(abs(r['sum_inf']-1) for r in rs):.1e}")
    ns = len(starts)
    for a, s in enumerate(starts):
        d = {g: out[g][a]['eta'] - out[g][ns+a]['eta'] for g in GAMMAS if g > 0}
        gm = max(d, key=lambda g: abs(d[g]))
        print(f"        start BChl {s+1}: largest quantum-classical gap at gamma = {gm:.3g} "
              f"cm^-1 ({out[gm][a]['eta']:.3f} vs {out[gm][ns+a]['eta']:.3f})")
    print("        eta at a fixed 100 ps window instead (NOT the handout rule):")
    for s in starts:
        print(f"          q  start BChl {s+1}: " + ", ".join(
            f"{g:g}:{efficiency(Hw, g, s, trap)['eta100']:.3f}" for g in GAMMAS_100PS))
    print(f"          cl start BChl {starts[0]+1}: " + ", ".join(
        f"{g:g}:{efficiency(Hw, g, starts[0], trap, True)['eta100']:.3f}"
        for g in GAMMAS_100PS if g > 0))


# ------------------------------------------------------------------ Part 4
def heom(Hcm, start, T_K, depth, benchmark=False):
    """0-1 ps, one Drude-Lorentz bath per site; returns a dict of results."""
    N = Hcm.shape[0]
    lam, gc, kT = LAM_CM*W, 1/TAU_C, KB*T_K*W            # rad/fs, 1/fs, rad/fs
    Qs = [qt.projection(N, j, j) for j in range(N)]
    H = qt.Qobj(Hcm*W)
    if not benchmark:
        # Ishizaki-Fleming high-T limit of the Drude-Lorentz C(t): one exponent.
        # (DrudeLorentzBath/DrudeLorentzEnvironment with Nk=0 would instead use the
        # exact coefficient lam*gc*cot(gc/2kT), which is NOT the handout's model.)
        env = qt.ExponentialBosonicEnvironment(
            ck_real=[2*lam*kT], vk_real=[gc], ck_imag=[-lam*gc], vk_imag=[gc], T=kT)
    else:
        # Exact coefficients: Pade expansion plus a terminator for the remainder.
        dl = qt.DrudeLorentzEnvironment(T=kT, lam=lam, gamma=gc)
        env, delta = dl.approximate("pade", Nk=1, compute_delta=True)
        H = qt.liouvillian(H) + sum(qt.system_terminator(Q, delta) for Q in Qs)
    t0 = time.time()
    solver = HEOMSolver(H, [(env, Q) for Q in Qs], max_depth=depth, options=HEOM_OPTS)
    t = np.linspace(0, 1000, 501)
    res = solver.run(qt.fock_dm(N, start), t, e_ops=Qs + [qt.qeye(N)])
    P = np.array(res.expect).real                        # rows: sites, then trace
    jm, im = np.unravel_index(np.argmin(P[:-1]), P[:-1].shape)
    mineig = min(float(np.min((0.5*(r + r.dag())).eigenenergies())) for r in res.states)
    return dict(t=t, P=P, n=len(solver.ados.labels), sec=time.time() - t0,
                minpop=P[jm, im], minsite=jm, mintime=t[im], mineig=mineig,
                trace=abs(P[-1] - 1).max())


def heom_line(d, r, start, idx, prev):
    msg = (f"          depth {d} ({r['n']} ADOs, {r['sec']:.1f} s): "
           f"P{start+1} = {fmt(r['P'][start, idx])} | min P = {r['minpop']:.1e} "
           f"(BChl {r['minsite']+1}, {r['mintime']:.0f} fs), min eig rho = {r['mineig']:.1e}"
           f", |trace-1| = {r['trace']:.0e}")
    if prev is None:
        return msg, None
    dP = abs(r['P'][:-1] - prev[1][:-1]).max()
    return msg + f" | max|dP| vs depth {prev[0]} = {dP:.1e}", dP


def part4(Hcm, start, depths, tol):
    idx = [0, 50, 100, 200, 300, 500]                    # 0/100/200/400/600/1000 fs
    auto = depths is None
    print(f"Part 4  HEOM, start BChl {start+1}, no trap/loss, lambda = {LAM_CM:g} cm^-1, "
          f"1/gamma_c = {TAU_C:g} fs (hbar gamma_c = {1/TAU_C/W:.0f} cm^-1); "
          "P(t) at 0/100/200/400/600/1000 fs; max|dP| over all sites and 0-1 ps")
    for T_K in TEMPS:
        print(f"        T = {T_K} K, kT = {KB*T_K:.0f} cm^-1, high-T exponent (Ishizaki-Fleming)"
              + (f"; depth raised until max|dP| < {tol:g}" if auto else ""))
        prev, dP, last = None, None, None
        for d in (range(3, HEOM_MAX_DEPTH + 1) if auto else depths):
            r = heom(Hcm, start, T_K, d)
            msg, dP = heom_line(d, r, start, idx, prev)
            print(msg)
            prev = last = (d, r['P'])
            res = r
            if auto and dP is not None and dP < tol:
                break
        d_acc, r = last[0], res
        state = "converged" if dP is not None and dP < tol else "NOT converged"
        print(f"          -> depth {d_acc} {state} (tol {tol:g}): P{start+1}(1 ps) = "
              f"{r['P'][start, -1]:.3f}; populations "
              + ("stay >= 0" if r['minpop'] > -1e-6 else
                 f"go negative (min {r['minpop']:.1e}), a failure of the high-T approximation"))
        prev = None
        for d in (3, 4):
            b = heom(Hcm, start, T_K, d, benchmark=True)
            msg, _ = heom_line(d, b, start, idx, prev)
            print("          beyond high-T, Pade Nk=1 + terminator:" + msg[9:])
            prev = (d, b['P'])


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--hamiltonian", default=os.path.join(HERE, "..", "data",
                                                          "fmo_hamiltonian_cm-1.csv"),
                    help="N x N site Hamiltonian in cm^-1, comma separated, '#' comments")
    ap.add_argument("--trap", type=int, default=3, help="trap site, 1-based (default 3)")
    ap.add_argument("--starts", type=int, nargs="+", default=None,
                    help="starting sites, 1-based (default 1 6); Part 4 uses the first")
    ap.add_argument("--parts", type=int, nargs="+", default=[1, 2, 3], choices=[1, 2, 3, 4])
    ap.add_argument("--depths", type=int, nargs="+", default=None,
                    help="fixed HEOM depths for Part 4 (default: raise the depth from 3 "
                         "until converged)")
    ap.add_argument("--tol", type=float, default=HEOM_TOL,
                    help=f"Part 4 convergence tolerance on populations (default {HEOM_TOL:g})")
    a = ap.parse_args()

    Hcm = np.atleast_2d(np.loadtxt(a.hamiltonian, delimiter=",", comments="#"))
    N = Hcm.shape[0]
    if Hcm.shape != (N, N) or N < 2 or not qt.Qobj(Hcm).isherm:
        ap.error(f"{a.hamiltonian}: expected a symmetric N x N matrix with N >= 2, "
                 f"got {Hcm.shape}")
    if a.depths and min(a.depths) < 1:
        ap.error("--depths must be >= 1")
    starts = a.starts or [s for s in (1, 6) if s <= N]
    for s in starts + [a.trap]:
        if not 1 <= s <= N:
            ap.error(f"site {s} is outside 1..{N}")
    starts, trap = [s - 1 for s in starts], a.trap - 1
    print(f"QuTiP {qt.__version__}; {N} sites from {os.path.normpath(a.hamiltonian)}; "
          f"trap BChl {trap+1}; starts {[s+1 for s in starts]}")

    E, w = part1(Hcm, show=1 in a.parts)
    for p, f in ((2, lambda: part2(Hcm, E, w, starts, trap)),
                 (3, lambda: part3(Hcm, starts, trap)),
                 (4, lambda: part4(Hcm, starts[0],
                                   sorted(a.depths) if a.depths else None, a.tol))):
        if p in a.parts:
            t0 = time.time()
            f()
            print(f"        [Part {p}: {time.time()-t0:.1f} s]")


if __name__ == "__main__":
    main()
