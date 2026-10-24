import os as _os; ROOT=_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'')  # project folder, portable
import csv, collections, sys
rows=list(csv.DictReader(open(ROOT+'data/games_2026.csv')))
issues=[]
games=[]
for r in rows:
    hl=float(r['home_line']); sp=float(r['spread']); fav=r['favorite']
    exp = -sp if fav==r['home'] else (sp if fav==r['away'] else None)
    if sp==0: exp=0.0
    if exp is None or abs(exp-hl)>1e-9: issues.append(f"{r['game_id']}: favorite/spread {fav} {sp} vs home_line {hl}")
    hs,as_=int(r['home_score']),int(r['away_score'])
    adj=(hs-as_)+hl
    if adj>0: cov=r['home']; res='home'
    elif adj<0: cov=r['away']; res='away'
    else: cov='PUSH'; res='push'
    favcov = 'push' if res=='push' or sp==0 else ('fav' if cov==fav else 'dog')
    games.append(dict(game_id=r['game_id'],week=int(r['week']),date=r['date'],away=r['away'],home=r['home'],location=r['location'],
        favorite=fav if sp else 'PK',spread=sp,home_line=hl,away_score=as_,home_score=hs,home_margin=hs-as_,cover_margin_home=adj,
        ats_winner=cov,result=res,fav_or_dog_covered=favcov,half_point_sensitive=int(abs(adj)<=0.5)))
f=ROOT+'reports/ats_by_game_2026.csv'
w=csv.DictWriter(open(f,'w',newline=''),fieldnames=list(games[0].keys())); w.writeheader(); w.writerows(games)
T=collections.defaultdict(lambda: collections.Counter())
for g in games:
    for side,team in (('home',g['home']),('away',g['away'])):
        c=T[team]; opp='away' if side=='home' else 'home'
        k='P' if g['result']=='push' else ('W' if g['result']==side else 'L')
        c[k]+=1; c[side+k]+=1
        role = None if g['spread']==0 else ('fav' if team==g['favorite'] else 'dog')
        if role: c[role+k]+=1
        margin = g['cover_margin_home'] if side=='home' else -g['cover_margin_home']
        c['margin_sum']+=margin; c['g']+=1
recs=[]
fmt=lambda c,p: f"{c[p+'W']}-{c[p+'L']}-{c[p+'P']}"
for t,c in T.items():
    dec=c['W']+c['L']
    recs.append(dict(team=t,games=c['g'],ats=f"{c['W']}-{c['L']}-{c['P']}",cover_pct=round(c['W']/dec,3) if dec else '',
        home=fmt(c,'home'),away=fmt(c,'away'),as_fav=fmt(c,'fav'),as_dog=fmt(c,'dog'),avg_cover_margin=round(c['margin_sum']/c['g'],2)))
recs.sort(key=lambda x:(-(x['cover_pct'] or 0),-x['avg_cover_margin']))
w=csv.DictWriter(open(ROOT+'reports/ats_team_records_2026.csv','w',newline=''),fieldnames=list(recs[0].keys())); w.writeheader(); w.writerows(recs)
# markdown
_lw=max(g["week"] for g in games); _n=sum(1 for g in games if g["week"]==_lw)
L=[f"# 2026 NFL ATS report (through Week {_lw}, {_n} games that week)","",f"Source: data/games_2026.csv ({len(games)} games, nflverse consensus closing lines). Cover = final margin plus the home team's line; zero is a push.",""]
if issues: L+=["## Data issues"]+["- "+i for i in issues]+[""]
tot=collections.Counter(g['result'] for g in games); fd=collections.Counter(g['fav_or_dog_covered'] for g in games)
L+=["## League-wide",f"- Home {tot['home']}, away {tot['away']}, push {tot['push']}",f"- Favorites {fd['fav']}, underdogs {fd['dog']}, push/PK {fd['push']}",""]
for wk in sorted({g['week'] for g in games}):
    L+=[f"## Week {wk}","| Matchup | Line | Final | Covered |","|---|---|---|---|"]
    for g in [g for g in games if g['week']==wk]:
        line='PK' if g['spread']==0 else f"{g['favorite']} -{g['spread']:g}"
        flag=' (half-point)' if g['half_point_sensitive'] else ''
        L.append(f"| {g['away']} @ {g['home']} | {line} | {g['away']} {g['away_score']}, {g['home']} {g['home_score']} | {g['ats_winner']}{flag} |")
    L.append("")
L+=["## Season-to-date ATS by team","| Team | ATS | Cover % | Home | Away | As fav | As dog | Avg cover margin |","|---|---|---|---|---|---|---|---|"]
for r in recs: L.append(f"| {r['team']} | {r['ats']} | {r['cover_pct']} | {r['home']} | {r['away']} | {r['as_fav']} | {r['as_dog']} | {r['avg_cover_margin']:+} |")
open(ROOT+'reports/ats_report_2026.md','w').write("\n".join(L)+"\n")
print("issues",issues); print(tot,fd); print(sum(g['half_point_sensitive'] for g in games),"half-pt")
for r in recs[:5]+recs[-5:]: print(r)
print([ (g['game_id'],g['cover_margin_home']) for g in games if g['week']==5])

# ---- situational splits (division, spread size, rest) ----
D={r['game_id']:r for r in rows}
def feats(r):
    sp=float(r['spread']); f=r['favorite']
    if sp==0: return None
    fr=int(r['home_rest'] if f==r['home'] else r['away_rest']); dr=int(r['away_rest'] if f==r['home'] else r['home_rest'])
    return dict(div_game=int(r['div_game']), spread_bucket='<=3' if sp<=3 else ('3.5-6.5' if sp<7 else '7+'),
                rest_edge='fav' if fr>dr else ('dog' if dr>fr else 'equal'))
