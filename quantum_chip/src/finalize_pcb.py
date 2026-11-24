"""Load the generated board in KiCad (pcbnew), fill all zones, save, and write a DRC report."""
import os, sys, pcbnew
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
src = os.path.join(OUT, "rf_carrier_unfilled.kicad_pcb")
dst = os.path.join(OUT, "rf_carrier.kicad_pcb")
b = pcbnew.LoadBoard(src)
print("loaded:", len(b.GetFootprints()), "footprints,", len(b.GetTracks()), "tracks/vias,", b.GetCopperLayerCount(), "copper layers")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(dst)
b2 = pcbnew.LoadBoard(dst)
rep = os.path.join(OUT, "drc_report.txt")
ok = pcbnew.WriteDRCReport(b2, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
print("DRC written:", ok)
os.remove(src)
