import yaml, json, glob, os, sys, random, statistics as st
from datetime import date, timedelta
root, out = sys.argv[1], sys.argv[2]
ev = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "model-releases.json")))["families"]
TEAMMAP = {"alfa-romeo":"audi","kick-sauber":"audi","alphatauri":"racing-bulls","rb":"racing-bulls"}
races = []
for d in sorted(glob.glob(os.path.join(root, "20*/races/*"))):
    if not os.path.exists(os.path.join(d, "race-results.yml")): continue
    meta = yaml.safe_load(open(os.path.join(d, "race.yml")))
    pts, pos, tot = {}, {}, 0
    for f in ("race-results.yml", "sprint-race-results.yml"):
        p = os.path.join(d, f)
        if not os.path.exists(p): continue
        rows = yaml.safe_load(open(p)) or []; n = len(rows)
        for r in rows:
            t = TEAMMAP.get(r["constructorId"], r["constructorId"])
            v = r.get("points") or 0; pts[t] = pts.get(t, 0) + v; tot += v
            if f == "race-results.yml":
                ps = r.get("position"); pos.setdefault(t, []).append(ps if isinstance(ps, int) else n)
    races.append({"date": str(meta["date"]), "season": int(str(meta["date"])[:4]), "round": meta["round"], "gp": meta["grandPrixId"],
                  "sprint": os.path.exists(os.path.join(d, "sprint-race-results.yml")), "total": tot, "pts": pts,
                  "share": {t: round(100 * v / tot, 2) for t, v in pts.items()},
                  "pos": {t: round(sum(v) / len(v), 2) for t, v in pos.items()}})
races.sort(key=lambda r: r["date"])
TEAMS = ["mclaren","mercedes","red-bull","ferrari","williams","aston-martin","racing-bulls","alpine","haas","audi","cadillac"]
PARTNER = {"mclaren":("gemini","2025-10-19"),"williams":("claude","2026-02-02"),"aston-martin":("cohere","2026-03-04"),
           "mercedes":("openai","2026-01-22"),"ferrari":("granite","2024-11-07")}
ANY = sorted({r[0] for f in ev.values() for r in f["releases"]})
def shift(d, days): return (date.fromisoformat(d) + timedelta(days=days)).isoformat()
def series(t, metric):
    key = {"share": "share", "pos": "pos"}[metric]
    s = [(r["date"], r["season"], r[key][t]) for r in races if t in r[key]]
    return [(d, y, -v if metric == "pos" else v) for d, y, v in s]
def gidx(ser, d):
    for i, x in enumerate(ser):
        if x[0] >= d: return i
def delta(ser, i, k):
    # k races before vs k races after, all inside one season
    if i is None or i - k < 0 or i + k > len(ser): return None
    w = ser[i-k:i+k]
    if len({x[1] for x in w}) > 1: return None
    return st.mean(x[2] for x in ser[i:i+k]) - st.mean(x[2] for x in ser[i-k:i])
def test(t, metric, dates, k=3, since=None, lag=0, iters=20000, seed=7):
    ser = series(t, metric)
    ok = lambda g: delta(ser, g, k) is not None and (since is None or ser[g-k][0] >= since)
    gaps = sorted({gidx(ser, shift(d, lag)) for d in dates} - {None})
    gaps = [g for g in gaps if ok(g)]
    pool = [delta(ser, g, k) for g in range(1, len(ser)) if ok(g)]
    if not gaps or len(pool) < len(gaps) + 2: return None
    m = len(gaps); obs = st.mean(delta(ser, g, k) for g in gaps)
    rnd = random.Random(seed); sims = sorted(st.mean(rnd.sample(pool, m)) for _ in range(iters))
    mu = st.mean(pool); ext = sum(1 for s in sims if abs(s - mu) >= abs(obs - mu) - 1e-9)
    sd = st.pstdev(pool) or 1
    return {"n": m, "d": round(obs, 2), "p": round(ext / iters, 4), "z": round((obs - mu) / (sd / m ** .5), 2),
            "lo": round(sims[int(.025 * iters)], 2), "hi": round(sims[int(.975 * iters) - 1], 2), "mu": round(mu, 2),
            "up": sum(1 for g in gaps if delta(ser, g, k) > 0), "gaps": [ser[g][0] for g in gaps]}
def bh(ps):
    idx = sorted(range(len(ps)), key=lambda i: ps[i]); n = len(ps); q = [0] * n; prev = 1
    for rank, i in reversed(list(enumerate(idx, 1))):
        prev = min(prev, ps[i] * n / rank); q[i] = prev
    return q
LAGS = [0, 14, 30, 60]
OUT = {}
for metric in ("share", "pos"):
    rows, flat = [], []
    for t in TEAMS:
        row = {"team": t, "tests": {}}
        fam = PARTNER.get(t, (None,))[0]
        if fam:
            rel = [r[0] for r in ev[fam]["releases"]]; since = PARTNER[t][1]
            for lag in LAGS:
                row["tests"][f"since_l{lag}"] = test(t, metric, rel, since=since, lag=lag)
            row["tests"]["since_k1"] = test(t, metric, rel, k=1, since=since)
            row["tests"]["all_l0"] = test(t, metric, rel)
            row["tests"]["all_k1"] = test(t, metric, rel, k=1)
        row["tests"]["any_l0"] = test(t, metric, ANY)
        row["tests"]["any_k1"] = test(t, metric, ANY, k=1)
        for k, v in row["tests"].items():
            if v: flat.append((t, k, v))
        rows.append(row)
    qs = bh([v["p"] for *_, v in flat])
    for (t, k, v), q in zip(flat, qs): v["q"] = round(q, 3)
    def pooled(key):
        zs = [r["tests"][key]["z"] for r in rows if r["tests"].get(key)]
        return {"teams": len(zs), "z": round(sum(zs) / len(zs) ** .5, 2)} if zs else None
    OUT[metric] = {"rows": rows, "ntests": len(flat), "minp": min(v["p"] for *_, v in flat), "minq": min(qs),
                   "pooled": {k: pooled(k) for k in ("all_l0", "since_l0", "any_l0", "any_k1")}}
# setbacks: races inside a lab-confirmed degradation window vs the same team's other races that season
SB = []
for t, (fam, since) in PARTNER.items():
    for s, e, desc, url in ev[fam]["setbacks"]:
        for metric in ("share",):
            ser = series(t, metric)
            inn = [x for x in ser if s <= x[0] <= e]
            if not inn: continue
            season = inn[0][1]; rest = [x for x in ser if x[1] == season and not (s <= x[0] <= e)]
            SB.append({"team": t, "fam": fam, "start": s, "end": e, "desc": desc, "url": url, "races": len(inn),
                       "inside": round(st.mean(x[2] for x in inn), 2), "rest": round(st.mean(x[2] for x in rest), 2),
                       "partnered": s >= since})
json.dump({"races": races, "metrics": OUT, "setbacks": SB, "families": ev, "partner": PARTNER, "teams": TEAMS, "lags": LAGS},
          open(out, "w"))
print(len(races), "races", races[0]["date"], "->", races[-1]["date"], "sprints", sum(r["sprint"] for r in races))
for m, o in OUT.items():
    print("==", m, "tests", o["ntests"], "min p", o["minp"], "min q", round(o["minq"], 3), o["pooled"])
    for r in o["rows"]:
        print(r["team"], {k: (v["n"], v["d"], v["p"], v["q"]) if v else None for k, v in r["tests"].items()})
print(json.dumps(SB, indent=0))
