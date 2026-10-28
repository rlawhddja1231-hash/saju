# saju — accurate Four Pillars (BaZi / 사주) for Claude

**[한국어 설명 →](README.ko.md)**

Ask an AI for your *saju* or *BaZi* chart and it will usually guess the pillars from memory. The year, month and hour pillars depend on the **exact minute of the solar terms** (입춘 Start of Spring, 경칩 …), on **historical time zones and daylight saving time**, and on **conventions that differ between apps**. Guessing gets them wrong.

This Claude skill makes Claude **calculate** the chart with a bundled, dependency-free calculator. Claude then interprets that result only.

```
You:    Read my saju. 1990-05-15, 2:30 pm, female, born in Seoul.
Claude: (runs saju.py) …庚午 / 辛巳 / 庚辰 / 癸未, Day Master 庚 Metal…
```

![Example chart (Korean output)](docs/img/chart-ko.jpg)

## What makes it different

| | saju (this) | a chatbot guessing |
|---|---|---|
| Solar-term times | Charts for 1900–2100; solar-term table computed by two independent methods (寿星 algorithm and VSOP87) that agree within **57 seconds** | memory |
| Korea's DST (1948–60, 1987–88) and UTC+8:30 era (1908–11, 1954–61) | applied automatically, verified minute-by-minute against the tz database | usually ignored |
| Korean lunar calendar (KASI) 1900–2049, leap months | ✅ | often off by a day |
| Different app conventions (clock time / longitude / true solar time, 23:00 vs 00:00 day change) | chooses the common default **and warns when another convention gives different pillars** | silent |
| Born minutes from a solar term | ⚠️ tells you the month (and year) pillar depends on the exact minute | silent |
| Install | nothing to install (Python standard library only) | — |

### Tested

- **30,000 random moments** (10,000 of them within 90 seconds of a solar term) compared against the independent [lunar-python](https://github.com/6tail/lunar-python) library: **0 mismatches** in all four pillars. The 23:00 day-change mode was tested on 15,000 more moments, also with 0 mismatches.
- 3,000 luck-pillar (大運) charts: same direction and first pillar every time, with the start age within 0.01 year.
- Korean lunar ↔ solar conversion: 18,242 dates checked with 0 errors.
- Start of Spring times match KASI's published minutes (2000-02-04 21:40, 1984-02-05 00:19, 2026-02-04 05:02).
- Run `python3 plugins/saju/skills/saju/tests/selftest.py` to check it yourself.

## Features

- Four pillars with hidden stems (지장간), Ten Gods (십신), 12 life stages (12운성), and element counts
- Combinations, clashes, punishments, harms, breaks and 원진 inside the chart
- Common symbolic stars: Nobleman, Peach Blossom, Travelling Horse, Canopy, Yang Blade, 괴강, and Void
- **Luck pillars (대운)** with exact start age, plus **annual pillars (세운)** and how each year hits your chart
- **Compatibility (궁합)** between two people: day-master relation, spouse-palace relation, cross-chart combos and clashes, and which elements each person fills for the other
- **Yearly fortune by zodiac animal (띠별 운세)**: each animal's clash/harmony with the year and the Korean *sam-jae* (3 hard years), with the animal decided at Start of Spring (not Jan 1 or Lunar New Year)
- Today's day pillar (일진), 24 solar terms of any year, and solar ↔ lunar conversion
- Korean or English output (`--lang en`) for every command, plus `--json` for the full data

## Install

### Claude Code
```
/plugin marketplace add rlawhddja1231-hash/saju
/plugin install saju@saju-plugins
```

### claude.ai (web and app)
1. Download [`saju.zip`](https://github.com/rlawhddja1231-hash/saju/raw/main/dist/saju.zip).
2. Go to claude.ai → Customize → Skills → **+ Add → Upload skill**.
3. Code execution must be turned on.

## Use

Just talk to Claude:

- "Read my BaZi: 1990-05-15 14:30, female, born in Seoul"
- "Lunar 1990-04-21, time unknown, male. What's my luck pillar now?"
- "Compatibility: me 1990-05-15 14:30 f, him 1988-07-01 23:20 m"
- "What's today's day pillar?"
- "Show the 2026 fortune for each zodiac animal"

Or run the calculator yourself:

```
python3 plugins/saju/skills/saju/scripts/saju.py chart --date 1990-05-15 --time 14:30 --gender f --lang en
python3 plugins/saju/skills/saju/scripts/saju.py chart --date 1990-04-21 --lunar --gender m
python3 plugins/saju/skills/saju/scripts/saju.py compat --a "1990-05-15 14:30 f" --b "1988-07-01 23:20 m"
python3 plugins/saju/skills/saju/scripts/saju.py terms --year 2026
```

Options:

| Option | Meaning |
|---|---|
| `--basis clock` (default) / `lmt` / `true` | clock time / local mean time by longitude / true solar time |
| `--zi midnight` (default) / `23` | day changes at 00:00 / at 23:00 (조자시) |
| `--place 부산` or `--lon 129.08` | birthplace, used by `lmt` and `true` |
| `--tz America/New_York` or `--tz UTC-5` | for births outside Korea |

Examples: [Korean chart](docs/example-ko.md) · [English chart](docs/example-en.md) · [born 10 minutes before Start of Spring](docs/example-boundary.md) · [compatibility](docs/example-compat-en.md)

## Interpretation stance

Claude reads the chart as a tool for fun and self-reflection. It describes tendencies, not fate. It won't predict death, illness or divorce, and it won't sell talismans. For big health, money or legal decisions, it points you to real experts.

## Data and credits

- Solar-term instants were generated with [lunar-python](https://github.com/6tail/lunar-python) (MIT) and cross-checked with [PyEphem](https://rhodesmill.org/pyephem/) (VSOP87). See `dev/`.
- The Korean lunar table comes from [korean_lunar_calendar_py](https://github.com/usingsky/korean_lunar_calendar_py) (MIT), which is based on KASI data.
- Korean time-zone history matches the IANA tz database (`Asia/Seoul`).

MIT License.
