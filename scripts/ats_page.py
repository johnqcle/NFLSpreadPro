import os as _os; ROOT=_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'')  # project folder, portable
import csv,html,datetime
R=ROOT+'reports/'
def tab(f,title,cols=None):
    rows=list(csv.DictReader(open(R+f)));cols=cols or list(rows[0].keys())
    h=f"<h2>{title}</h2><table class=s><thead><tr>"+"".join(f"<th>{html.escape(c)}</th>" for c in cols)+"</tr></thead><tbody>"
    for r in rows: h+="<tr>"+"".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in cols)+"</tr>"
    return h+"</tbody></table>"
g=list(csv.DictReader(open(R+'ats_by_game_2026.csv')))
dog=sum(r['fav_or_dog_covered']=='dog' for r in g);fav=sum(r['fav_or_dog_covered']=='fav' for r in g);p=len(g)-dog-fav
ou=list(csv.DictReader(open(R+'ou_by_game_2026.csv')));ov=sum(r['ou_result']=='over' for r in ou);un=sum(r['ou_result']=='under' for r in ou)
wk=max(int(r['week']) for r in g)
body=f"""<h1>2026 NFL ATS Dashboard</h1><p class=m>Through Week {wk} &middot; {len(g)} games &middot; source games_2026.csv (nflverse closing consensus) &middot; built {datetime.datetime.now():%b %d, %Y %I:%M %p} PT</p>
<div class=c><div><b>{dog}</b>Underdog covers</div><div><b>{fav}</b>Favorite covers</div><div><b>{p}</b>Pushes</div><div><b>{ov}-{un}</b>Over-under</div></div>
<input id=q placeholder="Filter tables (team, week...)">"""
body+=tab('ats_team_records_2026.csv','Season ATS by team')
body+=tab('ats_team_splits_2026.csv','Team splits and last-3 form')
body+=tab('ats_splits_2026.csv','League situational splits')
body+=tab('ats_by_game_2026.csv','Every game',['week','away','home','favorite','spread','away_score','home_score','cover_margin_home','ats_winner','fav_or_dog_covered'])
body+=tab('ou_by_game_2026.csv','Over/under by game')
body+=tab('upcoming_situational_2026.csv','Upcoming games: situational flags')
css="body{font:14px system-ui;margin:24px;background:#0f1419;color:#e6e6e6}h1{margin:0}.m{color:#8a96a3}.c{display:flex;gap:12px;margin:16px 0}.c div{background:#1b232c;padding:12px 18px;border-radius:8px}.c b{display:block;font-size:24px}table{border-collapse:collapse;margin-bottom:28px}th,td{padding:4px 10px;border-bottom:1px solid #2a333d;text-align:left}th{cursor:pointer;background:#1b232c;position:sticky;top:0}input{padding:6px;width:280px;background:#1b232c;color:#eee;border:1px solid #333}"
js="""document.querySelectorAll('th').forEach(th=>th.onclick=()=>{const t=th.closest('table'),i=[...th.parentNode.children].indexOf(th),b=t.tBodies[0],a=th.dataset.a=th.dataset.a!='1'?'1':'0';[...b.rows].sort((x,y)=>{let p=x.cells[i].innerText,q=y.cells[i].innerText,n=parseFloat(p)-parseFloat(q);return (isNaN(n)?p.localeCompare(q):n)*(a=='1'?1:-1)}).forEach(r=>b.appendChild(r))});
q.oninput=()=>document.querySelectorAll('tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q.value.toLowerCase())?'':'none')"""
open(R+'ats_dashboard_2026.html','w').write(f"<!doctype html><meta charset=utf-8><title>2026 NFL ATS</title><style>{css}</style>{body}<script>{js}</script>")
