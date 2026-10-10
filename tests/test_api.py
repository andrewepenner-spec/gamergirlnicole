import json
from fastapi.testclient import TestClient
from server import app as service


def setup(tmp_path):
 service.DB_PATH=tmp_path/'test.db'
 return TestClient(service.app)

def test_catalog_and_health(tmp_path):
 client=setup(tmp_path)
 r=client.get('/api/catalog')
 assert r.status_code==200
 catalog=r.json()
 assert len(catalog['cases'])==18
 assert len(catalog['chapters'])==3
 assert all('murders' not in c and 'clues' not in c for c in catalog['cases'])
 assert client.get('/api/health').json()['status']=='ok'
 assert client.get('/').status_code==200
 assert client.get('/main.js').status_code==200
 assert client.get('/styles.css').status_code==200
 assert client.get('/assets/scene-0.webp').status_code==200


def test_room_join_permissions_and_private_views(tmp_path):
 client=setup(tmp_path)
 host=client.post('/api/rooms',json={'name':'Ada'}).json()
 code=host['code']
 guest=client.post('/api/join',json={'name':'Byron','code':code}).json()
 a={'x-player-token':host['token']}
 b={'x-player-token':guest['token']}
 assert client.get(f'/api/rooms/{code}').status_code==401
 assert client.get(f'/api/rooms/{code}',headers={'x-player-token':'invalid'}).status_code==401
 assert client.get(f'/api/rooms/{code}',headers=a).json()['phase']=='LOBBY'
 assert client.post(f'/api/rooms/{code}/command',headers=b,json={'type':'select','data':{'case_id':'secrets-6'}}).status_code==400
 assert client.post(f'/api/rooms/{code}/command',headers=a,json={'type':'select','data':{'case_id':'secrets-6'}}).status_code==200
 assert client.post(f'/api/rooms/{code}/command',headers=a,json={'type':'start','data':{}}).status_code==200
 hostview=client.get(f'/api/rooms/{code}',headers=a).json()
 guestview=client.get(f'/api/rooms/{code}',headers=b).json()
 assert hostview['private']['identity']!=guestview['private']['identity']
 assert 'solution' not in hostview and 'identities' not in guestview
 assert 'token' not in json.dumps(hostview)
 assert 'murders' not in hostview['case']
 assert len(hostview['private']['hand'])==5
 assert client.post(f'/api/rooms/{code}/command',headers=b,json={'type':'next_scene','data':{}}).status_code==400
 assert client.post(f'/api/rooms/{code}/command',headers=a,json={'type':'next_scene','data':{}}).json()['phase']=='WATCHING'
 assert client.post(f'/api/rooms/{code}/command',headers=a,json={'type':'close_scene','data':{}}).json()['phase']=='DISCLOSURE'
 assert client.post(f'/api/rooms/{code}/command',headers=a,json={'type':'reveal_fact','data':{'index':0}}).status_code==200
 result=client.post(f'/api/rooms/{code}/command',headers=b,json={'type':'reveal_fact','data':{'index':0}})
 assert result.status_code==200 and result.json()['phase']=='TURN'
 assert result.json()['turn_player']==host['player_id']


def test_valid_note_saves_private_only(tmp_path):
 client=setup(tmp_path)
 host=client.post('/api/rooms',json={'name':'Ada'}).json()
 guest=client.post('/api/join',json={'code':host['code'],'name':'Byron'}).json()
 h={'x-player-token':host['token']};g={'x-player-token':guest['token']};url=f'/api/rooms/{host["code"]}'
 assert client.post(url+'/command',headers=h,json={'type':'save','data':{'notes':{'free':'SECRET PRIVATE NOTE'}}}).status_code==200
 assert client.get(url,headers=h).json()['private']['notes']['free']=='SECRET PRIVATE NOTE'
 assert 'SECRET PRIVATE NOTE' not in json.dumps(client.get(url,headers=g).json())


def test_http_two_player_complete_game_with_final_solution(tmp_path):
 from server.content import CASE_MAP
 client=setup(tmp_path)
 host=client.post('/api/rooms',json={'name':'Ada'}).json()
 guest=client.post('/api/join',json={'code':host['code'],'name':'Byron'}).json()
 users={host['player_id']:host,guest['player_id']:guest}
 url=f'/api/rooms/{host["code"]}'
 def run(user,type,**data):
  rsp=client.post(url+'/command',headers={'x-player-token':user['token']},json={'type':type,'data':data})
  assert rsp.status_code==200,(type,data,rsp.text)
  return rsp.json()
 def get(user):return client.get(url,headers={'x-player-token':user['token']}).json()
 run(host,'select',case_id='search-5')
 run(host,'start')
 for scene_idx in range(5):
  run(host,'next_scene')
  state=run(host,'close_scene')
  assert state['scene']['index']==scene_idx
  for user in [host,guest]: run(user,'reveal_fact',index=0)
  r=get(host);current_round=r['round']
  for _ in range(10):
   if r['phase']!='TURN' or r['round']>current_round:break
   seat=users[r['turn_player']]
   snapshot=get(seat)
   options=[card for card in snapshot['private']['hand'] if card['type']=='action']
   if options:
    choice=next((x for x in options if x['id']==snapshot['drawn_action']),options[0])
    other=guest if seat is host else host
    owns=[x for x in snapshot['private']['hand'] if x['type']!='action']
    r=run(seat,'play',card=choice['id'],target=other['player_id'],own_card=owns[0]['id'] if owns else None)
   else:r=run(seat,'draw')
   if r['pending']:
    target=users[r['pending']['target']]
    if r['pending']['kind']=='identity':r=run(target,'respond',index=0)
    else:
     t=get(target); eligible=[x for x in t['private']['hand'] if x['type']!='action']
     assert eligible
     r=run(target,'respond',card=eligible[0]['id'])
  assert r['phase']=='READY' if scene_idx<4 else r['phase']=='TURN'
 # Simulate a detective who has independently inferred every clue correctly.
 actor=users[r['turn_player']]
 guesses={other['player_id']:get(other)['private']['identity'] for other in [host,guest] if other is not actor}
 solution=CASE_MAP['search-5']['murders']
 finished=run(actor,'accuse',murders=solution,identities=guesses)
 assert finished['phase']=='ENDED' and finished['champion']==actor['player_id']
 assert len(finished['solution'])==4


def test_public_theater_contains_no_secret_identity_or_hand(tmp_path):
 client=setup(tmp_path)
 host=client.post('/api/rooms',json={'name':'Ada'}).json()
 guest=client.post('/api/join',json={'code':host['code'],'name':'Byron'}).json()
 url=f'/api/rooms/{host["code"]}'
 a={'x-player-token':host['token']}
 client.post(url+'/command',headers=a,json={'type':'start','data':{}})
 private=client.get(url,headers=a).json()
 public=client.get(url+'/public').json()
 assert public['phase']=='IDENTITY'
 assert 'private' not in public and 'identities' not in public and 'solution' not in public
 assert 'token' not in json.dumps(public)
 assert 'hand' not in public and all('hand' not in x for x in public['roster'])
 assert private['private']['identity'] not in json.dumps(public)
 assert client.get('/theater?code='+host['code']).status_code==200
 assert client.get('/theater.js').status_code==200
