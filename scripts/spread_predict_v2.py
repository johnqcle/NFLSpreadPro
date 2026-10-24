"""Spread Predictor v2 (research only). Base: ridge margin ratings (lam 25) blended 50/50 with the line.
v2 adds the 3 Cover Analyst splits as underdog-side adjustments, each estimated ONLY from earlier weeks
(ridge-shrunk mean underdog cover margin within that split vs outside it):
  div   = division game;  big = spread >= 7;  favrest = favorite has more rest than underdog."""
import os as _os; ROOT=_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'')  # project folder, portable
import numpy as np, pandas as pd, sys
from math import erf, sqrt, comb
D=ROOT; SIGMA=13.5; LAM=25; K=40   # K = shrinkage games for split effects
Phi=lambda z:0.5*(1+erf(z/sqrt(2)))
g=pd.read_csv(D+'data/games_2026.csv'); up=pd.read_csv(D+'data/upcoming_2026.csv')
teams=sorted(set(g.home)|set(g.away)|set(up.home)|set(up.away)); ix={t:i for i,t in enumerate(teams)}
def prep(df):
    df=df.copy(); df['dog_home']=df.home_line>0
    fr=np.where(df.home_line<0,df.home_rest,df.away_rest); dr=np.where(df.home_line<0,df.away_rest,df.home_rest)
    df['div']=df.div_game==1; df['big']=df.spread>=7; df['favrest']=fr>dr
    return df
FRESH=sys.argv[1] if len(sys.argv)>1 else None
if FRESH:   # override upcoming lines with a fresh nflverse pull (spread_line >0 = home favored)
    f=pd.read_csv(FRESH).set_index('game_id')
    up['old_home_line']=up.home_line
    up['home_line']=[-f.loc[i,'spread_line'] for i in up.game_id]
    up['favorite']=np.where(up.home_line<0,up.home,up.away); up['spread']=up.home_line.abs()
g=prep(g); up=prep(up)
g['margin']=g.home_score-g.away_score; g['cover']=g.margin+g.home_line
g['dogcov']=np.where(g.dog_home,g.cover,-g.cover)   # >0 underdog covered
def X(df):
    M=np.zeros((len(df),len(teams)+1))
    for k,(h,a,l) in enumerate(zip(df.home,df.away,df.location)): M[k,ix[h]]=1;M[k,ix[a]]=-1;M[k,-1]=0 if l=='Neutral' else 1
    return M
def ratings(tr):
    A=X(tr); P=np.eye(A.shape[1])*LAM; P[-1,-1]=LAM*0.1
    return np.linalg.solve(A.T@A+P,A.T@tr.margin.values)
def split_eff(tr):
    e={}
    for f in ['div','big','favrest']:
        a=tr[tr[f]].dogcov; b=tr[~tr[f]].dogcov
        e[f]=a.sum()/(len(a)+K)-b.sum()/(len(b)+K)   # shrunk difference in dog cover margin
    return e
W_ATS=6; KA=6   # user rule: always include prior ATS records. Shrunk cover rate (padded 6 games at 50%)
def ats_feat(tr,te):
    rec={}
    for t in teams:
        c=pd.concat([tr[tr.home==t].cover,-tr[tr.away==t].cover]); c=c[c!=0]
        rec[t]=((c>0).sum()+KA*0.5)/(len(c)+KA)-0.5
    return np.array([rec[h]-rec[a] for h,a in zip(te.home,te.away)])
def predict(tr,te,v2):
    base=0.5*(X(te)@ratings(tr)+te.home_line.values)    # predicted home cover margin
    if not v2: return base,{}
    e=split_eff(tr); adj=sum(np.where(te[f],e[f],0) for f in e)
    return base+np.where(te.dog_home,adj,-adj)+W_ATS*ats_feat(tr,te),e
def backtest(v2):
    r=[]
    for wk in range(2,int(g.week.max())+1):
        tr,te=g[g.week<wk],g[g.week==wk]; p,_=predict(tr,te,v2)
        for c,pc,dh in zip(te.cover,p,te.dog_home):
            if c==0: continue
            r.append((wk,(c>0)==(pc>=0),((pc>=0)==dh),(Phi(pc/SIGMA)-(c>0))**2))
    return pd.DataFrame(r,columns=['wk','win','dogpick','sq'])
for v2 in [False,True]:
    b=backtest(v2); n=len(b); w=int(b.win.sum()); k=max(w,n-w); pv=min(1,2*sum(comb(n,i) for i in range(k,n+1))/2**n)
    print('v2' if v2 else 'v1',f'{w}-{n-w} ({w/n:.1%}) brier {b.sq.mean():.4f} p={pv:.2f} dogpicks {int(b.dogpick.sum())}/{n}',
          b.groupby('wk').win.agg(lambda s:f'{s.sum()}-{len(s)-s.sum()}').to_dict())
    b3=b[b.wk>=4]; print('   weeks 4-6 only:',f'{int(b3.win.sum())}-{len(b3)-int(b3.win.sum())}')
p,e=predict(g,up,True); p1,_=predict(g,up,False)
print('split effects (pts toward dog):',{k:round(v,2) for k,v in e.items()})
up['p_home_cover']=[Phi(x/SIGMA) for x in p]; up['v1_p_home_cover']=[Phi(x/SIGMA) for x in p1]
up['lean']=np.where(up.p_home_cover>=.5,up.home,up.away); up['p_lean']=np.maximum(up.p_home_cover,1-up.p_home_cover)
up['line']=up.favorite+' -'+up.spread.astype(str)
o=up[['game_id','date','weekday','kickoff_et','away','home','line','div','big','favrest','v1_p_home_cover','p_home_cover','lean','p_lean']].round(3)
wk=int(up.week.iloc[0]); tag=sys.argv[2] if len(sys.argv)>2 else ''
if 'old_home_line' in up: o['old_home_line']=up.old_home_line
o.to_csv(D+f'predictions/week{wk}_cover_probs_v2_2026{tag}.csv',index=False)
print(o.sort_values('p_lean',ascending=False).to_string(index=False))
