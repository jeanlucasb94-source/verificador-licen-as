"""
App web local — rode com:  python app.py   (abre em http://localhost:8000)
"""
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

import connectors

app = FastAPI(title="Verificador de Licenças — EUA")


@app.get("/api/states")
def states():
    return [
        {"code": s, "name": c.state_name, "agency": c.agency,
         "auto": s in ("FL", "CA"), "verify_url": c.verify_url}
        for s, c in sorted(connectors.CONNECTORS.items())
    ]


@app.get("/api/verify")
def verify(state: str = Query(...), license: str = Query("", alias="license"),
           name: str = Query("")):
    try:
        conn = connectors.get(state)
    except KeyError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    try:
        if license:
            results = conn.verify_by_number(license)
        elif name:
            results = conn.search_by_name(name)
        else:
            return JSONResponse({"error": "Informe license ou name"}, status_code=400)
    except NotImplementedError as e:
        return JSONResponse({"error": str(e),
                             "manual_url": conn.manual_link(license or name)},
                            status_code=501)
    except Exception as e:
        return JSONResponse({"error": f"Falha ao consultar {conn.state_name}: {e}",
                             "manual_url": conn.manual_link(license or name)},
                            status_code=502)
    return {"results": [r.to_dict() for r in results],
            "manual_url": conn.manual_link(license or name)}


PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verificador de Licenças — EUA</title>
<style>
  :root{
    --paper:#f7f5ef; --ink:#1c2430; --line:#d8d2c4;
    --seal-ok:#1e6f43; --seal-bad:#9b2c2c; --seal-warn:#8a6d1d;
    --accent:#28527a;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);
       font:16px/1.55 Georgia,'Times New Roman',serif}
  .wrap{max-width:780px;margin:0 auto;padding:48px 20px 80px}
  header{border-bottom:3px double var(--ink);padding-bottom:18px;margin-bottom:28px}
  header h1{font-size:1.7rem;margin:0;letter-spacing:.5px}
  header p{margin:6px 0 0;color:#5a6372;font-size:.95rem}
  form{display:grid;grid-template-columns:120px 1fr 1fr auto;gap:10px;align-items:end}
  label{display:block;font-family:ui-monospace,Consolas,monospace;
        font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;
        color:#5a6372;margin-bottom:4px}
  select,input{width:100%;padding:10px 12px;border:1px solid var(--line);
        border-radius:4px;background:#fff;font:inherit}
  input{font-family:ui-monospace,Consolas,monospace}
  button{padding:11px 22px;border:none;border-radius:4px;background:var(--ink);
        color:var(--paper);font:inherit;cursor:pointer}
  button:hover{background:var(--accent)}
  button:focus-visible,input:focus-visible,select:focus-visible{
        outline:2px solid var(--accent);outline-offset:2px}
  .hint{margin-top:10px;font-size:.85rem;color:#5a6372}
  .card{position:relative;background:#fff;border:1px solid var(--line);
        border-radius:6px;padding:22px 24px;margin-top:22px;
        box-shadow:0 1px 3px rgba(28,36,48,.07)}
  .seal{position:absolute;top:16px;right:18px;
        font-family:ui-monospace,Consolas,monospace;font-weight:700;
        font-size:.8rem;letter-spacing:.18em;text-transform:uppercase;
        padding:6px 12px;border:2px solid currentColor;border-radius:4px;
        transform:rotate(-6deg)}
  .ok{color:var(--seal-ok)} .bad{color:var(--seal-bad)} .warn{color:var(--seal-warn)}
  .num{font-family:ui-monospace,Consolas,monospace;font-size:1.15rem;font-weight:700}
  dl{display:grid;grid-template-columns:130px 1fr;gap:4px 14px;margin:14px 0 0}
  dt{font-family:ui-monospace,Consolas,monospace;font-size:.72rem;
     text-transform:uppercase;letter-spacing:.12em;color:#5a6372;padding-top:3px}
  dd{margin:0}
  a{color:var(--accent)}
  .empty,.error{margin-top:22px;padding:18px 20px;border:1px dashed var(--line);
        border-radius:6px;color:#5a6372}
  .error{border-color:var(--seal-bad);color:var(--seal-bad)}
  .loading{margin-top:22px;color:#5a6372;font-style:italic}
  @media(max-width:680px){form{grid-template-columns:1fr 1fr}
    form button{grid-column:1/-1}}
  @media(prefers-reduced-motion:no-preference){
    .card{animation:in .25s ease-out}
    @keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1}}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Verificador de Licenças Profissionais</h1>
    <p>Contractors &middot; órgãos estaduais oficiais dos EUA</p>
  </header>

  <form id="f">
    <div>
      <label for="st">Estado</label>
      <select id="st"></select>
    </div>
    <div>
      <label for="lic">Nº da licença</label>
      <input id="lic" placeholder="ex.: CGC1234567" autocomplete="off">
    </div>
    <div>
      <label for="nm">ou nome</label>
      <input id="nm" placeholder="ex.: SILVA CONSTRUCTION" autocomplete="off">
    </div>
    <button type="submit">Verificar</button>
  </form>
  <p class="hint" id="hint"></p>

  <div id="out"></div>
</div>

<script>
const f=document.getElementById('f'),out=document.getElementById('out'),
      st=document.getElementById('st'),hint=document.getElementById('hint');
let states=[];

fetch('/api/states').then(r=>r.json()).then(d=>{
  states=d;
  st.innerHTML=d.map(s=>`<option value="${s.code}">${s.code} — ${s.name}${s.auto?'':' (link oficial)'}</option>`).join('');
  upd();
});
st.addEventListener('change',upd);
function upd(){
  const s=states.find(x=>x.code===st.value);
  if(s) hint.textContent=s.agency+(s.auto?' — consulta automática':' — abre o portal oficial de verificação');
}

f.addEventListener('submit',async e=>{
  e.preventDefault();
  const lic=document.getElementById('lic').value.trim(),
        nm=document.getElementById('nm').value.trim();
  if(!lic&&!nm){out.innerHTML='<div class="error">Informe o número da licença ou o nome.</div>';return;}
  out.innerHTML='<div class="loading">Consultando '+st.value+'…</div>';
  const p=new URLSearchParams({state:st.value});
  if(lic)p.set('license',lic);else p.set('name',nm);
  let d;
  try{
    const r=await fetch('/api/verify?'+p);
    d=await r.json();
    if(!r.ok){
      out.innerHTML='<div class="error">'+esc(d.error||'Erro')+
        (d.manual_url?'<br><a href="'+d.manual_url+'" target="_blank" rel="noopener">Verificar manualmente no portal oficial →</a>':'')+'</div>';
      return;
    }
  }catch(err){out.innerHTML='<div class="error">Falha de conexão: '+esc(String(err))+'</div>';return;}
  if(!d.results.length){
    out.innerHTML='<div class="empty">Nenhum registro encontrado. '+
      '<a href="'+d.manual_url+'" target="_blank" rel="noopener">Confirme no portal oficial →</a></div>';
    return;
  }
  out.innerHTML=d.results.map(card).join('');
});

function card(r){
  const cls=r.is_valid===true?'ok':r.is_valid===false?'bad':'warn';
  const txt=r.is_valid===true?'Válida':r.is_valid===false?'Não válida':'Conferir';
  const src=/^https?:/.test(r.source)?'<a href="'+r.source+'" target="_blank" rel="noopener">'+esc(r.source)+'</a>':esc(r.source);
  return `<div class="card">
    <span class="seal ${cls}">${txt}</span>
    <div class="num">${esc(r.state)} · ${esc(r.license_number||'—')}</div>
    <dl>
      ${row('Titular',r.holder_name)}
      ${row('Tipo',r.license_type)}
      ${row('Status',r.raw_status)}
      ${row('Expira em',r.expires)}
      ${row('Endereço',r.address)}
      <dt>Fonte</dt><dd>${src}</dd>
      ${row('Nota',r.extra&&r.extra.note)}
      ${row('Consultado',r.checked_at&&r.checked_at.replace('T',' '))}
    </dl>
  </div>`;
}
function row(k,v){return v?`<dt>${k}</dt><dd>${esc(v)}</dd>`:'';}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE


if __name__ == "__main__":
    import os
    import threading
    import webbrowser

    port = int(os.environ.get("PORT", "8000"))
    if "RENDER" not in os.environ and "PORT" not in os.environ:
        # uso local: abre o navegador sozinho
        threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        # nuvem (Render etc.): escuta em todas as interfaces
        uvicorn.run(app, host="0.0.0.0", port=port)
