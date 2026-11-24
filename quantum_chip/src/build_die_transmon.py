"""(Previous design, kept for reference: build_die.py now makes the RFL die.)
Generate the 4-qubit flux-tunable transmon die with KQCircuits.

Outputs
  out/quantum_die.gds   - KQC layer set, cell Q4_FLUX_TRANSMON
  out/die_ports.json    - launcher pad geometry + net names (used by the PCB / bonds)
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from design_params import (DIE, QUBIT_X, QUBIT_Y, READOUT_F_GHZ, FEEDLINE_Y,
                           LAUNCHERS_PER_SIDE, LAUNCHER, TRANSMON_LAUNCHER_NETS as LAUNCHER_NETS)

from kqcircuits.pya_resolver import pya
from kqcircuits.chips.chip import Chip
from kqcircuits.qubits.swissmon import Swissmon
from kqcircuits.elements.waveguide_composite import WaveguideComposite
from kqcircuits.elements.waveguide_coplanar_splitter import WaveguideCoplanarSplitter
from kqcircuits.elements.meander import Meander
from kqcircuits.util.node import Node
from kqcircuits.util.coupler_lib import cap_params

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
C0 = 299792458.0


def half_wave_len_um(f_ghz):
    eps_eff = (DIE["substrate_eps_r"] + 1) / 2
    return C0 / (2 * f_ghz * 1e9 * math.sqrt(eps_eff)) * 1e6


class Q4FluxTransmon(Chip):
    """Four flux-tunable (SQUID) Swissmon transmons in a chain, bus-coupled nearest neighbours,
    individual lambda/2 readout resonators on a common probe line, individual XY drive and Z flux lines."""

    def build(self):
        L = LAUNCHER
        self.launchers = self.produce_n_launchers(
            LAUNCHERS_PER_SIDE, "RF", L["width"], L["gap"], L["indent"], L["pitch"],
            launcher_assignments=LAUNCHER_NETS,
        )
        # ---------------- qubits
        qb_kw = dict(
            fluxline_type="Fluxline Standard",
            junction_type="Manhattan",
            arm_length=[146] * 4, arm_width=[24] * 4, gap_width=[24] * 4,
            cpl_length=[120, 140, 120], cpl_width=[60, 24, 60], cpl_gap=[102, 90, 102],
            port_width=[10, 10, 10],
        )
        qb_mid = self.add_element(Swissmon, **qb_kw)
        # chain ends: no outward-facing coupler (cplr0 faces outward for both M0 and R180 placements)
        qb_end = self.add_element(Swissmon, **{**qb_kw, "cpl_length": [0, 140, 120]})
        self.qref = []
        for i, x in enumerate(QUBIT_X):
            # Q1,Q2: mirror about x-axis (SQUID north, drive port NW); Q3,Q4: rotate 180 (drive port NE)
            rot = pya.DTrans.M0 if i < 2 else pya.DTrans.R180
            qb = qb_end if i in (0, 3) else qb_mid
            _, ref = self.insert_cell(qb, pya.DTrans(x, QUBIT_Y) * rot, inst_name=f"QB{i+1}", rec_levels=None)
            self.qref.append(ref)

        # ---------------- nearest-neighbour bus couplers (floating CPW between coupler pads)
        for i in range(3):
            a, b = self.qref[i], self.qref[i + 1]
            # east-facing coupler of qubit i / west-facing coupler of qubit i+1
            pa = max((a["port_cplr0"], a["port_cplr2"]), key=lambda p: p.x)
            pb = min((b["port_cplr0"], b["port_cplr2"]), key=lambda p: p.x)
            self.insert_cell(WaveguideComposite, nodes=[Node(pa), Node(pb)], inst_name=f"BUS{i+1}{i+2}")

        # ---------------- probe line with T-splitters + finger caps + meandered resonators
        half = self.a / 2 + self.b
        tees = []
        for i, x in enumerate(QUBIT_X):
            _, t = self.insert_cell(
                WaveguideCoplanarSplitter, pya.DTrans(x, FEEDLINE_Y), inst_name=f"PLT{i+1}",
                lengths=[half, half, half + 20], angles=[0, 180, 90], port_names=["right", "left", "top"],
            )
            tees.append(t)
            cap = self.add_element(**cap_params(4, 40, "interdigital"))
            cref = self.get_refpoints(cap, pya.DTrans.R270)
            _, c = self.insert_cell(cap, pya.DTrans(t["port_top"] - cref["port_b"]) * pya.DTrans.R270,
                                    inst_name=f"RRC{i+1}")
            q = self.qref[i]
            top = q["port_cplr1"]
            straight = (top - c["port_a"]).length()
            target = half_wave_len_um(READOUT_F_GHZ[i])
            self.insert_cell(Meander, start_point=c["port_a"], end_point=top, length=target,
                             meanders=-1, n_bridges=6, inst_name=f"RR{i+1}")
            self.rr_lengths = getattr(self, "rr_lengths", []) + [(target, straight)]

        fl = [self.launchers["PROBE_IN"][0]]
        self.insert_cell(WaveguideComposite, inst_name="PL_IN", nodes=[
            Node(fl[0]), Node((fl[0].x + 600, fl[0].y)), Node((fl[0].x + 600, FEEDLINE_Y)),
            Node(tees[0]["port_left"], n_bridges=2)])
        for i in range(3):
            self.insert_cell(WaveguideComposite, inst_name=f"PL_{i+1}{i+2}", nodes=[
                Node(tees[i]["port_right"]), Node(tees[i + 1]["port_left"], n_bridges=2)])
        po = self.launchers["PROBE_OUT"][0]
        self.insert_cell(WaveguideComposite, inst_name="PL_OUT", nodes=[
            Node(tees[3]["port_right"], n_bridges=2), Node((po.x - 600, FEEDLINE_Y)),
            Node((po.x - 600, po.y)), Node(po)])

        # ---------------- flux lines (north launchers -> SQUID fluxline port)
        for i in range(4):
            n = f"Q{i+1}_FLUX"
            p = self.launchers[n][0]
            q = self.qref[i]
            jog_y = 8300 - 250 * (i % 2)
            self.insert_cell(WaveguideComposite, inst_name=f"FL{i+1}", nodes=[
                Node(p), Node((p.x, jog_y)), Node((q["port_flux"].x, jog_y), n_bridges=1),
                Node(q["port_flux_corner"]), Node(q["port_flux"])])

        # ---------------- XY drive lines (open-ended capacitive charge lines)
        def drive(net, pts):
            self.insert_cell(WaveguideComposite, inst_name=f"DL_{net}", term2=self.b,
                             nodes=[Node(p) for p in pts])

        for i, net in ((1, "Q2_DRIVE"), (2, "Q3_DRIVE")):
            p = self.launchers[net][0]
            d = self.qref[i]["port_drive"]
            drive(net, [p, (p.x, 7000), (d.x, 7000), d])
        p = self.launchers["Q1_DRIVE"][0]
        d = self.qref[0]["port_drive"]
        drive("Q1_DRIVE", [p, (d.x - 500, p.y), (d.x - 500, d.y + 450), (d.x, d.y + 450), d])
        p = self.launchers["Q4_DRIVE"][0]
        d = self.qref[3]["port_drive"]
        drive("Q4_DRIVE", [p, (d.x + 500, p.y), (d.x + 500, d.y + 450), (d.x, d.y + 450), d])


L_PAD = LAUNCHER["width"]    # KQC Launcher: s = l = launcher_width (square pad)
L_TAPER = LAUNCHER["width"]


def main():
    os.makedirs(OUT, exist_ok=True)
    from kqcircuits.util.library_helper import load_libraries, _register_pcell
    lib = load_libraries(path=Chip.LIBRARY_PATH)[Chip.LIBRARY_NAME]
    _register_pcell(Q4FluxTransmon, lib, Chip.LIBRARY_NAME)
    layout = pya.Layout()
    layout.dbu = 0.001
    cell = Q4FluxTransmon.create(layout, name_chip="", name_mask="EE143", name_brand="Q4 FLUX", name_copy="A1", with_grid=False,
                                 frames_enabled=[0])
    top = layout.create_cell("Q4_FLUX_TRANSMON")
    top.insert(pya.DCellInstArray(cell.cell_index(), pya.DTrans()))
    top.flatten(-1, True)

    # ---- launcher pads: pull from KQC refpoints layer
    refs = {}
    rp_layer = layout.layer(pya.LayerInfo(225, 0, "refpoints"))
    for sh in top.shapes(rp_layer).each():
        if sh.is_text():
            refs[sh.text.string] = (sh.text.x * layout.dbu, sh.text.y * layout.dbu)
    ports = []
    for pid, net in LAUNCHER_NETS.items():
        px, py = refs[f"{net}_port"]
        cx, cy = refs[f"{net}_port_corner"]
        # direction from inner corner toward pad (outward)
        dx, dy = px - cx, py - cy
        nrm = math.hypot(dx, dy)
        ux, uy = dx / nrm, dy / nrm
        side = "N" if uy > 0.5 else "S" if uy < -0.5 else "E" if ux > 0.5 else "W"
        off = L_TAPER + L_PAD / 2  # launcher taper length + half pad
        ports.append(dict(net=net, kqc_port_id=pid, side=side, port_um=[px, py],
                          outward=[round(ux), round(uy)],
                          pad_center_um=[round(px + ux * off, 3), round(py + uy * off, 3)],
                          pad_size_um=[L_PAD, L_PAD]))
    with open(os.path.join(OUT, "transmon_die_ports.json"), "w") as f:
        json.dump(dict(ports=ports, refpoints={k: v for k, v in refs.items()
                                               if k.endswith("_port") or k.startswith("QB")}), f, indent=1)
    layout.write(os.path.join(OUT, "transmon_die.gds"))
    print("wrote quantum_die.gds; bbox um:", top.dbbox())
    for p in ports:
        print(p)


if __name__ == "__main__":
    main()
