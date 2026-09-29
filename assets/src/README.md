# Profile graphics

Every image in `assets/` is generated from code in this folder. Text is outlined
into vector paths with the real font (shaped by HarfBuzz), because GitHub draws
README SVGs as images and web fonts never load inside them. That way the banner
and diagrams render identically everywhere.

```bash
pip install fonttools uharfbuzz brotli
./fetch_fonts.sh                  # Geist + Geist Mono from Google Fonts (SIL OFL) into ../fonts
python banner.py ..               # banner-dark.svg / banner-light.svg
python diag_hebb.py ..            # hebb-loop-*.svg
python diag_stack.py ..           # markets-stack-*.svg
python diag_vitals.py ..          # vitals-pipeline-*.svg
```

`cards.py` builds the 1280x640 social-preview cards; `render.js` rasterizes any
SVG to PNG with headless Chromium (`node render.js out.png in.svg`).
