"""HTTP + WebSocket multiplayer service backed by SQLite.
Run: python run.py  (defaults to http://127.0.0.1:8000)
"""
from pathlib import Path
from typing import Optional
import os, sqlite3, json, threading, secrets, asyncio
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import engine, enhancements as extra
from .content import public_catalog

ROOT=Path(__file__).resolve().parents[1]
DB_PATH=Path(os.environ.get('MYSTERY_DB',str(ROOT/'game.sqlite3')))
LOCK=threading.RLock()

def conn():
 DB_PATH.parent.mkdir(parents=True, exist_ok=True)
 connection=sqlite3.connect(DB_PATH,timeout=20)
 connection.execute('PRAGMA journal_mode=WAL')
 connection.execute('CREATE TABLE IF NOT EXISTS rooms (code TEXT PRIMARY KEY, state TEXT NOT NULL)')
 return connection

def get_room(code):
 with conn() as db:
  row=db.execute('SELECT state FROM rooms WHERE code=?',(code.upper(),)).fetchone()
 if not row:raise HTTPException(404,'No room exists with that code.')
 return json.loads(row[0])

def authenticated(s,token):
 p=next((x for x in s['players'] if token and secrets.compare_digest(x['token'],token) for _ in [0]),None)
 if p is None:raise HTTPException(401,'Invalid or missing player token.')
 return p

class CreateBody(BaseModel):
 name:str=Field(min_length=1,max_length=28)
 enhanced:bool=False
class JoinBody(BaseModel):
 code:str=Field(min_length=4,max_length=7)
 name:str=Field(min_length=1,max_length=28)
class CommandBody(BaseModel):
 type:str
 data:dict=Field(default_factory=dict)

app=FastAPI(title='Mystery Tapes: a playable video deduction game', docs_url='/api/docs')
clients={}

@app.get('/api/health')
def health():return {'status':'ok','engine':'mystery-tapes','database':DB_PATH.name}

@app.get('/api/catalog')
def catalog():return public_catalog()

@app.post('/api/rooms')
def create_room(body:CreateBody):
 with LOCK:
  for _ in range(30):
   code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(5))
   with conn() as db:
    if db.execute('SELECT 1 FROM rooms WHERE code=?',(code,)).fetchone():continue
    s,p=engine.make_room(code,body.name)
    s['enhanced']=body.enhanced
    db.execute('INSERT INTO rooms(code,state) VALUES (?,?)',(code,json.dumps(s)))
    return {'code':code,'player_id':p['id'],'token':p['token']}
 raise HTTPException(503,'Could not allocate a new room code.')

@app.post('/api/join')
def join(body:JoinBody):
 code=body.code.strip().upper()
 with LOCK:
  s=get_room(code)
  try:p=engine.join(s,body.name)
  except engine.GameError as exc:raise HTTPException(409,str(exc))
  s['revision']+=1
  with conn() as db:db.execute('UPDATE rooms SET state=? WHERE code=?',(json.dumps(s),code))
  return {'code':code,'player_id':p['id'],'token':p['token']}

@app.get('/api/rooms/{code}/public')
def public_room(code:str):
 return engine.public_view(get_room(code))

@app.get('/api/rooms/{code}')
def room(code:str,x_player_token:Optional[str]=Header(default=None)):
 s=get_room(code)
 p=authenticated(s,x_player_token)
 return engine.view(s,p['id'])

@app.post('/api/rooms/{code}/command')
async def command(code:str,body:CommandBody,x_player_token:Optional[str]=Header(default=None)):
 with LOCK:
  s=get_room(code)
  p=authenticated(s,x_player_token)
  pid=p['id'];d=body.data;t=body.type
  try:
   if t=='configure':extra.configure(s,pid,d.get('enhanced'))
   elif t=='talent_select':extra.talent_select(s,pid,d.get('talent'))
   elif t=='observe':extra.observe(s,pid,d.get('choice'))
   elif t=='vote':extra.vote(s,pid,d.get('choice'))
   elif t=='talent':extra.use_talent(s,pid,d.get('target'),d.get('dimension'),d.get('murder',0))
   elif t=='hint':extra.request_hint(s,pid,d.get('dimension'),d.get('murder',0))
   elif t=='select':engine.case_select(s,pid,d.get('case_id'))
   elif t=='start':engine.start(s,pid)
   elif t=='next_scene':engine.next_scene(s,pid)
   elif t=='close_scene':engine.close_scene(s,pid)
   elif t=='reveal_fact':engine.reveal_fact(s,pid,int(d.get('index',-1)))
   elif t=='draw':engine.draw(s,pid)
   elif t=='pass_turn':engine.pass_turn(s,pid)
   elif t=='play':engine.play(s,pid,d.get('card'),d.get('target'),d.get('own_card'))
   elif t=='respond':engine.respond(s,pid,d.get('card'),d.get('index'))
   elif t=='accuse':engine.accuse(s,pid,d.get('murders',[]),d.get('identities',{}))
   elif t=='pass':engine.pass_challenge(s,pid)
   elif t=='save':engine.save_notes(s,pid,d.get('notes'),d.get('marks'))
   else:raise engine.GameError('Unsupported command.')
  except (engine.GameError,TypeError,ValueError) as exc:raise HTTPException(400,str(exc))
  s['revision']+=1
  with conn() as db:db.execute('UPDATE rooms SET state=? WHERE code=?',(json.dumps(s),s['code']))
  revision=s['revision']
 # Only push a public revision. Browser must separately authenticate for private state.
 dead=[]
 for ws in list(clients.get(s['code'],set())):
  try:await ws.send_json({'revision':revision})
  except Exception:dead.append(ws)
 for ws in dead:clients.get(s['code'],set()).discard(ws)
 return engine.view(s,pid)

@app.websocket('/api/ws/{code}')
async def websocket(ws:WebSocket,code:str,token:str=''):
 try:
  s=get_room(code);authenticated(s,token)
 except HTTPException:
  await ws.close(code=4401);return
 await ws.accept()
 code=code.upper();clients.setdefault(code,set()).add(ws)
 try:
  while True:await ws.receive_text()
 except WebSocketDisconnect:pass
 finally:clients.get(code,set()).discard(ws)

web=ROOT/'web'
app.mount('/assets',StaticFiles(directory=web/'assets'),name='assets')
@app.get('/')
def index():return FileResponse(web/'index.html')
@app.get('/theater')
def theater():return FileResponse(web/'theater.html')
@app.get('/theater.js')
def theater_script():return FileResponse(web/'theater.js',media_type='text/javascript')
@app.get('/styles.css')
def styles():return FileResponse(web/'styles.css',media_type='text/css')
@app.get('/main.js')
def script():return FileResponse(web/'main.js',media_type='text/javascript')
