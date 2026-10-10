"""Integration and privacy regressions for enhanced rules; Classic remains unchanged."""
import json
import pytest
from fastapi.testclient import TestClient
from server import engine, enhancements as ex
from server.content import CASE_MAP
from server import app as service


def new_room():
 s,p=engine.make_room('ABCDE','Adler')
 q=engine.join(s,'Marlowe')
 ex.configure(s,p['id'],True)
 return s,p,q


def start_room(s,p,q):
 engine.start(s,p['id'])
 return [p,q]


def scene_round(s,p,q,index):
 engine.next_scene(s,p['id'])
 question=ex.challenge(s)
 assert s['phase']=='WATCHING' and index==s['scene']
 ex.observe(s,p['id'],question['answer'])
 engine.close_scene(s,p['id'])
 engine.reveal_fact(s,p['id'],0)
 engine.reveal_fact(s,q['id'],0)
 if s['phase']=='DECISION':
  ex.vote(s,p['id'],'archives')
  ex.vote(s,q['id'],'surveillance')
 assert s['phase']=='TURN'


def finish_actions(s):
 for _ in range(5):
  if s['phase']!='TURN':break
  actor=engine.active(s)
  acts=[c for c in actor['hand'] if c.startswith('A:')]
  if acts:
   card=s.get('drawn_action') or acts[0]
   target=next(x for x in s['players'] if x['id']!=actor['id'])
   own=engine.eligible_cards(actor)
   engine.play(s,actor['id'],card,target=target['id'],own_card=own[0] if own else None)
  elif s['deck'] or s['discard']:
   engine.draw(s,actor['id'])
  else:engine.pass_turn(s,actor['id'])
  if s.get('pending'):
   pend=s['pending'];target=engine.player(s,pend['target'])
   if pend['kind']=='identity':engine.respond(s,target['id'],fact_index=0)
   else:engine.respond(s,target['id'],card_id=engine.eligible_cards(target)[0])


def test_scene_observations_are_once_only_scored_and_private():
 s,p,q=new_room();start_room(s,p,q)
 engine.next_scene(s,p['id'])
 ch=ex.challenge(s)
 assert len(ch['options'])==4
 assert ch['answer'] in ch['options']
 wrong=next(x for x in ch['options'] if x!=ch['answer'])
 ex.observe(s,p['id'],ch['answer'])
 ex.observe(s,q['id'],wrong)
 assert p['score']>=12 and q['score']==0
 with pytest.raises(ValueError):ex.observe(s,p['id'],ch['answer'])
 own=engine.view(s,p['id'])
 rival=engine.view(s,q['id'])
 public=engine.public_view(s)
 assert own['my_observation']['correct'] is True
 assert rival['my_observation']['correct'] is False
 assert 'my_observation' not in public
 assert 'answer' not in own['scene_challenge']
 assert 'answer' not in json.dumps(public)
 assert 'token' not in json.dumps(public)


def test_majority_vote_reveals_evidence_and_keeps_ballots_secret():
 s,p,q=new_room();start_room(s,p,q)
 for index in range(2):
  engine.next_scene(s,p['id']);engine.close_scene(s,p['id'])
  engine.reveal_fact(s,p['id'],0);engine.reveal_fact(s,q['id'],0)
  if index==0:finish_actions(s)
 assert s['phase']=='DECISION'
 assert ex.vote(s,p['id'],'archives') is None
 assert engine.view(s,p['id'])['my_vote']=='archives'
 assert engine.view(s,q['id'])['my_vote'] is None
 assert 'ballot' not in engine.public_view(s) and 'my_vote' not in engine.public_view(s)
 with pytest.raises(ValueError):ex.vote(s,p['id'],'archives')
 before=len(s['public_clues'])
 outcome=ex.vote(s,q['id'],'surveillance')
 assert outcome['choice']=='archives'  # tie broken by host
 assert outcome['leads']==2
 assert s['phase']=='TURN'
 assert len(s['public_clues'])==before+2
 assert s['ballot_outcomes'][0]['counts']=={'archives':1,'surveillance':1}


