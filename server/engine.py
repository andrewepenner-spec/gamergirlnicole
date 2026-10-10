"""Deterministic, privacy-preserving game state machine.
All solution checks occur on the server; view() is a deliberately restricted projection.
"""
import random, secrets, time
from .content import CASE_MAP, PEOPLE, PEOPLE_MAP, ACTIONS, ACTION_MAP, all_card_ids, scene_info, case_clue_fact
from . import enhancements as extra

class GameError(ValueError): pass

def ensure(condition, message):
 if not condition: raise GameError(message)

def log(s,message,type='info'):
 s['events'].append({'at':int(time.time()), 'text':message,'type':type})
 s['events']=s['events'][-80:]

def make_room(code, username):
 pid=secrets.token_hex(5); token=secrets.token_urlsafe(28)
 p={'id':pid,'token':token,'name':username[:28].strip() or 'Detective','identity':None,'ready':True,'hand':[],'notes':{},'marks':{},'revelations':[], 'eliminated':False,'accused':False, 'talent':'observer'}
 s={'code':code,'phase':'LOBBY','host':pid,'case_id':'will-1','players':[p],'deck':[],'discard':[],'buried':[],
    'public_clues':[],'scene':-1,'scene_started':None,'turn_index':0,'acted':[],'round':0,'pending':None,
    'drawn_action':None,'champion':None,'candidate':None,'challengers':[],'challenge_index':0,'replay':None,'events':[], 'revision':1,'enhanced':False}
 log(s,f'{p["name"]} opened the investigation room.')
 return s,p

def join(s,username):
 ensure(s['phase']=='LOBBY','This investigation has already started.')
 ensure(len(s['players'])<6,'Room is full (6 players).')
 pid=secrets.token_hex(5); token=secrets.token_urlsafe(28)
 p={'id':pid,'token':token,'name':username[:28].strip() or 'Detective','identity':None,'ready':True,'hand':[],'notes':{},'marks':{},'revelations':[],'eliminated':False,'accused':False,'talent':'observer'}
 s['players'].append(p)
 log(s,f'{p["name"]} joined the game.')
 return p

def player(s,pid):
 return next((p for p in s['players'] if p['id']==pid),None)

def active(s):
 if s['phase']=='CHALLENGE':
  if s['challenge_index']>=len(s['challengers']): return None
  return player(s,s['challengers'][s['challenge_index']])
 return s['players'][s['turn_index']%len(s['players'])]

def is_my_turn(s,pid): return active(s) is not None and active(s)['id']==pid

def case_select(s,pid,case_id):
 ensure(pid==s['host'],'Only the host can choose a case.')
 ensure(s['phase']=='LOBBY','Case selection is only available in the lobby.')
 ensure(case_id in CASE_MAP,'Unknown case.')
 s['case_id']=case_id
 log(s,'The host selected '+CASE_MAP[case_id]['title']+'.')

def start(s,pid):
 ensure(pid==s['host'],'Only the host can start.')
 ensure(s['phase']=='LOBBY','Game already started.')
 ensure(2<=len(s['players'])<=6,'You need 2–6 players to begin.')
 c=CASE_MAP[s['case_id']]
 rng=random.SystemRandom()
 ids=[p['id'] for p in PEOPLE]; rng.shuffle(ids)
 unused=[]
 for i,p in enumerate(s['players']):
  p['identity']=ids[i]; p['hand']=[];p['eliminated']=False;p['accused']=False;p['revelations']=[];p['notes']={};p['marks']={}
 unused=ids[len(s['players']):]
 deck=['C:'+x for x in all_card_ids(c['chapter'])]
 for j in range(18): deck.append(f'A:{ACTIONS[j%len(ACTIONS)]["id"]}:{j}')
 deck+=['I:'+k for k in unused]
 rng.shuffle(deck)
 for _ in range(5):
  for p in s['players']:
   p['hand'].append(deck.pop())
 s['deck']=deck;s['discard']=[];s['buried']=[];s['public_clues']=[]
 s['scene']=-1;s['round']=0;s['turn_index']=0;s['acted']=[];s['pending']=None;s['drawn_action']=None;s['events']=[]
 s['phase']='IDENTITY';s['candidate']=None;s['champion']=None;s['challengers']=[];s['replay']=None
 extra.begin(s)
 log(s,'Secret identities have been dealt. Each player received five cards.','chapter')

