import sys, os, urllib.request, concurrent.futures as cf
root = sys.argv[1]
B = "https://raw.githubusercontent.com/f1db/f1db/main/src/data/seasons/"
paths = [l.strip() for l in open(os.path.join(os.path.dirname(__file__), "..", "data", "f1db-races.txt")) if l.strip()]
jobs = [(p, f) for p in paths for f in ("race.yml", "race-results.yml", "sprint-race-results.yml")]
def get(job):
    p, f = job
    try:
        data = urllib.request.urlopen(B + p + "/" + f, timeout=30).read()
    except Exception:
        return None
    d = os.path.join(root, p); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f), "wb").write(data)
    return job
with cf.ThreadPoolExecutor(32) as ex:
    n = sum(1 for r in ex.map(get, jobs) if r)
print("downloaded", n, "of", len(jobs))
