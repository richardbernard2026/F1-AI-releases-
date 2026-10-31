import sys, json
body = open(sys.argv[1]).read(); data = open(sys.argv[2]).read().strip(); outdir = sys.argv[3]; repo = sys.argv[4] if len(sys.argv) > 4 else ""
site_url = sys.argv[5] if len(sys.argv) > 5 else ""
body = body.replace("__DATA__", data).replace("__REPO__", repo)
fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">'
title = "Do F1 teams get faster when their AI gets smarter?"
desc = "88 race weekends, 64 AI model releases, 114 tests. A team's results after its AI partner ships a new model look like its results after any random date."
og = f'''<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{desc}">'''
if site_url:
    og += f'\n<meta property="og:url" content="{site_url}"><meta property="og:image" content="{site_url}/og.png"><meta name="twitter:image" content="{site_url}/og.png">'
site = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
{og}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23141414'/%3E%3Cpath d='M7 22h4V12H7zM14 22h4V8h-4zM21 22h4v-6h-4z' fill='%23d7261e'/%3E%3C/svg%3E">
{fonts}
</head>
<body>
{body}
</body>
</html>
'''
open(f"{outdir}/index.html", "w").write(site)
art = f"<title>Model Drops vs Race Pace</title>\n<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n{fonts}\n{body}"
open(f"{outdir}/artifact.html", "w").write(art)
print("ok", len(site))
