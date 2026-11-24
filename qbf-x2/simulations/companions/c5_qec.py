"""Companion device 5 - fluxon-based quantum error-correction module (one syndrome-extraction cycle).

Code: 3-qubit phase-flip repetition code (QBF-X2's dominant error is dephasing, i.e. Z). Data qubits are dual-rail
fluxons on racetrack ladders; two ancilla fluxons each cross two data lanes in collision couplers (two CZs per
flight). Stabilisers X1X2, X2X3 are measured with CZ gates sandwiched by beam-splitter Hadamards on the data:
    anc |+>, H_d CZ H_d on each of its two data qubits, H on anc, measure anc (rail detector)
Noise (from the QBF-X2 error budget, results/C_gate.json when present): every CZ is followed by independent Z errors
on both qubits with probability e_cz/2; memory dephasing p per data qubit per cycle; ancilla prep+measure flip p_m.
Exact density-matrix simulation (5 qubits); lookup decoder; logical error per cycle vs memory error p.
Energy per cycle: two ancilla fluxons created, crossed and detected (data fluxons circulate ballistically).
Outputs: figures/companion5_qec.png, results/companion5_qec.json
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import plt, save_json, savefig, ROOT, C_IND, C_MIX, C_TH, C_SIM  # noqa: E402
from classical.sg import rest_energy_numeric  # noqa: E402
from hardware.params import RailParams, H as HPL  # noqa: E402

nq = 5                                     # D1 D2 D3 A1 A2 (qubit 0 = most significant)
I2, X, Z = np.eye(2), np.array([[0, 1], [1, 0]]), np.diag([1.0, -1.0])
Hd = np.array([[1, 1], [1, -1]]) / math.sqrt(2)


def op(single, q):
    m = np.array([[1.0]])
    for i in range(nq):
        m = np.kron(m, single if i == q else I2)
    return m


def cz(a, b):
    d = np.ones(2 ** nq)
    for s in range(2 ** nq):
        if (s >> (nq - 1 - a)) & 1 and (s >> (nq - 1 - b)) & 1:
            d[s] = -1
    return np.diag(d)


def dephase(rho, q, p):
    Zq = op(Z, q)
    return (1 - p) * rho + p * Zq @ rho @ Zq


def flip(rho, q, p):
    Xq = op(X, q)
    return (1 - p) * rho + p * Xq @ rho @ Xq


def u(rho, U):
    return U @ rho @ U.conj().T


def cycle(rho, p_mem, e_cz, p_m):
    for q in range(3):
        rho = dephase(rho, q, p_mem)
    for anc, pair in ((3, (0, 1)), (4, (1, 2))):
        rho = u(rho, op(Hd, anc))
        for d in pair:
            rho = u(rho, op(Hd, d))
            rho = u(rho, cz(anc, d))
            rho = dephase(dephase(rho, anc, e_cz / 2), d, e_cz / 2)
            rho = u(rho, op(Hd, d))
        rho = u(rho, op(Hd, anc))
        rho = flip(rho, anc, p_m)
    # measure ancillas, decode (lookup) and correct with Z on the flagged data qubit
    out = np.zeros_like(rho)
    corr = {(0, 0): None, (1, 0): 0, (1, 1): 1, (0, 1): 2}
    for s1 in (0, 1):
        for s2 in (0, 1):
            P = op(np.diag([1 - s1, s1]), 3) @ op(np.diag([1 - s2, s2]), 4)
            r = P @ rho @ P
            q = corr[(s1, s2)]
            if q is not None:
                r = u(r, op(Z, q))
            # reset ancillas to |0>
            for a_, s_ in ((3, s1), (4, s2)):
                if s_:
                    r = u(r, op(X, a_))
            out += r
    return out


def logical_states():
    plus = np.array([1, 1]) / math.sqrt(2)
    minus = np.array([1, -1]) / math.sqrt(2)
    z0 = np.array([1, 0])
    pl = np.kron(np.kron(np.kron(np.kron(plus, plus), plus), z0), z0)
    mi = np.kron(np.kron(np.kron(np.kron(minus, minus), minus), z0), z0)
    return pl, mi


def logical_error(p_mem, e_cz, p_m):
    pl, mi = logical_states()
    errs = []
    for psi in (pl, mi, (pl + mi) / math.sqrt(2), (pl + 1j * mi) / math.sqrt(2)):
        rho = np.outer(psi, psi.conj())
        r = cycle(rho, p_mem, e_cz, p_m)
        errs.append(1 - float(np.real(psi.conj() @ r @ psi)))
    return float(np.mean(errs))


try:
    C = json.load(open(os.path.join(ROOT, "results", "C_gate.json")))
    e_opt = C["optimum_validation"]["budget"]["total"]
except Exception:
    e_opt = 5e-3
res = dict(e_cz_from_budget=e_opt)
ps = np.logspace(-4, -1, 13)
curves = {}
for e_cz in (0.0, 1e-3, e_opt, 2e-2):
    curves[f"{e_cz:.1e}"] = [logical_error(p, e_cz, p_m=1e-3) for p in ps]
    print(f"e_cz {e_cz:.1e}:", [f"{v:.1e}" for v in curves[f"{e_cz:.1e}"]])
res["logical_error_per_cycle"] = dict(p_memory=ps, curves=curves, p_meas=1e-3)
# break-even: logical < physical memory error (an unencoded qubit idles with error ~ 2p/3 averaged over states)
be = {}
for key, cv in curves.items():
    ok = [p for p, L in zip(ps, cv) if L < 2 * p / 3]
    be[key] = [min(ok), max(ok)] if ok else None
res["break_even_range_p"] = be

rail = RailParams()
E0 = rest_energy_numeric(rail.Lambda) * rail.EJ_GHz * 1e9 * HPL
beta = 0.45
KE = (1 / math.sqrt(1 - beta ** 2) - 1) * E0
res["energy_per_cycle_J"] = dict(ancilla_fluxons=2 * (E0 + KE), dispersive_readout=2 * 10 * HPL * 7e9,
                                 total=2 * (E0 + KE) + 2 * 10 * HPL * 7e9,
                                 note="2 ancilla fluxons created and destroyed per cycle; data fluxons circulate; control, "
                                      "amplification and refrigeration excluded")
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.9))
for (key, cv), col in zip(curves.items(), [C_SIM, C_MIX, "#7c3aed", C_IND]):
    lab = f"CZ error {float(key):.1e}" + (" (QBF-X2 budget at the optimum)" if abs(float(key) - e_opt) < 1e-12 else "")
    ax[0].loglog(ps, cv, "o-", ms=3, color=col, label=lab)
ax[0].loglog(ps, 2 * ps / 3, "k--", lw=1, label="unencoded qubit")
ax[0].set(xlabel="memory dephasing per data qubit per cycle", ylabel="logical error per cycle",
          title="(a) 3-qubit phase-flip code, fluxon syndrome extraction")
ax[0].legend(fontsize=7)
ax[1].axis("off")
ax[1].text(0.0, 0.95, "Syndrome-extraction cycle (simulated):\n"
           "  ancilla fluxon -> BS (H) -> crosses D1, D2 couplers (2 CZ)\n"
           "  -> BS (H) -> rail detector  => X1X2 ;  second ancilla => X2X3\n"
           "  data Hadamards: beam-splitter sections on the racetracks\n\n"
           f"On-chip energy per cycle (estimate): {res['energy_per_cycle_J']['total']:.1e} J\n"
           "  (two fluxons created, crossed, detected; data circulate)\n\n"
           "Not simulated: leakage/erasure handling, ancilla reuse,\n"
           "racetrack dephasing per lap, measurement back-action timing.",
           va="top", family="monospace", fontsize=8)
savefig(fig, "companion5_qec.png")
res["verdict"] = ("Density-matrix simulation of one fluxon-driven syndrome-extraction cycle of a 3-qubit phase-flip code. "
                  "With the CZ error of the QBF-X2 budget the code beats an unencoded qubit over the memory-error range listed "
                  "in break_even_range_p. A full QEC module (larger codes, repeated cycles, real-time decoding, leakage "
                  "handling) is beyond this study; no fluxon-driven syndrome extraction has been reported experimentally.")
save_json("companion5_qec.json", res)
print("done")
