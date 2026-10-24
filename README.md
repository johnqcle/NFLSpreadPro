# NFLSpreadPro

NFLSpreadPro is a small set of Python scripts that track how NFL teams do **against the spread (ATS)** in the 2026 season and estimate, for each upcoming game, which side is a bit more likely to cover.

> **Not gambling advice.** This is a research and hobby project. The model is built on only a few weeks of data, and its edges are small (most picks land between 50% and 60%). Do not use it to bet money you can't afford to lose. If gambling is a problem for you, call 1-800-GAMBLER (US).

## What "against the spread" means

Sportsbooks set a **point spread** to even out a game. If KC is a 3-point favorite (KC -3), KC must win by **more than 3** to **cover**. The underdog covers if it wins outright or loses by less than 3. If KC wins by exactly 3, it's a **push** (nobody covers).

In this project the math is: `cover margin = (home score - away score) + home_line`. Above 0 means the home team covered, below 0 means the away team covered, and exactly 0 is a push.

## Requirements

- Python 3.9 or newer (tested with 3.13)
- pandas and numpy, installed with `pip install -r requirements.txt`
- A web browser to view the HTML pages

## Install

1. Get the code by doing **one** of the following:
   - `git clone https://github.com/johnqcle/NFLSpreadPro.git`
   - On GitHub, click **Code > Download ZIP**, then unzip the file.
2. Open a terminal in the project folder:
   - Windows: open the folder in File Explorer, type `cmd` in the address bar, and press Enter.
   - Mac/Linux: `cd` into the folder.
3. Create a virtual environment (optional, but recommended) and install the dependencies:

| Windows (cmd / PowerShell) | Mac / Linux |
|---|---|
| `py -m venv .venv` | `python3 -m venv .venv` |
| `.venv\Scripts\activate` | `source .venv/bin/activate` |
| `py -m pip install -r requirements.txt` | `python3 -m pip install -r requirements.txt` |

