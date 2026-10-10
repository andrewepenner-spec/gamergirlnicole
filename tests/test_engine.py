import json
import pytest
from server import engine
from server.content import CASES,CASE_MAP,CHAPTERS,PEOPLE,ROOMS,WEAPONS,scene_info

def create():
 s,p=engine.make_room('ABCDE','Ada')
 q=engine.join(s,'Byron')
 return s,p,q

def progress_turn(s):
 p=engine.active(s)
 if not p:return
 acts=[x for x in p['hand'] if x.startswith('A:')]
 if acts:
  card=s.get('drawn_action') or acts[0]
  target=next(x for x in s['players'] if x['id']!=p['id'])
  own=engine.eligible_cards(p)
  engine.play(s,p['id'],card,target=target['id'],own_card=own[0] if own else None)
 elif s['deck'] or s['discard']:
  engine.draw(s,p['id'])
 else:
  # only possible after all 28 cards are gone; game requires an accusation here
  return 'empty'
 pend=s.get('pending')
 if pend:
  target=engine.player(s,pend['target'])
  if pend['kind']=='identity':engine.respond(s,target['id'],fact_index=0)
  else:
   eligible=engine.eligible_cards(target)
   if eligible:engine.respond(s,target['id'],card_id=eligible[0])
   else:raise AssertionError('invalid pending request')
 return None

@pytest.mark.parametrize('case_id',[x['id'] for x in CASES])
def test_eighteen_cases_playable_until_final_solved(case_id):
 s,p,q=create();engine.case_select(s,p['id'],case_id);engine.start(s,p['id'])
 assert s['phase']=='IDENTITY'
 # No private information from other players, solutions, or unrevealed clues in view.
 a=engine.view(s,p['id']);b=engine.view(s,q['id'])
 assert a['private']['identity']!=b['private']['identity']
 assert 'solution' not in a and 'identities' not in b
 assert not any(card['id'] in [item['id'] for item in a['private']['hand']] for card in b['private']['hand'])
 for i in range(5):
  engine.next_scene(s,p['id']);assert s['phase']=='WATCHING';assert s['scene']==i
  engine.close_scene(s,p['id']);assert s['phase']=='DISCLOSURE'
  engine.reveal_fact(s,p['id'],0);engine.reveal_fact(s,q['id'],0)
  assert s['phase']=='TURN'
  round_number=s['round']
  for _ in range(15):
   progress_turn(s)
   if s['phase']!='TURN' or s['round']>round_number:break
  assert s['phase']=='READY' or (i==4 and s['phase']=='TURN')
 c=CASE_MAP[case_id]
 assert s['scene']==4
 assert len(s['public_clues'])==c['murder_count']*4
 # Next eligible player can solve exactly, assuming all publicly presented evidence is understood.
 current=engine.active(s)
 guessed={x['id']:x['identity'] for x in s['players'] if x['id']!=current['id']}
 result=engine.accuse(s,current['id'],c['murders'],guessed)
 assert result['won'] is True and s['phase']=='ENDED' and s['champion']==current['id']
 assert len(engine.view(s,p['id'])['solution'])==c['murder_count']

def test_false_accusation_eliminates_without_leaking_solution():
 s,p,q=create();engine.start(s,p['id'])
 for i in range(2):
  engine.next_scene(s,p['id']);engine.close_scene(s,p['id'])
  for x in s['players']:engine.reveal_fact(s,x['id'],0)
  if i==0:
   for j in range(16):
    progress_turn(s)
    if s['phase']!='TURN':break
 c=CASE_MAP[s['case_id']]
 actor=engine.active(s)
 wrong=[dict(x) for x in c['murders']];wrong[0]['weapon']='incorrect-weapon'
 result=engine.accuse(s,actor['id'],wrong,{x['id']:x['identity'] for x in s['players'] if x['id']!=actor['id']})
 assert not result['won'] and actor['eliminated']
 assert 'solution' not in engine.view(s,actor['id'])

def test_correct_murders_wrong_identity_triggers_one_challenge():
 s,p,q=create();engine.start(s,p['id'])
 for i in range(2):
  engine.next_scene(s,p['id']);engine.close_scene(s,p['id'])
  for x in s['players']:engine.reveal_fact(s,x['id'],0)
  if i==0:
   for _ in range(16):
    progress_turn(s)
    if s['phase']!='TURN':break
 c=CASE_MAP[s['case_id']];actor=engine.active(s)
 opponent=next(x for x in s['players'] if x['id']!=actor['id'])
 bad='scarlet' if opponent['identity']!='scarlet' else 'mustard'
 res=engine.accuse(s,actor['id'],c['murders'],{opponent['id']:bad})
 assert res['correct_murders'] and not res['won'] and s['phase']=='CHALLENGE'
 assert engine.active(s)['id']==opponent['id']
 engine.pass_challenge(s,opponent['id'])
 assert s['phase']=='ENDED' and s['champion']==actor['id']

def test_18_cases_28_unique_clue_ids_per_case_and_distinct_answers():
 assert len(CASES)==18
 assert len(PEOPLE)==10 and len(ROOMS)==5 and len(WEAPONS)==5
 for c in CASES:
  assert len(c['clues'])==28
  assert len({x['id'] for x in c['clues']})==28
  assert 1<=c['murder_count']<=5
  assert len({tuple(x.values()) for x in c['murders']})==c['murder_count']
  assert set(x['scene'] for x in c['clues'] if x['kind']!='exclusion')==set(range(5)) if c['murder_count']>1 else set(range(4))
  for row in c['murders']:
   assert row['murderer']!=row['victim']
   assert any(x['id']==row['murderer'] for x in PEOPLE)
   assert any(x['id']==row['victim'] for x in PEOPLE)


def test_hidden_identities_are_never_stealable():
 s,p,q=create();engine.start(s,p['id']);before=q['identity']
 engine.next_scene(s,p['id']);engine.close_scene(s,p['id'])
 engine.reveal_fact(s,p['id'],0);engine.reveal_fact(s,q['id'],0)
 # First player may or may not have steal in hand; force a source card into their hand to test.
 card='A:steal:test';p['hand'].append(card)
 engine.play(s,p['id'],card,q['id'])
 assert q['identity']==before
 assert 'I:'+before not in p['hand']


def test_every_murder_is_deducible_from_the_released_observations():
 # Extract the relationships a rational detective can infer from costume/keepsake/room/trace.
 from server.content import PEOPLE,ROOMS,WEAPONS
 for case in CASES:
  observed=' '.join(piece for i in range(5) for piece in scene_info(case,i)['observations'])
  for n,answer in enumerate(case['murders']):
   clues=[f['text'] for f in case['clues'] if f['murder']==n]
   assert len(clues)==4
   for field,items,attribute in (
    ('murderer',PEOPLE,'trait'),('victim',PEOPLE,'keepsake'),
    ('room',ROOMS,'feature'),('weapon',WEAPONS,'trace')):
    candidates=[x['id'] for x in items if any(x[attribute] in fact for fact in clues)]
    assert candidates==[answer[field]],(case['id'],n,field,candidates)
    target=next(x for x in items if x['id']==answer[field])
    assert target[attribute] in observed
