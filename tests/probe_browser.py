import asyncio
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--no-proxy-server'])
  page=await browser.new_page()
  async def route_handler(route):
   print('ROUTE',route.request.url)
   await route.fulfill(status=200,content_type='text/html',body='<html><body><h1>Test Page</h1></body></html>')
  await page.route('**/*',route_handler)
  try:
   print('NAV',await page.goto('file:///mnt/data/clue_rebuilt/web/index.html',wait_until='domcontentloaded'))
   print('HEAD',await page.locator('h1').text_content())
  except Exception as e:print(type(e).__name__,str(e)[:300])
  await browser.close()
asyncio.run(main())
