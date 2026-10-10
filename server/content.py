"""Original scenario pack for a digital video-deduction game.
The 18 case solutions and all dialogue below are newly authored/generated.
The historic source casebook, clue wording and film are NOT included.
"""
import random
import hashlib

PEOPLE = [
  {'id':'scarlet','name':'Miss Scarlet','role':'The guest in crimson','trait':'a garnet feather','keepsake':'a silver cigarette case','facts':['I wear a garnet feather after dark.','I carry a silver cigarette case.','I insist on entering a room before everyone else.']},
  {'id':'mustard','name':'Colonel Mustard','role':'The retired officer','trait':'a brass compass pin','keepsake':'a regimental watch','facts':['A brass compass pin marks my lapel.','I keep a regimental watch.','I count each doorway before I enter.']},
  {'id':'plum','name':'Professor Plum','role':'The curious academic','trait':'a violet silk cravat','keepsake':'a folded laboratory ledger','facts':['I favor a violet silk cravat.','I own a folded laboratory ledger.','My notes are written in a cramped hand.']},
  {'id':'green','name':'Mr. Green','role':'The nervous financier','trait':'an emerald enamel cufflink','keepsake':'a monogrammed keyring','facts':['One cufflink is emerald enamel.','I possess a monogrammed keyring.','I cannot resist checking locked doors.']},
  {'id':'peacock','name':'Mrs. Peacock','role':'The sharp-tongued widow','trait':'a peacock-blue ribbon','keepsake':'a pearl-handled lorgnette','facts':['I wear a peacock-blue ribbon.','My favorite keepsake is a pearl-handled lorgnette.','I notice every change in the seating order.']},
  {'id':'white','name':'Mrs. White','role':'The keeper of the house','trait':'a white lace brooch','keepsake':'a copper recipe tin','facts':['A white lace brooch is pinned to my collar.','I keep recipes in a copper tin.','I know which floorboards are loose.']},
  {'id':'brunette','name':'Monsieur Brunette','role':'The discreet solicitor','trait':'a black onyx tiepin','keepsake':'a leather legal folio','facts':['I never remove my black onyx tiepin.','My legal folio is made of dark leather.','I make notes in red ink.']},
  {'id':'rose','name':'Madam Rose','role':'The visiting medium','trait':'a rose-gold necklace','keepsake':'a velvet tarot pouch','facts':['My necklace is rose-gold.','I carry a velvet tarot pouch.','I hear voices even after the lights go out.']},
  {'id':'gray','name':'Sergeant Gray','role':'The watchful investigator','trait':'a slate-gray armband','keepsake':'a brass police whistle','facts':['My armband is slate-gray.','I always carry a brass police whistle.','I know the railway timetable by memory.']},
  {'id':'peach','name':'Miss Peach','role':'The unexpected visitor','trait':'a peach-colored glove','keepsake':'a pressed violet letter','facts':['I wear a peach-colored glove on one hand.','I saved a pressed violet letter.','I arrived after the storm had started.']},
]
ROOMS = [
 {'id':'hall','name':'Hall','feature':'the cracked marble clock','description':'Candle smoke drifts through the grand entrance.'},
 {'id':'dining','name':'Dining Room','feature':'the twelve-place silver service','description':'A banquet for ten remains untouched.'},
 {'id':'conservatory','name':'Conservatory','feature':'the clouded glass roof','description':'Rain traces a hundred lines across the glass.'},
 {'id':'kitchen','name':'Kitchen','feature':'the blue tiled hearth','description':'Pots cool beside the enormous fireplace.'},
 {'id':'library','name':'Library','feature':'the carved walnut atlas stand','description':'Dust floats over shelves of locked books.'},
]
WEAPONS = [
 {'id':'knife','name':'Knife','trace':'a narrow sharpened blade'},
 {'id':'candlestick','name':'Candlestick','trace':'a bent brass candlestick'},
 {'id':'revolver','name':'Revolver','trace':'a spent pistol cartridge'},
 {'id':'poison','name':'Poison','trace':'a residue of bitter almond'},
 {'id':'rope','name':'Rope','trace':'a strand of twisted hemp'},
]
CHAPTERS=[
 {'id':'will','title':'The Will','color':'#9d5981','label':'BLUE DOSSIER','tagline':'A fortune changes hands, and every guest has a reason to lie.','scene_titles':['The Invitation','The Last Testament','A Cup Left Standing','Dinner at Nine','All Doors Locked'],
  'scene_texts':[
    ['The storm has washed away the bridge. Nobody is leaving tonight.','Ten guests stand beneath the portrait of a man who trusts none of them.','The house clock strikes once, though the hour is wrong.'],
    ['The solicitor places a new document before the assembled guests.','A single unsigned page has disappeared from the estate folio.','Someone turns a ring while the inheritance is read.'],
    ['Steam clouds the kitchen windows. Two cups are left beside the hearth.','A visitor pockets something small and metallic.','The cook insists the doors were shut the entire time.'],
    ['Silence settles over the long dining table.','An overturned glass interrupts a carefully practiced toast.','A shadow appears beyond the conservatory doors.'],
    ['The hall lights fail. Footsteps echo above the locked rooms.','One guest has an answer, but refuses to give it.','The butler announces that the investigation must begin.']]},
 {'id':'search','title':'The Search','color':'#6c9e8f','label':'GREEN DOSSIER','tagline':'A missing document sends the household searching its own secrets.','scene_titles':['Ashes in the Grate','The False Map','The Hidden Diary','Behind the Panel','Voices at Midnight'],
  'scene_texts':[
    ['The latest will has been burned in the study grate.','Only a corner of the seal survives.','The guests are told an older document still exists.'],
    ['A torn map shows a passage behind the library.','The hall clock rings out of time again.','A whispered bargain ends the conversation.'],
    ['A diary is uncovered behind a row of ancient novels.','A faded photograph identifies an unexpected visitor.','Someone demands the pages be returned without a word.'],
    ['An iron latch opens onto a cold stone passage.','Fresh earth stains the hem of an evening coat.','A second sealed envelope waits behind the panel.'],
    ['Candlelight sways as the guests gather in the conservatory.','A voice repeats a phrase nobody admits to knowing.','In the confusion, a single key goes missing.']]},
 {'id':'secrets','title':'The Secrets','color':'#bd675b','label':'RED DOSSIER','tagline':'Blackmail, old loyalties and a final night of impossible alibis.','scene_titles':['The Third Envelope','The Blackmail List','A Family Portrait','The Last Alibi','The Reckoning'],
  'scene_texts':[
    ['A third envelope is opened in the hall.','Inside is a list of private debts and borrowed names.','Every guest has something to lose.'],
    ['The dining room has become an improvised courtroom.','Nobody agrees who saw the missing letter last.','A match goes out beside a half-written confession.'],
    ['An altered portrait reveals a name beneath the paint.','Old family ties are not what they appear to be.','Someone asks that the photograph never be shown again.'],
    ['The final alibis fall apart one by one.','A metallic sound comes from the empty kitchen.','An impossible journey is suddenly explained.'],
    ['All ten are summoned to the library.','The storm ends, but the accusations do not.','The answer has been in the evidence from the beginning.']]},
]
CASE_TITLES=[
 ['A Poisoned Promise','A Matter of Estate','The Uninvited Guest','The Silent Toast','Inheritance of Shadows','Ten Minutes to Midnight'],
 ['The Vanishing Folio','Ink and Ashes','The Mirror Passage','The Locked Diary','The False Heiress','A House of Witnesses'],
 ['The Unsigned Threat','The Last Photograph','The Peacock Affair','Secrets Under Glass','The Fifth Confession','The Final Testament'],
]

