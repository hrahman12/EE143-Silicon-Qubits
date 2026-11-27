"""Instructor reference solution (not for distribution to students).
Checks that every task in the handout is doable and gives sane numbers."""
import numpy as np, itertools, sys, os
from scipy.integrate import solve_ivp
from scipy.linalg import expm

HERE = os.path.dirname(os.path.abspath(__file__))
H = np.loadtxt(os.path.join(HERE, "../data/fmo_hamiltonian_cm-1.csv"), delimiter=",", comments="#")
N = 7
C = 2*np.pi*2.99792458e10*1e-15   # rad/fs per cm^-1  (omega = 2 pi c nu~)
Hw = H*C                           # rad/fs
kB_cm = 0.6950348                  # cm^-1 / K

# ---------- Part 1: exciton structure
E, V = np.linalg.eigh(H)
ipr = 1/np.sum(np.abs(V)**4, axis=0)
print("Part 1  exciton energies (cm^-1, rel. 12210):", np.round(E,1))
print("        participation number:", np.round(ipr,2))
print("        dominant sites per exciton:", [list(np.argsort(-abs(V[:,k]))[:2]+1) for k in range(N)])

# ---------- Part 2: coherent dynamics from site 1
t = np.linspace(0, 1000, 4001)  # fs
psi0 = np.zeros(N); psi0[0] = 1
P = np.array([np.abs(V @ (np.exp(-1j*E*C*tt) * (V.T @ psi0)))**2 for tt in t])
f = np.fft.rfftfreq(len(t), d=(t[1]-t[0])*1e-15)/2.99792458e10   # cm^-1
S = np.abs(np.fft.rfft(P[:,0]-P[:,0].mean()))
pk = f[np.argmax(S[1:])+1]
print(f"Part 2  site-1 beat at {pk:.0f} cm^-1 -> period {1e15/(pk*2.99792458e10):.0f} fs;"
      f" E2-E1 gap pair from excitons on sites 1/2: check list of |Ei-Ej|")

# ---------- Part 3: Lindblad with dephasing, trap at site 3, loss
def liouvillian(gamma_cm, kappa_ps=1.0, loss_ns=1.0):
    # basis: 7 sites + sink (index 7) + ground (index 8)
    d = N+2
    Hf = np.zeros((d,d), complex); Hf[:N,:N] = Hw
    Ls = []
    g = gamma_cm*C
    for j in range(N):
        A = np.zeros((d,d)); A[j,j] = 1; Ls.append((g, A))            # pure dephasing (rate g)
        A = np.zeros((d,d)); A[N+1,j] = 1; Ls.append((loss_ns*1e-6, A))  # loss to ground
    A = np.zeros((d,d)); A[N,2] = 1; Ls.append((kappa_ps*1e-3, A))       # trap from BChl 3
    I = np.eye(d)
    # row-major vec: vec(A rho B) = kron(A, B.T) vec(rho)
    L = -1j*(np.kron(Hf,I) - np.kron(I,Hf.T))
    for r,A in Ls:
        AdA = A.conj().T@A
        L += r*(np.kron(A, A.conj()) - 0.5*np.kron(AdA,I) - 0.5*np.kron(I,AdA.T))
    return L, d

def efficiency(gamma_cm, start=0, T=100000.0):
    L, d = liouvillian(gamma_cm)
    rho = np.zeros((d,d), complex); rho[start,start] = 1
    r = expm(L*T) @ rho.reshape(-1)
    r = r.reshape(d,d)
    return r[N,N].real, np.trace(r).real

for s in (0,5):
    out = [(g, *efficiency(g, s)) for g in (0, 1, 10, 30, 100, 300, 1000, 1e4, 1e5)]
    print(f"Part 3  start BChl {s+1}: eta(100 ps) vs gamma[cm^-1]:",
          ", ".join(f"{g:g}:{e:.3f}" for g,e,_ in out), "| trace", round(out[3][2],6))

# classical Haken-Strobl rate model
def classical_eff(gamma_cm, start=0, T=100000.0):
    g = gamma_cm*C
    K = np.zeros((N+2,N+2))
    for i in range(N):
        for j in range(N):
            if i!=j:
                dE = (Hw[i,i]-Hw[j,j])
                K[i,j] = 2*Hw[i,j]**2*g/(g**2+dE**2) if g>0 else 0   # rate j->i ; (dephasing rate g per site -> coherence decay g)
    for j in range(N): K[j,j] = -K[:N,j].sum()
    K[N,2] += 1e-3; K[2,2] -= 1e-3
    for j in range(N): K[N+1,j] += 1e-6; K[j,j] -= 1e-6
    p = np.zeros(N+2); p[start] = 1
    return (expm(K*T)@p)[N]
print("Part 3  classical rate eta(100 ps):", ", ".join(f"{g:g}:{classical_eff(g):.3f}" for g in (1,10,100,1000,1e4)))

# ---------- Part 4: HEOM, Drude-Lorentz, high-T (no Matsubara), Ishizaki-Fleming
def heom(Tk, depth=4, lam=35.0, tau=50.0, tmax=1000.0, start=0):
    gam = 1/tau                       # 1/fs
    lamw = lam*C                      # rad/fs
    beta = 1/(kB_cm*Tk*C)             # fs (since energies in rad/fs)
    idx = [n for n in itertools.product(range(depth+1), repeat=N) if sum(n)<=depth]
    pos = {n:i for i,n in enumerate(idx)}
    M = len(idx)
    Vj = [np.diag(np.eye(N)[j]) for j in range(N)]
    def rhs(t, y):
        R = y.reshape(M, N, N); dR = np.empty_like(R)
        for a, n in enumerate(idx):
            r = R[a]
            d = -1j*(Hw@r - r@Hw) - sum(n)*gam*r
            for j in range(N):
                # truncation correction (Ishizaki-Tanimura) on terminal tier omitted; depth checked instead
                up = list(n); up[j] += 1; up = tuple(up)
                if up in pos:
                    ru = R[pos[up]]
                    d += -1j*(Vj[j]@ru - ru@Vj[j])
                if n[j] > 0:
                    dn = list(n); dn[j] -= 1; rd = R[pos[tuple(dn)]]
                    comm = Vj[j]@rd - rd@Vj[j]
                    acom = Vj[j]@rd + rd@Vj[j]
                    d += -1j*n[j]*(2*lamw/beta*comm - 1j*lamw*gam*acom)
            dR[a] = d
        return dR.reshape(-1)
    y0 = np.zeros((M,N,N), complex); y0[0,start,start] = 1
    ts = np.linspace(0, tmax, 501)
    sol = solve_ivp(rhs, (0,tmax), y0.reshape(-1), t_eval=ts, rtol=1e-6, atol=1e-9)
    rho = sol.y.reshape(M,N,N,-1)[0]
    return ts, np.real(np.einsum('iit->it', rho)), M

if "--heom" in sys.argv:
    for Tk in (77, 300):
        for depth in (3, 4):
            ts, pops, M = heom(Tk, depth)
            print(f"Part 4  HEOM T={Tk}K depth={depth} ({M} ADOs): P1(t)= "
                  + ", ".join(f"{int(ts[i])}fs:{pops[0,i]:.3f}" for i in (0,50,100,200,300,500))
                  + f" | trace(1ps)={pops[:,-1].sum():.4f}")
