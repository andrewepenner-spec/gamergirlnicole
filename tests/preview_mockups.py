from pathlib import Path
import asyncio, json, base64, re
from playwright.async_api import async_playwright
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import engine, enhancements as ex
from server.content import public_catalog
ROOT=Path(__file__).resolve().parents[1]
s,p=engine.make_room('ABCDE','Ada')
q=engine.join(s,'Byron')
ex.configure(s,p['id'],True)
fixtures={}
fixtures['lobby']=engine.view(s,p['id'])
engine.start(s,p['id']);engine.next_scene(s,p['id'])
fixtures['film']=engine.view(s,p['id'])
engine.close_scene(s,p['id']);engine.reveal_fact(s,p['id'],0);engine.reveal_fact(s,q['id'],0)
fixtures['tools']=engine.view(s,p['id'])
for x in fixtures.values():
 if x.get('scene'):
  asset=x['scene']['image'].split('/')[-1]
  img=(ROOT/'web/assets'/asset).read_bytes()
  x['scene']['image']='data:image/webp;base64,'+base64.b64encode(img).decode()
js=(ROOT/'web/main.js').read_text().replace("session:JSON.parse(localStorage.getItem('mystery.session')||'null')","session:null")
assert js.endswith('init();\n')
js=js[:js.rfind('init();')]
styles=(ROOT/'web/styles.css').read_text()
styles=re.sub(r"@import url\('[^']+'\);",'',styles)
for asset in sorted((ROOT/'web/assets').glob('*.webp')):
 data='data:image/webp;base64,'+base64.b64encode(asset.read_bytes()).decode()
 styles=styles.replace('/assets/'+asset.name,data)
async def run():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.set_content('<html><head><style>'+styles+'</style></head><body><div id="app"></div><div id="toast"></div></body></html>')
  await page.add_script_tag(content=js)
  cat=json.dumps(public_catalog())
  for key,room in fixtures.items():
   await page.evaluate('(payload)=>{state.catalog=payload.catalog;state.room=payload.room;state.screen="auto";renderApp();}', {'catalog':public_catalog(),'room':room})
   await page.wait_for_timeout(320)
   await page.screenshot(path=str(ROOT/'docs'/('preview-'+key+'.png')),full_page=True)
   print(key,'heading:',await page.locator('.page-heading h2, .director-lobby h3').all_text_contents(), 'errors:',len(errors))
  await page.locator('.nav [data-nav="notebook"]').click()
  print('notebook text',await page.locator('.page-heading h2').inner_text())
  phone=await browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
  phone.on('pageerror',lambda e:errors.append(str(e)))
  await phone.set_content('<html><head><style>'+styles+'</style></head><body><div id="app"></div><div id="toast"></div></body></html>')
  await phone.add_script_tag(content=js)
  await phone.evaluate('(payload)=>{state.catalog=payload.catalog;state.room=payload.room;state.screen="auto";renderApp();}', {'catalog':public_catalog(),'room':fixtures['film']})
  await phone.wait_for_timeout(320)
  await phone.screenshot(path=str(ROOT/'docs'/'preview-mobile.png'),full_page=True)
  print('mobile challenge present?',await phone.locator('.scene-challenge .choice-tile').count(),'errors',errors)
  await browser.close()
asyncio.run(run())