def _random(seed):
 return random.Random(int(hashlib.sha256(seed.encode()).hexdigest(),16))

def make_cases():
 result=[]
 for ch_idx,chapter in enumerate(CHAPTERS):
  for case_idx in range(6):
   rng=_random(chapter['id']+':'+str(case_idx))
   count=[1,2,2,3,4,5][case_idx]
   ids=rng.sample(range(10),count*2)
   locations=rng.sample(ROOMS,count)
   weapons=rng.sample(WEAPONS,count)
   murders=[]
   facts=[]
   for n in range(count):
    killer=PEOPLE[ids[n]]; victim=PEOPLE[ids[n+count]]; room=locations[n]; weapon=weapons[n]
    murders.append({'murderer':killer['id'],'victim':victim['id'],'room':room['id'],'weapon':weapon['id']})
    ref=f'Death {n+1}'
    facts.extend([
      {'kind':'murderer','murder':n,'text':f'{ref}: the killer wore {killer["trait"]}.', 'scene':n%5},
      {'kind':'victim','murder':n,'text':f'{ref}: the victim owned {victim["keepsake"]}.', 'scene':(n+1)%5},
      {'kind':'room','murder':n,'text':f'{ref}: the fatal act occurred beside {room["feature"]}.', 'scene':(n+2)%5},
      {'kind':'weapon','murder':n,'text':f'{ref}: investigators found {weapon["trace"]} at the scene.', 'scene':(n+3)%5},
    ])
   # Every chapter's 28 physical clue cards has one fact for each of the 6 cases.
   nonkillers=[p for p in PEOPLE if p['id'] not in {x['murderer'] for x in murders}]
   while len(facts)<28:
    p=nonkillers[(len(facts)-count*4)%len(nonkillers)]
    facts.append({'kind':'exclusion','murder':None,'text':f'Corroborated alibi: the wearer of {p["trait"]} did not commit a murder in this case.', 'scene':len(facts)%5})
   case={'id':f'{chapter["id"]}-{case_idx+1}', 'chapter':chapter['id'],'chapter_index':ch_idx,'number':case_idx+1,
     'title':CASE_TITLES[ch_idx][case_idx], 'murders':murders,'murder_count':count,'difficulty':['Novice','Detective','Detective','Expert','Master','Master'][case_idx],
     'description':f'{chapter["tagline"]} A case involving {count} unexplained death'+('' if count==1 else 's')+'.',
     'clues':[{**f,'id':f'{chapter["id"]}-clue-{idx+1:02d}', 'number':idx+1} for idx,f in enumerate(facts)]}
   result.append(case)
 return result

