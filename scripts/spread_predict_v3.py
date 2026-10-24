"""v3 (research only): v2 + EPA-per-play team ratings, seeded from 2025 season EPA (regressed 50%).
Team net EPA = off - def EPA/play; current-season plays blended with a prior worth P0 plays.
EPA margin = S*(net_h-net_a) + home field; S fit walk-forward (ridge toward 30). Model margin = mean(ridge, EPA)."""
import os as _os; ROOT=_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'')  # project folder, portable
import sys,os; P0=float(os.environ.get('P0',400)); sys.argv=[sys.argv[0]]
src=open(ROOT+'scripts/spread_predict_v2.py').read().split('for v2 in [False,True]:')[0].split("o=up[[")[0]
exec(src)
e=pd.read_csv(D+'data/team_epa_by_game_2026.csv'); pr=pd.read_csv(D+'data/team_epa_season_2025.csv').set_index('team')
prior=0.5*(pr.off_epa_per_play-pr.def_epa_per_play)
def epa_r(wk):
    c=e[e.week<wk]; r={}
    for t in teams:
        x=c[c.team==t]; n=x.off_plays.sum()+x.def_plays.sum()
        cur=((x.off_epa_per_play*x.off_plays).sum()-(x.def_epa_per_play*x.def_plays).sum())/max(n/2,1)
        r[t]=(P0*prior.get(t,0)+ (n/2)*cur)/(P0+n/2)
    return r
def epa_margin(tr,te,wk):
    # fit S on training games using ratings as of each game's week (walk-forward inside)
    xs=[];ys=[]
    for w in sorted(tr.week.unique()):
        r=epa_r(w); q=tr[tr.week==w]
        for h,a,l,m in zip(q.home,q.away,q.location,q.margin): xs.append(r[h]-r[a]); ys.append(m-(0 if l=='Neutral' else 1.5))
    xs,ys=np.array(xs),np.array(ys); S=(xs@ys+30*20)/(xs@xs+20) if len(xs) else 30
    r=epa_r(wk); return np.array([S*(r[h]-r[a])+(0 if l=='Neutral' else 1.5) for h,a,l in zip(te.home,te.away,te.location)])
def pred3(tr,te,wk,use_epa=True,ats=True):
    rm=X(te)@ratings(tr); mm=0.5*(rm+epa_margin(tr,te,wk)) if use_epa else rm
    base=0.5*(mm+te.home_line.values)
    ef=split_eff(tr); adj=sum(np.where(te[f],ef[f],0) for f in ef)
    return base+np.where(te.dog_home,adj,-adj)+(W_ATS*ats_feat(tr,te) if ats else 0)
def run(use_epa,ats):
    r=[]
    for wk in range(2,7):
        tr,te=g[g.week<wk],g[g.week==wk]; p=pred3(tr,te,wk,use_epa,ats)
        for gid,c,pc in zip(te.game_id,te.cover,p): r.append((wk,gid,c,pc,Phi(abs(pc)/SIGMA)))
    return pd.DataFrame(r,columns=['wk','gid','cover','pc','P'])
def rec(d):
    w=((d.cover>0)==(d.pc>=0))&(d.cover!=0); p=d.cover==0
    return f'{int(w.sum())}-{int((~w&~p).sum())}'+(f'-{int(p.sum())}' if p.sum() else '')
if os.environ.get("MODE")=="backtest":
  for ue,a in [(False,True),(True,True),(True,False)]:
      d=run(ue,a); l2=d[d.wk>=5]
      top=pd.concat([d[d.wk==w].nlargest(4,'P') for w in (5,6)])
      print(('EPA' if ue else 'noEPA')+('+ATS' if a else ''),'wk2-6',rec(d),'last2',rec(l2),'top4 last2',rec(top),
            {w:rec(d[d.wk==w].nlargest(4,'P')) for w in (5,6)})
      if ue and a:
          for w in (5,6):
              t=d[d.wk==w].nlargest(4,'P').merge(g[['game_id','away','home','home_line']],left_on='gid',right_on='game_id')
              for _,x in t.iterrows():
                  s,ln=(x.home,x.home_line) if x.pc>=0 else (x.away,-x.home_line)
                  print(' ',w,s,ln,round(x.P,3),'W' if x.cover!=0 and (x.cover>0)==(x.pc>=0) else ('P' if x.cover==0 else 'L'))

if __name__=='__main__' and os.environ.get('MODE','predict')=='predict':
    # Predict upcoming games from Lines Collector's upcoming_2026.csv (this bot never fetches lines itself).
    tag=os.environ.get('TAG',''); u=prep(up); wk=int(u.week.iloc[0]); p=pred3(g,u,wk,True,True)
    u['P']=[Phi(abs(x)/SIGMA) for x in p]
    u['side']=np.where(p>=0,u.home,u.away); u['ln']=np.where(p>=0,u.home_line,-u.home_line); u['opp']=np.where(p>=0,u.away,u.home)
    o=u.sort_values('P',ascending=False)[['game_id','weekday','side','ln','opp','home_line','P']].round(3)
    o.to_csv(D+f'predictions/week{wk}_cover_probs_v3_2026{tag}.csv',index=False); print(o.to_string(index=False))