S=collections.defaultdict(collections.Counter)
for g in games:
    ft=feats(D[g['game_id']])
    if not ft: continue
    for k,v in ft.items(): S[(k,str(v))][g['fav_or_dog_covered']]+=1
out=[dict(split=k,value=v,dog_covers=c['dog'],fav_covers=c['fav'],pushes=c['push'],
          dog_cover_pct=round(c['dog']/(c['dog']+c['fav']),3) if c['dog']+c['fav'] else '') for (k,v),c in sorted(S.items())]
w=csv.DictWriter(open(ROOT+'reports/ats_splits_2026.csv','w',newline=''),fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
up=list(csv.DictReader(open(ROOT+'data/upcoming_2026.csv')))
uo=[]
for r in up:
    ft=feats(r) or dict(div_game=int(r['div_game']),spread_bucket='PK',rest_edge='n/a')
    dog = r['home'] if r['favorite']==r['away'] else r['away']
    uo.append(dict(game_id=r['game_id'],favorite=r['favorite'],underdog=dog,spread=r['spread'],**ft))
w=csv.DictWriter(open(ROOT+'reports/upcoming_situational_2026.csv','w',newline=''),fieldnames=list(uo[0].keys())); w.writeheader(); w.writerows(uo)
with open(ROOT+'reports/ats_report_2026.md','a') as fh:
    fh.write("\n## Situational splits (underdog vs favorite covers)\n| Split | Value | Dog | Fav | Push | Dog cover % |\n|---|---|---|---|---|---|\n")
    for o in out: fh.write(f"| {o['split']} | {o['value']} | {o['dog_covers']} | {o['fav_covers']} | {o['pushes']} | {o['dog_cover_pct']} |\n")

# ---- team ATS record entering each week (prior weeks only, no leakage) ----
weeks=sorted({g['week'] for g in games}); nxt=max(weeks)+1
pre=[]
for wk in weeks+[nxt]:
    c=collections.defaultdict(collections.Counter)
    for g in games:
        if g['week']>=wk: continue
        for side,team in (('home',g['home']),('away',g['away'])):
            k='P' if g['result']=='push' else ('W' if g['result']==side else 'L')
            c[team][k]+=1; c[team]['m']+=(g['cover_margin_home'] if side=='home' else -g['cover_margin_home']); c[team]['g']+=1
    for t in sorted(T):
        x=c[t]; dec=x['W']+x['L']
        pre.append(dict(entering_week=wk,team=t,ats_w=x['W'],ats_l=x['L'],ats_p=x['P'],
            cover_pct=round(x['W']/dec,3) if dec else '',avg_cover_margin=round(x['m']/x['g'],2) if x['g'] else ''))
w=csv.DictWriter(open(ROOT+'reports/ats_entering_week_2026.csv','w',newline=''),fieldnames=list(pre[0].keys())); w.writeheader(); w.writerows(pre)

# ---- added 2026-10-21: over/under, per-team situational splits, recent form ----
G=sorted(games,key=lambda g:(g['week'],g['game_id'])); raw={r['game_id']:r for r in rows}
ou=[]
for g in G:
    r=raw[g['game_id']]; t=r.get('total','').strip(); pts=g['away_score']+g['home_score']
    if not t: ou.append(dict(game_id=g['game_id'],week=g['week'],total='missing',points=pts,ou_result='missing',ou_margin='')); continue
    t=float(t); d=pts-t
    ou.append(dict(game_id=g['game_id'],week=g['week'],total=t,points=pts,ou_result='over' if d>0 else ('under' if d<0 else 'push'),ou_margin=d))
w=csv.DictWriter(open(ROOT+'reports/ou_by_game_2026.csv','w',newline=''),fieldnames=list(ou[0].keys())); w.writeheader(); w.writerows(ou)
ouc=collections.Counter(o['ou_result'] for o in ou)
TS=collections.defaultdict(lambda:collections.defaultdict(lambda:[0,0,0])); RF=collections.defaultdict(list)
for g in G:
    r=raw[g['game_id']]; ft=feats(r)
    for side in ('home','away'):
        team=g[side]; m=g['cover_margin_home'] if side=='home' else -g['cover_margin_home']
        i=0 if m>0 else (1 if m<0 else 2); RF[team].append(i)
        if ft:
            TS[team]['div' if ft['div_game'] else 'nondiv'][i]+=1
            TS[team]['spread_'+ft['spread_bucket']][i]+=1
            mine=int(r[side+'_rest']); opp=int(r[('away' if side=='home' else 'home')+'_rest'])
            TS[team]['rest_'+('more' if mine>opp else 'less' if mine<opp else 'equal')][i]+=1
keys=sorted({k for t in TS.values() for k in t}); f3=lambda x:f"{x[0]}-{x[1]}-{x[2]}"
tr=[]
for team in sorted(RF):
    l3=RF[team][-3:]; d=dict(team=team,last3_ats=f3([l3.count(0),l3.count(1),l3.count(2)]))
    for k in keys: d[k]=f3(TS[team][k])
    tr.append(d)
w=csv.DictWriter(open(ROOT+'reports/ats_team_splits_2026.csv','w',newline=''),fieldnames=list(tr[0].keys())); w.writeheader(); w.writerows(tr)
with open(ROOT+'reports/ats_report_2026.md','a') as fh:
    fh.write(f"\n## Over/under\n- Over {ouc['over']}, under {ouc['under']}, push {ouc['push']}, missing total {ouc['missing']}\n- Per game: ou_by_game_2026.csv. Per-team splits and last-3 ATS form: ats_team_splits_2026.csv\n")
