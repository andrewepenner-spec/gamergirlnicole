"""Director's Cut gameplay: observation challenges, group choices and detective tools.
Only server-side projections may expose a secret. Compatible with legacy classic rooms.
"""
import random
import time
from .content import CASE_MAP, PEOPLE, PEOPLE_MAP, ROOMS, WEAPONS

TALENTS = {
 'observer': {'name':'Eagle Eye','description':'Once per case, privately spot an unrevealed murder clue.'},
 'archivist': {'name':'Archivist','description':'Once per case, take a bonus private clue card without ending your turn.'},
 'interrogator': {'name':'Interrogator','description':'Once per case, learn a truthful secret fact about one other detective.'},
 'analyst': {'name':'Analyst','description':'Once per case, rule out two innocent choices for one murder dimension.'},
}
VOTES = [
 {'id':'archives','name':'Search the Archives','description':'Publish two corroborated alibis to narrow the suspect list.'},
 {'id':'surveillance','name':'Follow the Shadow','description':'Reveal one important future murder clue to everyone.'},
]

def ensure(test, message):
 if not test: raise ValueError(message)

def configure(s,pid,enhanced):
 ensure(pid==s['host'],'Only the host may set game mode.')
 ensure(s['phase']=='LOBBY','Change the game mode before starting.')
 ensure(isinstance(enhanced,bool),'Choose a valid mode.')
 s['enhanced']=enhanced

def talent_select(s,pid,talent):
 ensure(s['phase']=='LOBBY','Choose a specialty before starting.')
 ensure(talent in TALENTS,'Unknown detective specialty.')
 p=next((p for p in s['players'] if p['id']==pid),None)
 ensure(p is not None,'Unknown detective.')
 p['talent']=talent

def begin(s):
 s['scoreboard_enabled']=bool(s.get('enhanced',False))
 s['tension']=12
 s['scene_checks']={}
 s['ballot']={}
 s['ballot_outcomes']=[]
 for p in s['players']:
  p['score']=0;p['talent_used']=False;p['private_leads']=[];p['hint_count']=0;p['observation_streak']=0;p['observations_correct']=0
  p.setdefault('talent','observer')

def challenge(s):
 """Non-answer-spoiling observation prompt using data already shown in the scene."""
 index=s['scene']
 if index<0:return None
 if index%3==0:
  owner=PEOPLE[(index*2)%len(PEOPLE)];target=owner['keepsake']
  pool=[p['keepsake'] for p in PEOPLE]
  question=f'Which keepsake did {owner["name"]} carry in this scene?'
 elif index%3==1:
  room=ROOMS[index];target=room['feature']
  pool=[r['feature'] for r in ROOMS]
  question='Which detail identified the room in the scene?'
 else:
  weapon=WEAPONS[index];target=weapon['trace']
  pool=[w['trace'] for w in WEAPONS]
  question='Which forensic trace did the ledger describe?'
 rng=random.Random(f'{s["case_id"]}:observation:{index}')
 options=rng.sample([v for v in pool if v!=target],3)+[target]
 rng.shuffle(options)
 return {'question':question,'options':options,'answer':target,'scene':index}

def observe(s,pid,choice):
 ensure(s.get('enhanced',False),'Observation challenges require Director’s Cut mode.')
 ensure(s['phase']=='WATCHING','Observations must be answered while the scene is playing.')
 p=next((x for x in s['players'] if x['id']==pid),None)
 ensure(p is not None,'Unknown detective.')
 key=str(s['scene']);checks=s.setdefault('scene_checks',{}).setdefault(key,{})
 ensure(pid not in checks,'You already submitted this scene observation.')
 prompt=challenge(s)
 ensure(isinstance(choice,str) and choice in prompt['options'],'Select an available observation.')
 correct=choice==prompt['answer']
 bonus=3 if correct and max(0,time.time()-s['scene_started'])<=25 else 0
 points=12+bonus if correct else 0
 p['score']=p.get('score',0)+points
 p['observations_correct']=p.get('observations_correct',0)+int(correct)
 p['observation_streak']=p.get('observation_streak',0)+1 if correct else 0
 checks[pid]={'choice':choice,'correct':correct,'points':points}
 return {'correct':correct,'points':points}

def begin_ballot(s):
 s['phase']='DECISION';s['ballot']={}

def _new_public(s,fact,source):
 if not fact or any(x['id']==fact['id'] for x in s['public_clues']):return False
 s['public_clues'].append({'id':fact['id'],'text':fact['text'],'scene':fact['scene'],'source':source})
 return True

def vote(s,pid,choice):
 ensure(s.get('enhanced',False) and s['phase']=='DECISION','No group decision is open.')
 ensure(choice in ('archives','surveillance'),'Choose one of the two leads.')
 ensure(any(p['id']==pid for p in s['players']),'Unknown detective.')
 ensure(pid not in s.setdefault('ballot',{}),'Your ballot has already been cast.')
 s['ballot'][pid]=choice
 p=next(p for p in s['players'] if p['id']==pid);p['score']=p.get('score',0)+4
 if len(s['ballot'])<len(s['players']):return None
 votes=s['ballot'];scores={option:sum(v==option for v in votes.values()) for option in ('archives','surveillance')}
 chosen=max(scores,key=lambda k:(scores[k],k==votes.get(s['host'])))
 c=CASE_MAP[s['case_id']]
 if chosen=='archives':
  pool=[x for x in c['clues'] if x['kind']=='exclusion' and not any(y['id']==x['id'] for y in s['public_clues'])]
  selected=pool[:2]
 else:
  pool=[x for x in c['clues'] if x['kind']!='exclusion' and x['scene']>s['scene'] and not any(p['id']==x['id'] for p in s['public_clues'])]
  selected=pool[:1]
 actual=sum(_new_public(s,x,'Group decision: '+('Archives' if chosen=='archives' else 'Surveillance')) for x in selected)
 result={'scene':s['scene'],'choice':chosen,'counts':scores,'leads':actual}
 s['ballot_outcomes'].append(result)
 s['phase']='TURN';s['round']+=1;s['acted']=[];s['turn_index']=0
 s['tension']=min(100,s.get('tension',12)+8)
 return result

