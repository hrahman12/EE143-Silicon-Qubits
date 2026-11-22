import json, re, difflib
T = json.load(open("drive_dl/transcript.json"))
N = json.load(open("/home/user/EE143-Silicon-Qubits/notes/speaker_notes_final.json"))
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
W = [(w[0], w[1], w[2].strip()) for s in T for w in s["words"] if norm(w[2])]
tws = [norm(w[2]) for w in W]
nw, sl = [], []
for k in sorted(N, key=int):
    for w in N[k].replace("-", " ").split():
        if norm(w): nw.append(norm(w)); sl.append(int(k))
sm = difflib.SequenceMatcher(None, nw, tws, autojunk=False)
m = {}
for a, b, n in sm.get_matching_blocks():
    for i in range(n): m[a + i] = b + i
last = {}
for i, k in enumerate(sl):
    if i in m and (k not in last or m[i] > last[k]): last[k] = m[i]
B = {1: 0.0}
for k in range(2, 30):
    j = last[k - 1]
    # guard: last matched word must be before this slide's first matched word
    B[k] = round((W[j][1] + W[j + 1][0]) / 2, 2)
B.update({30: 1680.5, 31: 1683.0, 32: 1687.6, 33: 1691.8})
for k in range(2, 34):
    t = B[k]; i = next(x for x in range(len(W)) if W[x][0] >= t)
    print(k, t, "|", " ".join(w[2] for w in W[max(0, i-5):i]), "||", " ".join(w[2] for w in W[i:i+8]))
json.dump(B, open("boundaries.json", "w"))
