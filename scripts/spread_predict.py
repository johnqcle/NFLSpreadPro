"""Spread Predictor: walk-forward cover-probability model (research only).
Model: ridge ratings fitted to each game's result vs the closing line (cover margin
from the home side), with a home term. Predicted cover margin for home = r_home - r_away + h
(neutral: no h). P(home covers) = Phi(pred / SIGMA). Ratings shrunk by LAMBDA.
Also reports a ridge model on raw margins blended with the line, for comparison."""
import os as _os; ROOT=_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'')  # project folder, portable
import numpy as np, pandas as pd
from math import erf, sqrt
D=ROOT
g=pd.read_csv(D+'data/games_2026.csv'); up=pd.read_csv(D+'data/upcoming_2026.csv')
teams=sorted(set(g.home)|set(g.away)|set(up.home)|set(up.away)); ix={t:i for i,t in enumerate(teams)}
SIGMA=13.5
Phi=lambda z:0.5*(1+erf(z/sqrt(2)))
g['margin']=g.home_score-g.away_score
g['cover']=g.margin+g.home_line   # >0 home covers
def X(df):
    M=np.zeros((len(df),len(teams)+1))
    for k,(h,a,l) in enumerate(zip(df.home,df.away,df.location)):
        M[k,ix[h]]=1;M[k,ix[a]]=-1;M[k,-1]=0 if l=='Neutral' else 1
    return M
def fit(df,y,lam):
    A=X(df); P=np.eye(A.shape[1])*lam; P[-1,-1]=lam*0.1
    return np.linalg.solve(A.T@A+P,A.T@y)
def pred_cover(train,test,lam,mode):
    if mode=='ats': w=fit(train,train.cover.values,lam); return X(test)@w
    if mode=='margin':  # rating margin minus line, shrunk 50% toward market
        w=fit(train,train.margin.values,lam); return 0.5*(X(test)@w+test.home_line.values)
    if mode=='home': return np.full(len(test),train.cover.mean())
def backtest(lam,mode):
    rows=[]
    for wk in sorted(g.week.unique())[1:]:
        tr,te=g[g.week<wk],g[g.week==wk]
        p=pred_cover(tr,te,lam,mode)
        for (_,r),pc in zip(te.iterrows(),p):
            ph=Phi(pc/SIGMA); 
            if r.cover==0: continue
            pick_home=ph>=0.5; win=(r.cover>0)==pick_home
            rows.append(dict(game_id=r.game_id,week=wk,p_home=ph,pick='home' if pick_home else 'away',win=win,home_cov=int(r.cover>0)))
    return pd.DataFrame(rows)
res={}
for mode in ['ats','margin','home']:
    for lam in ([1,4,10,25] if mode!='home' else [0]):
        b=backtest(lam,mode); n=len(b); w=b.win.sum()
        brier=((b.p_home-b.home_cov)**2).mean()
        res[(mode,lam)]=b
        from math import comb
        k=max(w,n-w); pv=min(1,2*sum(comb(n,i) for i in range(k,n+1))/2**n)
        print(f'{mode:6} lam={lam:<3} {w}-{n-w} ({w/n:.1%}) brier={brier:.4f} (coinflip .2500) p_vs_50={pv:.2f}  by week:',
              b.groupby('week').win.agg(lambda s:f'{s.sum()}-{len(s)-s.sum()}').to_dict())

# ---- Week 5 forecast: margin model, lam=25 (best Brier in backtest) trained on all completed games
LAM=25
w=fit(g,g.margin.values,LAM)
up['model_home_margin']=X(up)@w
up['pred_cover_home']=0.5*(up.model_home_margin+up.home_line)
up['p_home_cover']=[Phi(c/SIGMA) for c in up.pred_cover_home]
up['lean']=np.where(up.p_home_cover>=0.5,up.home,up.away)
up['p_lean']=np.maximum(up.p_home_cover,1-up.p_home_cover)
up['line']=up.favorite+' -'+up.spread.astype(str)
out=up[['game_id','date','away','home','line','home_line','model_home_margin','p_home_cover','lean','p_lean']].round(3)
out.to_csv(D+'predictions/week5_cover_probs_2026.csv',index=False)
bt=res[('margin',LAM)]; bt.to_csv(D+'predictions/backtest_margin_lam25.csv',index=False)
print(out.sort_values('p_lean',ascending=False).to_string(index=False))
print('HFA',round(w[-1],2)); print(pd.Series(w[:-1],teams).sort_values().round(1).to_string())
