"""Schematic Figure 1 for the handout (conceptual, not a simulation result)."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
import os
H = np.loadtxt(os.path.join(os.path.dirname(__file__), "../data/fmo_hamiltonian_cm-1.csv"), delimiter=",", comments="#")
# schematic 2D layout (not the crystal geometry)
pos = {1:(0.0,1.0),2:(1.0,1.35),3:(2.2,0.2),4:(1.6,-0.5),5:(0.6,-1.0),6:(-0.4,-0.3),7:(0.9,0.2)}
trap = (3.3,0.2)
teal = "#2a9d8f"; ink="#264653"; orange="#e76f51"

def network(ax, title, node_alpha=None, edges_style="-"):
    for i in range(7):
        for j in range(i+1,7):
            J = abs(H[i,j])
            if J > 15:
                x=[pos[i+1][0],pos[j+1][0]]; y=[pos[i+1][1],pos[j+1][1]]
                ax.plot(x,y,edges_style,color="#9aa5ad",lw=0.5+J/25,zorder=1)
    for k,(x,y) in pos.items():
        a = 0.25 if node_alpha is None else node_alpha[k-1]
        ax.add_patch(Circle((x,y),0.22,fc=teal,alpha=a,ec=ink,lw=1,zorder=3))
        ax.text(x,y,str(k),ha="center",va="center",fontsize=12,color=ink,zorder=4,fontweight="bold")
    ax.add_patch(Circle(trap,0.28,fc="#f4a261",ec=ink,lw=1,zorder=3))
    ax.text(trap[0],trap[1],"RC",ha="center",va="center",fontsize=10,zorder=4,color=ink,fontweight="bold")
    ax.add_patch(FancyArrowPatch(pos[3],trap,arrowstyle="-|>",mutation_scale=12,color=orange,lw=1.6,shrinkA=12,shrinkB=14,zorder=2))
    ax.text(-1.05,1.95,"light from baseplate",fontsize=10,color=ink,ha="left",va="top")
    ax.add_patch(FancyArrowPatch((-0.7,1.6),pos[1],arrowstyle="-|>",mutation_scale=10,color=ink,lw=1,shrinkB=12))
    ax.set_title(title,fontsize=14,color=ink,pad=4)
    ax.set_xlim(-1.1,3.8); ax.set_ylim(-1.6,1.95); ax.set_aspect("equal"); ax.axis("off")

fig, axes = plt.subplots(1,3,figsize=(10.5,3.9))
# (a) incoherent hopping
network(axes[0],"(a) classical hopping")
hops=[(1,2),(2,3),(6,5),(5,4),(4,3)]
for a,b in hops:
    axes[0].add_patch(FancyArrowPatch(pos[a],pos[b],arrowstyle="-|>",connectionstyle="arc3,rad=0.35",
        mutation_scale=10,color=ink,lw=1.1,shrinkA=11,shrinkB=11,zorder=5))
axes[0].text(1.3,-1.45,"one site at a time, incoherent rates",ha="center",fontsize=11,color=ink)
# (b) coherent wave: amplitude spread, phase colouring
amp=[0.95,0.8,0.15,0.35,0.3,0.45,0.55]
network(axes[1],"(b) coherent exciton wave",node_alpha=amp)
for k,(x,y) in pos.items():
    axes[1].add_patch(Circle((x,y),0.32,fill=False,ec=teal,lw=1,ls=(0,(2,2)),alpha=amp[k-1],zorder=2))
axes[1].text(1.3,-1.45,"delocalized, beats, never settles",ha="center",fontsize=11,color=ink)
# (c) noise-assisted
amp2=[0.5,0.45,0.9,0.7,0.4,0.35,0.6]
network(axes[2],"(c) environment-assisted",node_alpha=amp2)
rng=np.random.default_rng(3)
for k,(x,y) in pos.items():
    th=np.linspace(0,2*np.pi,60); r=0.33+0.025*rng.standard_normal(60)
    axes[2].plot(x+r*np.cos(th),y+r*np.sin(th),color="#8d99ae",lw=0.7,zorder=2)
axes[2].text(1.3,-1.45,"protein noise breaks traps, feeds RC",ha="center",fontsize=11,color=ink)
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__),"../figure1.png"),dpi=220,bbox_inches="tight",pad_inches=0.05)
