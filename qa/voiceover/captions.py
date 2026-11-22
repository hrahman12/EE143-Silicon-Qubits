import json, re, difflib
T = json.load(open("drive_dl/transcript.json"))
N = json.load(open("/home/user/EE143-Silicon-Qubits/notes/speaker_notes_final.json"))
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
W = [[w[0], w[1], w[2]] for s in T for w in s["words"] if w[2].strip()]
# 1) fix misheard words using the notes text where they line up
nw_raw = [w for k in sorted(N, key=int) for w in N[k].replace("\n", " ").split()]
nw = [norm(w) for w in nw_raw]
keep = [i for i, w in enumerate(nw) if w]; nw = [nw[i] for i in keep]; nw_raw = [nw_raw[i] for i in keep]
tw = [norm(w[2]) for w in W]
sm = difflib.SequenceMatcher(None, nw, tw, autojunk=False)
fixed = 0
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op == "replace" and (a2 - a1) == (b2 - b1):
        for a, b in zip(range(a1, a2), range(b1, b2)):
            if tw[b].isdigit() or any(c.isdigit() for c in tw[b]): continue
            if difflib.SequenceMatcher(None, nw[a], tw[b]).ratio() >= 0.6 and not nw[a].isdigit():
                core = re.sub(r"[^\w'-]", "", nw_raw[a]); lead = W[b][2][:len(W[b][2]) - len(W[b][2].lstrip())]; orig = W[b][2].strip()
                pre = re.match(r"^\W*", orig).group(); post = re.search(r"\W*$", orig).group()
                if orig[len(pre):len(pre)+1].isupper(): core = core[:1].upper() + core[1:]
                W[b][2] = lead + pre + core + post; fixed += 1
# 2) manual fixes for things the matcher can't catch
M = {r"\b(column|Coulomb) pole\b": "Coulomb pull", r"\bEE143\b": "EE143", r"\baspect sheet\b": "EE spec sheet", r"\bNeal\b": "Neil",
     r"\bKerson\b": "Curson", r"\bKursum\b": "Curson", r"\bArseem\b": "arsine", r"\barseine\b": "arsine", r"\bIntanglement\b": "Entanglement",
     r"\bDopon\b": "Dopant", r"\btiles\b": "titles", r"\bphosphorous\b": "phosphorus", r"\bshowing 1 electron\b": "sharing 1 electron",
     r"\b2 cubic gate\b": "2-qubit gate", r"\bcubic\b": "qubit", r"\bsides\b": "sites", r"\bP to the N\b": "p to the n"}
M.update({r"\bball radi": "Bohr radi", r"\bRead out term spin": "Readout turns spin", r"\btwo are over": "two r over",
 r"\bis an optimal optional\b": "isn't optional", r"\b(r ?-?sign|r sine|our sign)\b": "arsine", r"\bA List of Solved\b": "a list of solved",
 r"\banneal cap\b": "anneal, cap", r"\bk ?t\b": "kT", r"\bpico picoamps at 15 nanometers": "picoamps at 50 nanometers",
 r"\be-bim\b": "e-beam", r"\bMKT\b": "m k T", r"\bonce (heat|cold)\b": r"wants \1", r"\bWhole bars\b": "Hall bars",
 r"\bmillikelvin-kelvin\b": "millikelvin", r"\bomic\b": "ohmic", r"\bRS equals 1 over Q times NS\b": "Rs equals 1 over q times Ns",
 r"\bSolve for NS\b": "Solve for Ns", r"\bgo search\b": "Grover's search", r"\bmott\b": "Mott", r"\bHF at\b": "hf at",
 r"\bHC over\b": "hc over", r"\bburied 13 nanometers\b": "buried 30 nanometers", r"\bmight asked\b": "might ask",
 r"\b3 is speed\b": "Three is speed", r"\bbell fidelities\b": "Bell fidelities", r"\bprobability P\b": "probability p",
 r"\bN site array\b": "n-site array", r"\bpushes P\b": "pushes p", r"\bpushed P\b": "pushed p", r"\bthrough P\b": "through p",
 r"\bspin's-Zeeman\b": "spin's Zeeman", r"\btri-phenyl bismuth\b": "triphenyl-bismuth", r"\bsingle-phosphorus\b": "single phosphorus"})
# 3) build cues: break on sentence end or pause, max 2 lines x 46 chars
cues, cur = [], []
def flush():
    if cur: cues.append([cur[0][0], cur[-1][1], "".join(w[2] for w in cur).strip()]); cur.clear()
for i, w in enumerate(W):
    if cur and (w[0] - cur[-1][1] > 0.7 or len("".join(x[2] for x in cur + [w])) > 92): flush()
    cur.append(w)
    if re.search(r"[.?!]$", w[2].strip()) and len("".join(x[2] for x in cur)) > 35: flush()
flush()
merged = []
for c in cues:
    if merged and len(c[2]) < 18 and len(merged[-1][2]) + len(c[2]) < 100 and c[0] - merged[-1][1] < 0.7:
        merged[-1][1] = c[1]; merged[-1][2] += " " + c[2]
    else: merged.append(c)
cues = merged
for c in cues:
    for k, v in M.items(): c[2] = re.sub(k, v, c[2], flags=re.I if k not in (r"\bEE143\b", r"\bmott\b", r"\bHF at\b", r"\bHC over\b", r"\bMKT\b", r"\bRS equals 1 over Q times NS\b", r"\bSolve for NS\b") else 0)
# timing: hold each cue until the next starts (max +0.8 s), min 1 s
for i, c in enumerate(cues):
    nxt = cues[i + 1][0] if i + 1 < len(cues) else c[1] + 1
    c[1] = min(max(c[1] + 0.3, c[0] + 1.0), nxt - 0.02)
def ts(t, ass=False):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}" if ass else f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s%1)*1000)):03d}".replace(",1000", ",999")
def wrap(t, n=46):
    if len(t) <= n: return t
    mid = len(t) // 2; sp = [i for i, ch in enumerate(t) if ch == " "]
    j = min(sp, key=lambda i: abs(i - mid)); return t[:j] + "\\N" + t[j+1:]
srt = [f"{i+1}\n{ts(c[0])} --> {ts(c[1])}\n{wrap(c[2]).replace(chr(92)+'N', chr(10))}\n" for i, c in enumerate(cues)]
open("/home/user/EE143-Silicon-Qubits/deck/atom_by_atom_silicon_voiceover.srt", "w").write("\n".join(srt))
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "",
       "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,DejaVu Sans,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,60,60,30,1", "",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
ass += [f"Dialogue: 0,{ts(c[0],1)},{ts(c[1],1)},Cap,,0,0,0,,{wrap(c[2])}" for c in cues]
open("captions.ass", "w").write("\n".join(ass) + "\n")
print(len(cues), "cues;", fixed, "words fixed from notes")