def next_scene(s,pid):
 ensure(pid==s['host'],'Only the host controls the shared film.')
 ensure(s['phase'] in ('IDENTITY','READY'),'Finish the current investigation round first.')
 ensure(s['scene']<4,'All five scenes have been watched.')
 s['scene']+=1;s['phase']='WATCHING';s['scene_started']=time.time();s['replay']=None
 if s.get('enhanced'):s['tension']=min(100,s.get('tension',12)+12)
 log(s,f'Scene {s["scene"]+1}: {scene_info(CASE_MAP[s["case_id"]],s["scene"])["title"]} has begun.','chapter')

def close_scene(s,pid):
 ensure(pid==s['host'],'Only the host may end the scene.')
 ensure(s['phase']=='WATCHING','The scene is not currently playing.')
 c=CASE_MAP[s['case_id']]
 new=[x for x in c['clues'] if x['scene']==s['scene'] and x['kind']!='exclusion']
 added=0
 for clue in new:
  if not any(x.get('id')==clue['id'] for x in s['public_clues']):
   s['public_clues'].append({'id':clue['id'],'text':clue['text'],'scene':s['scene'],'source':'Scene investigation'})
   added+=1
 s['phase']='DISCLOSURE';s['disclosed']=[]
 if s.get('enhanced'):s['tension']=min(100,s.get('tension',12)+8)
 log(s,f'Scene {s["scene"]+1} finished: {added} new public leads were recorded. All detectives must reveal one truthful personal fact.','chapter')

def reveal_fact(s,pid,fact_index,forced=False):
 ensure(s['phase'] in ('DISCLOSURE','TURN','CHALLENGE'),'Identity facts cannot be shared in this phase.')
 p=player(s,pid)
 ensure(p is not None,'Unknown player.')
 if s['phase']=='DISCLOSURE': ensure(pid not in s.get('disclosed',[]),'You already gave a fact in this intermission.')
 if forced:
  pend=s.get('pending')
  ensure(pend and pend['kind']=='identity' and pend['target']==pid,'No identity disclosure was requested of you.')
 else:
  ensure(s['phase']=='DISCLOSURE','Use the investigation card to request a personal fact.')
 facts=PEOPLE_MAP[p['identity']]['facts']
 ensure(isinstance(fact_index,int) and 0<=fact_index<len(facts),'Unknown personal fact.')
 text=facts[fact_index]
 p['revelations'].append(fact_index)
 log(s,f'{p["name"]} revealed a personal fact: “{text}”','identity')
 if forced:
  s['pending']=None
  finish_turn(s)
 else:
  s['disclosed'].append(pid)
  if len(s['disclosed'])==len(s['players']):
   if s.get('enhanced') and s['scene'] in (1,3):
    extra.begin_ballot(s)
    log(s,'A crossroads: everyone must vote on the next investigative lead.','chapter')
   else:
    s['phase']='TURN';s['round']+=1;s['acted']=[];s['turn_index']=0
    log(s,'The personal-fact round is complete. Investigation turns begin.','chapter')

def eligible_cards(p): return [x for x in p['hand'] if x.startswith(('C:','I:'))]

def draw(s,pid):
 ensure(s['phase']=='TURN','You cannot draw right now.')
 ensure(is_my_turn(s,pid),'It is not your turn.')
 ensure(not s['pending'],'Resolve the pending request first.')
 ensure(not s['drawn_action'],'Play the investigation card you just drew.')
 p=player(s,pid)
 ensure(not any(x.startswith('A:') for x in p['hand']),'You must play an investigation card in your hand instead of drawing.')
 if not s['deck']:
  s['deck']=s['discard'][:];s['discard']=[]
  random.SystemRandom().shuffle(s['deck'])
 ensure(s['deck'],'The card deck is empty.')
 card=s['deck'].pop()
 p['hand'].append(card)
 log(s,f'{p["name"]} drew a card.','turn')
 if card.startswith('A:'):
  s['drawn_action']=card
  log(s,f'{p["name"]} drew an investigation action and must play it immediately.','turn')
 else: finish_turn(s)