def test_specialty_selection_locks_after_game_starts():
 s,p,q=new_room()
 ex.talent_select(s,p['id'],'interrogator')
 ex.talent_select(s,q['id'],'analyst')
 start_room(s,p,q)
 with pytest.raises(ValueError):ex.talent_select(s,p['id'],'observer')
 engine.next_scene(s,p['id']);engine.close_scene(s,p['id'])
 ex.use_talent(s,p['id'],target=q['id'])
 assert p['private_leads'][0]['source'].startswith('Interrogation of')
 assert 'private_leads' not in engine.view(s,q['id'])['private']
 assert engine.view(s,q['id'])['private_leads']==[]
 with pytest.raises(ValueError):ex.use_talent(s,p['id'],target=q['id'])
 ex.use_talent(s,q['id'],dimension='room',murder=0)
 assert 'eliminate' in q['private_leads'][0]['text']


def test_observer_archivist_hints_and_guardrails():
 s,p,q=new_room();ex.talent_select(s,q['id'],'archivist');start_room(s,p,q)
 engine.next_scene(s,p['id']);engine.close_scene(s,p['id'])
 ex.use_talent(s,p['id'])
 assert len(p['private_leads'])==1
 original=len(q['hand'])
 ex.use_talent(s,q['id'])
 assert len(q['hand'])==original+1
 ex.request_hint(s,p['id'],'weapon',0)
 assert p['hint_count']==1
 with pytest.raises(ValueError):ex.request_hint(s,p['id'],'weapon',0)
 ex.request_hint(s,p['id'],'room',0)
 with pytest.raises(ValueError):ex.request_hint(s,p['id'],'murderer',0)
 assert p['score']==6-16
 assert all('answer' not in x for x in p['private_leads'])


def test_all_eighteen_cases_win_with_branching_mode():
 for case_id,case in CASE_MAP.items():
  s,p,q=new_room();engine.case_select(s,p['id'],case_id);start_room(s,p,q)
  for i in range(5):
   scene_round(s,p,q,i)
   finish_actions(s)
  assert s['scene']==4 and s['phase']=='TURN'
  assert len(s['ballot_outcomes'])==2
  assert set(x['kind'] for x in case['clues'] if x['kind']!='exclusion')=={'murderer','victim','room','weapon'}
  actor=engine.active(s)
  identities={x['id']:x['identity'] for x in s['players'] if x['id']!=actor['id']}
  verdict=engine.accuse(s,actor['id'],case['murders'],identities)
  assert verdict['won'] is True
  result=engine.view(s,p['id'])
  assert result['phase']=='ENDED' and result['scoreboard'] is not None
  assert result['enhanced'] and any(x['score']>=50 for x in result['scoreboard'])


def test_full_http_directors_cut_and_private_projections(tmp_path):
 service.DB_PATH=tmp_path/'enhanced.sqlite3'
 client=TestClient(service.app)
 p=client.post('/api/rooms',json={'name':'Host','enhanced':True}).json()
 q=client.post('/api/join',json={'code':p['code'],'name':'Guest'}).json()
 url='/api/rooms/'+p['code']
 def call(who,action,**data):
  rsp=client.post(url+'/command',headers={'x-player-token':who['token']},json={'type':action,'data':data})
  assert rsp.status_code==200,(action,rsp.text)
  return rsp.json()
 call(q,'talent_select',talent='interrogator')
 call(p,'select',case_id='will-1')
 call(p,'start')
 snap=call(p,'next_scene')
 assert snap['scene_challenge']['options']
 question=ex.challenge(service.get_room(p['code']))
 snap=call(p,'observe',choice=question['answer'])
 assert snap['my_observation']['correct']
 public=client.get(url+'/public').json()
 assert 'scene_challenge' not in public and 'private_leads' not in public and 'private' not in public
 assert 'solution' not in public
 assert 'token' not in json.dumps(public)
 call(p,'close_scene')
 call(q,'talent',target=p['player_id'])
 host_view=client.get(url,headers={'x-player-token':p['token']}).json()
 guest_view=client.get(url,headers={'x-player-token':q['token']}).json()
 assert guest_view['private_leads']
 assert host_view['private_leads']==[]


def test_classic_unchanged_and_mode_permissions():
 s,p=engine.make_room('ABCDE','Ada');q=engine.join(s,'Byron')
 assert not s.get('enhanced')
 with pytest.raises(ValueError):ex.configure(s,q['id'],True)
 engine.start(s,p['id'])
 assert not engine.view(s,p['id'])['enhanced']
 with pytest.raises(ValueError):ex.observe(s,p['id'],'x')
 engine.next_scene(s,p['id']);engine.close_scene(s,p['id'])
 engine.reveal_fact(s,p['id'],0);engine.reveal_fact(s,q['id'],0)
 assert s['phase']=='TURN'