On Windows, `python` works in place of `py` if Python is on your PATH. Every command below is run from the project folder. Windows users should replace `python3` with `py` and `/` with `\` in paths.

The scripts locate their files relative to their own folder, so you can put the project anywhere.

## Weekly workflow

### 1. Add results and lines

Do **either** A or B.

**A. Rebuild from nflverse (easiest).** Download the latest `games.csv` from https://github.com/nflverse/nfldata/blob/master/data/games.csv (click "Download raw file") and save it as `data/nflverse_games.csv`. Then run this command, with today's date:

```
python3 scripts/build_lines.py 2026-10-27
```

This **overwrites** `data/games_2026.csv` (every 2026 regular-season game with a final score) and `data/upcoming_2026.csv` (the next week's unplayed games and their current lines). It then lists any games that are missing lines.

**B. Edit by hand.** Open `data/games_2026.csv` in Excel or a text editor and add one row per finished game (see the column list below). Put next week's games in `data/upcoming_2026.csv` with the score columns left blank. In Excel, save the file as **CSV**, not .xlsx.

The v3 predictor also needs `data/team_epa_by_game_2026.csv`, which holds per-game EPA stats (see the column list below). For each finished game, add one row per team, or the EPA part of the model will use stale data. These numbers can be computed from nflverse play-by-play data. No script in this project builds that file.

### 2. Run the ATS report

```
python3 scripts/ats_report.py
python3 scripts/ats_page.py
```

`ats_report.py` writes the following to `reports/`:
- `ats_report_2026.md`: a readable week-by-week report and team table
- `ats_by_game_2026.csv`, `ats_team_records_2026.csv`, `ats_team_splits_2026.csv`, `ats_splits_2026.csv`, `ats_entering_week_2026.csv`, `ou_by_game_2026.csv`, and `upcoming_situational_2026.csv`

`ats_page.py` turns those files into `reports/ats_dashboard_2026.html`, a dashboard with sortable, filterable tables. Run `ats_report.py` first.

### 3. Run the predictions (v3 is the main model)

| Windows (cmd) | Mac / Linux |
|---|---|
| `py scripts\spread_predict_v3.py` | `python3 scripts/spread_predict_v3.py` |

The script prints the picks, sorted from most to least confident, and saves them to `predictions/weekN_cover_probs_v3_2026.csv`.

Options (environment variables):
- `TAG`: adds a suffix to the file name so earlier runs aren't overwritten, for example `_fri`. Windows: `set TAG=_fri` then run the command. Mac/Linux: `TAG=_fri python3 scripts/spread_predict_v3.py`.
- `MODE=backtest`: tests the model on past weeks instead of predicting. Note: the backtest week range is hardcoded to Weeks 2-6.
- `P0`: how much weight the 2025 EPA prior gets, in plays (default 400).

Older models, kept for comparison:
- `spread_predict_v2.py [fresh_lines.csv] [tag]` writes `predictions/weekN_cover_probs_v2_2026<tag>.csv` and prints a backtest. If you pass an nflverse-format CSV as the first argument, its `spread_line` values replace the upcoming lines.
- `spread_predict.py` is v1. **Note:** v1 always writes its output to `predictions/week5_cover_probs_2026.csv` and `predictions/backtest_margin_lam25.csv`, whatever the current week is.

### 4. View the output

- Picks: open `predictions/weekN_cover_probs_v3_2026.csv` in Excel.
- Report: open `reports/ats_report_2026.md` in any Markdown viewer or text editor.
- Dashboard: double-click `reports/ats_dashboard_2026.html`.
- `site/index.html` is the published Week 7 picks page. **No script in this project creates it**, so it won't update when you run the scripts. Use the dashboard and the predictions CSV for current results.

## Data format: `data/games_2026.csv` (and `upcoming_2026.csv`)

| Column | Meaning |
|---|---|
| game_id | `2026_WW_AWAY_HOME`, for example `2026_01_NE_SEA` |
| week, date, weekday, kickoff_et | Week number, YYYY-MM-DD, day name, kickoff time (Eastern) |
| away, home | Team codes (nflverse codes such as LA, LAC, KC) |
| location | `Home`, or `Neutral` for neutral-site and international games |
| favorite | The favored team, or `PK` for a pick'em |
| spread | Points the favorite gives, always positive (for example 3.5) |
| home_line | The spread from the home team's side. Negative means the home team is favored, for example -3.5 |
| total | Over/under line |
| away_score, home_score | Final scores (blank in upcoming_2026.csv) |
| overtime | 1 if the game went to overtime |
| div_game | 1 if it's a division game |
| away_rest, home_rest | Days of rest |
| pfr_id, espn_id, source | Reference IDs and a note on the data source (informational) |

`favorite`, `spread`, and `home_line` must agree. `ats_report.py` lists any rows where they don't under "Data issues".

`team_epa_by_game_2026.csv` columns: `game_id, week, team, off_plays, off_epa_per_play, off_success_rate, def_plays, def_epa_per_play, def_success_rate`. `team_epa_season_2025.csv` has the same columns minus game_id and week, with one row per team.

## What the output means

v3 prediction columns:
- `side`: the model's **lean**, the team it expects to cover
- `ln`: that team's line (for example -3.0 means the team is laying 3, and +3.0 means it's getting 3)
- `opp`: the opponent
- `home_line`: the line from the home team's view
- `P`: **confidence**, the model's estimated chance that `side` covers (0.57 = 57%)

Because the market line is already close to a coin flip, values near 0.50 mean "no real opinion". Even 0.60+ is a modest lean, not a lock.

How v3 works: it combines ridge team ratings from game margins with EPA-per-play ratings (seeded from 2025), then blends that 50/50 with the market line. It adjusts for division games, big spreads, and rest edges, plus each team's season ATS record. Win chance is a normal distribution with a standard deviation of 13.5 points.

v2 columns: `p_home_cover` is the chance the home team covers, `lean` is the pick, and `p_lean` is the confidence.

## Folder layout

```
NFLSpreadPro/
  requirements.txt
  scripts/
    build_lines.py           rebuild game files from nflverse
    ats_report.py            ATS report + CSVs
    ats_page.py              HTML dashboard
    spread_predict_v3.py     main predictor (loads parts of v2's code, so keep v2 in the folder)
    spread_predict_v2.py     older predictor
    spread_predict.py        v1 (research)
  data/        games_2026.csv, upcoming_2026.csv, EPA files, raw nflverse pulls, snapshots/
  reports/     outputs of ats_report.py / ats_page.py
  predictions/ outputs of the predictors
  site/        static Week 7 picks page (not regenerated)
```

## Troubleshooting

- **`'python' is not recognized` / `python3: command not found`**: On Windows, use `py`, or reinstall Python with "Add to PATH" checked.
- **`ModuleNotFoundError: pandas`**: Run `pip install -r requirements.txt` in the same environment you use to run the scripts (activate `.venv` first).
- **`FileNotFoundError`**: Check that the file exists under `data/`. For `build_lines.py`, you need to download `data/nflverse_games.csv` first.
- **`KeyError` with a team code**: A team code is misspelled, or a game_id in the upcoming file has no matching row. Use nflverse team codes.
- **`ValueError: could not convert string to float`**: A spread or score cell is blank or contains text (like "PK") where a number belongs. Use 0 for a pick'em spread.
- **Predictions look stale**: Make sure `upcoming_2026.csv` contains next week's games, and that you re-ran the scripts in order: report, then predict.
- **Excel changed my CSV**: Excel can reformat dates and drop leading zeros. Save as "CSV (Comma delimited)", or edit the file in a text editor.
- **Text looks garbled on Windows**: Run `set PYTHONUTF8=1` before running the scripts.

## Disclaimer

NFLSpreadPro is for education and entertainment only. It is **not gambling, betting, or financial advice**, and nothing here guarantees results. Lines and scores come from public nflverse data and may contain errors. Check local laws before wagering.