def pass_turn(s,pid):
 ensure(s['phase']=='TURN','No investigation turn is in progress.')
 ensure(is_my_turn(s,pid),'It is not your turn.')
 ensure(not s['pending'] and not s['drawn_action'],'Resolve the pending card first.')
 p=player(s,pid)
 ensure(not any(x.startswith('A:') for x in p['hand']),'You must play your investigation card.')
 ensure(not s['deck'] and not s['discard'],'Cards remain available to draw.')
 log(s,f'{p["name"]} passed: no drawable cards remain.','turn')
 finish_turn(s)

def _check_turn(s,pid):
 ensure(s['phase']=='TURN','The game is not in an action round.')
 ensure(is_my_turn(s,pid),'It is not your turn.')
 ensure(not s['pending'],'Resolve the pending response first.')

def play(s,pid,card_id,target=None,own_card=None):
 _check_turn(s,pid)
 p=player(s,pid)
 ensure(card_id in p['hand'] and card_id.startswith('A:'),'Investigation card is not in your hand.')
 if s['drawn_action']:ensure(card_id==s['drawn_action'],'Play the card you just drew.')
 else:ensure(not s['drawn_action'],'Must play the freshly drawn action.')
 kind=card_id.split(':')[1]
 ensure(kind in ACTION_MAP,'Unknown action.')
 p['hand'].remove(card_id);s['discard'].append(card_id);s['drawn_action']=None
 log(s,f'{p["name"]} played “{ACTION_MAP[kind]["name"]}”.','turn')
 q=player(s,target) if target else None
 if kind in ('public_reveal','steal','request','identity'):
  ensure(q is not None and q['id']!=pid,'Choose another player.')
  if kind=='steal':
   choices=eligible_cards(q)
   if choices:
    stolen=random.SystemRandom().choice(choices);q['hand'].remove(stolen);p['hand'].append(stolen)
    log(s,f'{p["name"]} took a private card from {q["name"]}.','turn')
   else: log(s,f'{q["name"]} had no eligible cards.','turn')
   finish_turn(s)
  elif kind=='identity':
   s['pending']={'kind':'identity','actor':pid,'target':target}
   log(s,f'{q["name"]} must disclose one truthful personal fact.','identity')
  elif eligible_cards(q):
   s['pending']={'kind':kind,'actor':pid,'target':target}
   log(s,f'{q["name"]} must choose an eligible card.','turn')
  else:
   log(s,f'{q["name"]} holds no eligible cards.','turn');finish_turn(s)
 elif kind=='bury':
  if own_card in p['hand'] and own_card.startswith(('C:','I:')):
   p['hand'].remove(own_card);s['buried'].append(own_card)
   log(s,f'{p["name"]} concealed one private card.','turn')
  finish_turn(s)
 elif kind=='replay':
  s['replay']=s['scene'];log(s,f'{p["name"]} requested a replay of scene {s["scene"]+1}.','chapter');finish_turn(s)
 else:finish_turn(s)

def respond(s,pid,card_id=None,fact_index=None):
 pend=s.get('pending')
 ensure(pend is not None and pend['target']==pid,'No response is due from you.')
 if pend['kind']=='identity': return reveal_fact(s,pid,int(fact_index),forced=True)
 p=player(s,pid)
 ensure(card_id in eligible_cards(p),'Choose an eligible card you currently hold.')
 p['hand'].remove(card_id)
 if pend['kind']=='request':
  recipient=player(s,pend['actor']);recipient['hand'].append(card_id)
  log(s,f'{p["name"]} gave one private card to {recipient["name"]}.','turn')
 else:
  s['public_clues'].append(_public_card(s,card_id,p['name']))
  log(s,f'{p["name"]} revealed a card for all detectives.','clue')
 s['pending']=None
 finish_turn(s)

def _public_card(s,card_id,source):
 if card_id.startswith('I:'):
  p=PEOPLE_MAP[card_id.split(':')[1]]
  return {'id':card_id,'text':f'{p["name"]} is not the personal identity assigned to any active player.','scene':None,'source':source}
 c=CASE_MAP[s['case_id']];f=case_clue_fact(c,card_id[2:])
 ensure(f is not None,'Card does not belong to the selected chapter.')
 return {'id':card_id,'text':f['text'],'scene':f['scene'],'source':source}