CASES=make_cases()
CASE_MAP={c['id']:c for c in CASES}
CHAPTER_MAP={c['id']:c for c in CHAPTERS}
PEOPLE_MAP={p['id']:p for p in PEOPLE}
ROOM_MAP={p['id']:p for p in ROOMS}
WEAPON_MAP={p['id']:p for p in WEAPONS}
ACTIONS = [
 {'id':'expose','name':'Public testimony','description':'Ask another player to reveal a fact card to everyone.','kind':'public_reveal'},
 {'id':'steal','name':'An unseen hand','description':'Take a random clue or unassigned identity card from another player.','kind':'steal'},
 {'id':'request','name':'The exchange','description':'A chosen player gives you an eligible card of their choice.','kind':'request'},
 {'id':'bury','name':'Buried evidence','description':'Remove one of your clue cards from circulation.','kind':'bury'},
 {'id':'replay','name':'One more look','description':'Replay the most recently viewed scene.','kind':'replay'},
 {'id':'identity','name':'Tell me one thing','description':'Force another player to disclose a truthful personal fact.','kind':'identity'},
]
ACTION_MAP={x['id']:x for x in ACTIONS}

def public_catalog():
 return {'people':[{k:v for k,v in p.items() if k not in ('facts',)} for p in PEOPLE], 'rooms':ROOMS,'weapons':WEAPONS,
  'chapters':[{k:v for k,v in ch.items() if k not in ('scene_texts',)} for ch in CHAPTERS],
  'cases':[{k:v for k,v in c.items() if k not in ('murders','clues')} for c in CASES], 'actions':ACTIONS}

def scene_info(case, scene_idx):
 ch=CHAPTER_MAP[case['chapter']]
 # Observations are public after the scene. By the end, every identifying prop is observable.
 observations=[]
 for p in PEOPLE[scene_idx*2:scene_idx*2+2]:
  observations.append(f'{p["name"]} wears {p["trait"]} and carries {p["keepsake"]}.')
 observations.append(f'The {ROOMS[scene_idx]["name"]} contains {ROOMS[scene_idx]["feature"]}.')
 observations.append(f'The forensic ledger describes {WEAPONS[scene_idx]["trace"]} as the trace of a {WEAPONS[scene_idx]["name"]}.')
 return {'index':scene_idx,'title':ch['scene_titles'][scene_idx], 'location':ROOMS[scene_idx]['name'], 'lines':ch['scene_texts'][scene_idx],
         'observations':observations,'image':f'/assets/scene-{(scene_idx+case["chapter_index"]*2)%6}.webp'}

def case_clue_fact(case,card_id):
 return next((x for x in case['clues'] if x['id']==card_id),None)

def all_card_ids(chapter_id):
 return [f'{chapter_id}-clue-{i+1:02d}' for i in range(28)]
