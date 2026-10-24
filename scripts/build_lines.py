"""Rebuild games_2026.csv and upcoming_2026.csv from the raw nflverse games.csv.
Usage: python3 build_lines.py <pull_date YYYY-MM-DD>"""
import os as _os; ROOT=_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'')  # project folder, portable
import csv, sys
D = ROOT+'data/'
pulled = sys.argv[1]
SRC = f"nflverse nfldata games.csv (https://github.com/nflverse/nfldata/blob/master/data/games.csv), pulled {pulled}; PFR boxscore id in pfr_id"
COLS = "game_id,week,date,weekday,kickoff_et,away,home,location,favorite,spread,home_line,total,away_score,home_score,overtime,div_game,away_rest,home_rest,pfr_id,espn_id,source".split(',')
raw = [r for r in csv.DictReader(open(D + 'nflverse_games.csv')) if r['season'] == '2026' and r['game_type'] == 'REG']

def f1(x):
    return '' if x == '' else f"{float(x):.1f}"

def row(r, scores):
    sl = r['spread_line']
    if sl == '':
        fav, spread, hl = '', '', ''
    else:
        s = float(sl)  # nflverse: positive = home favored
        fav = r['home_team'] if s > 0 else r['away_team'] if s < 0 else 'PK'
        spread, hl = f"{abs(s):.1f}", f"{-s + 0.0:.1f}"
    return dict(game_id=r['game_id'], week=r['week'], date=r['gameday'], weekday=r['weekday'], kickoff_et=r['gametime'],
                away=r['away_team'], home=r['home_team'], location=r['location'], favorite=fav, spread=spread, home_line=hl,
                total=f1(r['total_line']), away_score=r['away_score'] if scores else '', home_score=r['home_score'] if scores else '',
                overtime=r['overtime'] if scores else '', div_game=r['div_game'], away_rest=r['away_rest'], home_rest=r['home_rest'],
                pfr_id=r['pfr'], espn_id=r['espn'], source=SRC)

done = [r for r in raw if r['away_score'] != '' and r['home_score'] != '']
todo = [r for r in raw if not (r['away_score'] != '' and r['home_score'] != '')]
def w(path, rs, scores):
    with open(path, 'w', newline='') as fh:
        wr = csv.DictWriter(fh, COLS); wr.writeheader()
        for r in rs: wr.writerow(row(r, scores))
w(D + 'games_2026.csv', done, True)
nxt = min(int(r['week']) for r in todo) if todo else None
up = [r for r in todo if int(r['week']) == nxt]
w(D + 'upcoming_2026.csv', up, False)
print('completed', len(done), 'weeks', sorted({int(r['week']) for r in done}), 'next week', nxt, len(up))
print('missing lines (completed):', [r['game_id'] for r in done if r['spread_line'] == '' or r['total_line'] == ''])
print('missing lines (upcoming):', [r['game_id'] for r in up if r['spread_line'] == '' or r['total_line'] == ''])
print('unplayed games in weeks < next:', [r['game_id'] for r in todo if nxt and int(r['week']) < nxt])
from collections import Counter
print('per week completed:', sorted(Counter(int(r['week']) for r in done).items()))
