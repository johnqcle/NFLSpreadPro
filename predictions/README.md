# Spread Predictor: Week 5 2026 cover probabilities (research only, not betting advice)
Script: scripts/spread_predict.py. Output: week5_cover_probs_2026.csv (p_home_cover = chance home team covers the current line).
Model: ridge team ratings on final margins (65 games), shrunk hard (lambda 25), averaged 50/50 with the line, normal error sd 13.5.
Walk-forward backtest (train on earlier weeks only, Weeks 2-5 TNF, pushes excluded, 45 games):
- margin model lam=25: 27-18 (60.0%), Brier 0.237 vs 0.250 coin flip, two-sided p=0.23 vs 50%.
- lambdas 1/4/10 gave 53%/51%/64%; lam=25 chosen on Brier, but choosing among 4 settings after the fact inflates it.
- 43 of 45 picks were underdogs; "always take the dog" went 27-18 too. So the edge is just this season's dog run, not team skill.
- Betting teams with good ATS records (ats-residual model) went 18-27 / 19-26: chasing ATS records lost.
- Break-even at -110 is 52.4%; 45 games can't separate 60% from 50%.
Lines are current and can move; 8 completed results were within 0.5 of the line.

## v2, Oct 20 (scripts/spread_predict_v2.py)
Adds Cover Analyst's 3 splits (division game, spread >= 7, favorite better rested) as adjustments, each estimated only from earlier weeks and shrunk (K=40).
Walk-forward Weeks 2-6, 72 games: v1 41-31 (56.9%, Brier .2405) vs v2 44-28 (61.1%, Brier .2344, p=0.08 vs 50%). That's 3 extra wins.
Caveat: the splits were picked after looking at all 93 games, so this backtest is still optimistic. The real test is Weeks 7+.
Week 7 output: week7_cover_probs_v2_2026.csv (current lines as of Oct 20, they can move).
