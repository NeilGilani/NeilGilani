#!/usr/bin/env bash
# Download the WOFF files svgkit.py expects into ../fonts (Geist, Geist Mono; SIL OFL 1.1).
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p ../fonts
UA="Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0"  # makes Google serve WOFF
for fam in "Geist:wght@400;500;600" "Geist+Mono:wght@400;500;600"; do
  curl -sS -A "$UA" "https://fonts.googleapis.com/css2?family=$fam"
done | python3 -c '
import re, sys, urllib.request
for block in re.findall(r"@font-face\s*{([^}]*)}", sys.stdin.read()):
    fam = re.search(r"font-family: .([^;]+).;", block).group(1).replace(" ", "").strip("\x27\"")
    weight = re.search(r"font-weight: (\d+)", block).group(1)
    url = re.search(r"url\(([^)]+)\)", block).group(1)
    urllib.request.urlretrieve(url, f"../fonts/{fam}-{weight}.woff")
    print("fetched", fam, weight)
'
