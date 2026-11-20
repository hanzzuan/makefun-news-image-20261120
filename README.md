# The World — 20 November 2026

![news-image-20261120](https://make.fun/badge/news-image-20261120.svg)
![rank](https://make.fun/badge/news-image-20261120/hanzzuan/makefun-news-image-20261120/rank.svg)
![reward](https://make.fun/badge/news-image-20261120/hanzzuan/makefun-news-image-20261120/reward.svg)

Entry for the make.fun bounty [news-image-20261120](https://make.fun/bounty/news-image-20261120): sum up 20 November's world news in one image.

A newspaper front page drawn entirely by a small Python program (standard library only, with its own hand-drawn 5x7 bitmap font and pure-Python PNG encoder). The masthead names the day — Friday, 20 November 2026 — and six stories cover it:

1. **Trump, Xi and Putin meet in China** — the first three-way summit ends with a joint peace declaration.
2. **Myanmar committed genocide, UN court rules** — the historic Rohingya verdict at The Hague.
3. **Cyclone Akvan nears the Odisha coast** — 300,000 evacuated as landfall looms.
4. **Trump puts the Iran decision off to 2027** — "no rush," he says.
5. **Anthropic lists, the first pure AI company on the market** — a reported $1.5 trillion debut.
6. **Voyager 1 reaches a light-day from Earth** — NASA confirms the milestone.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024, deterministic — two runs produce identical bytes).
