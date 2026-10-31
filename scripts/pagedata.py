import json, sys
a = json.load(open(sys.argv[1]))
NAMES = {"sao-paulo":"São Paulo","barcelona-catalunya":"Barcelona","united-states":"United States","great-britain":"Great Britain",
 "saudi-arabia":"Saudi Arabia","abu-dhabi":"Abu Dhabi","las-vegas":"Las Vegas","emilia-romagna":"Emilia-Romagna"}
races = [{"d": r["date"], "gp": NAMES.get(r["gp"], r["gp"].replace("-", " ").title()), "s": r["sprint"],
          "p": r["pts"], "h": r["share"], "q": r["pos"]} for r in a["races"]]
for m in a["metrics"].values():
    for row in m["rows"]:
        for v in row["tests"].values():
            if v: v.pop("gaps", None)
out = {"races": races, "families": a["families"], "partner": a["partner"], "metrics": a["metrics"], "setbacks": a["setbacks"], "lags": a["lags"]}
print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