def use_talent(s,pid,target=None,dimension=None,murder=0):
 ensure(s.get('enhanced',False),'Detective specialties require Director’s Cut mode.')
 ensure(s['phase'] in ('DISCLOSURE','DECISION','TURN','READY'),'Your specialty is unavailable during a scene or after the case ends.')
 p=next((x for x in s['players'] if x['id']==pid),None)
 ensure(p is not None and not p['eliminated'],'This detective cannot use a specialty.')
 ensure(not p.get('talent_used',False),'You have already used your specialty.')
 role=p.get('talent','observer');c=CASE_MAP[s['case_id']]
 if role=='observer':
  pool=[x for x in c['clues'] if x['kind']!='exclusion' and not any(y['id']==x['id'] for y in s['public_clues']) and x['id'] not in [v['id'] for v in p['private_leads']]]
  ensure(pool,'All crucial clues are already revealed.')
  fact=pool[0]
  p['private_leads'].append({'id':fact['id'],'text':fact['text'],'source':'Eagle Eye'})
 elif role=='archivist':
  pool=[card for card in s['deck'] if card.startswith('C:')]
  ensure(pool,'There are no clue cards left in the deck.')
  card=random.SystemRandom().choice(pool)
  s['deck'].remove(card);p['hand'].append(card)
 elif role=='interrogator':
  target_player=next((x for x in s['players'] if x['id']==target and x['id']!=pid),None)
  ensure(target_player is not None,'Select another detective to question.')
  known=[x['text'] for x in p['private_leads']]
  facts=PEOPLE_MAP[target_player['identity']]['facts']
  selected=next((f for f in facts if f not in known),None)
  ensure(selected is not None,'You already know every fact about this detective.')
  p['private_leads'].append({'id':f'private-identity-{target}-{len(p["private_leads"])}','text':selected,'source':'Interrogation of '+target_player['name']})
 elif role=='analyst':
  ensure(isinstance(murder,int) and 0<=murder<c['murder_count'],'Choose a numbered murder.')
  ensure(dimension in ('murderer','victim','room','weapon'),'Choose what to analyze.')
  answer=c['murders'][murder][dimension]
  candidates=PEOPLE if dimension in ('murderer','victim') else ROOMS if dimension=='room' else WEAPONS
  exclusions=[x['name'] for x in candidates if x['id']!=answer][:2]
  p['private_leads'].append({'id':f'analysis-{murder}-{dimension}','text':f'Death {murder+1}, {dimension}: eliminate {" and ".join(exclusions)}.','source':'Analyst'})
 else:raise ValueError('Unknown specialty.')
 p['talent_used']=True;p['score']=p.get('score',0)+6
 return role

def request_hint(s,pid,dimension,murder):
 ensure(s.get('enhanced',False),'Hints require Director’s Cut mode.')
 ensure(s['phase'] in ('DISCLOSURE','DECISION','TURN','READY','CHALLENGE'),'Hints are unavailable right now.')
 p=next((x for x in s['players'] if x['id']==pid),None)
 ensure(p is not None and not p['eliminated'],'Detective is not eligible.')
 ensure(p.get('hint_count',0)<2,'You have already used both hints.')
 c=CASE_MAP[s['case_id']]
 ensure(isinstance(murder,int) and 0<=murder<c['murder_count'],'Invalid death number.')
 ensure(dimension in ('murderer','victim','room','weapon'),'Invalid clue category.')
 key=f'hint-{murder}-{dimension}'
 ensure(not any(x['id']==key for x in p['private_leads']),'You already requested this hint.')
 answer=c['murders'][murder][dimension]
 candidates=PEOPLE if dimension in ('murderer','victim') else ROOMS if dimension=='room' else WEAPONS
 eliminated=[x['name'] for x in candidates if x['id']!=answer][:2]
 p['private_leads'].append({'id':key,'text':f'Death {murder+1}: {" and ".join(eliminated)} can be ruled out as {dimension}.','source':'Private hint (–8 points)'})
 p['hint_count']+=1;p['score']=p.get('score',0)-8

def projection(s,pid,public=False):
 if not s.get('enhanced',False):return {'enhanced':False}
 base={'enhanced':True,'tension':s.get('tension',12),'ballot_outcomes':s.get('ballot_outcomes',[]), 'decision_options':VOTES,
       'ballots_cast':len(s.get('ballot',{})),'observations_submitted':len(s.get('scene_checks',{}).get(str(s['scene']),{})),
       'scoreboard':[{'id':p['id'],'name':p['name'],'score':p.get('score',0),'talent':p.get('talent','observer'),'correct_observations':p.get('observations_correct',0)} for p in s['players']] if s['phase']=='ENDED' else None}
 if public:return base
 p=next(x for x in s['players'] if x['id']==pid)
 own=s.get('scene_checks',{}).get(str(s['scene']),{}).get(pid)
 ballot=s.get('ballot',{})
 base.update({'specialties':TALENTS,'my_talent':p.get('talent','observer'),'talent_used':p.get('talent_used',False),
              'my_score':p.get('score',0),'private_leads':p.get('private_leads',[]),'hints_remaining':2-p.get('hint_count',0),
              'scene_challenge':({k:v for k,v in challenge(s).items() if k!='answer'} if s['phase']=='WATCHING' else None),
              'my_observation':own,'my_vote':ballot.get(pid)})
 return base
