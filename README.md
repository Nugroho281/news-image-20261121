# The World in One Page — 21 November 2026

[![make.fun bounty](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/Nugroho281/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/Nugroho281/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121)

A one-page newspaper front page that sums up the world news of
**Saturday 21 November 2026** in a single 1024×1024 image: 41 stories —
15 of them drawn as picture panels, 26 more in brief — under one giant
date line.

The hero story is Iran's strike on US bases in Bahrain and the fire at
a civilian industrial plant. The pictured panels cover the missile hit
on Kryvyi Rih, the capture of FBI most-wanted cartel boss Chapo Isidro
in Mexico, the AI stock sell-off, COP31 running into overtime in
Antalya, the Shenzhen three-way summit, the UN court's Myanmar
genocide finding, the claimed AI-assisted Riemann proof, BepiColombo
reaching Mercury, GTA VI's record launch day, Wolbachia mosquitoes
cutting dengue in Brazil, the Peru earthquake, Leeds stunning Chelsea
4–1, Alcaraz reaching the ATP Finals final, and Princess Kate
announcing she is in remission.

## How it is made

`main.py` is a pure Python 3 standard-library program — no Pillow, no
numpy, no network. It draws the whole page at 2048×2048 (2×
supersample) with flat saturated shapes and a hand-built 5×7 pixel
font, then box-downscales to 1024×1024 so every letter and edge stays
sharp and the colours stay vivid. Every story was checked against the
day's reporting (BBC, Al Jazeera, Reuters, AP, The Guardian, UPI,
France 24, Euronews, CBC, NPR and the sports wires); the one
unconfirmed item — the Riemann proof — is labelled a claim.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024×1024, well under the 1 MiB gate).
The program is deterministic: two runs write identical bytes.

## License

MIT — see `LICENSE`.

---

Optional: earn referral rewards, a second way to make money on
make.fun — [join with my referral link](https://make.fun/r/scz7tdtw).