def voluntarily_reveal(s,pid,card_id):
 # Use only for explicit revelation via an action; no free leak during your turn.
 raise GameError('Use an investigation action to reveal a card publicly.')

def finish_turn(s):
 if s['phase']!='TURN':return
 s['acted'].append(active(s)['id'])
 n=len(s['players'])
 for j in range(1,n+1):
  idx=(s['turn_index']+j)%n
  if not s['players'][idx]['eliminated'] and s['players'][idx]['id'] not in s['acted']:
   s['turn_index']=idx;return
 if all(p['eliminated'] for p in s['players']):
  s['phase']='ENDED';log(s,'Every detective has been eliminated. Case sealed.','result');return
 if s['scene']<4:
  s['phase']='READY';s['drawn_action']=None
  log(s,'Investigation round complete. Host may start the next scene.','chapter')
 else:
  s['round']+=1;s['acted']=[];s['turn_index']=next((i for i,p in enumerate(s['players']) if not p['eliminated']),0)
  log(s,'Final investigation round: take turns gathering clues or making accusations.','turn')

def _normalized(murders):
 return sorted(tuple(row.get(x) for x in ('murderer','victim','room','weapon')) for row in murders)

def accuse(s,pid,murders,identities):
 ensure(s['phase'] in ('TURN','CHALLENGE'),'An accusation is only available on your turn.')
 ensure(is_my_turn(s,pid),'It is not your turn.')
 ensure(s['scene']>=1,'Wait until at least two scenes have been investigated.')
 ensure(not s['pending'],'Complete the requested response first.')
 p=player(s,pid);ensure(not p['eliminated'],'Eliminated detectives cannot accuse.')
 case=CASE_MAP[s['case_id']]
 ensure(isinstance(murders,list) and len(murders)==case['murder_count'],'Your accusation must address every death.')
 for item in murders:
  ensure(all(item.get(k) for k in ('murderer','victim','room','weapon')),'Complete each murder row.')
 others=[x for x in s['players'] if x['id']!=pid]
 ensure(isinstance(identities,dict) and all(identities.get(x['id']) for x in others),'Name every rival identity.')
 correctly_solved=_normalized(murders)==_normalized(case['murders'])
 if not correctly_solved:
  p['eliminated']=True;p['accused']=True
  log(s,f'{p["name"]} made an incorrect murder accusation and is out of contention.','result')
  if s['phase']=='CHALLENGE': advance_challenge(s)
  else: finish_turn(s)
  return {'correct_murders':False,'won':False}
 correct_ids=all(identities.get(x['id'])==x['identity'] for x in others)
 if correct_ids:
  s['champion']=pid;s['phase']='ENDED';s['pending']=None
  if s.get('enhanced'):p['score']=p.get('score',0)+50
  log(s,f'{p["name"]} solved every death AND named every hidden identity. Case closed!','result')
  return {'correct_murders':True,'won':True}
 if s['phase']=='CHALLENGE':
  p['accused']=True;log(s,f'{p["name"]} solved the murders but failed the rival identity test.','result');advance_challenge(s)
 else:
  s['candidate']=pid
  s['challengers']=[x['id'] for x in s['players'] if x['id']!=pid and not x['eliminated']]
  s['challenge_index']=0;s['phase']='CHALLENGE';s['drawn_action']=None;s['pending']=None
  log(s,f'{p["name"]} solved all murders, but named at least one identity incorrectly. Rivals have ONE chance to challenge.','result')
  if not s['challengers']:advance_challenge(s)
 return {'correct_murders':True,'won':False}

def advance_challenge(s):
 s['challenge_index']+=1
 if s['challenge_index']>=len(s['challengers']):
  s['champion']=s['candidate'];s['phase']='ENDED'
  if s.get('enhanced'):player(s,s['candidate'])['score']+=50
  candidate=player(s,s['candidate'])
  log(s,f'{candidate["name"]} held the claim after the final challenge round and wins.','result')

def pass_challenge(s,pid):
 ensure(s['phase']=='CHALLENGE' and is_my_turn(s,pid),'It is not your challenge turn.')
 log(s,f'{player(s,pid)["name"]} declined the final challenge.','turn');advance_challenge(s)

def save_notes(s,pid,notes=None,marks=None):
 p=player(s,pid)
 ensure(p is not None,'Unknown player')
 if notes is not None:
  ensure(isinstance(notes,dict) and len(str(notes))<12000,'Notes too long.')
  p['notes']=notes
 if marks is not None:
  ensure(isinstance(marks,dict) and len(str(marks))<24000,'Marks too long.')
  p['marks']=marks

def _card_view(s,card):
 if card.startswith('C:'):
  f=case_clue_fact(CASE_MAP[s['case_id']],card[2:]);return {'id':card,'type':'clue','title':f'Clue #{f["number"]:02d}','text':f['text'],'scene':f['scene']+1}
 if card.startswith('I:'):
  p=PEOPLE_MAP[card.split(':')[1]];return {'id':card,'type':'identity','title':f'Unassigned: {p["name"]}','text':f'{p["name"]} is not among the active players.','scene':None}
 action=ACTION_MAP[card.split(':')[1]]
 return {'id':card,'type':'action','action':action['kind'],'title':action['name'],'text':action['description'],'scene':None}

def view(s,pid):
 p=player(s,pid)
 ensure(p is not None,'Unknown player.')
 c=CASE_MAP[s['case_id']]
 scene=scene_info(c,s['scene']) if s['scene']>=0 else None
 private={'identity':p['identity'],'facts':PEOPLE_MAP[p['identity']]['facts'] if p['identity'] else [],
          'hand':[_card_view(s,x) for x in p['hand']],'notes':p['notes'],'marks':p['marks'],
          'revelations':p['revelations'],'eliminated':p['eliminated'],'accused':p['accused']}
 roster=[{'id':x['id'],'name':x['name'],'eliminated':x['eliminated'],'card_count':len(x['hand']),
         'disclosed':x['id'] in s.get('disclosed',[]),'is_host':x['id']==s['host'],'is_self':x['id']==pid} for x in s['players']]
 # Truth and other players' identities intentionally omitted until game ends.
 output={'code':s['code'],'revision':s['revision'],'phase':s['phase'],'host':s['host'], 'me':pid,'is_host':pid==s['host'],
   'roster':roster,'case':{k:v for k,v in c.items() if k not in ('clues','murders')},'scene':scene,'scene_started':s['scene_started'],
   'turn_player':active(s)['id'] if active(s) else None,'round':s['round'],'deck_remaining':len(s['deck']),'discard_remaining':len(s['discard']),
   'public_clues':s['public_clues'],'events':s['events'][-30:],'pending':s['pending'], 'drawn_action':s['drawn_action'] if s['drawn_action'] in p['hand'] else None,
   'replay':s['replay'],'candidate':s['candidate'],'champion':s['champion'],'private':private}
 output.update(extra.projection(s,pid))
 if s['phase']=='ENDED':
  output['solution']=[{**x} for x in c['murders']]
  output['identities']={x['id']:x['identity'] for x in s['players']}
 return output


def public_view(s):
 """Safe read-only projection for a television; never includes hands, identities or case truth."""
 c=CASE_MAP[s['case_id']]
 scene=scene_info(c,s['scene']) if s['scene']>=0 else None
 result={'code':s['code'],'revision':s['revision'],'phase':s['phase'],'case':{k:v for k,v in c.items() if k not in ('murders','clues')},
  'scene':scene,'scene_started':s['scene_started'],'public_clues':s['public_clues'],
  'roster':[{'id':p['id'],'name':p['name'],'eliminated':p['eliminated']} for p in s['players']],
  'active_player':active(s)['id'] if active(s) else None,'events':s['events'][-15:],
  'champion':s['champion'],'challenge':s['phase']=='CHALLENGE'}
 result.update(extra.projection(s,None,public=True))
 if s['phase']=='ENDED':
  result['solution']=[{**m} for m in c['murders']]
  result['identities']={p['id']:p['identity'] for p in s['players']}
 return result
